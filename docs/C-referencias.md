<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Apéndice C — Referencias: bibliografía anotada

> **Tipo:** reference (bibliografía anotada; no es un listado de enlaces).
> **Audiencia:** quienes escriben, revisan u operan agentes y chatbots, y necesitan verificar de dónde sale cada afirmación del manual.
> **Meta:** al terminar, sabes qué leer primero, qué fuente sostiene cada capítulo, cuáles son secundarias y cómo mantener esta lista sin convertirla en un cementerio de URLs.
> **Edición:** primera, con consulta de fuentes al 2026-11-04.

## La respuesta primero

Una bibliografía no se lee de principio a fin: se consulta. Si solo tienes una hora, lee en este orden:

1. **OWASP GenAI LLM Top 10 2026**, entradas LLM01, LLM02, LLM03 y LLM06.
2. **Anthropic, Building Effective Agents** y **OpenAI, A Practical Guide to Building Agents**.
3. Las fuentes de **evaluación** de la sección 3.
4. **OpenTelemetry GenAI Semantic Conventions**, cuando ya tengas algo que medir.
5. Los **frameworks**, al final: es la capa que más cambia y la que menos decide.

La razón del orden es simple: las cuatro primeras capas definen qué construyes, qué riesgo aceptas y cómo sabrás si funciona. El framework solo ejecuta esa decisión. Un equipo que empieza por el framework termina adaptando el problema a la herramienta.

## Cómo usar este apéndice

### Prioridad de lectura

| Orden | Fuente | Para qué | Cuándo |
|---|---|---|---|
| 1 | OWASP LLM Top 10 2026 | Modelo de amenazas y contención | Antes de diseñar tools, prompts o permisos |
| 2 | Anthropic y OpenAI | Decidir workflow vs agente y clasificar tools por riesgo | Antes de elegir framework |
| 3 | Evals (OpenAI, Anthropic, LangChain, Google) | Definir "funciona" con evidencia | Antes del primer prompt de producción |
| 4 | OTel GenAI | Medir, depurar y costear | Antes del primer deploy |
| 5 | Frameworks | Implementar | Después de las decisiones anteriores |

### Cómo leer una entrada

Cada entrada declara organismo, fecha o edición, capítulos que la usan, URL verificable, por qué leerla y una advertencia. Salvo que se indique otra cosa, todas las fuentes se consultaron el **2026-11-04**.

- **Primaria:** la afirmación se puede rastrear al documento original del organismo o del autor.
- **Secundaria:** interpreta, compara o resume a otros. Sirve para orientarte y descubrir fuentes, no para sostener un hecho técnico.
- **Cambiante:** precios, límites, features o versiones que el proveedor puede modificar sin aviso. Cuando una entrada depende de esos datos, su advertencia lo indica y se enlaza la página oficial; no se copia el número.

Si una entrada no tiene URL, es porque el brief de investigación no permitió verificarla. En ese caso se cita título y organismo; no se completa con una URL supuesta.

## 1. Seguridad y riesgo

Si solo lees una sección de este apéndice, lee esta. Los capítulos 0, 7, 8, 9, 10 y 13 la usan para distintos recortes del mismo problema: injection, fuga de información, agencia excesiva y consumo sin límite.

### 1.1 OWASP GenAI LLM Top 10 2026
**Tipo:** primaria. **Organismo:** OWASP GenAI Security Project. **Publicado:** 2026-08-04. **Capítulos:** 0, 7, 8, 9, 10, 13.
**URL:** https://genai.owasp.org/llm-top-10/ y https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/
**Por qué leerla:** es el mapa de riesgo que ordena el capítulo 8. La edición 2026 se contrastó por primera vez con un registro de incidentes reales (unos 7.714, de los cuales 6.639 son clasificables), no solo con votación de expertos. Ese detalle importa: es un punto de partida para el threat model, no un ranking de popularidad.
**Advertencia:** la lista y el orden cambian entre ediciones. En 2026, Excessive Agency sube del puesto 6 al 3, Unbounded Consumption del 10 al 6, Improper Output Handling baja del 5 al 10 y System Prompt Leakage se renombra Hidden Context Exposure. No mezcles la numeración de 2025 con la de 2026. Licencia CC BY-SA 4.0: si reproduces la lista, atribuye.

