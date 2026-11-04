<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Guía estándar para crear agentes IA y chatbots

Manual en español para diseñar, construir, evaluar y operar agentes y chatbots con LLM. No es una recopilación de teoría: es una destilación de decisiones reales tomadas en cuatro proyectos del autor, con evidencia `path:line` y fuentes externas fechadas.

**Estado:** v1.0 · 2026-11-04 · 20 documentos · 8.470 líneas en `docs/` según `scripts/check_docs.py`.
**Base empírica:** cuatro proyectos del autor —AgroVoz, copiloto-recepcion, ManttoAI y Wenuke—. Sus repositorios no forman parte de este repositorio: las citas `path:line` de los capítulos apuntan a su código, y `scripts/check_docs.py` verifica esas citas cuando los repos están presentes.
**Idioma:** prosa en español neutro/profesional; código, identificadores y artefactos técnicos en inglés.
**Licencia:** prosa CC BY-SA 4.0; código original de plantillas y scripts MIT. Ver [LICENSE](LICENSE), [LICENSES/](LICENSES/) y [NOTICE](NOTICE).

---

## La tesis en una frase

**Un agente confiable es un orquestador determinista con un LLM acotado, no un prompt gigante.**

El código decide el flujo, los permisos, las tools, los datos y los fallbacks. El modelo interpreta lenguaje y redacta; no decide permisos, no inventa datos y no ejecuta acciones por su cuenta.

---

## Qué es y qué no es

| Es | No es |
|---|---|
| Un conjunto de invariantes, patrones y criterios de evidencia | Una norma ISO ni una certificación |
| Una guía de arquitectura y operación | Un curso de prompting |
| Un manual con plantillas copiables | Una receta única para todos los casos |
| Una síntesis honesta de 4 proyectos, con sus fracasos | Un benchmark de modelos o frameworks |
| Un punto de partida para la comunidad | Asesoría legal |

---

## Por dónde empezar

### Si tienes 1 hora

1. [Capítulo 0 — Introducción y mapa de decisión](docs/00-introduccion.md)
2. [Capítulo 1 — Principios fail-closed](docs/01-principios-fail-closed.md)
3. [Capítulo 15 — Anti-patrones](docs/15-anti-patrones.md), sección "Top 10"

### Si tienes 1 día

1. [Capítulo 0](docs/00-introduccion.md) → [1](docs/01-principios-fail-closed.md) → [4](docs/04-orquestacion-tools.md) → [7](docs/07-evaluacion.md)
2. [Capítulo 8 — Seguridad](docs/08-seguridad.md), tabla OWASP 2026
3. [Capítulo 14 — Plantillas](docs/14-plantillas.md), esqueleto y checklists

### Si vas a construir esta semana

1. [Capítulo 2 — Stack base](docs/02-stack-base.md)
2. [Capítulo 3 — System prompts](docs/03-system-prompts.md)
3. [Capítulo 4 — Orquestación y tools](docs/04-orquestacion-tools.md)
4. [Capítulo 5 — Datos y RAG](docs/05-datos-rag.md)
5. [Capítulo 6 — Canales y memoria](docs/06-canales-memoria.md)
6. [Capítulo 14 — Plantillas](docs/14-plantillas.md)

### Por rol

