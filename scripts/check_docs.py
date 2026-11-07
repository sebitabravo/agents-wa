#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Structural and citation checks for the agents-wa guide.

Run from the repository root:

    python3 scripts/check_docs.py
    python3 scripts/check_docs.py --repos-root /path/to/parent-of-the-four-repos
    python3 scripts/check_docs.py --no-repo-check

The last form is for community clones that do not have the four case-study
repositories next to this one: structure, links and SPDX are still verified,
and citation resolution is reported as skipped. By default the run is strict:
a missing case-study repository is a hard failure, not a skip.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

EXPECTED_DOCS = [
    "00-introduccion.md",
    "01-principios-fail-closed.md",
    "02-stack-base.md",
    "03-system-prompts.md",
    "04-orquestacion-tools.md",
    "05-datos-rag.md",
    "06-canales-memoria.md",
    "07-evaluacion.md",
    "08-seguridad.md",
    "09-observabilidad.md",
    "10-costos-modelos.md",
    "11-despliegue.md",
    "12-arquitecturas.md",
    "13-casos-de-estudio.md",
    "14-plantillas.md",
    "15-anti-patrones.md",
    "16-comunidad.md",
    "A-glosario.md",
    "B-comparativas.md",
    "C-referencias.md",
]

EXPECTED_LICENSES = [
    "LICENSE",
    "NOTICE",
    "LICENSES/CC-BY-SA-4.0.txt",
    "LICENSES/MIT.txt",
]

# Repository directory names as they exist on disk.
REPO_DIRS = ["AgroVoz", "copiloto-recepcion", "ManttoAI", "Wenuke"]
# Short names the prose uses, mapped to directory names.
REPO_ALIASES = {"copiloto": "copiloto-recepcion"}
# Bases without a line number are prose mentions, not evidence.
CITATION = re.compile(
    r"(?<![\w/.-])([A-Za-z0-9_./-]+\.(?:py|yml|yaml|json|toml|ini|md|txt|cfg|js|jsx|ts|tsx))"
    r":(\d+)((?:[,-]\d+)*)"
)
LINK = re.compile(r"\]\(([^)#]+\.md)(?:#[^)]*)?\)")
SPDX = re.compile(r"SPDX-License-Identifier:\s*(.+)")
ABSOLUTE = re.compile(r"/Users/[^\s`)]+")
PENDING = re.compile(r"\b(?:TODO|TBD|FIXME|XXX)\b")

# Directories skipped when indexing the case-study repositories.
IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".next",
    "dist",
    "build",
    ".ruff_cache",
    ".playwright-mcp",
}


def build_index(repos_root: Path) -> dict[str, dict[str, Path]]:
    """Map repository name -> {relative path: absolute path}.

    Relative paths are normalized to POSIX separators so the index and the
    citation text agree on every platform.
    """
    index: dict[str, dict[str, Path]] = {}
    for name in REPO_DIRS:
        base = repos_root / name
        if not base.is_dir():
            continue
        files: dict[str, Path] = {}
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
            for filename in filenames:
                full = Path(dirpath) / filename
                files[full.relative_to(base).as_posix()] = full
        index[name] = files
    return index


def named_repo(path: str) -> str | None:
    """Return the repository a cited path explicitly names, or None.

    The first segment names a repository when it matches a directory name or
    an alias. Anything else (``backend/...``, ``README.md``) leaves the
    repository to the surrounding section context.
    """
    prefix = path.split("/", 1)[0]
    if prefix in REPO_DIRS or prefix in REPO_ALIASES:
        return REPO_ALIASES.get(prefix, prefix)
    return None


def resolve(path: str, index: dict[str, dict[str, Path]]) -> list[tuple[str, str]]:
    """Resolve a cited path to (repository, relative path) candidates.

    A leading repository name (or its alias) pins the resolution to that one
    repository, and its cited range must fit that repository's file. Without
    one, the path is searched in every repository: a unique hit is enough,
    exactly as the guide's evidence convention allows inside a case-study
    section; more than one hit must be disambiguated with a prefix.
    """
    repo = named_repo(path)
    candidate = path.split("/", 1)[1] if repo and "/" in path else path
    hits: list[tuple[str, str]] = []
    for name, files in index.items():
        if repo and name != repo:
            continue
        lookup = candidate if repo else path
        if lookup in files:
            hits.append((name, lookup))
            continue
        suffixes = [rel for rel in files if rel.endswith("/" + lookup)]
        if suffixes:
            hits.append((name, sorted(suffixes, key=len)[0]))
    return hits