### 1.2 OWASP LLM01:2026 — Prompt Injection
**Tipo:** primaria (entrada del Top 10 2026). **Organismo:** OWASP. **Publicado:** 2026-08-04. **Capítulos:** 0, 8, 13.
**URL:** https://genai.owasp.org/llm-top-10/ (entrada LLM01 de la edición 2026)
**Por qué leerla:** el modelo no distingue instrucciones de datos. Cualquier texto recuperado, resultado de una tool o mensaje de un tercero puede intentar cambiar el objetivo. La consecuencia práctica no es "buscar el filtro que la elimina", sino asumir que será explotada y limitar el daño: privilegios mínimos, tools acotadas, datos mínimos y confirmación humana en acciones irreversibles.
**Advertencia:** la entrada describe el riesgo y mitigaciones generales, no una receta infalible. La eficacia de cada control depende del modelo, del canal y de la tool. La edición 2026 mantiene Prompt Injection en el puesto 1.

### 1.3 OWASP LLM02:2026 — Sensitive Information Disclosure
**Tipo:** primaria (entrada del Top 10 2026). **Organismo:** OWASP. **Publicado:** 2026-08-04. **Capítulos:** 8, 9.
**URL:** https://genai.owasp.org/llm-top-10/ (entrada LLM02 de la edición 2026)
**Por qué leerla:** la fuga no es solo la respuesta final. También son superficie los argumentos de una tool, las trazas de razonamiento, los fragmentos recuperados, los logs, la telemetría, los embeddings y hasta el timing o la longitud de los tokens. El capítulo 9 la usa para justificar que el contenido no se loggee por defecto.
**Advertencia:** incluye datos personales de terceros y secretos, no solo datos del usuario que conversa. La obligación legal aplicable se revisa en la sección 7 y requiere abogado.

### 1.4 OWASP Top 10 for Agentic Applications (ASI)
**Tipo:** primaria (complementaria del Top 10 2026). **Organismo:** OWASP. **Publicado:** anunciado el 2025-12-09 y mapeado en el apéndice del Top 10 2026. **Capítulos:** 8 (lectura complementaria).
**URL:** no verificada en el brief; citar por título y organismo, o consultar el apéndice del Top 10 2026.
**Por qué leerla:** los riesgos de sistemas que actúan con autonomía, identidad y herramientas no se agotan en el Top 10 de LLM. Úsala para revisar la arquitectura completa, no para reemplazar el análisis de prompt injection o de fuga de información.
**Advertencia:** este apéndice no reproduce su lista porque el brief no la verificó. No inventes identificadores ASI ni cites una numeración que no puedas contrastar. Es complementaria, no un sustituto.

### 1.5 NIST AI Risk Management Framework (AI 100-1)
**Tipo:** primaria. **Organismo:** NIST. **Año:** 2023. **Capítulos:** 8.
**URL:** https://www.nist.gov/itl/ai-risk-management-framework
**Por qué leerla:** da vocabulario de gobernanza —Govern, Map, Measure, Manage— y exige documentar la tolerancia al riesgo. Es útil para justificar por qué un agente con acciones irreversibles necesita controles y evidencia, no solo un prompt que pide prudencia.
**Advertencia:** es un marco voluntario; no certifica cumplimiento. Verifica la versión vigente y los perfiles aplicables a tu sector. No es un catálogo técnico de controles.

### 1.6 NIST AI 600-1 — Generative AI Profile
**Tipo:** primaria. **Organismo:** NIST. **Año:** 2024. **Capítulos:** 8.
**URL:** https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
**Por qué leerla:** es un perfil de riesgo específico para IA generativa. Su lista de riesgos transversales —confabulación, fuga de información, contenido dañino, seguridad, propiedad intelectual— ayuda a construir el threat model sin empezar de cero.
**Advertencia:** es un perfil de 2024; no cubre capacidades aparecidas después. Úsalo como checklist de identificación, no como estándar cerrado ni como prueba de cumplimiento.