La tabla canónica de rutas por rol —fundador/PM, backend, frontend/canal, QA, seguridad y ops— vive en el [Capítulo 0](docs/00-introduccion.md#cómo-leer-esta-guía-según-tu-rol). Este README no la duplica para evitar que las rutas deriven.

---

## Índice completo

### Fundamentos

| # | Documento | Qué resuelve |
|---|---|---|
| 00 | [Introducción y mapa de decisión](docs/00-introduccion.md) | Taxonomía N0-N5, cuándo necesitas un LLM, 10 invariantes, madurez L0-L4. |
| 01 | [Principios fail-closed](docs/01-principios-fail-closed.md) | Sin dato verificado no hay respuesta con datos; fallback, whitelist, degradación. |
| 02 | [Stack base](docs/02-stack-base.md) | FastAPI, config fail-fast, SQLite primero, rate-limit, observabilidad mínima. |
| 03 | [System prompts](docs/03-system-prompts.md) | Estructura, anti-inyección, citas de fuente y fecha, prompts para voz. |
| 04 | [Orquestación y tools](docs/04-orquestacion-tools.md) | Loop acotado, validación en servidor, doble confirmación, tool specs. |
| 05 | [Datos y RAG](docs/05-datos-rag.md) | Corpus versionado, TF-IDF vs API viva, frescura, citas. |
| 06 | [Canales y memoria](docs/06-canales-memoria.md) | WhatsApp, voz y web; sesiones acotadas; handoff; métricas. |

### Calidad y operación

| # | Documento | Qué resuelve |
|---|---|---|
| 07 | [Evaluación y testing](docs/07-evaluacion.md) | Golden dataset, capability vs regression, LLM-as-judge, pass^k, CI. |
| 08 | [Seguridad](docs/08-seguridad.md) | OWASP GenAI LLM Top 10 2026, prompt injection, excessive agency, PII, Ley 21.719. |
| 09 | [Observabilidad](docs/09-observabilidad.md) | Traza por turno, OpenTelemetry GenAI, métricas, alertas, incident response. |
| 10 | [Costos y selección de modelos](docs/10-costos-modelos.md) | Costo por turno/conversación, routing, caching, local vs API, presupuestos. |
| 11 | [Despliegue](docs/11-despliegue.md) | Docker, serverless, colas, DB, CI/CD, rollback, runbooks. |

### Arquitectura y práctica

| # | Documento | Qué resuelve |
|---|---|---|
| 12 | [Arquitecturas](docs/12-arquitecturas.md) | Workflows vs agentes, 9 patrones, multi-agente, MCP, frameworks 2026. |
| 13 | [Casos de estudio](docs/13-casos-de-estudio.md) | Los 4 proyectos: arquitectura, aciertos, fallos, tests, costos y lecciones. |
| 14 | [Plantillas](docs/14-plantillas.md) | 16 plantillas copiables: prompt, tool, loop, eval, checklist, ADR, runbook. |
| 15 | [Anti-patrones](docs/15-anti-patrones.md) | 55 anti-patrones con síntoma, ejemplo real, arreglo y detección. |
| 16 | [Comunidad](docs/16-comunidad.md) | Versionado, contribución, licencias, citación, roadmap. |

### Apéndices

| # | Documento | Qué resuelve |
|---|---|---|
| A | [Glosario](docs/A-glosario.md) | 70 términos operativos, con "por qué importa" y errores comunes. |
| B | [Comparativas](docs/B-comparativas.md) | Stacks, DB, retrieval, proveedores, frameworks, canales, deploy, observabilidad. |
| C | [Referencias](docs/C-referencias.md) | Bibliografía anotada con fuente, fecha, capítulo y advertencia. |

**Total:** 8.470 líneas en `docs/`, verificado con `python3 scripts/check_docs.py`.

---

## Los 10 invariantes

Si un proyecto incumple uno, no está listo para el nivel siguiente.

| # | Invariante | En una frase |
|---|---|---|
| 1 | **Fail-closed** | Sin dato verificado no hay respuesta con datos: hay un fallback constante y acotado. |
| 2 | **Tool-first** | Todo dato factual sale de una tool o corpus con fuente; el modelo redacta, no inventa. |
| 3 | **Validación en servidor** | Fechas, permisos, nombres, montos y cupos se validan en código, nunca en el prompt. |
| 4 | **Loop acotado** | Todo loop tiene deadline, máximo de pasos, traza y payload truncado. |
| 5 | **Frescura y procedencia** | Cada dato declara fuente, fecha y vigencia; lo vencido falla cerrado. |
| 6 | **Memoria como presupuesto** | Historial y contexto tienen tope, TTL y consentimiento. |
| 7 | **Fallback observable** | La respuesta degradada se marca, se registra y se mide. |
| 8 | **Consentimiento y mínimo privilegio** | Cada permiso es separado, explícito y verificable en código. |
| 9 | **Evals y regresión** | Cada incidente se convierte en un caso; cada cambio se compara contra un baseline. |
| 10 | **Límites honestos** | Lo no probado se declara como no probado; no se presenta como producción. |

Detalle, evidencia y capítulo dueño de cada invariante: [Capítulo 0](docs/00-introduccion.md#los-10-invariantes-del-estándar).

---

## Los 4 proyectos en una tabla

| Proyecto | Qué es | Canal | Lección principal |
|---|---|---|---|
| **AgroVoz** | Asistente agrícola con precios, clima y orientación citada | WhatsApp, texto, voz, web | Orquestador determinista + TF-IDF + 19 tools + fail-closed. |
| **copiloto-recepcion** | Copiloto de recepción de hotel con PMS y handoff humano | Chatwoot, web, WhatsApp, voz | El bot propone; la persona confirma; el "sí" se verifica en el texto. |
| **ManttoAI** | Monitoreo IoT con chat híbrido reglas + Ollama | Widget web, API | Reglas primero; el chat sin ADR/alcance/eval es deuda, no adorno. |
| **Wenuke** | Alertas climáticas agrícolas por WhatsApp | WhatsApp saliente, web | Sin webhook de entrada no hay chatbot; las tools declarativas no son tools reales. |

Análisis completo, con aciertos, fallos y citas: [Capítulo 13](docs/13-casos-de-estudio.md).

---

## Estándar de evidencia

La guía distingue tres tipos de afirmación:

| Tipo | Cómo se reconoce |
|---|---|
| **Hecho verificado** | Lleva `path:line` relativo a la raíz del proyecto, o URL con fecha de consulta. |
| **Recomendación de esta guía** | Se declara como tal y no se atribuye a una fuente. |
| **Límite declarado** | Dice qué no se probó y por qué. |

Convención de rutas: cuando el capítulo nombra el proyecto, `backend/...` es relativo a la raíz de ese proyecto; cuando hace falta desambiguar, se prefija el nombre del repo (`AgroVoz/backend/...`).

---

## Verificación reproducible

El manual se verifica con un runner versionado, no con una afirmación manual:

```bash
python3 scripts/check_docs.py
```

El runner comprueba estructura, enlaces internos, rutas absolutas, marcadores pendientes, cabeceras SPDX, presencia de los archivos de licencia y, desde la revisión de citas de esta edición, **resuelve cada cita `path:line`**: falla si el archivo no existe, si el rango supera la longitud del archivo o si un nombre de archivo ambiguo se cita sin prefijo de proyecto. Cuando los cuatro repos no están presentes —el caso de quien clona solo la guía— la resolución se informa como omitida en lugar de fallar, y puedes fijar su ubicación con `--repos-root` o `AGENTS_WA_REPOS_ROOT`.

Salida esperada al cierre de esta edición:

```text
== agents-wa docs check ==
Documentos: 20/20
Lineas en docs/: 8470
Lineas en README.md: 249
Citas path:line: 1388
Enlaces rotos: 0
Rutas absolutas: 0
Marcadores pendientes: 0
Archivos sin SPDX: 0
Archivos de licencia: 4/4
Citas resueltas: 1388/1388
Citas fuera de rango: 0
Citas ambiguas sin prefijo: 0

OK: estructura, enlaces, citas, rutas, SPDX y licencias.
```

La verificación es estructural y de resolución, no una corrida de los cuatro proyectos: prueba que cada cita apunta a un archivo y una línea existentes, no que la línea diga lo que la frase afirma. Esa segunda comprobación se hizo una vez, con lectura semántica de 921 citas, y su resultado quedó registrado en `odd/audit/defectos.md`. Las suites de los cuatro repos no se ejecutaron; las cifras de tests y cobertura son las que cada proyecto declara. Donde un proyecto declara cifras contradictorias, la guía muestra la discrepancia en vez de elegir una.

---

## Plantillas

El [Capítulo 14](docs/14-plantillas.md) incluye 16 plantillas copiables:

- esqueleto de proyecto y `.env.example`
- system prompt ES/EN + variante de voz
- tool spec read-only y write con validación, idempotencia y confirmación
- agent loop con deadline, `MAX_STEPS`, whitelist y traza
- corpus RAG YAML con fuente, fecha y vigencia
- caso de eval, rúbrica de judge y manifest
- checklists de seguridad, observabilidad, launch y costos
- ADR, runbooks y Definition of Done

---

## Licencia

La licencia está en vigor desde el 2026-11-04 y es un split explícito:

| Material | Licencia | Archivo |
|---|---|---|
| Prosa, tablas, checklists y diagramas | **CC BY-SA 4.0** | [`LICENSES/CC-BY-SA-4.0.txt`](LICENSES/CC-BY-SA-4.0.txt) |
| Código original de plantillas y scripts | **MIT** | [`LICENSES/MIT.txt`](LICENSES/MIT.txt) |

Cada archivo declara su identificador SPDX. Los archivos que mezclan prosa y código, como `docs/14-plantillas.md`, usan `CC-BY-SA-4.0 AND MIT`: el texto es CC BY-SA 4.0 y los bloques de código originales son MIT.

Los fragmentos citados de los cuatro proyectos **no se relicencian**: AgroVoz sigue bajo AGPL-3.0, Wenuke bajo MIT, y copiloto-recepcion y ManttoAI no tienen licencia de proyecto, por lo que conservan todos los derechos. Antes de reutilizar cualquier snippet, lee [`NOTICE`](NOTICE).

Esta es una declaración de licencia, no asesoría legal.

---

## Comunidad

La guía está pensada para adaptarse. Los invariantes viajan; el stack, el canal y el país son decisiones locales.

- Contribución, versionado y estándar de evidencia: [Capítulo 16](docs/16-comunidad.md).
- Precedente de la prosa: **OWASP GenAI LLM Top 10 2026**, publicado bajo CC BY-SA 4.0 (https://genai.owasp.org/llm-top-10/, 2026-08-04).
- Para máxima adopción sin share-alike, la alternativa es CC BY 4.0; para código con patentes, Apache-2.0. No son la licencia actual.

---

## Fuentes principales

- OWASP GenAI LLM Top 10 2026, publicado 2026-08-04 — [genai.owasp.org/llm-top-10](https://genai.owasp.org/llm-top-10/)
- Anthropic, *Building effective agents*, 2024-12-19 — [anthropic.com/research/building-effective-agents](https://www.anthropic.com/research/building-effective-agents)
- OpenAI, *A practical guide to building agents*, 2025 — [PDF](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)
- Model Context Protocol, especificación 2025-06-18 / 2025-11-25 — [modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-11-25)
- OpenTelemetry GenAI Semantic Conventions, 2026-10 — [github.com/open-telemetry/semantic-conventions-genai](https://github.com/open-telemetry/semantic-conventions-genai)
- Bibliografía anotada completa: [Apéndice C](docs/C-referencias.md)

---

## Próximos pasos

1. Leer el [Capítulo 0](docs/00-introduccion.md) y clasificar tu caso.
2. Copiar el esqueleto y el system prompt del [Capítulo 14](docs/14-plantillas.md).
3. Implementar fail-closed y una tool de lectura antes de agregar cualquier otra cosa.
4. Escribir el primer set de evals antes de la primera demo con usuarios reales.
5. Declarar el nivel de madurez con evidencia, no con intención.
