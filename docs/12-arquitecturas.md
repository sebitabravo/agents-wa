<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Capítulo 12 — Arquitecturas: del workflow de un paso al multi-agente

> **Tipo:** explanation (por qué elegir una arquitectura) con how-to (cómo decidirla).
> **Audiencia:** desarrolladores y arquitectos que ya tienen un caso de uso y deben elegir
> cuánta autonomía, estado y orquestación necesita.
> **Meta:** al terminar, puedes mapear tu problema a uno de nueve patrones, justificar por qué
> NO usas multi-agente, y detectar cuándo un framework está resolviendo un problema que no tienes.

La mayoría de los sistemas que se venden como "agentes" no necesitan autonomía. Necesitan un
workflow con un LLM acotado: una ruta que el código ya conoce, con el modelo rellenando los
puntos donde el lenguaje natural es la única interfaz razonable. La autonomía se paga en tres
monedas a la vez —tokens, latencia y errores compuestos— y solo se justifica cuando el problema
es tan abierto que no puedes escribir la ruta.

La tesis de este capítulo cabe en una línea: **la arquitectura correcta es la más simple
que resuelve el problema con un radio de daño (blast radius) aceptable**. Todo lo demás
—patrones, frameworks, protocolos— son medios para comparar esa solución contra la siguiente
más simple.

## La respuesta primero

| # | Regla | En una frase |
|---|-------|--------------|
| A1 | Workflow antes que agente | Si puedes dibujar la ruta, escríbela en código; deja al modelo solo los tramos ambiguos. |
| A2 | Una tool, un contrato | Cada herramienta declara schema, validación, error, efecto e idempotencia antes de existir. |
| A3 | Estado explícito antes que memoria implícita | Los pasos, las transiciones y los terminales viven en código, no en el historial del prompt. |
| A4 | Humano donde el efecto es irreversible | La confirmación no es una instrucción del prompt: es una transición de estado. |
| A5 | Multi-agente solo con especialización real | Varios agentes multiplican llamadas, estado y modos de fallo; rara vez multiplican calidad. |
| A6 | El framework no es la arquitectura | LangGraph, Pydantic AI o el SDK que elijas no deciden tu radio de daño; tu diseño sí. |

Si solo recuerdas una cosa: **cada capa de autonomía que agregas debe pagar su costo con una
capacidad que no podías obtener de forma determinista**.

---

## 1. Workflows vs agentes