### 1.7 MITRE ATLAS
**Tipo:** primaria (base de conocimiento). **Organismo:** MITRE. **Año:** base viva, sin fecha de edición única. **Capítulos:** 8 (lectura complementaria; todavía no se cita en el cuerpo).
**URL:** https://atlas.mitre.org/
**Por qué leerla:** traduce el riesgo a tácticas y técnicas de adversario, con una lógica similar a ATT&CK pero para sistemas de IA. Sirve para diseñar casos de red team y para mapear qué control detiene qué técnica, en lugar de acumular mitigaciones sin relación con un ataque concreto.
**Advertencia:** es una base de conocimiento viva, no una norma. Los identificadores, la cobertura y las técnicas cambian. No concluyas que un control es suficiente porque "cubre ATLAS"; verifica el escenario.

## 2. Arquitectura de agentes

Estas fuentes responden la pregunta que ningún framework responde: ¿esto necesita un agente o un workflow? El capítulo 12 usa las tres primeras para elegir topología; el capítulo 0, para el mapa de decisión.

### 2.1 Anthropic — Building Effective Agents
**Tipo:** primaria (investigación de vendor). **Organismo:** Anthropic. **Publicado:** 2024-12-19. **Capítulos:** 0, 10, 12.
**URL:** https://www.anthropic.com/research/building-effective-agents
**Por qué leerla:** distingue **workflows** (rutas de código que orquestan LLM y tools) de **agents** (el LLM dirige dinámicamente su proceso). Propone empezar por la solución más simple y cinco patrones de workflow: prompt chaining, routing, parallelization, orchestrator-workers y evaluator-optimizer. También advierte que un framework puede ocultar prompts y respuestas y dificultar la depuración. Es la fuente intelectual de la tesis "orquestador determinista, LLM acotado".
**Advertencia:** es una publicación de Anthropic con ejemplos ilustrativos, no un benchmark independiente. La frontera entre workflow y agente depende de la capacidad del modelo, del costo y de la tolerancia al error; vuelve a evaluarla cuando cambie el modelo.

### 2.2 OpenAI — A Practical Guide to Building Agents
**Tipo:** primaria (guía de vendor). **Organismo:** OpenAI. **Publicado:** 2025. **Capítulos:** 0, 8, 12.
**URL:** https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf
**Por qué leerla:** reduce un agente a tres componentes —model, tools, instructions— y recomienda empezar con un solo agente antes de orquestar varios. Su aporte más útil para esta guía es la clasificación de tools por riesgo: lectura vs escritura, reversibilidad, permisos e impacto financiero. El capítulo 8 la usa para decidir qué tool exige aprobación humana.
**Advertencia:** es una guía de vendor y asume el ecosistema OpenAI. No es una norma ni un estudio independiente. Los patrones manager y handoffs son opciones, no una progresión obligatoria.

### 2.3 Model Context Protocol — especificaciones
**Tipo:** primaria (especificación). **Organismo:** Model Context Protocol. **Publicado:** revisiones 2025-06-18 y 2025-11-25. **Capítulos:** 0, 8, 12; 11 lo menciona como feature flag.
**URL:** https://modelcontextprotocol.io/specification/2025-06-18 y https://modelcontextprotocol.io/specification/2025-11-25
**Por qué leerla:** estandariza cómo un server expone resources (contexto), prompts (plantillas) y tools (funciones), y aclara quién controla cada primitiva: tools model-controlled, resources application-controlled, prompts user-controlled. Su sección de seguridad exige consentimiento explícito, control de acceso, validación de inputs, rate limit, sanitización de outputs y human-in-the-loop para operaciones sensibles.
**Advertencia:** el protocolo evoluciona por revisiones; fija la versión en tu implementación. Estandariza la interfaz, no la política de negocio: la validación de tu dominio y el consentimiento siguen siendo responsabilidad de la aplicación. Las anotaciones de una tool son untrusted salvo que provengan de un server confiable.

### 2.4 Agent2Agent (A2A)
**Tipo:** mención; no verificada en el brief. **Organismo:** iniciativa impulsada por Google. **Año:** sin fecha verificada. **Capítulos:** 12 (mención).
**URL:** no citada; no se pudo verificar una URL canónica en este brief.
**Por qué leerla:** es un protocolo abierto para que agentes de distintos proveedores se comuniquen. Solo es relevante si tu arquitectura cruza límites organizacionales o de vendor; los cuatro proyectos de esta guía no lo necesitan.
**Advertencia:** tecnología emergente. No la adoptes como default ni cites versiones o fechas que no puedas verificar. Si la usas, documenta el contrato, la autenticación y qué pasa cuando el otro agente no responde.

