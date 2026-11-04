<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Capítulo 0 — Introducción: el estándar, la tesis y el mapa de decisión

> **Tipo:** explanation (por qué existe este estándar) + how-to (cómo clasificar tu caso y arrancar).
> **Audiencia:** fundadores, PM, desarrolladores backend y frontend, QA, seguridad y operaciones que construyen agentes o chatbots con LLM.
> **Meta:** al terminar, clasificas tu sistema en uno de seis niveles, decides si necesitas un LLM y qué arquitectura mínima, y sabes qué capítulos leer según tu rol.

## La respuesta primero

**Un agente confiable es un orquestador determinista con un LLM acotado, no un prompt gigante.**

| Pregunta | Respuesta corta |
|---|---|
| ¿Qué hace confiable a un agente? | Código que decide flujo, permisos, datos y fallbacks; el modelo solo redacta o propone. |
| ¿Cuándo necesito un LLM? | Cuando una regla, plantilla o consulta estructurada no resuelve el caso. |
| ¿Por dónde empiezo? | Por el canal, las reglas y el fallback; el prompt es la última pieza. |
| ¿Cómo sé que funciona? | Con evals, trazas y un fallback observable; no con una demo feliz. |
| ¿Cuándo paso a producción? | Cuando el nivel de madurez tiene evidencia, no cuando el código "ya lo contempla". |

Esta guía no promete que el LLM acierte siempre. Promete que, cuando falle, el sistema falle de forma visible, acotada y barata.

## Qué es esta guía

Un manual estándar en español para diseñar, construir, evaluar y operar agentes de IA y chatbots. Se apoya en cuatro proyectos reales del autor: AgroVoz, copiloto-recepción, ManttoAI y Wenuke. No describe un framework ni una librería; describe decisiones de arquitectura, controles y criterios de aceptación que sobreviven a un cambio de modelo o de proveedor.

El estándar tiene tres capas:

1. **Principios** (capítulos 1-6): fail-closed, stack, prompts, orquestación, datos y canales.
2. **Ciclo de vida** (capítulos 7-11): evaluación, seguridad, observabilidad, costos y despliegue.
3. **Arquitecturas y comunidad** (capítulos 12-16 y apéndices): patrones avanzados, casos de estudio, plantillas, anti-patrones, contribución y referencias.

Cada afirmación sobre los cuatro repos lleva `path:line` relativo a la raíz de ese proyecto. Cada afirmación externa lleva URL y fecha de consulta. Si algo es una opinión del autor de la guía, se marca como **recomendación de esta guía**.

### Qué significa "estándar" en esta guía

No es una norma ISO ni una certificación. Es un conjunto de invariantes y criterios de evidencia que se pueden auditar:

- **Invariantes**: diez reglas que no dependen del modelo ni del framework.
- **Niveles**: L0-L4 con evidencia exigible para promover.
- **Plantillas**: estructuras copiables para prompts, tools, evals y runbooks.
- **Anti-patrones**: fallos observados en los cuatro proyectos, con su antídoto.

Un equipo puede adoptar el estándar sin adoptar el stack. Si cambia FastAPI por otro framework, los invariantes siguen; si cambia el proveedor de LLM, los niveles siguen.

## Qué NO es esta guía