Anthropic define la frontera en *Building effective agents* (2024-12-19,
https://www.anthropic.com/research/building-effective-agents, consultado 2026-11-04):
un **workflow** es un sistema donde los LLM y las tools se orquestan por rutas de código
predefinidas; un **agente** es un sistema donde el LLM dirige dinámicamente su propio proceso
y el uso de herramientas. La diferencia no es "usa tools o no": es **quién decide el próximo
paso**.

| Dimensión | Workflow | Agente |
|---|---|---|
| Quién decide la ruta | Código determinista | El modelo, en cada iteración |
| Previsibilidad | Alta: el conjunto de caminos es finito y testeable | Baja: el camino se descubre en runtime |
| Costo por turno | Acotado por construcción | Variable; depende de cuántos pasos decida dar |
| Latencia | Suma fija de etapas | Suma variable; un paso lento contamina el turno |
| Errores | Aislables por etapa | Compuestos: cada paso arrastra el error del anterior |
| Debugging | Traza de etapas y estados | Traza de mensajes, tool calls y decisiones |
| Cuándo | Ruta conocida, pasos finitos, auditoría | Problema abierto, número de pasos impredecible |

El costo de los errores compuestos no es retórica. Si cada paso acierta con probabilidad `p` y
los pasos fueran independientes, la probabilidad de que todos acierten es `p^n`. Con `p = 0.95`
y `n = 10`, el resultado es 0.60. Es aritmética ilustrativa, no una medición de estos proyectos:
sirve para recordar que diez pasos "casi siempre correctos" producen un sistema que falla
cuatro de cada diez veces.

**Cuándo cruzar la frontera.** Anthropic recomienda empezar por la solución más simple y
aumentar complejidad solo cuando mejora el resultado. En términos operativos, cruza a agente
solo si se cumplen las tres condiciones:

1. No puedes enumerar los pasos antes de ejecutar (el plan depende de lo que devuelva el mundo).
2. Cada paso es verificable por una tool o un guardrail (no estás confiando en la narración).
3. Existe un sandbox, un presupuesto y un fallback que limitan el daño si el modelo se equivoca.

Si falla cualquiera de las tres, estás construyendo un workflow con pasos de más.

---

## 2. Catálogo de patrones

Los cuatro proyectos instancian cinco de los nueve patrones; los otros cuatro se documentan
porque aparecen en la literatura y en frameworks, no porque hagan falta aquí: **un patrón que no
tienes evidencia de necesitar es una hipótesis, no un requisito**.

| Patrón | Instancia real en los 4 proyectos | Complejidad | Riesgo principal |
|---|---|---|---|
| Single-shot + reglas | ManttoAI, Wenuke | Baja | La regla tapa la pregunta específica |
| Router / clasificador | copiloto, AgroVoz | Baja-media | Clasificación errónea silenciosa |
| Prompt chaining | Sin instancia directa | Media | El paso intermedio no verifica nada |
| Parallelization | Sin instancia | Media-alta | Costo y latencia sin mejora medible |
| Orchestrator-workers | Sin instancia | Alta | Planificación impredecible |
| Evaluator-optimizer | Sin instancia en runtime | Media | Criterio de evaluación flojo |
| Tool loop acotado | AgroVoz, copiloto | Media | Loop sin cotas, tool mal parametrizada |
| State machine + HITL | copiloto, AgroVoz | Media | Estado implícito, handoff sin contexto |
| Fallback en cascada | AgroVoz, Wenuke | Baja | Fallback que inventa o no está probado |

### 2.1 Single-shot + reglas

```text
request -> normalize -> rule match? --yes--> template response
                            |
                           no
                            v
                     one LLM call -> response
                            |
                        error/timeout -> fixed fallback
```

**Cuándo:** FAQ estable, datos precalculados, redacción sobre un contexto pequeño. Es el patrón
por defecto y el más barato de operar.
**Cuándo no:** el dato cambia fuera de tu sistema, la respuesta exige varios pasos, o la regla
por palabra clave secuestra preguntas que necesitan datos.
**Ejemplo real:** ManttoAI busca primero en `REGLAS_MANTENIMIENTO` y solo si no hay match llama
a Ollama una vez, con fallback fijo si el modelo falla (`backend/app/services/chat_service.py:61-87`;
fast path en `:71-75`). Wenuke calcula alertas con reglas puras (`backend/reglas.py:173-255`) y
usa el LLM solo para redactar (`backend/main.py:555-572`, `backend/llm.py:130-159`).

### 2.2 Router / clasificador

```text
request -> classify (code or small model) -> domain A handler
                                          -> domain B handler
                                          -> human queue
```

**Cuándo:** hay dominios con tools, permisos o costos distintos, y la clasificación es barata y
observable. **Cuándo no:** una sola ruta, o el clasificador se equivoca más de lo que ahorra.
**Ejemplo real:** copiloto enruta por `state.step` y por intención determinista hacia el flujo
guiado, la IA o el handoff (`copiloto-recepcion/copiloto/src/copiloto/flow.py:160-163`, `:204-235`).
AgroVoz recorta el bloque de tools según `consulta_tipo` para bajar el costo de prompt eval
(`backend/app/services/llm_service.py:762-795`).

### 2.3 Prompt chaining

```text
draft -> check (schema/rules) -> revise -> final
```

**Cuándo:** subtareas secuenciales donde cada salida tiene un criterio verificable antes de
pasar a la siguiente. **Cuándo no:** una sola llamada basta, o el paso intermedio no tiene un
check real y solo agrega latencia.
**Ejemplo real:** ninguno de los cuatro encadena prompts con verificación intermedia. El pipeline
de voz de AgroVoz (STT → LLM → TTS) es una cadena de etapas, no de prompts.

### 2.4 Parallelization (sectioning y voting)

```text
        -> worker A -
input -- -> worker B --> join / aggregate -> response
        -> worker C -
```

**Sectioning** reparte subtareas independientes; **voting** repite la misma tarea para decidir
por mayoría. **Cuándo:** las subtareas no comparten contexto y la latencia se justifica.
**Cuándo no:** el costo se multiplica sin una métrica que demuestre mejora.
**Ejemplo real:** sin instancia en los cuatro proyectos. Copiloto ejecuta una tool por paso y
no reparte el turno entre workers.

### 2.5 Orchestrator-workers

```text
orchestrator -> plan -> worker 1 --\
                     -> worker 2 ----> synthesize -> response
                     -> worker 3 --/
```

**Cuándo:** el número y la forma de las subtareas no se conocen de antemano, son paralelizables
y cada worker tiene un contrato claro. **Cuándo no:** el plan es fijo (usa chaining), hay un solo
dominio, o los workers comparten el mismo contexto y se pisan.
**Ejemplo real:** sin instancia. Los cuatro proyectos son single-agent; el handoff de copiloto
deriva a un humano, no a otro agente (`copiloto-recepcion/copiloto/src/copiloto/flow.py:622-643`).

### 2.6 Evaluator-optimizer

```text
generate -> evaluate (criteria) -> pass? --yes--> done
                |                   |
                +----- no ----------+
                        |
                     revise -> generate
```

**Cuándo:** existe un criterio objetivo y barato de evaluar (schema válido, tests, rúbrica
cerrada, lista de hechos permitidos). **Cuándo no:** el criterio es "se ve bien", el evaluador es
el mismo modelo sin rúbrica, o el segundo pase duplica el costo sin reducir errores medidos.
**Ejemplo real:** no se usa en runtime. Copiloto tiene evaluación offline contra un endpoint
(`copiloto-recepcion/scripts/model_eval.py:14-16`), que es un eval de release, no un evaluator-optimizer
dentro del turno.

### 2.7 Tool loop acotado

```text
messages -> LLM -> tool_calls? --no--> final answer
              ^        |
              |       yes
              |        v
              +-- execute + validate + truncate payload
                  (max steps, deadline, whitelist)
```

**Cuándo:** la respuesta correcta depende de datos externos que solo aparecen después de
observar (disponibilidad, precio, estado de una reserva). **Cuándo no:** puedes inyectar el
contexto en el prompt y responder de una vez; el loop agrega pasos sin agregar información.
**Ejemplo real:** copiloto implementa `MAX_STEPS = 5`, deadline de turno y truncado de payload
(`copiloto-recepcion/copiloto/src/copiloto/ai/agent.py:19-21`, `:116-233`). AgroVoz usa `MAX_TOOL_ITERATIONS = 3`
con whitelist y presupuesto único de generación (`backend/app/services/llm_service.py:128`,
`:141`, `:1756`). La mecánica completa está en el [Capítulo 4](04-orquestacion-tools.md).

### 2.8 State machine + handoff humano

```text
start -> menu -> ask_dates -> ask_adults -> ask_children -> pick_room -> proposal
   |                                                                    |
   +--> handoff (human_requested | pms_down | error | commercial) <-----+
                                                                        v
                                                                   handed_off (terminal)
```

**Cuándo:** hay un flujo comercial con pasos, SLA, y una acción que una persona debe confirmar.
**Cuándo no:** conversación abierta sin estados claros, o un FAQ que no necesita recordar dónde
quedó el usuario.
**Ejemplo real:** copiloto persiste estado, eventos e inicio de SLA en una transacción antes de
abrir la conversación a recepción (`copiloto-recepcion/copiloto/src/copiloto/flow.py:622-643`) y enruta por paso
(`:204-235`). AgroVoz declara un enum con estados terminales `CERRADO` y `DERIVADO`
(`backend/app/services/conversation_state.py:26-82`).

### 2.9 Fallback en cascada

```text
primary model -> secondary model -> local model -> rules/template
       |               |                |                 |
       +--- observable, con causa y texto público acotado ---+
```

**Cuándo:** la disponibilidad o el costo importan y existe un camino determinista real, probado.
**Cuándo no:** el fallback no está testeado, o "fallback" significa pedirle al modelo que improvise.
**Ejemplo real:** AgroVoz corta a los 10 s y cae a un fallback por keywords
(`backend/app/services/llm_service.py:141`, `:1144`, `:67-78`); Wenuke devuelve siempre
`{"respuesta", "offline"}` y resuelve desde JSON local cuando Groq falla (`backend/llm.py:130-159`).
El principio fail-closed está en el [Capítulo 1](01-principios-fail-closed.md).

---

## 3. Multi-agente: cuándo se justifica y cuándo no

OpenAI describe dos formas de orquestar varios agentes (*A practical guide to building agents*,
2025, https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf,
consultado 2026-11-04):

```text
Manager (agents as tools)          Decentralized (handoffs)

  +-----------+                      +---------+  handoff  +---------+
  |  manager  |                      | agent A | --------> | agent B |
  +-----+-----+                      +---------+           +---------+
        | calls as tools
   +----+----+
   v         v
+-------+ +-------+
| agent | | agent |
+-------+ +-------+
```

En el modelo **manager**, un agente coordinador llama a los especialistas como herramientas y
conserva el control del turno. En el modelo **decentralized**, un agente transfiere la
conversación a otro y el control cambia de manos.

**Se justifica cuando** hay tareas abiertas que el manager no puede resolver en un solo contexto,
especialización real (tools, permisos o prompts que no se pueden mezclar sin degradar), o
paralelismo genuino entre subtareas independientes.

**No se justifica cuando** el caso es un FAQ, hay un solo dominio, el presupuesto es ajustado o
el equipo es pequeño. Multi-agente multiplica llamadas, latencia y modos de fallo: un error de un
paso se propaga entre agentes que no comparten estado, y el debugging pasa de leer una traza a
reconstruir quién dijo qué a quién.

Regla práctica: **agrega tools antes de agregar agentes**. OpenAI lo recomienda explícitamente y
los cuatro proyectos lo confirman: ninguno necesita un segundo agente para resolver su dominio.
El handoff de copiloto es a un humano, que es el especialista con permisos que el bot no tiene.

---

## 4. Estado y grafos: por qué la máquina de estados suele ganar

Un agente libre guarda su estado en el historial de mensajes. Eso funciona hasta que necesitas
responder tres preguntas: ¿en qué paso está?, ¿qué transiciones son válidas desde aquí?, ¿qué
pasa si el proceso se cae en medio del turno? El historial no responde ninguna de las tres.

Una máquina de estados explícita sí:

| Mecanismo | Qué compra | Qué cuesta |
|---|---|---|
| Estados nombrados | Sabes dónde está la conversación sin interpretar el prompt | Mantener el enum y sus transiciones |
| Transiciones validadas | Un paso no puede saltar a otro que no corresponde | Más código que un `if` suelto |
| Terminales | `handed_off`, `CERRADO`, `DERIVADO` no vuelven al bot por accidente | Definir qué hace el sistema después |
| Checkpoint | Persistir estado + eventos + reloj en una transacción | Una escritura por transición |
| Interrupt | Pausar para aprobación humana y reanudar con contexto | Un lugar donde guardar la pausa |
| Durabilidad | Sobrevivir a un reinicio o a un reintento | Cola o almacén durable; no es gratis |

**Checkpoint** es el punto donde el estado se persiste antes de un efecto externo: copiloto lo
hace antes de abrir la conversación a recepción (`copiloto-recepcion/copiloto/src/copiloto/flow.py:622-643`).
**Interrupt** es la pausa para aprobación humana; la propuesta de reserva lo es: el bot no escribe
hasta que el huésped confirma en un turno posterior (`copiloto-recepcion/copiloto/src/copiloto/ai/tools.py:298-336`).

**Durabilidad** es la parte que más se declara y menos se implementa. Copiloto procesa a lo más
una vez y no tiene cola durable: si Chatwoot cae mientras el bot responde, ese mensaje no se
reintenta (`copiloto-recepcion/README.md:138-140`). Una máquina de estados sin almacén durable sigue
perdiendo el turno cuando el proceso muere, por más estados que declare.

Por eso una máquina de estados suele vencer a un agente libre: **el estado deja de ser una
interpretación del modelo y pasa a ser un dato que puedes leer, testear y auditar**.

---

## 5. Diseño de tools: el contrato antes del código

Una tool no es una función que el modelo puede llamar: es una interfaz pública con un contrato
que el servidor hace cumplir. Estos son los once puntos que hay que decidir antes de escribirla.

| Punto | Regla | Evidencia real |
|---|---|---|
| Nombre | Verbo + objeto, estable, sin ambigüedad (`check_availability`, no `check`) | `copiloto-recepcion/copiloto/src/copiloto/ai/tools.py:73-106` |
| Descripción | Dice qué hace y cuándo usarla; algunas tools delimitan qué no hacen. Es parte del prompt | `copiloto-recepcion/copiloto/src/copiloto/ai/tools.py:76-105` |
| Schema | Tipos, enums, mínimos/máximos y `additionalProperties: false` | `copiloto-recepcion/copiloto/src/copiloto/ai/tools.py:73-88` |
| Validación | El servidor revalida todo: fechas, rangos, pertenencia, permisos | `copiloto-recepcion/copiloto/src/copiloto/ai/tools.py:243-287` |
| Errores | Código estable + instrucción pública; nunca el stack trace al modelo | `copiloto-recepcion/copiloto/src/copiloto/ai/tools.py:313-320` |
| Idempotencia | Un reintento no duplica el efecto; clave de deduplicación o consulta previa | `copiloto-recepcion/copiloto/src/copiloto/ai/tools.py:294-297` |
| Efectos secundarios | Lectura y escritura separadas; la escritura no se reintenta a ciegas | `backend/app/services/llm_service.py:105-117` (AgroVoz) |
| Confirmación | Efecto irreversible en un turno posterior al de la propuesta | `copiloto-recepcion/copiloto/src/copiloto/ai/tools.py:298-307` |
| Timeout | El cliente del PMS tiene timeout HTTP y el loop tiene deadline de turno | `copiloto-recepcion/copiloto/src/copiloto/pms.py:66-78`; `copiloto-recepcion/copiloto/src/copiloto/ai/agent.py:118` |
| Salida | Truncar el payload antes de reinyectarlo al historial | `copiloto-recepcion/copiloto/src/copiloto/ai/agent.py:21`, `:227` |
| Versionado | Cambiar schema o semántica es un cambio de contrato: versión o migración | Recomendación de esta guía |

### Tabla de riesgo de tools

| Riesgo | Ejemplos | Control mínimo | Confirmación | Reintento |
|---|---|---|---|---|
| Lectura | Precio, clima, disponibilidad, FAQ | Schema, timeout, whitelist | No | Sí, con backoff |
| Escritura reversible | Guardar preferencia, crear borrador | Validación, idempotencia, auditoría | Según impacto | Sí, con clave de idempotencia |
| Escritura irreversible | Reserva, alta de usuario, envío de mensaje | Validación completa, permiso, traza | Sí, en turno posterior | No a ciegas |
| Financiero / alto impacto | Pago, descuento, cancelación con costo | Doble control, límite, aprobación humana | Sí, explícita | No |

La tabla es una adaptación de la clasificación de *tool safeguards* de OpenAI (riesgo bajo, medio
y alto según lectura, escritura, reversibilidad, permisos e impacto financiero). La regla que la
resume: **cuanto más difícil es deshacer el efecto, más capas de código debe atravesar antes de
ejecutarse**.

Dos ejemplos: copiloto declara `additionalProperties: false` y enums cerrados
(`copiloto-recepcion/copiloto/src/copiloto/ai/tools.py:73-88`) y luego revalida en `_booking` que la lectura del PMS
sea fresca, que la habitación esté entre las ofrecidas y que el nombre lo haya escrito el huésped
(`:243-287`); AgroVoz excluye las tools de escritura del intento remoto primario para que un
reintento no duplique un registro (`backend/app/services/llm_service.py:105-117`).

---

## 6. MCP: estandarizar la interfaz, no la política

El Model Context Protocol (MCP) es un protocolo abierto para conectar modelos con datos y tools
(https://modelcontextprotocol.io/specification/2025-06-18 y la revisión 2025-11-25, consultadas
2026-11-04). Un servidor MCP expone tres primitivas, y cada una tiene un controlador distinto:

| Primitiva | Controlada por | Qué es | Ejemplo | Riesgo si se ignora |
|---|---|---|---|---|
| Resources | Aplicación | Contexto que la app decide cargar | Un documento, un registro, un archivo | Inyectar contexto no autorizado |
| Prompts | Usuario | Plantillas que el usuario elige | "Resume este contrato" | Ejecutar una plantilla no revisada |
| Tools | Modelo | Funciones que el modelo puede invocar | `search`, `create_ticket` | Acciones no consentidas |

La distinción importa porque **el modelo controla las tools, no los resources ni los prompts**.
Si tu aplicación deja que el modelo decida qué resource cargar, ya no estás usando MCP: estás
usando un agente con acceso libre a datos.

**Seguridad y consentimiento.** La especificación recomienda consentimiento explícito, control de
acceso, validación de inputs, rate limit, sanitización de outputs, timeouts, logging y
human-in-the-loop para operaciones sensibles. Las anotaciones de una tool no son confiables salvo que
vengan de un servidor confiable: una tool puede declararse "read-only" y mentir.

**Cuándo usar MCP:** cuando varios clientes u hosts necesitan el mismo conjunto de tools, cuando
integras un servidor de terceros, o cuando quieres una interfaz reusable entre agentes. **Cuándo
basta una función interna:** cuando hay una sola aplicación, un solo dominio y ninguna
reutilización prevista. Para los cuatro proyectos, una función interna con schema y validación
es suficiente; MCP agregaría un proceso, un transporte y una superficie de permisos sin resolver
ningún problema que ya no esté resuelto.

MCP estandariza la interfaz, no la política: validación, confirmación y límite de daño siguen
siendo responsabilidad de tu aplicación (ver [08-seguridad.md](08-seguridad.md)).

**A2A.** Agent2Agent (A2A) aparece en el ecosistema 2026 como protocolo para que agentes se
comuniquen entre sí, asociado a Google ADK en las comparativas. Esta guía no lo evalúa: no hay
implementación en los cuatro proyectos ni evidencia propia. No lo confundas con MCP: MCP conecta
un modelo con tools y datos; A2A conecta agentes entre sí.

---

## 7. Frameworks 2026: comparativa secundaria, no benchmark

Esta tabla se basa en comparativas de terceros consultadas el 2026-11-04
(https://nomadx.ae/blog/google-adk-vs-openai-agents-sdk-vs-pydantic-ai-vs-langgraph/, 2026-09-05;
https://dbggr.dev/articles/agent-frameworks-compared/, 2026-10-16;
https://www.promptise.com/guides/view/python-ai-agent-frameworks-compared, 2026-10-15). No es una
medición propia ni un ranking: es un mapa para reducir opciones, y sus capacidades cambian entre
versiones. "No destacado" significa que la fuente no lo menciona, no que no exista.

| Framework | Modelo mental | Durabilidad | HITL | MCP | Tracing | Mejor para | Costo de adopción |
|---|---|---|---|---|---|---|---|
| LangGraph | Grafo de estado con nodos y aristas | Checkpoints e interrupts; ejecución durable | Explícito en el grafo | Sí | Según integración | Workflows complejos con ramas, ciclos y aprobación | Medio-alto: más trabajo de integración |
| Pydantic AI | Agentes tipados con validación Pydantic | Vía Temporal, DBOS o Prefect | Según integración | Sí | Según integración | Equipos Python/FastAPI que ya viven en tipos | Medio: ecosistema Pydantic |
| OpenAI Agents SDK | Minimalista: agents, tools, handoffs, guardrails, sessions | Sessions; durabilidad no destacada | Guardrails y handoffs | Sí | Por defecto | Empezar rápido en el ecosistema OpenAI | Bajo |
| Google ADK | Workflow agents (sequential, parallel, loop) y grafo 2.0 | Según despliegue en Vertex AI | Según integración | No destacado en la comparativa | Evals y despliegue gestionado | Google Cloud/Gemini | Medio: acopla al stack Google |
| CrewAI | Equipos de roles que colaboran | No destacada; estado menos explícito | No destacado | No destacado | No destacado | Prototipado rápido de equipos | Bajo para demo, alto para producción |
| Mastra / Vercel AI SDK | Workflows y agentes en TypeScript | Workflows; memoria | Según integración | Sí | Según integración | Equipos TypeScript/Next.js | Bajo-medio |
| Claude Agent SDK | Sesiones, hooks y permisos para Claude | Sesiones | Hooks y permisos | No destacado en la comparativa | No destacado | Automatización con Claude | Bajo si ya usas Claude |

**La regla que ordena la tabla:** el framework no es la arquitectura. Elige por (1) forma del
workflow, (2) durabilidad requerida, (3) modelo y proveedor, (4) lenguaje y equipo, (5)
observabilidad y evals. Para un bot de FAQ con reglas y una llamada single-shot, cualquiera de
estos frameworks es sobreingeniería: la dependencia agrega superficie de actualización y oculta
el prompt que necesitas depurar.

Anthropic advierte además que los frameworks pueden ocultar prompts y respuestas y volver el
debugging difícil; su recomendación es empezar con APIs directas y bajar de abstracción en
producción. Los cuatro proyectos son consistentes con eso: ninguno usa un framework de agentes.
Copiloto y AgroVoz implementan el loop a mano; ManttoAI y Wenuke ni siquiera lo necesitan.

---

## 8. Árbol de decisión de arquitectura

```text
¿Hay acciones?
├─ no → ¿hay documentos o datos que inyectar?
│        ├─ sí → single-shot + RAG (cap. 5)
│        └─ no → single-shot + reglas (2.1)
└─ sí → ¿son irreversibles?
         ├─ no  → tool loop acotado (2.7)
         └─ sí  → state machine + HITL (2.8)
```

Las diez preguntas que confirman o desmienten esa primera respuesta:

| # | Pregunta | Si la respuesta es sí | Si la respuesta es no |
|---|---|---|---|
| 1 | ¿Hay acciones sobre sistemas externos? | Tools y loop acotado | Single-shot o reglas |
| 2 | ¿Son irreversibles o financieras? | Confirmación en turno posterior, HITL, idempotencia | Lectura con timeout y whitelist |
| 3 | ¿Cuántos pasos? ¿Puedes enumerarlos? | Si no puedes, considera agente; si puedes, workflow | Workflow con etapas fijas |
| 4 | ¿Necesita estado entre turnos? | State machine + persistencia + TTL | Stateless por request |
| 5 | ¿Es multi-tenant? | Aislamiento por tenant, permisos por recurso, trazas por tenant | Un solo ámbito, más simple |
| 6 | ¿Humano en el loop? | Interrupt, cola, SLA y handoff con contexto | Todo automático con guardrails |
| 7 | ¿Presupuesto ajustado? | Reglas primero, modelo pequeño, cache, fallback local | Puedes pagar más pasos |
| 8 | ¿Latencia estricta? | Menos pasos, streaming, modelo pequeño, fast path | Puedes permitir un loop |
| 9 | ¿Equipo pequeño? | Menos piezas: sin framework, sin multi-agente, sin cola | Puedes operar más infraestructura |
| 10 | ¿Observabilidad y evals existen? | Puedes iterar con datos | No agregues autonomía todavía |

Las preguntas 7 a 10 son las que más se ignoran y las que más caro salen. Un agente que no se
puede observar no se puede mejorar; un agente que no se puede pagar no se puede operar; un
agente que un equipo de dos personas no puede depurar es deuda desde el día uno.

---

## 9. Mapa de los cuatro proyectos

| Proyecto | Patrón dominante | Patrones de apoyo | Evidencia | Por qué encaja |
|---|---|---|---|---|
| AgroVoz | Tool loop acotado | Fast paths, router por intención, fallback en cascada | `AgroVoz/backend/app/services/llm_service.py:128`, `:1144`, `:1756` | El dato vive en ODEPA, clima y corpus; la ruta crítica es consultar, no planificar |
| copiloto | State machine + HITL | Tool loop, router, guardrails, fallback guiado | `copiloto-recepcion/copiloto/src/copiloto/flow.py:204-235`, `:622-643`; `copiloto-recepcion/copiloto/src/copiloto/ai/agent.py:116-233` | Hay pasos comerciales, SLA y una escritura que una persona debe confirmar |
| ManttoAI | Rules-first single-shot | Fallback fijo, contexto de dashboard | `ManttoAI/backend/app/services/chat_service.py:61-87` | FAQ operativa sobre datos ya calculados; no hay acción externa |
| Wenuke | Reglas + single-shot + offline | Fallback JSON, scheduler | `Wenuke/backend/reglas.py:173-255`; `Wenuke/backend/llm.py:130-159` | El núcleo es determinista y el LLM solo redacta; la conectividad no está garantizada |

Tres observaciones que la tabla no muestra:

1. **AgroVoz parece más "agente" de lo que es.** Su loop tiene tres iteraciones y un presupuesto
   de 10 segundos; antes del loop corre un preflight determinista por keywords
   (`AgroVoz/backend/app/services/llm_service.py:1144`, `:1756`). La autonomía está encajonada entre dos
   capas de código.
2. **Copiloto parece más "flujo" de lo que es.** El flujo guiado y la máquina de estados
   conviven con un loop de tools; la IA solo entra en los estados donde aporta
   (`copiloto-recepcion/copiloto/src/copiloto/flow.py:146-172`). Es un híbrido deliberado, no una transición
   incompleta.
3. **ManttoAI y Wenuke demuestran que el patrón simple puede ser el correcto.** Ninguno necesita
   tools ni estado conversacional para su función principal; el chat de ManttoAI entró sin ADR ni
   requisito de alcance (`ManttoAI/docs/alcance/06-enunciado-alcance.md:6-12`): crecimiento de alcance.

---

## 10. Anti-patrones de arquitectura

1. **Multi-agente para un FAQ.** Varios agentes para responder horarios y políticas. Antídoto:
   reglas + single-shot; mide cuántas preguntas necesitan realmente un modelo.
2. **Framework-first.** Elegir LangGraph o CrewAI antes de saber si hay estado, tools o HITL.
   Antídoto: si la ruta cabe en un `switch`, no necesita framework.
3. **El agente que planea todo.** Un planner que descompone cada turno en pasos aunque la ruta
   sea conocida. Antídoto: workflow con etapas fijas y el modelo solo dentro de la etapa.
4. **Loop sin límite.** Sin `MAX_STEPS`, sin deadline y sin presupuesto de tokens. Antídoto:
   cotas independientes y fallback al agotarlas (ver [Capítulo 4](04-orquestacion-tools.md)).
5. **Orquestación por prompt.** "Eres el manager y decides qué agente responde" sin estado ni
   contratos. Antídoto: routing en código; el prompt no es un scheduler.
6. **Tools sin schema.** Descripciones en prosa y argumentos libres que el servidor interpreta
   con `getattr`. Antídoto: schema cerrado, validación y errores tipificados.
7. **Handoff sin contexto.** Derivar el chat vacío a una cola. Antídoto: nota con últimos turnos,
   intención, causa y datos capturados (ver [Capítulo 6](06-canales-memoria.md)).
8. **Estado implícito.** El "estado" es el historial del prompt y nadie sabe en qué paso está.
   Antídoto: enum, transiciones y terminales.
9. **El "agente" que solo envía mensajes.** No recibe ni interpreta: no hay webhook de entrada.
   Antídoto: nombra el sistema por lo que hace, no por lo que aspiras a que haga.

---

## 11. Checklist de 12 puntos para elegir arquitectura

- [ ] 1. Escribe la ruta más simple que resuelve el caso, sin LLM, y pruébala.
- [ ] 2. Sé qué parte de la ruta es ambigua y necesita lenguaje natural.
- [ ] 3. Puedo enumerar los pasos o justificar por qué no se pueden enumerar.
- [ ] 4. Cada tool tiene schema, validación en servidor y error tipificado.
- [ ] 5. Las tools de escritura están separadas de las de lectura y no se reintentan a ciegas.
- [ ] 6. Todo efecto irreversible ocurre en un turno posterior a su propuesta.
- [ ] 7. El estado es explícito: enum, transiciones y terminales.
- [ ] 8. Existe un checkpoint antes de cada efecto externo y sé qué pasa si el proceso muere.
- [ ] 9. Hay un límite de pasos, un deadline y un presupuesto de tokens por turno.
- [ ] 10. El fallback es determinista, está probado y no inventa datos.
- [ ] 11. Puedo explicar por qué NO uso multi-agente, o qué especialización real lo justifica.
- [ ] 12. Tengo trazas, evals y una métrica de costo antes de agregar la siguiente capa.

Si alguna casilla queda vacía, la respuesta no es "agregar un framework": es volver al paso
anterior y reducir el alcance.

---

## Cierre

La arquitectura se elige por la forma del problema, no por el framework de moda: si la ruta es
conocida, escríbela; si el dato vive afuera, agrega una tool de lectura; si el efecto es
irreversible, agrega estado y un humano; si el problema es abierto y verificable, recién entonces
considera autonomía. Multi-agente, MCP y grafos durables son para casos que ya justificaron su costo.

Los cuatro proyectos confirman que el patrón simple gana: AgroVoz y copiloto usan loops acotados
porque el dato lo exige; ManttoAI y Wenuke resuelven con reglas y una sola llamada, sin multi-agente.

**Siguiente paso:** implementa el loop y la validación con
[04-orquestacion-tools.md](04-orquestacion-tools.md), define cómo vas a medir la calidad con
[07-evaluacion.md](07-evaluacion.md), estima el costo por turno con
[10-costos-modelos.md](10-costos-modelos.md), elige el despliegue con
[11-despliegue.md](11-despliegue.md), contrasta tu caso con
[13-casos-de-estudio.md](13-casos-de-estudio.md) y copia las plantillas de
[14-plantillas.md](14-plantillas.md).

### Fuentes externas citadas

- Anthropic, *Building effective agents*, 2024-12-19:
  https://www.anthropic.com/research/building-effective-agents (consultado 2026-11-04).
- OpenAI, *A practical guide to building agents*, 2025:
  https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf
  (consultado 2026-11-04).
- Model Context Protocol, especificación 2025-06-18 y 2025-11-25:
  https://modelcontextprotocol.io/specification/2025-06-18 y
  https://modelcontextprotocol.io/specification/2025-11-25 (consultadas 2026-11-04).
- Comparativas secundarias de frameworks: nomadx.ae (2026-09-05), dbggr.dev (2026-10-16) y
  promptise.com (2026-10-15), según el brief externo del proyecto.