## 3. Evaluación

El capítulo 7 cubre la deuda más común de los cuatro proyectos: tienen tests, pero en general no tienen evals de calidad. Estas cuatro fuentes cubren diseño de casos, jueces y CI.

### 3.1 OpenAI — Evaluation best practices
**Tipo:** primaria (documentación de vendor). **Organismo:** OpenAI. **Fecha:** sin fecha de publicación visible en la página consultada. **Capítulos:** 7.
**URL:** https://developers.openai.com/api/docs/guides/evaluation-best-practices
**Por qué leerla:** describe el flujo práctico de evaluación: definir criterios, construir el dataset, elegir graders, correr en CI y revisar regresiones. Complementa a Anthropic con la mecánica de plataforma y con ejemplos de graders deterministas y asistidos por modelo.
**Advertencia:** página viva y específica de OpenAI; los nombres de productos y las rutas pueden cambiar. No es un estándar independiente ni una garantía de que tu caso esté bien representado en el dataset.

### 3.2 Anthropic — Demystifying evals for AI agents
**Tipo:** primaria (investigación de vendor). **Organismo:** Anthropic. **Publicado:** 2026-01-09. **Capítulos:** 7.
**URL:** https://www.anthropic.com/research/demystifying-evals-for-ai-agents
**Por qué leerla:** es la mejor fuente para separar **capability evals** (¿qué puede hacer?) de **regression evals** (¿sigue haciendo lo que ya hacía?), entender `pass^k` cuando el sistema no es determinista y reconocer los riesgos de LLM-as-judge: posición en comparaciones pairwise, preferencia por el modelo productor y falta de calibración humana. También insiste en baseline, noise floor y casos extraídos de producción.
**Advertencia:** son recomendaciones basadas en productos Anthropic, no una norma. La calibración del juez contra humanos y la revisión de casos de alto riesgo siguen siendo obligatorias en tu contexto.

### 3.3 LangChain — LLM testing
**Tipo:** secundaria (recurso de vendor). **Organismo:** LangChain. **Publicado:** 2026-10-27. **Capítulos:** 7.
**URL:** https://www.langchain.com/resources/llm-testing
**Por qué leerla:** aporta una estructura de pruebas para aplicaciones con LLM y ayuda a separar tests deterministas de evaluaciones de calidad; es útil para decidir qué corre en cada commit y qué se ejecuta a demanda, y para no confundir un test de contrato con una eval.
**Advertencia:** recurso de vendor con ejemplos de su stack; no es un benchmark ni una comparativa neutral. Úsalo para vocabulario y estructura, no para concluir qué framework es mejor.

### 3.4 Google — Stax evaluation best practices
**Tipo:** primaria (documentación de producto). **Organismo:** Google. **Fecha:** sin fecha verificada en el brief. **Capítulos:** 7.
**URL:** https://developers.google.com/stax/best-practices
**Por qué leerla:** es la referencia de Google para diseñar evaluaciones dentro de su plataforma; es útil si tu organización ya opera en Google Cloud o necesita una segunda implementación de referencia.
**Advertencia:** documentación de producto; puede requerir acceso, cambiar de ruta o estar orientada a Stax. No sustituye el diseño de tu golden set ni la calibración de tus propios jueces.

## 4. Observabilidad

Sin trazas, un agente es una caja que a veces responde. Estas dos fuentes son la referencia para instrumentar sin inventar nombres de spans ni atributos.

### 4.1 OpenTelemetry GenAI Semantic Conventions
**Tipo:** primaria (especificación). **Organismo:** OpenTelemetry. **Estado:** Development, 2026-10. **Capítulos:** 9, 10.
**URL:** https://github.com/open-telemetry/semantic-conventions-genai
**Por qué leerla:** define spans para `invoke_agent`, `chat`/inference, `execute_tool`, `retrieval`, `embeddings` y `memory`; métricas como duración, tokens y tool calls; y atributos como modelo, tokens de entrada/salida y `finish_reasons`. También aclara que prompts y completions **no** se capturan por defecto: es opt-in por privacidad y costo, y en producción conviene guardar el contenido aparte y registrar una referencia.
**Advertencia:** está en estado Development; nombres y atributos pueden cambiar. Fija la versión y no asumas que todos los proveedores emiten las mismas convenciones. Una traza completa no reemplaza una eval: te dice qué pasó, no si estuvo bien.