| No es | Por qué importa |
|---|---|
| Un curso de prompting | El prompt es una pieza; la confiabilidad vive en el orquestador, las tools y la validación. |
| Una receta única | El estándar fija invariantes, no una arquitectura cerrada; los proyectos de la guía lo demuestran con stacks y canales distintos. |
| Asesoría legal | Para datos personales, contratos o cumplimiento normativo, revisa con un abogado. La guía da criterios técnicos, no una certificación. |
| Un benchmark de modelos | No inventamos precios, latencias ni comparativas; cada proyecto declara sus propias cifras y límites. |
| Un catálogo de frameworks | Un framework no es la arquitectura. MCP estandariza la interfaz de tools, no la política de negocio (https://modelcontextprotocol.io/specification/2025-11-25, consultado 2026-11-04). |
| Una garantía de producción | El modelo de madurez de este capítulo dice qué falta en cada nivel. |

## Método y límites de la evidencia

Este capítulo y los que siguen se apoyan en handoffs de lectura read-only de los cuatro repositorios. No se ejecutaron tests, servicios ni deploys durante esa exploración. Por eso:

- Las afirmaciones sobre código llevan `path:line` y describen lo que el archivo declara, no el resultado de una corrida.
- Las cifras de tests, cobertura y latencia son las que cada proyecto documenta; cuando dos documentos del mismo proyecto discrepan, se muestra la discrepancia en lugar de elegir una cifra.
- Las rutas son relativas a la raíz de cada proyecto; el mismo nombre de archivo puede existir en dos repos con contenido distinto.
- Las afirmaciones externas se limitan a las fuentes consultadas el 2026-11-04 y llevan URL.
- Lo que no se pudo verificar se marca como límite o se omite. No se rellena con una suposición.

Este método es parte del estándar: una guía que cita mal su propia evidencia no puede exigir fail-closed a un agente.

## La tesis central: orquestador determinista, LLM acotado

La frase que ordena todo el manual es la de arriba. Conviene desglosarla porque cada capítulo la implementa desde un ángulo distinto.

**Orquestador determinista** significa que el código decide cinco cosas:

1. El flujo y los estados de la conversación.
2. Qué tools existen y quién puede ejecutarlas.
3. Qué datos se leen y con qué vigencia.
4. Cuándo se llama al modelo y cuándo no.
5. Qué pasa cuando el modelo, una tool o la red fallan.

**LLM acotado** significa que el modelo recibe un contexto preparado y un trabajo pequeño: interpretar lenguaje y redactar una respuesta breve. No decide permisos, no inventa datos y no ejecuta acciones por su cuenta.

Los cuatro proyectos usan parámetros deliberadamente conservadores:

| Proyecto | Temperatura | Límite de salida | Evidencia |
|---|---|---|---|
| AgroVoz | 0.0 | 128 tokens en la llamada local | `backend/app/services/llm_worker.py:182-186`; `backend/app/services/llm_service.py:1763-1768` |
| copiloto-recepción | 0.3 | 500 tokens | `copiloto/src/copiloto/ai/llm.py:36-50` |
| ManttoAI | 0.2 | 250 tokens (`num_predict`) | `backend/app/services/chat_service.py:142-158` |
| Wenuke | 0.3 | 500 tokens | `backend/llm.py:144-152` |

Ninguno usa el modelo como fuente de verdad. AgroVoz declara una whitelist de 19 tools y un presupuesto de 10 segundos para generación, tools y fallback (`backend/app/services/llm_service.py:81-103`, `:127-141`). copiloto-recepción usa 4 tools y un loop de 5 pasos (`copiloto/src/copiloto/ai/tools.py:73-106`; `copiloto/src/copiloto/ai/agent.py:19`). ManttoAI evalúa reglas antes de llamar a Ollama (`backend/app/services/chat_service.py:61-87`). Wenuke calcula las alertas con reglas y deja al LLM solo la redacción (`backend/main.py:566-571`; `backend/reglas.py:173-255`).

La literatura externa converge en la misma dirección. Anthropic distingue **workflows** (rutas de código que orquestan LLM y tools) de **agents** (el LLM dirige su propio proceso) y recomienda empezar por lo simple (https://www.anthropic.com/research/building-effective-agents, publicado 2024-12-19, consultado 2026-11-04). OpenAI recomienda empezar con un solo agente y agregar tools antes de orquestar varios (https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf, 2025, consultado 2026-11-04).

OWASP GenAI LLM Top 10 2026 ubica prompt injection en LLM01 y excessive agency en LLM03. Ambos problemas se contienen con límites de código —privilegios, tools, datos y acciones—, no con más instrucciones en el prompt (https://genai.owasp.org/llm-top-10/, publicado 2026-08-04, consultado 2026-11-04).

## Taxonomía de sistemas conversacionales

No todo sistema conversacional es un agente. Esta taxonomía ordena por autonomía, no por tecnología. La escala A0-A5, el costo y el riesgo son una convención cualitativa de esta guía; los ejemplos y las citas son verificables.

### N0 — Notificador (solo envía)

Envía un mensaje por evento o programación. No interpreta la respuesta ni mantiene conversación.

| Dimensión | Valor |
|---|---|
| Autonomía | A0: ninguna; el contenido es plantilla o dato precalculado. |
| Costo | Bajo: sin tokens; solo canal e infraestructura. |
| Riesgo | Bajo técnico; alto de negocio si el mensaje llega tarde, duplicado o sin opt-in. |
| Cuándo usar | Alertas, recordatorios, estado de pedido, confirmaciones. |
| Ejemplo real | El módulo de WhatsApp de Wenuke implementa el envío saliente por Graph (`Wenuke/backend/whatsapp.py:1-102`); no documenta un handler de entrada en ese módulo. |

### N1 — Bot de FAQ o guía (menú + reglas)

Responde con menús, botones, plantillas o reglas. Puede tener una máquina de estados y no necesitar LLM.

| Dimensión | Valor |
|---|---|
| Autonomía | A1: elige entre opciones predefinidas. |
| Costo | Bajo o medio: sin tokens, o una llamada corta para redactar. |
| Riesgo | Medio: callejón sin salida, respuesta rígida o una regla que tapa una pregunta específica. |
| Cuándo usar | FAQ, horarios, precios fijos, políticas, derivación a una persona. |
| Ejemplo real | copiloto-recepción tiene un flujo guiado con máquina de estados (`copiloto/src/copiloto/flow.py:204-235`) y FAQ por keywords (`copiloto/src/copiloto/hotel.py:51-62`). ManttoAI usa 15 claves de mantenimiento antes del LLM (`backend/app/services/chat_service.py:23-39`); su límite es que el match por token exacto puede secuestrar una pregunta de datos (`backend/app/services/chat_service.py:51-58`, `:69-75`). |

### N2 — Chatbot con LLM single-shot

Una llamada al modelo por turno, sin tools y sin loop. El contexto se inyecta como resumen, FAQ o documento.

| Dimensión | Valor |
|---|---|
| Autonomía | A2: redacta, no actúa. |
| Costo | Medio: una llamada por turno. |
| Riesgo | Medio: alucinación, prompt injection, inconsistencia entre turnos. |
| Cuándo usar | Redactar, resumir, explicar un dato ya calculado, ajustar tono. |
| Ejemplo real | ManttoAI llama a Ollama una sola vez y cae a un mensaje fijo si falla (`backend/app/services/chat_service.py:61-87`, `:142-158`). Wenuke responde `/preguntar` con un prompt de sistema y un resumen de clima (`backend/main.py:555-572`; `backend/llm.py:135-152`). |

### N3 — Copiloto con tools y human-in-the-loop

Lee datos de sistemas externos, propone una acción y deriva a una persona. No escribe sin confirmación humana.

| Dimensión | Valor |
|---|---|
| Autonomía | A3: consulta y propone; la persona decide. |
| Costo | Medio-alto: varias llamadas y tools por turno. |
| Riesgo | Medio-alto: tool mal parametrizada, dato viejo, falsa confirmación. |
| Cuándo usar | Disponibilidad, precios, estado de pedido, pre-reserva, soporte con datos. |
| Ejemplo real | copiloto-recepción: 4 tools, pre-reserva de 15 minutos y confirmación de recepción (`copiloto/src/copiloto/ai/tools.py:73-106`, `:32-39`; `README.md:3-7`). |

### N4 — Agente con loop y acciones

Encadena observaciones y ejecuta acciones acotadas. Requiere loop con deadline, validación en servidor, confirmación y idempotencia.

| Dimensión | Valor |
|---|---|
| Autonomía | A4: ejecuta acciones acotadas dentro de un flujo aprobado. |
| Costo | Alto: varias llamadas, tools y verificación. |
| Riesgo | Alto: efectos persistentes, duplicados, loops, costo difícil de acotar. |
| Cuándo usar | Tareas multi-paso verificables, con escrituras reversibles o confirmadas. |
| Ejemplo real | copiloto-recepción en modo `full` solo dentro de sandbox, con `create_booking` (`copiloto/src/copiloto/ai/tools.py:95-105`; `copiloto/src/copiloto/config.py:142-147`). AgroVoz usa un loop de 3 iteraciones con tools de escritura detrás de feature gates (`backend/app/services/llm_service.py:127-128`, `:801-809`). |

### N5 — Workflow multi-agente

Varios agentes o workflows con routing, handoffs o especialistas. La orquestación también es código.

| Dimensión | Valor |
|---|---|
| Autonomía | A5: el sistema decide qué especialista actúa y en qué orden. |
| Costo | Alto: múltiples llamadas, estado compartido y debugging. |
| Riesgo | Alto: errores compuestos, permisos cruzados, costo y latencia difíciles de acotar. |
| Cuándo usar | Especialidades realmente separadas, catálogos de tools grandes o permisos distintos por dominio. |
| Ejemplo real | Los cuatro handoffs describen un solo agente; ninguno documenta un workflow multi-agente. OpenAI recomienda empezar con un solo agente y agregar tools antes de orquestar varios (https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf, 2025, consultado 2026-11-04). |

Las dos fronteras que más se cruzan sin querer son N2→N3 y N3→N4. La primera ocurre cuando el LLM "responde" datos que en realidad viven en un PMS, una base o una API: en cuanto el dato cambia, el prompt no alcanza. La segunda ocurre cuando se agrega una tool de escritura sin confirmación ni validación: eso ya no es un copiloto, es un agente con permiso de escribir.

## Mapa de decisión: ¿necesito un LLM?

Se recorre de arriba abajo. Cada nivel agrega una capacidad y un riesgo; no saltes pasos.

```text
regla/plantilla → single-shot → RAG → tools de lectura → loop con escritura → multi-agente
```

| Señal en el caso | Nivel mínimo | Qué agregar | Qué no agregar todavía |
|---|---|---|---|
| La respuesta es fija o sigue un menú | N0 / N1 | Plantillas, máquina de estados, opt-in | LLM |
| Hay que redactar sobre un contexto pequeño | N2 | Prompt acotado, fallback | Tools |
| Hay que responder sobre documentos | N2 + RAG | Corpus versionado, citas, vigencia | Loop |
| El dato vive en otro sistema y cambia | N3 | Tool de lectura y validación | Escrituras |
| Hay que ejecutar varios pasos o escribir | N4 | Loop acotado, confirmación, idempotencia | Multi-agente |
| Hay especialidades o permisos separados | N5 | Routing, contratos, trazas | Autonomía sin límites |

**RAG no es sinónimo de vector database.** AgroVoz resuelve un corpus pequeño con TF-IDF top-3 y score mínimo 0.05 (`backend/app/services/rag_service.py:83-88`). copiloto-recepción resuelve FAQ con keywords (`copiloto/src/copiloto/hotel.py:51-62`). Si el corpus es pequeño y estable, un YAML versionado y una búsqueda léxica pueden ser suficientes. Recomendación de esta guía: mide el corpus y la ambigüedad antes de agregar embeddings; la complejidad de un vector store se paga con operación, no con una demo.

**Si una regla resuelve el 80%, no empieces por el LLM.** Es una recomendación de esta guía, no un umbral medido en los proyectos. Implementa la regla, mide el 20% restante y usa el modelo solo para esa cola. ManttoAI y Wenuke implementan ese patrón: reglas deterministas para el núcleo y LLM para redactar (`backend/app/services/chat_service.py:61-87`; `backend/reglas.py:173-255`). La advertencia es la otra cara: una regla sin escape puede tapar la pregunta específica que el usuario necesita (`backend/app/services/chat_service.py:51-58`, `:69-75`).

Antes de escribir código, responde:

- ¿Puedo resolver el caso con una regla, plantilla o dato fijo?
- ¿El dato es estable o cambia fuera de mi sistema?
- ¿La acción escribe, y quién la confirma?

### Tres casos resueltos con el mapa

**Caso A — Alerta de helada.** El usuario necesita un aviso, no una conversación. Nivel N0: regla determinista sobre el pronóstico, mensaje de plantilla y opt-in. Wenuke calcula la alerta con umbrales por cultivo y deja al LLM solo la redacción (`backend/reglas.py:173-255`; `backend/main.py:566-571`). Recomendación de esta guía: si el canal no tiene webhook de entrada, no lo vendas como chatbot (`backend/whatsapp.py:26`, `:53-64`).

**Caso B — FAQ de recepción.** La mayoría son horarios, ubicación y políticas. Nivel N1: menú, máquina de estados y FAQ por keywords; el LLM es opcional. copiloto-recepción lo resuelve con `flow.py` y `hotel.py` (`copiloto/src/copiloto/flow.py:204-235`; `copiloto/src/copiloto/hotel.py:51-62`). Si agregas un LLM aquí, úsalo para redactar, no para decidir la respuesta.

**Caso C — Disponibilidad y pre-reserva.** El dato vive en un PMS y la acción tiene efecto comercial. Nivel N3: tool de lectura, validación en servidor y confirmación humana. copiloto-recepción exige lectura vigente y valida la reserva en servidor con múltiples comprobaciones (`copiloto/src/copiloto/ai/tools.py:243-336`). Recomendación de esta guía: no pases a N4 hasta que la lectura y la propuesta estén medidas.

## Los 4 proyectos en una tabla

Las rutas de evidencia son relativas a la raíz de cada proyecto; cuando hace falta desambiguar, se prefija el nombre del proyecto. Los cuatro son proyectos reales con alcances distintos: copiloto y ManttoAI se declaran prototipos académicos, y Wenuke se describe como MVP (`copiloto/README.md:9-10`; `ManttoAI/README.md:9-12`; `Wenuke/docs/ARCHITECTURE.md:124-142`).

| Proyecto | Problema | Usuario | Canal | LLM | Tools | Datos | Memoria | Deploy | Lección principal |
|---|---|---|---|---|---|---|---|---|---|
| **AgroVoz** | Precios y clima fragmentados; el agricultor no navega webs ni instala apps (`README.md:17-20`; `docs/negocio/02-problema-y-mercado.md:20`) | Pequeño agricultor (`README.md:9-13`) | WhatsApp vía Open-WA y demo web (`docs/ARCHITECTURE.md:65-98`; `backend/app/api/demo.py:57-90`) | Qwen2.5-3B local Q4_K_M; OpenRouter free opcional (`README.md:46-55`; `backend/app/core/config.py:136-147`) | Whitelist de 19; 7 con feature gate; solo lectura en el intento remoto (`backend/app/services/llm_service.py:81-103`, `:801-809`) | TF-IDF top-3 con citas; frescura por fuente (`backend/app/services/rag_service.py:83-88`, `:395-429`; `backend/app/services/data_hub_service.py:421-445`) | Stateless por defecto; estado efímero de 30 min; historial opt-in de 28 días (`backend/app/core/config.py:214-224`) | Docker con 1 worker y 3 CPU/8 GB (`docker-compose.prod.yml:126-188`) | Whitelist + fallback por causa; el modelo propone, el backend decide (`backend/app/services/llm_service.py:66-78`, `:81-103`) |
| **copiloto-recepción** | La ventana comercial es de minutos; recepción saturada (`docs/caso-de-estudio.md:11-21`) | Hotel boutique y recepción (`docs/caso-de-estudio.md:11-21`) | Chatwoot (web/WhatsApp), voz, demo web (`README.md:36-43`; `copiloto/src/copiloto/app.py:440-479`) | DeepSeek o Qwen local vía API OpenAI-compatible; temp 0.3, max 500 (`copiloto/src/copiloto/ai/llm.py:36-50`) | 4 tools con esquema estricto; `MAX_STEPS=5` (`copiloto/src/copiloto/ai/tools.py:73-106`; `copiloto/src/copiloto/ai/agent.py:19`) | `hotel.yaml` con source/status; FAQ por keywords; PMS con `read_at` (`data/hotel.yaml:1-2`; `copiloto/src/copiloto/hotel.py:51-62`; `copiloto/src/copiloto/pms.py:39-55`) | Historial de 12 mensajes, tope de 60 turnos del flujo IA; demo de 24 h (`copiloto/src/copiloto/config.py:68-75`; `copiloto/src/copiloto/flow.py:60,687-690`) | Docker Compose con Chatwoot CE, Postgres y Redis; 4 GB (`docs/despliegue.md:12-26`) | El bot prepara; la persona confirma; el "sí" se verifica en el texto (`README.md:3-7`; `copiloto/src/copiloto/ai/tools.py:303-307`) |
| **ManttoAI** | Mantenimiento reactivo caro; sin SCADA asequible (`README.md:9-12`) | Operadores que consultan telemetría y alertas (`README.md:23`) | Widget web y API HTTP; sin WhatsApp (`frontend/src/components/layout/Layout.jsx:9-10`; `backend/app/routers/chat.py:88-109`) | Ollama `qwen2.5:0.5b` single-shot; temp 0.2, `num_predict=250` (`backend/app/config.py:132-134`; `backend/app/services/chat_service.py:142-158`) | Ninguna; sin function calling (`backend/app/services/chat_service.py:78-87`) | Resumen SQL del dashboard; sin RAG (`backend/app/services/chat_service.py:90-127`) | Ninguna; `historial` se acepta y se ignora (`backend/app/schemas/chat.py:13-15`; `backend/app/routers/chat.py:96`) | Vercel + Render Free + Neon; Ollama fuera del tier público (`docs/despliegue-render.md:8-29`; `render.yaml:52-53`) | Reglas primero y fallback etiquetado; el chat no aparece en el alcance (`backend/app/services/chat_service.py:61-87`; `docs/alcance/06-enunciado-alcance.md:6-12`) |
| **Wenuke** | Pronósticos urbanos; hasta 30% de pérdida anual (`README.md:34`) | Pequeño agricultor (`README.md:3-4`) | Envío saliente de WhatsApp y demo web; el módulo de WhatsApp no define un webhook de entrada (`Wenuke/backend/whatsapp.py:1-102`) | Groq `llama-3.1-70b-versatile`; temp 0.3, max 500 (`backend/config.py:10`; `backend/llm.py:144-152`) | Ninguna real; `tool_definitions.json` es declarativo (`tool_definitions.json:1-149`; `backend/llm.py:144-152`) | Open-Meteo y reglas YAML como contexto (`backend/reglas.py:35-144`; `backend/clima.py:16-66`) | Stateless; sin tabla de mensajes (`backend/main.py:555-572`) | Vercel serverless + Turso (`Wenuke/backend/vercel.json:1-14`; `Wenuke/docs/ARCHITECTURE.md:66-77`) | Canal completo o promesa honesta; reglas + offline (`backend/whatsapp.py:53-64`; `backend/llm.py:130-159`) |

Lo que comparten:

- **Determinismo antes del modelo.** Los cuatro tienen reglas, fast paths o validación en código antes de la generación libre (`backend/app/services/chat_service.py:61-87`; `backend/reglas.py:173-255`; `copiloto/src/copiloto/ai/tools.py:243-336`; `backend/app/services/llm_service.py:81-103`).
- **Fallback como ruta de primera clase.** AgroVoz usa constantes por causa (`backend/app/services/llm_service.py:66-78`); Wenuke devuelve `offline: true` (`backend/llm.py:130-159`); ManttoAI etiqueta `fuente="fallback"` (`backend/app/services/chat_service.py:78-87`).
- **Modelos y límites declarados.** AgroVoz llama al modelo local; ManttoAI configura Ollama; copiloto usa una API compatible con OpenAI; Wenuke configura Groq (`backend/app/services/llm_worker.py:182-186`; `backend/app/config.py:132-134`; `copiloto/src/copiloto/ai/llm.py:1-3`; `Wenuke/backend/config.py:8-10`).
- **Un solo agente.** Los cuatro handoffs describen una sola instancia de agente; ninguno documenta un workflow multi-agente. La complejidad está en las tools, las reglas y los canales, no en una flota de agentes.

## Los 10 invariantes del estándar

Un invariante es una regla que se cumple en todos los niveles y no se negocia por velocidad. Si un capítulo desaparece, el invariante sigue.

| # | Invariante | En una frase | Evidencia en los 4 proyectos | Capítulo dueño |
|---|---|---|---|---|
| 1 | **Fail-closed** | Sin dato verificado no hay respuesta con datos: hay un fallback constante y acotado. | AgroVoz define un fallback por causa (`backend/app/services/llm_service.py:66-78`); Wenuke devuelve `offline: true` (`backend/llm.py:130-159`). | [1](01-principios-fail-closed.md) |
| 2 | **Tool-first** | Todo dato factual sale de una tool o corpus con fuente; el modelo redacta, no inventa. | copiloto-recepción construye la respuesta sobre tools y valida el resultado (`copiloto/src/copiloto/ai/tools.py:243-336`); AgroVoz rechaza tools fuera de su whitelist (`backend/app/services/llm_service.py:81-103,1833-1842`). | [4](04-orquestacion-tools.md) |
| 3 | **Validación en servidor** | Fechas, permisos, nombres, montos y cupos se validan en código, nunca en el prompt. | La reserva de copiloto valida en servidor fechas, personas, habitación, nombre y confirmación (`copiloto/src/copiloto/ai/tools.py:243-336`). | [4](04-orquestacion-tools.md) |
| 4 | **Loop acotado** | Todo loop tiene deadline, máximo de pasos, traza y payload truncado. | copiloto: `MAX_STEPS=5` (`copiloto/src/copiloto/ai/agent.py:19`, `:173-234`); AgroVoz: 3 iteraciones y presupuesto de 10 s (`backend/app/services/llm_service.py:127-141`). | [4](04-orquestacion-tools.md) |
| 5 | **Frescura y procedencia** | Cada dato declara fuente, fecha y vigencia; lo vencido falla cerrado. | AgroVoz excluye hechos vencidos del RAG (`backend/app/services/rag_service.py:198-233`); el PMS de copiloto expone `read_at` y la reserva exige lectura vigente (`copiloto/src/copiloto/pms.py:39-55`; `copiloto/src/copiloto/ai/tools.py:266-273`). | [5](05-datos-rag.md) |
| 6 | **Memoria como presupuesto** | Historial y contexto tienen tope, TTL y consentimiento; no se guarda "por si acaso". | copiloto: 12 mensajes de historial y tope de 60 turnos del flujo IA (`copiloto/src/copiloto/config.py:68`; `copiloto/src/copiloto/flow.py:60,687-690`); AgroVoz: stateless por defecto y 28 días opt-in (`backend/app/core/config.py:214-224`). | [6](06-canales-memoria.md) |
| 7 | **Fallback observable** | La respuesta degradada se marca, se registra y se mide. | Wenuke devuelve el flag `offline` (`backend/llm.py:130-159`; `frontend/app.js:238-240`); ManttoAI devuelve `fuente="fallback"` (`backend/app/services/chat_service.py:78-87`). | [9](09-observabilidad.md) |
| 8 | **Consentimiento y mínimo privilegio** | Cada permiso es separado, explícito y verificable en código; el modo restrictivo gana. | copiloto: sandbox con allowlist y sin pedir RUT, tarjeta, teléfono ni correo (`copiloto/src/copiloto/config.py:142-147`; `copiloto/src/copiloto/ai/prompts.py:26-27`); AgroVoz: consentimiento granular y TTL por dato (`backend/app/core/config.py:214-224`). | [8](08-seguridad.md) |
| 9 | **Evals y regresión** | Cada incidente se convierte en un caso y cada cambio se compara contra un baseline. | copiloto incluye un script de 12 conversaciones con fallos bloqueantes (`scripts/model_eval.py:132-161`); AgroVoz publica cobertura y snapshots de suite (`docs/negocio/05-estado-del-proyecto.md:27-29`). | [7](07-evaluacion.md) |
| 10 | **Límites honestos** | Lo no probado se declara como no probado; no se presenta como producción. | copiloto se declara prototipo académico con datos ficticios (`README.md:9-10`); AgroVoz mantiene gates abiertos de benchmark, WER, piloto y legal (`docs/validacion-operativa.md:226-244`). | [11](11-despliegue.md) |

Si un proyecto falla un invariante, no está listo para el nivel siguiente. Los capítulos 1-11 explican cómo implementar cada uno; el [Capítulo 15](15-anti-patrones.md) muestra qué pasa cuando se omiten.

### Cómo se conectan los invariantes

No son diez reglas sueltas; tienen un orden de dependencia:

1. **Fail-closed** es la base: define qué hacer cuando no hay dato.
2. **Tool-first** y **validación en servidor** permiten afirmar un dato sin inventarlo.
3. **Loop acotado** contiene la autonomía cuando el agente ya puede actuar.
4. **Frescura y procedencia** aseguran que el dato validado siga siendo válido.
5. **Memoria como presupuesto** y **consentimiento** limitan qué información entra y cuánto tiempo se guarda.
6. **Fallback observable** y **evals** convierten los fallos en evidencia medible.
7. **Límites honestos** evitan vender como cerrado lo que todavía no tiene evidencia.

Recomendación de esta guía: si tuvieras que implementar solo uno, implementa fail-closed. Si tuvieras que elegir el segundo, elige validación en servidor.

## Modelo de madurez L0-L4

**Recomendación de esta guía:** el nivel se declara por evidencia, no por intención. No se sube de nivel por tener más features, sino por cerrar controles. Los criterios son verificables; no son una certificación.

| Nivel | Nombre | Criterio de entrada | Criterios verificables | Evidencia en los 4 proyectos |
|---|---|---|---|---|
| **L0** | Demo | Corre local, con datos ficticios o sandbox y sin credenciales reales. | Arranque reproducible en un comando; README con límites; fallback fijo; sin PII real; aviso visible de demo. | copiloto se declara prototipo académico con datos ficticios (`README.md:9-10`); ManttoAI se declara prototipo académico (`README.md:9-12`). |
| **L1** | Piloto | Usuarios reales en cohorte pequeña; lecturas reales o escrituras en sandbox. | Auth; secretos de 16+ caracteres; rate limit; consentimiento; `request_id`; kill switch; primer set de evals. | copiloto exige 5 secretos de 16+ y allowlist de sandbox (`copiloto/src/copiloto/config.py:123-140`, `:142-147`); AgroVoz valida HMAC y aplica rate limit por IP (`backend/app/core/security.py:284-320`; `backend/app/core/security.py:214-264`; `backend/app/core/config.py:166-171`). |
| **L2** | Producción interna | Operadores internos; escrituras reales con confirmación humana. | Validación en servidor; doble confirmación; idempotencia; backups probados; retención; on-call; dashboards. | copiloto exige doble confirmación en dos turnos (`copiloto/src/copiloto/ai/tools.py:303-307`); AgroVoz distingue `pending` de `delivered` en el estado persistido (`backend/app/models/consultation.py:52-57`; `backend/app/services/delivery_service.py:41-47`); copiloto tiene backup con `integrity_check` (`Makefile:65-67`). |
| **L3** | Producción con SLA | Usuarios externos y compromiso de latencia/disponibilidad. | SLO y error budget; respuesta a incidentes; prueba de carga; revisión de seguridad; simulacro de recuperación; plan de capacidad; revisión legal. | Ninguno de los cuatro handoffs documenta un SLA externo cerrado. copiloto mide un SLA interno de handoff de 120/180 s (`copiloto/src/copiloto/sla.py:1-5`, `:54-72`); AgroVoz mantiene gates operativos abiertos (`docs/validacion-operativa.md:226-244`). |
| **L4** | Multi-tenant | Varias organizaciones sobre infraestructura compartida. | Aislamiento por tenant en base y contexto; cuotas por tenant; roles; evals por tenant; facturación; auditoría; sin estado mutable compartido. | copiloto lista multi-tenant como deuda (`docs/escalabilidad.md:18-27`); ManttoAI filtra el contexto por organización (`backend/app/dependencies.py:186`; `ManttoAI/backend/app/services/tenant_scope.py:13-20`), pero ninguno de los handoffs declara L4 completo. |

**Evidencia mínima para una revisión de nivel:**

| Nivel | Qué mostrar en la revisión |
|---|---|
| L0 | Guion de demo reproducible y lista de datos ficticios. |
| L1 | Test de auth, rate limit y consentimiento; primer set de evals; kill switch probado. |
| L2 | Test de doble confirmación e idempotencia; restore de backup ejecutado; dashboard y on-call. |
| L3 | Prueba de carga; runbook de incidentes; revisión de seguridad; simulacro de recuperación; SLO con error budget. |
| L4 | Test de aislamiento por tenant; cuotas; roles; facturación; evals por tenant. |

**Regla de promoción:** un nivel se cierra cuando puedes mostrar la evidencia —test, traza, runbook o backup probado—, no cuando el código "ya lo contempla". Si no hay evidencia, el nivel sigue abierto. Esto es una recomendación de esta guía y aplica igual a un proyecto interno y a uno comunitario.

## Cómo leer esta guía según tu rol

Esta es la tabla canónica de rutas por rol. El README y el capítulo 16 remiten aquí para no duplicar la misma información en tres lugares.

| Rol | Ruta mínima | Entregable al terminar | Señal de comprensión |
|---|---|---|---|
| **Fundador / PM** | [0](00-introduccion.md) → [1](01-principios-fail-closed.md) → [10](10-costos-modelos.md) → [11](11-despliegue.md) → [13](13-casos-de-estudio.md) | Alcance de una página: nivel N0-N5, presupuesto y límite explícito. | Puede decir qué NO hará el agente y cuánto cuesta cada turno. |
| **Dev backend** | [1](01-principios-fail-closed.md) → [2](02-stack-base.md) → [3](03-system-prompts.md) → [4](04-orquestacion-tools.md) → [5](05-datos-rag.md) | Esqueleto con fallback, una tool de lectura y validación en servidor. | Ningún dato factual sale del modelo sin fuente. |
| **Dev frontend / canal** | [0](00-introduccion.md) → [3](03-system-prompts.md) → [6](06-canales-memoria.md) → [14](14-plantillas.md) | Flujo de canal con estado degradado y handoff. | El usuario ve "sin conexión" y sabe qué hacer. |
| **QA** | [1](01-principios-fail-closed.md) → [4](04-orquestacion-tools.md) → [7](07-evaluacion.md) → [15](15-anti-patrones.md) | Set de evals y casos de regresión por incidente. | Cada incidente tiene un caso que lo reproduce. |
| **Seguridad** | [1](01-principios-fail-closed.md) → [8](08-seguridad.md) → [4](04-orquestacion-tools.md) → [15](15-anti-patrones.md) | Modelo de amenazas y matriz de permisos por tool. | Toda tool de escritura tiene permiso, validación y confirmación. |
| **Ops** | [2](02-stack-base.md) → [9](09-observabilidad.md) → [10](10-costos-modelos.md) → [11](11-despliegue.md) | Dashboard, runbook y presupuesto por turno. | Puede explicar el costo, la latencia y el fallback sin abrir el código. |

Recomendación de esta guía: las rutas largas no son obligatorias. La ruta mínima cubre lo necesario para no romper un invariante; el resto se lee cuando el proyecto lo exige.

## Qué NO copiar de los 4 proyectos

Ningún proyecto es una plantilla perfecta. Estos son los puntos que el estándar corrige; el catálogo completo, con síntoma y antídoto, está en el [Capítulo 15](15-anti-patrones.md).

- **Escrituras en AgroVoz sin paso de confirmación en las funciones revisadas.** Las funciones de registro comprueban gate, identidad y consentimiento y luego persisten el gasto o la parcela (`backend/app/services/expense_service.py:267-310`; `backend/app/services/parcela_service.py:83-133`). No se verificó aquí si otro punto del flujo exige un "¿confirmas?"; no lo tomes como patrón para acciones irreversibles.
- **`BackgroundTasks` como cola durable en copiloto.** Si Chatwoot cae mientras el bot responde, ese mensaje no se reintenta (`copiloto-recepcion/README.md:138-140`; `docs/escalabilidad.md:21`). Una cola durable es requisito antes de escalar.
- **OpenWA como canal de producción.** Es un cliente no oficial y puede suspender el número (`copiloto/docs/whatsapp-demo.md:3-12`); AgroVoz lo documenta como riesgo estructural (`SECURITY.md:97-108`). Úsalo para demo, no para operación.
- **Reglas por token exacto sin escape en ManttoAI.** "Vibración" coincide, pero "vibraciones" no; una pregunta específica puede recibir la regla genérica (`backend/app/services/chat_service.py:51-58`, `:69-75`). Toda regla necesita una ruta de excepción.
- **Tools declarativas sin function calling en Wenuke.** `tool_definitions.json` describe tools, pero el LLM nunca las recibe (`tool_definitions.json:1-149`; `backend/llm.py:144-152`). Tool definitions no son tools reales.
- **Rate limit y scheduler en memoria dentro de serverless en Wenuke.** El estado se pierde entre invocaciones (`backend/main.py:69-80`; `backend/scheduler.py:32-37`). En serverless, usa un store externo o un cron.
- **Historial de chat en ManttoAI.** Cada intercambio se persiste con el mensaje y la respuesta completos (`backend/app/routers/chat.py:88-103`; `backend/app/models/chat.py:15-32`); no se verificó aquí una purga específica. Guardar filas no es memoria conversacional ni política de privacidad.
- **Cifras de tests copiadas a mano.** ManttoAI declara 375/372/3 en el README y 373/370/3 en otro documento (`ManttoAI/README.md:137-143`; `docs/auditoria/estado-implementacion.md:82-84`). AgroVoz tiene snapshots de suite contradictorios (`docs/pmbok/06-calidad.md:26-30`; `docs/negocio/05-estado-del-proyecto.md:27-29`). Genera las cifras desde el runner y publícalas con fecha.

## Checklist de arranque: 10 preguntas antes de escribir código

- [ ] 1. ¿Quién es el usuario y en qué canal ya vive?
- [ ] 2. ¿Qué decisión toma con la respuesta y qué pasa si es incorrecta?
- [ ] 3. ¿Qué porcentaje del caso resuelven reglas, plantillas o datos fijos?
- [ ] 4. ¿Qué dato es obligatorio, de qué fuente sale y con qué vigencia?
- [ ] 5. ¿Qué tools de lectura y escritura existen; cuáles son irreversibles?
- [ ] 6. ¿Quién confirma una acción irreversible y en qué turno?
- [ ] 7. ¿Qué pasa si el LLM, una tool o la red fallan?
- [ ] 8. ¿Qué memoria se guarda, por cuánto tiempo y con qué consentimiento?
- [ ] 9. ¿Qué eval demuestra que funciona y contra qué baseline se compara?
- [ ] 10. ¿Cuál es el costo por turno, el presupuesto y el límite duro?

Si no puedes responder las preguntas 1, 3, 5, 7 y 10, no escribas código: todavía no sabes qué estás construyendo.

## Glosario mínimo

| Término | Definición operativa |
|---|---|
| Orquestador | Código que decide el flujo, los permisos, las tools y los fallbacks. |
| Tool | Función con contrato e input validado que el orquestador puede ejecutar. |
| Fail-closed | Ante duda o fallo, el sistema no afirma datos: devuelve un fallback acotado. |
| RAG | Recuperar contexto de un corpus y citarlo; no es sinónimo de base vectorial. |
| HITL | Human-in-the-loop: una persona confirma o decide en un punto del flujo. |
| Eval | Caso reproducible con criterio de éxito, distinto de un test unitario. |
| Tenant | Organización o cliente aislado dentro de una misma infraestructura. |

## Preguntas frecuentes

**¿Puedo empezar directamente con un agente con tools?**
Sí, si el caso exige datos externos y ya tienes reglas, fallback y validación. Si no, empieza por N1 o N2 y mide. La pregunta 5 del checklist de arranque te dice si las tools son necesarias.

**¿Necesito un framework de agentes?**
Para N0-N3, no. Un framework no reemplaza la validación, la whitelist ni el fallback. Para N4-N5, elige por forma del workflow, durabilidad requerida, lenguaje del equipo y observabilidad; el framework no es la arquitectura. Esto es una recomendación de esta guía.

**¿Cuánto prompt necesito?**
El mínimo que exprese el rol, los límites y el formato de salida. Si el prompt crece para compensar datos que faltan o validaciones que no existen, el problema no es el prompt. El [Capítulo 3](03-system-prompts.md) cubre el contrato.

**¿Cómo sé que estoy listo para producción?**
Cuando puedes mostrar la evidencia del nivel de madurez que declaras: tests de permisos, doble confirmación, backup restaurado, trazas y un eval con baseline. La intención no cuenta.

## Checklist de cierre del capítulo

- [ ] Puedo nombrar el nivel N0-N5 de mi caso y justificarlo.
- [ ] Sé qué parte del caso resuelve una regla y qué parte necesita un LLM.
- [ ] Identifiqué si mi dato es estable o si necesita una tool.
- [ ] Sé qué acción es irreversible y quién la confirma.
- [ ] Puedo nombrar el fallback de cada camino de fallo.
- [ ] Conozco el capítulo dueño de cada invariante que mi proyecto incumple.
- [ ] Declaré el nivel de madurez actual con evidencia, no con intención.

## Siguiente capítulo

Continúa con el [Capítulo 1 — Principios fail-closed](01-principios-fail-closed.md). Ahí se define la regla que sostiene todo lo demás: sin dato verificado no hay respuesta con datos, hay un fallback explícito. Los capítulos 2-6 construyen el stack, los prompts, la orquestación, los datos y los canales sobre esa base.

**Mapa completo del manual:**

| Bloque | Capítulos |
|---|---|
| Fundamentos | [1](01-principios-fail-closed.md) · [2](02-stack-base.md) · [3](03-system-prompts.md) · [4](04-orquestacion-tools.md) |
| Datos y canales | [5](05-datos-rag.md) · [6](06-canales-memoria.md) |
| Calidad y operación | [7](07-evaluacion.md) · [8](08-seguridad.md) · [9](09-observabilidad.md) · [10](10-costos-modelos.md) · [11](11-despliegue.md) |
| Arquitectura y comunidad | [12](12-arquitecturas.md) · [13](13-casos-de-estudio.md) · [14](14-plantillas.md) · [15](15-anti-patrones.md) · [16](16-comunidad.md) |
| Apéndices | [A](A-glosario.md) · [B](B-comparativas.md) · [C](C-referencias.md) |