def line_count(path: Path) -> int:
    return sum(1 for _ in path.open("rb"))


def exceeds(path: Path, spec: str) -> int | None:
    """Return the offending line when the cited range runs past the file."""
    last = max(int(part) for part in re.findall(r"\d+", spec))
    total = line_count(path)
    return last if last > total else None


def check_citations(
    files: list[Path], repos_root: Path, index: dict[str, dict[str, Path]]
) -> tuple[list[str], list[str], list[str], list[str]]:
    """Return defects for every citation in the guide."""
    unresolved: list[str] = []
    out_of_range: list[str] = []
    ambiguous: list[str] = []
    abbreviated: list[str] = []
    for path in files + [ROOT / "README.md"]:
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            for match in CITATION.finditer(line):
                cited, start, rest = match.group(1), match.group(2), match.group(3)
                if cited.startswith("/"):
                    continue
                if cited.startswith("http"):
                    continue
                where = f"{path.relative_to(ROOT)}:{lineno}"
                if ".../" in cited:
                    abbreviated.append(f"{where} -> {cited}")
                    continue
                hits = resolve(cited, index)
                if not hits:
                    unresolved.append(f"{where} -> {cited}")
                    continue
                if named_repo(cited) is None and len(hits) > 1:
                    # Several repositories hold this path and the citation does
                    # not name one: report it instead of attributing it to
                    # whichever candidate happens to fit the cited range.
                    ambiguous.append(
                        f"{where} -> {cited} ({', '.join(sorted({h[0] for h in hits}))})"
                    )
                    continue
                # Exactly one candidate, or pinned to the repository the
                # citation names: the cited range must fit that exact file.
                name, rel = hits[0]
                size = line_count(index[name][rel])
                bad = exceeds(index[name][rel], start + rest)
                if bad is not None:
                    out_of_range.append(
                        f"{where} -> {name}/{rel}:{start}{rest} (archivo de "
                        f"{size} lineas, se cita {bad})"
                    )
    return unresolved, out_of_range, ambiguous, abbreviated