### 4.2 OpenTelemetry — "Inside the LLM Call: GenAI Observability with OpenTelemetry"
**Tipo:** secundaria (blog técnico). **Organismo:** OpenTelemetry. **Publicado:** 2026-05-14. **Capítulos:** 9, 10.
**URL:** https://opentelemetry.io/blog/2026/genai-observability/
**Por qué leerla:** explica cómo instrumentar una llamada LLM de punta a punta y qué mirar cuando algo tarda o cuesta. Es el puente entre la especificación y el dashboard, con ejemplos de spans y propagación de contexto.
**Advertencia:** es una entrada de blog, no una especificación. Los ejemplos pueden quedar desfasados respecto de las convenciones. Para afirmaciones normativas, cita el repositorio de semantic conventions.

## 5. Operación y despliegue

El capítulo 11 no trata de "elegir un proveedor de alojamiento": trata de estado, salud, versiones y rollback. Estas fuentes sostienen esa parte.

### 5.1 The Twelve-Factor App
**Tipo:** primaria (manifiesto). **Organismo:** The Twelve-Factor App. **Fecha:** sitio de referencia sin fecha de edición visible. **Capítulos:** 11.
**URL:** https://12factor.net
**Por qué leerla:** configuración en el entorno, procesos stateless, logs como flujo de eventos, disposabilidad y paridad dev/prod. Es la base de por qué el estado conversacional va a un store externo y por qué el deploy debe poder matar un proceso sin perder trabajo.
**Advertencia:** está escrito para aplicaciones web, no para agentes. "Logs como eventos" no autoriza loggear PII ni prompts completos. No es una certificación ni cubre requisitos de residencia de datos.

### 5.2 Docker documentation
**Tipo:** primaria (documentación oficial). **Organismo:** Docker Inc. **Fecha:** documentación viva; consultada 2026-11-04. **Capítulos:** 11.
**URL:** https://docs.docker.com
**Por qué leerla:** es la referencia para multi-stage builds, usuario no root, filesystem de solo lectura, healthchecks y límites de recursos. Son los controles que el capítulo 11 aplica a los contenedores de los proyectos.
**Advertencia:** las flags, versiones y prácticas recomendadas cambian. Verifica contra tu engine y tu orquestador. Una imagen endurecida no reemplaza el análisis de vulnerabilidades ni la gestión de secretos.

### 5.3 Documentación de plataformas: Vercel, Render, Neon y Turso
**Tipo:** primaria (documentación oficial de cada proveedor). **Fecha:** documentación viva; consultada 2026-11-04. **Capítulos:** 11.
**URL:** https://vercel.com/docs · https://render.com/docs · https://neon.tech/docs · https://docs.turso.tech
**Por qué leerla:** cada plataforma define runtime, variables de entorno, healthchecks, límites del free tier, pooling de conexiones y persistencia. Consulta la doc del proveedor antes de copiar un `render.yaml`, un `vercel.json` o una cadena de conexión.
**Advertencia:** precios, límites y features cambian sin aviso; este apéndice no copia cifras. Neon y Turso son bases gestionadas: revisa pooling, región y backup. No asumas que el free tier de un proveedor se comporta como el de otro, ni que un límite documentado hoy seguirá igual en el próximo deploy.

### 5.4 Precios y límites de proveedores de modelo
**Tipo:** cambiante. **Organismos:** Anthropic, OpenAI, Google, DeepSeek, Groq y OpenRouter, entre otros. **Fecha:** consultar al momento del deploy. **Capítulos:** 10.
**URL:** no se fija una URL única; cada proveedor publica su tabla de precios y la modifica sin aviso. El capítulo 10 enlaza la de DeepSeek y advierte que no fue verificada en este manual.
**Por qué leerla:** el costo por turno se calcula con la tabla vigente del proveedor, no con una copia de este apéndice. La entrada correcta incluye modelo exacto, unidad (por millón de tokens), precio de entrada y salida, y condiciones de caching o batch.
**Advertencia:** no copies precios en documentación que va a envejecer. Registra la fecha de consulta y vuelve a calcular cuando cambie el modelo o el contrato. Un precio de prototipo no es un precio de producción.

