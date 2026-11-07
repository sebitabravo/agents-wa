# SPDX-License-Identifier: MIT
"""Tests for scripts/check_docs.py.

The verification gate must fail closed: a missing case-study repository, a
citation that names the wrong repository, an ambiguous bare name, an
abbreviated citation and a broken link are all hard errors.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
SPDX = "SPDX-License-Identifier: MIT"


def load_check_docs():
    """Import scripts/check_docs.py without installing a package."""
    spec = importlib.util.spec_from_file_location(
        "check_docs_under_test", SCRIPTS / "check_docs.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_repo(repos_root: Path, name: str, files: dict[str, int]) -> None:
    """Create a fake case-study repo where each file has `lines` lines."""
    base = repos_root / name
    base.mkdir(parents=True)
    for rel, lines in files.items():
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "\n".join(f"linea {i}" for i in range(1, lines + 1)) + "\n",
            encoding="utf-8",
        )


def make_guide(tmp_path: Path, docs_text: str):
    """Build a minimal guide tree and point the loaded module at it."""
    root = tmp_path / "guia"
    docs = root / "docs"
    docs.mkdir(parents=True)
    (docs / "00-introduccion.md").write_text(
        f"{SPDX}\n{docs_text}", encoding="utf-8"
    )
    (root / "README.md").write_text(f"{SPDX}\n", encoding="utf-8")
    (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    module = load_check_docs()
    module.ROOT = root
    module.DOCS = docs
    module.EXPECTED_DOCS = ["00-introduccion.md"]
    module.EXPECTED_LICENSES = ["LICENSE"]
    module.REPO_DIRS = ["Alfa", "Beta"]
    module.REPO_ALIASES = {"AlfaCorto": "Alfa"}
    return module, root, tmp_path / "repos"


def run_check(monkeypatch, capsys, module, repos_root: Path, *flags: str):
    monkeypatch.setattr(
        sys, "argv", ["check_docs.py", "--repos-root", str(repos_root), *flags]
    )
    code = module.main()
    return code, capsys.readouterr().out


def test_missing_repos_fail_closed(tmp_path, monkeypatch, capsys):
    """Without --no-repo-check, one missing repo is a hard failure."""
    module, _root, repos_root = make_guide(tmp_path, "Guia vacia.\n")
    write_repo(repos_root, "Alfa", {"src/app.py": 10})
    code, out = run_check(monkeypatch, capsys, module, repos_root)
    assert code == 1
    assert "Faltan repositorios" in out
    assert "Beta" in out
    assert str(repos_root) in out
    assert "Modo: citas verificadas" in out


def test_no_repo_check_keeps_structural_only_run(tmp_path, monkeypatch, capsys):
    """--no-repo-check keeps the old structural-only run, exit 0."""
    module, _root, repos_root = make_guide(tmp_path, "Guia vacia.\n")
    code, out = run_check(monkeypatch, capsys, module, repos_root, "--no-repo-check")
    assert code == 0
    assert "Modo: solo estructura (--no-repo-check)" in out
    assert "Resolucion de citas: omitida" in out


def test_prefixed_citation_must_fit_named_repo(tmp_path, monkeypatch, capsys):
    """A repo-prefixed citation is checked against the repo it names."""
    module, _root, repos_root = make_guide(tmp_path, "Véase Alfa/notes.md:50.\n")
    write_repo(repos_root, "Alfa", {"notes.md": 5})
    write_repo(repos_root, "Beta", {"notes.md": 60})
    code, out = run_check(monkeypatch, capsys, module, repos_root)
    assert code == 1
    assert "Citas fuera de la longitud del archivo" in out
    assert "Alfa/notes.md" in out


def test_ambiguous_bare_readme_requires_prefix(tmp_path, monkeypatch, capsys):
    """A bare README.md with several candidates is ambiguous, not resolved."""
    module, _root, repos_root = make_guide(tmp_path, "Cita README.md:3.\n")
    write_repo(repos_root, "Alfa", {"README.md": 5, "unica.py": 10})
    write_repo(repos_root, "Beta", {"README.md": 5, "unica.py": 10})
    code, out = run_check(monkeypatch, capsys, module, repos_root)
    assert code == 1
    assert "Citas ambiguas sin prefijo" in out
    assert "README.md" in out
    assert "Alfa" in out and "Beta" in out


def test_slash_path_in_two_repos_requires_prefix(tmp_path, monkeypatch, capsys):
    """backend/core.py in two repos cannot be silently attributed to either."""
    module, _root, repos_root = make_guide(
        tmp_path, "Véase backend/core.py:50.\n"
    )
    write_repo(repos_root, "Alfa", {"backend/core.py": 60})
    write_repo(repos_root, "Beta", {"backend/core.py": 3})
    code, out = run_check(monkeypatch, capsys, module, repos_root)
    assert code == 1
    assert "Citas ambiguas sin prefijo" in out


def test_bare_unique_name_still_resolves(tmp_path, monkeypatch, capsys):
    """A bare name found in exactly one repo resolves against it."""
    module, _root, repos_root = make_guide(tmp_path, "Véase unica.py:10.\n")
    write_repo(repos_root, "Alfa", {"unica.py": 20})
    write_repo(repos_root, "Beta", {"otro.py": 20})
    code, out = run_check(monkeypatch, capsys, module, repos_root)
    assert code == 0
    assert "Citas resueltas: 1/1" in out
    assert "Citas abreviadas: 0" in out


def test_abbreviated_citation_counted_separately(tmp_path, monkeypatch, capsys):
    """.../ abbreviated citations are reported apart and never 'resolved'."""
    module, _root, repos_root = make_guide(
        tmp_path, "Véase paquete/.../algo.py:5.\n"
    )
    write_repo(repos_root, "Alfa", {"algo.py": 10})
    write_repo(repos_root, "Beta", {"algo.py": 10})
    code, out = run_check(monkeypatch, capsys, module, repos_root)
    assert code == 1
    assert "Citas abreviadas: 1" in out
    assert "Citas resueltas: 0/1" in out
    assert "Citas con ruta abreviada" in out


def test_absolute_path_is_an_error(tmp_path, monkeypatch, capsys):
    """/Users/... paths in the guide prose are a hard error."""
    module, _root, repos_root = make_guide(
        tmp_path, "Ejecutado en /Users/alguien/nota.md.\n"
    )
    write_repo(repos_root, "Alfa", {"x.py": 5})
    write_repo(repos_root, "Beta", {"x.py": 5})
    code, out = run_check(monkeypatch, capsys, module, repos_root)
    assert code == 1
    assert "Rutas absolutas: 1" in out


def test_broken_internal_link_is_an_error(tmp_path, monkeypatch, capsys):
    """A link to a missing .md sibling is a hard error."""
    module, _root, repos_root = make_guide(tmp_path, "Mira [esto](falta.md).\n")
    write_repo(repos_root, "Alfa", {"x.py": 5})
    write_repo(repos_root, "Beta", {"x.py": 5})
    code, out = run_check(monkeypatch, capsys, module, repos_root)
    assert code == 1
    assert "Enlaces internos rotos: 1" in out


def test_verified_run_ok_with_alias(tmp_path, monkeypatch, capsys):
    """A clean run: alias-prefixed citation resolves and everything passes."""
    module, _root, repos_root = make_guide(
        tmp_path, "Véase AlfaCorto/src/app.py:10.\n"
    )
    write_repo(repos_root, "Alfa", {"src/app.py": 20})
    write_repo(repos_root, "Beta", {"src/app.py": 20})
    code, out = run_check(monkeypatch, capsys, module, repos_root)
    assert code == 0
    assert "Modo: citas verificadas" in out
    assert "Citas resueltas: 1/1" in out
    assert "Citas abreviadas: 0" in out
    assert "OK: estructura, enlaces, citas, rutas, SPDX y licencias." in out