def main() -> int:
    parser = argparse.ArgumentParser(description="agents-wa docs check")
    parser.add_argument(
        "--repos-root",
        default=os.environ.get("AGENTS_WA_REPOS_ROOT", str(ROOT.parent)),
        help="directory that contains AgroVoz, copiloto-recepcion, ManttoAI, Wenuke",
    )
    parser.add_argument(
        "--no-repo-check",
        action="store_true",
        help="skip citation resolution when the case-study repos are absent",
    )
    args = parser.parse_args()

    errors: list[str] = []
    files = sorted(DOCS.glob("*.md"))
    names = {p.name for p in files}
    missing = [n for n in EXPECTED_DOCS if n not in names]
    extra = [n for n in names if n not in EXPECTED_DOCS]
    if missing:
        errors.append(f"Faltan documentos: {', '.join(missing)}")
    if extra:
        errors.append(f"Documentos no esperados: {', '.join(extra)}")

    missing_licenses = [p for p in EXPECTED_LICENSES if not (ROOT / p).exists()]
    if missing_licenses:
        errors.append(f"Faltan archivos de licencia: {', '.join(missing_licenses)}")

    total_lines = 0
    broken: list[str] = []
    absolute: list[str] = []
    pending: list[str] = []
    no_spdx: list[str] = []

    for path in files + [ROOT / "README.md"]:
        text = path.read_text(encoding="utf-8")
        if path.parent == DOCS:
            total_lines += len(text.splitlines())
        for match in LINK.finditer(text):
            target = (path.parent / match.group(1)).resolve()
            if not target.exists():
                broken.append(f"{path.relative_to(ROOT)} -> {match.group(1)}")
        if ABSOLUTE.search(text):
            absolute.append(str(path.relative_to(ROOT)))
        if PENDING.search(text):
            pending.append(str(path.relative_to(ROOT)))
        if not SPDX.search(text):
            no_spdx.append(str(path.relative_to(ROOT)))

    repos_root = Path(args.repos_root)
    index = build_index(repos_root)

    counts_text = "".join(f.read_text(encoding="utf-8") for f in files) + (
        ROOT / "README.md"
    ).read_text(encoding="utf-8")
    citations = len(CITATION.findall(counts_text))

    missing_repos = [name for name in REPO_DIRS if name not in index]
    if args.no_repo_check:
        unresolved, out_of_range, ambiguous, abbreviated = [], [], [], []
        skipped = True
    elif missing_repos:
        errors.append(
            f"Faltan repositorios en {repos_root}: {', '.join(missing_repos)}"
        )
        unresolved, out_of_range, ambiguous, abbreviated = [], [], [], []
        skipped = True
    else:
        unresolved, out_of_range, ambiguous, abbreviated = check_citations(
            files, repos_root, index
        )
        skipped = False

    if broken:
        errors.append(f"Enlaces internos rotos: {len(set(broken))}")
        errors.extend(f"  {item}" for item in sorted(set(broken)))
    if absolute:
        errors.append(f"Rutas absolutas: {', '.join(absolute)}")
    if pending:
        errors.append(f"Marcadores pendientes: {', '.join(pending)}")
    if no_spdx:
        errors.append(f"Archivos sin SPDX: {', '.join(no_spdx)}")
    if unresolved:
        errors.append(f"Citas sin archivo en los repos: {len(unresolved)}")
        errors.extend(f"  {item}" for item in unresolved)
    if out_of_range:
        errors.append(f"Citas fuera de la longitud del archivo: {len(out_of_range)}")
        errors.extend(f"  {item}" for item in out_of_range)
    if ambiguous:
        errors.append(f"Citas ambiguas sin prefijo de proyecto: {len(ambiguous)}")
        errors.extend(f"  {item}" for item in ambiguous)
    if abbreviated:
        errors.append(f"Citas con ruta abreviada '.../': {len(abbreviated)}")
        errors.extend(f"  {item}" for item in abbreviated)

    readme_lines = len((ROOT / "README.md").read_text(encoding="utf-8").splitlines())

    print("== agents-wa docs check ==")
    if args.no_repo_check:
        print("Modo: solo estructura (--no-repo-check)")
    else:
        print("Modo: citas verificadas")
    print(f"Documentos: {len(files)}/{len(EXPECTED_DOCS)}")
    print(f"Lineas en docs/: {total_lines}")
    print(f"Lineas en README.md: {readme_lines}")
    print(f"Citas path:line: {citations}")
    print(f"Enlaces rotos: {len(set(broken))}")
    print(f"Rutas absolutas: {len(absolute)}")
    print(f"Marcadores pendientes: {len(pending)}")
    print(f"Archivos sin SPDX: {len(no_spdx)}")
    print(
        f"Archivos de licencia: {len(EXPECTED_LICENSES) - len(missing_licenses)}/"
        f"{len(EXPECTED_LICENSES)}"
    )
    if skipped:
        print("Resolucion de citas: omitida (repos no disponibles)")
    else:
        resolved = citations - len(unresolved) - len(abbreviated)
        print(f"Citas resueltas: {resolved}/{citations}")
        print(f"Citas abreviadas: {len(abbreviated)}")
        print(f"Citas fuera de rango: {len(out_of_range)}")
        print(f"Citas ambiguas sin prefijo: {len(ambiguous)}")

    if errors:
        print("\nERRORES:")
        for error in errors:
            print(f"- {error}")
        return 1

    if skipped:
        print("\nOK: estructura, enlaces, rutas, SPDX y licencias.")
        print("Sin verificar: resolucion de citas (faltan los repos de casos de estudio).")
        return 0

    print("\nOK: estructura, enlaces, citas, rutas, SPDX y licencias.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