## 6. Frameworks

Un framework no es la arquitectura (capítulo 12). Las URLs de esta sección son el repositorio o la documentación oficial de cada proyecto; son documentación viva, consultada el 2026-11-04, y por eso no se cita una fecha de publicación. Las descripciones de "para qué sirve" provienen de las comparativas secundarias del brief (2026-09 y 2026-10), **no de un benchmark propio**. Léelas como hipótesis de selección, no como veredicto.

La regla de elección de esta guía: primero la forma del workflow, después la durabilidad requerida, después el modelo y el proveedor, después el lenguaje y el equipo, y al final la observabilidad y las evals. Para un chatbot de un turno con reglas, un framework de agentes es sobreingeniería.

### 6.1 LangGraph
**Tipo:** primaria (repositorio oficial). **Organismo:** LangChain. **Capítulos:** 12.
**URL:** https://github.com/langchain-ai/langgraph
**Para qué sirve:** grafo de estado, checkpoints, interrupts y ejecución durable; encaja en workflows con ramas, ciclos y aprobación humana. **Advertencia:** más trabajo de conexión para casos simples, y la API y los patrones cambian rápido.

### 6.2 Pydantic AI
**Tipo:** primaria (repositorio oficial). **Organismo:** Pydantic. **Capítulos:** 12.
**URL:** https://github.com/pydantic/pydantic-ai
**Para qué sirve:** tipado y validación de inputs/outputs con Pydantic, independencia de modelo, integración con MCP y ejecución durable vía Temporal, DBOS o Prefect; encaja en equipos Python/FastAPI. **Advertencia:** ecosistema más joven; verifica que la integración durable que necesitas exista y esté mantenida.

### 6.3 OpenAI Agents SDK
**Tipo:** primaria (repositorio oficial). **Organismo:** OpenAI. **Capítulos:** 12.
**URL:** https://github.com/openai/openai-agents-python
**Para qué sirve:** primitivas mínimas —agents, tools, handoffs, guardrails, sessions—, tracing por defecto y MCP; es la vía rápida si ya estás en el ecosistema OpenAI. **Advertencia:** acoplamiento al vendor; los handoffs no reemplazan el diseño de estado ni la idempotencia.

### 6.4 Google Agent Development Kit (ADK)
**Tipo:** primaria (repositorio oficial). **Organismo:** Google. **Capítulos:** 12.
**URL:** https://github.com/google/adk-python
**Para qué sirve:** workflow agents (sequential, parallel, loop), grafo en la versión 2.0, evals, A2A y despliegue en Vertex AI; encaja si el equipo vive en Google Cloud y Gemini. **Advertencia:** dependencia de Gemini/Vertex; verifica qué features de la versión 2.0 están disponibles en tu runtime.

### 6.5 CrewAI
**Tipo:** primaria (repositorio oficial). **Organismo:** CrewAI. **Capítulos:** 12.
**URL:** https://github.com/crewAIInc/crewAI
**Para qué sirve:** equipos de agentes con roles y prototipado rápido; útil para explorar un flujo multi-agente sin escribir toda la orquestación. **Advertencia:** la metáfora de roles puede ocultar el estado y el control explícito; no es la mejor base para un workflow auditable con acciones irreversibles.

### 6.6 Mastra y Vercel AI SDK
**Tipo:** primaria (repositorios oficiales). **Organismos:** Mastra y Vercel. **Capítulos:** 12.
**URL:** https://github.com/mastra-ai/mastra · https://github.com/vercel/ai
**Para qué sirve:** TypeScript, workflows, memoria, evals y MCP (Mastra); herramientas de modelo, streaming y UI (AI SDK). Son dos productos distintos: no los trates como sinónimos. **Advertencia:** el ecosistema TypeScript se mueve rápido; fija versiones y revisa la compatibilidad con tu runtime serverless.

### 6.7 Claude Agent SDK
**Tipo:** primaria (repositorio oficial). **Organismo:** Anthropic. **Capítulos:** 12.
**URL:** https://github.com/anthropics/claude-agent-sdk-python
**Para qué sirve:** sesiones, hooks y permisos para agentes basados en Claude; útil si el producto ya está construido sobre ese modelo. **Advertencia:** es específico de Claude y no es portable a otros proveedores; no lo elijas si la independencia de modelo es un requisito.

### 6.8 Comparativas secundarias de frameworks
**Tipo:** secundaria. **Organismos:** publicaciones de terceros. **Fechas:** 2026-09-05, 2026-10-16 y 2026-10-15. **Capítulos:** 12.
**URL:** https://nomadx.ae/blog/google-adk-vs-openai-agents-sdk-vs-pydantic-ai-vs-langgraph/ · https://dbggr.dev/articles/agent-frameworks-compared/ · https://www.promptise.com/guides/view/python-ai-agent-frameworks-compared
**Por qué leerlas:** ofrecen vocabulario y preguntas de selección —estado, durabilidad, lenguaje, proveedor, evals— que el capítulo 12 usa como contraste. Son útiles para descubrir qué mirar en la documentación oficial.
**Advertencia:** no son benchmarks. No declaran una metodología reproducible ni miden los mismos casos; pueden tener conflicto de interés o sesgo de ecosistema. No las cites para afirmar que un framework es "mejor"; cita la documentación oficial para la API y tu propia eval para la decisión.

## 7. Legal y privacidad (Chile)

Esta sección no es asesoría legal. Es la referencia mínima para que el diseño técnico no ignore las obligaciones de datos personales.

### 7.1 Ley 21.719 — Protección de Datos Personales
**Tipo:** primaria (texto legal). **Organismo:** Biblioteca del Congreso Nacional de Chile (BCN). **Vigencia:** diciembre de 2026, según el brief consultado. **Capítulos:** 8, 9, 13.
**URL:** https://www.bcn.cl/leychile (buscar "Ley 21.719")
**Por qué leerla:** fija principios de licitud, finalidad, proporcionalidad, seguridad y retención, y derechos ARCOP (acceso, rectificación, cancelación, oposición y portabilidad). Es la referencia para justificar por qué el agente no pide datos innecesarios, por qué la memoria tiene TTL y por qué el borrado debe contemplar logs y backups.
**Advertencia:** esta guía no es asesoría legal. Verifica el texto vigente y su reglamentación antes de publicar; la entrada en vigor puede tener régimen transitorio. La fecha de diciembre de 2026 es la que reporta el brief, no una interpretación jurídica.

### 7.2 Ley 19.628 — régimen anterior
**Tipo:** primaria (texto legal). **Organismo:** BCN. **Año:** 1999, norma anterior a la 21.719. **Capítulos:** 8 (contexto; no citada en el cuerpo).
**URL:** https://www.bcn.cl/leychile (buscar "Ley 19.628")
**Por qué leerla:** entender el régimen que la 21.719 reemplaza ayuda a leer decisiones heredadas de los proyectos: consentimiento, retención, tratamiento de RUT y teléfono, y qué se consideraba dato sensible.
**Advertencia:** no la cites como régimen vigente sin verificar la transición. Puede estar derogada o coexistir durante el período que fije la ley; para una decisión de cumplimiento, revisa el texto con abogado.

**Recomendación de esta guía:** antes de cualquier deploy con datos personales, haz una revisión legal del flujo completo: qué se recolecta, dónde vive, cuánto se retiene, quién accede, cómo se borra y qué se comparte con proveedores de modelo. La bibliografía no reemplaza al abogado.

## 8. Proyectos de referencia

Los cuatro repositorios del autor son el corpus empírico del manual. No son productos ni benchmarks: son prototipos de portfolio. El análisis, las rutas y las cifras están en [13-casos-de-estudio.md](13-casos-de-estudio.md).

| Proyecto | Qué enseña | Límite declarado |
|---|---|---|
| **AgroVoz** | Llevar datos públicos con procedencia y vigencia a WhatsApp, con LLM local y fallback determinista. | Demo de portfolio; el piloto y su infraestructura ya no existen. |
| **copiloto-recepción** | Preparar una acción comercial sin ejecutarla: tools, validación en servidor y confirmación humana. | Prototipo académico con datos ficticios; sin validación con recepción ni huéspedes. |
| **ManttoAI** | Agregar un asistente a un producto IoT existente sin convertirlo en el producto. | Prototipo académico open source; no es SCADA ni sistema industrial certificado. |
| **Wenuke** | Calcular alertas agronómicas confiables y redactarlas con un LLM barato. | MVP desplegado; el canal WhatsApp solo envía mensajes, no recibe inbound. |

**Advertencia:** no los uses como referencia de producción ni copies sus cifras como si fueran benchmarks. Su valor es mostrar decisiones y fallos con `path:line`, no probar que el enfoque escala. No se incluye URL porque el brief no verificó un remoto público para los cuatro; si publicas un enlace, que sea al repositorio exacto y con fecha de commit.

## Lecturas que NO recomiendo como fuente primaria

Esta sección existe porque el manual exige trazabilidad. Una fuente que no se puede verificar puede orientar, pero no sostener una afirmación.

| Tipo de lectura | Por qué no sirve como fuente primaria |
|---|---|
| Blogs sin fecha, autor o versión | No puedes saber si describen el modelo, la API o el precio actual. Úsalos para descubrir la fuente original, no para citar. |
| Benchmarks sin metodología | Sin dataset, prompts, versiones, número de corridas y criterio de éxito, el número no es comparable con nada. |
| Comparativas de vendors | El que publica suele ganar. No son evidencia independiente y a menudo omiten el costo de integración. |
| Posts que copian a otros | Generan deriva de citas: la cita se aleja del original y pierde precisión. Si no llegan a la fuente, no la reemplazan. |
| Listicles de "top frameworks" sin código | Dan vocabulario, no una decisión. No muestran el estado, la durabilidad ni el costo real. |
| Páginas de precios replicadas en un blog | Cambian sin aviso. Ve siempre a la página oficial del proveedor y registra la fecha de consulta. |
| Hilos de redes sociales | Pueden ser señal de un incidente, pero no son fuente primaria. Busca el postmortem, el CVE o el comunicado del organismo. |
| Documentación sin número de versión | No es reproducible. Si no sabes a qué versión se refiere, no puedes verificar el comportamiento. |

El criterio es uno: **¿el lector puede reproducir o verificar la afirmación?** Si la respuesta es no, la lectura puede servir para explorar, pero no para fundamentar un capítulo. Cuando uses una de estas fuentes para descubrir algo, cita la fuente primaria a la que te llevó.

## Cómo mantener esta bibliografía

Una bibliografía sin mantenimiento se convierte en una lista de enlaces muertos. Este es el contrato mínimo:

| Frecuencia | Acción |
|---|---|
| Cada edición del manual | Revisar todas las URLs y fechas; actualizar el campo de consulta. |
| Cada 6 meses | Revisar OWASP, MCP, OTel y la Ley 21.719; son las fuentes que más cambian. |
| Cada release de un framework | Revisar solo la sección 6; no reescribir el resto por un cambio de API. |
| Ante un enlace muerto | Buscar la página canónica del organismo; si no existe, archivar la fuente y anotar el reemplazo. |
| Ante un cambio de precio o límite | No copiar el número: enlazar la página oficial y fechar la consulta. |

Reglas de versionado:

- Cada entrada declara edición o fecha. Los cambios se registran en el historial de abajo; no se sobrescriben en silencio.
- Para páginas que cambian —especificaciones, precios, documentación de producto— guarda una copia con fecha o un enlace de archivo. La cita debe seguir siendo verificable aunque la página cambie.
- Un PR de bibliografía incluye qué capítulo la usa y por qué. Un PR que solo agrega enlaces se rechaza.
- Una fuente retirada no se borra: se mueve al historial con el motivo y la fuente que la reemplaza.
- La sección 7 se revalida con revisión legal antes de cada edición. La fecha de consulta no es una opinión jurídica.

### Historial de revisiones

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-11-04 | Primera edición; fuentes consultadas para los capítulos 0 a 13. |

## Cierre

Una bibliografía es la parte del manual que permite auditarlo. Si una frase de esta guía no se puede rastrear a una fuente de este apéndice o a un `path:line` de los repositorios, trátala como recomendación de esta guía, no como hecho.

El orden de lectura no es arbitrario: primero el riesgo, después la arquitectura, después la evidencia, después la instrumentación y al final la implementación. Ese orden evita el error más común en 2026: elegir un framework antes de saber qué problema resuelves, cómo falla y cómo lo vas a medir.

Vuelve a esta página cuando cambie una especificación, no cuando cambie la moda. Y si una fuente deja de ser verificable, retírala con el mismo rigor con el que la citaste.
