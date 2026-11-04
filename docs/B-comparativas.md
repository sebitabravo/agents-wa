<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Apéndice B — Comparativas para decidir

> **Tipo:** reference (comparativas con criterio) + how-to (cómo elegir).
> **Audiencia:** equipos que ya tienen un caso y deben elegir stack, base, retrieval, proveedor, framework, canal, despliegue, observabilidad o controles.
> **Meta:** al terminar, puedes reducir opciones con una tabla, decir qué opción es "mejor para" tu restricción y justificar por qué descartas las demás.

## Cómo leer estas comparativas

Este apéndice compara opciones, no corona ganadores. Una comparación honesta dice **"mejor para"** y también **"evitar cuando"**. No existe un stack, una base o un proveedor correcto para todos los casos; existen restricciones —equipo, latencia, privacidad, presupuesto, operación— que hacen que una opción sea peor que otra.

No hay precios, tarifas ni benchmarks propios en este documento. Cuando una celda dice "verificar", la respuesta correcta exige consultar la página vigente del proveedor o la documentación de la herramienta, con su fecha. Las comparativas de frameworks y de herramientas de observabilidad son **secundarias**: provienen de fuentes de terceros y documentación pública consultada el 2026-11-04, no de una medición de los cuatro proyectos.

Los cuatro proyectos son evidencia de decisiones, no de rankings. AgroVoz, copiloto y ManttoAI usan Python/FastAPI; Wenuke usa Python/FastAPI en serverless. Ninguno usa un framework de agentes. Esa ausencia también es un dato: la ruta simple fue suficiente para los cuatro casos de este manual.

**Tres preguntas eliminan la mayor parte de la tabla:**

1. ¿El dato cambia por minuto o es estable durante semanas?
2. ¿La acción es reversible o irreversible?
3. ¿Quién opera el sistema a las 3 de la mañana?

**Mapa de decisión rápida.** Es un punto de partida, no un veredicto: cada fila supone que la restricción indicada domina y que las demás son secundarias.

| Restricción dominante | Opción inicial | Evitar de entrada |
|---|---|---|
| Equipo Python con RAG, evals o modelos locales | FastAPI y PostgreSQL o SQLite según el despliegue | Go o Java solo por performance teórica |
| Producto web TypeScript con streaming | Node/TypeScript y serverless | Reescribir la UI en Python |
| Alta concurrencia contra APIs externas | Go con un binario simple | Framework de agentes pesado |
| Organización JVM con IAM y compliance | Java/Kotlin con Spring AI o LangChain4j | Prototipo en Go sin equipo de soporte |
| Serverless sin disco persistente | Turso/libSQL o PostgreSQL gestionado | SQLite en `/tmp` |
| Corpus pequeño, estable y con términos exactos | TF-IDF, BM25 o keywords | Vector store y reindexado |
| Dato que cambia por minuto | API en vivo con hora de lectura | Corpus congelado |
| Privacidad estricta o volumen bajo | Modelo local con operación propia | API externa sin contrato de datos |
| WhatsApp masivo en producción | WhatsApp Cloud API | OpenWA sobre un número real |
| Acción irreversible o financiera | HITL, allowlist e idempotencia | Autonomía total con confirmación del modelo |

**Qué no compara este apéndice:** precios exactos, benchmarks de modelos, latencias medidas, costo total de propiedad completo —hardware, energía, personas—, features no verificadas de frameworks y herramientas, rendimiento en tu dominio, cumplimiento legal de una jurisdicción concreta ni calidad de soporte comercial. Cada una de esas preguntas exige una prueba propia o una consulta vigente.

**Cómo leer las columnas de costo:** "bajo", "medio" y "alto" son una carga relativa para el caso típico de la columna, no una tarifa ni una factura. El costo real se calcula por turno y por conversación con el [Capítulo 10](10-costos-modelos.md); una opción "barata" por token puede ser cara por reintentos, tools o contexto.

## 1. Stacks backend

| Stack | Ecosistema IA | Tipado | Async | Deploy | Equipo | Mejor para |
|---|---|---|---|---|---|---|
| **Python / FastAPI** | Muy amplio: SDKs de proveedores, embeddings, evals, runtimes locales y ciencia de datos | Progresivo: type hints, mypy/pyright, Pydantic | Bueno para I/O; el trabajo CPU-bound (modelo local, ffmpeg) exige proceso o worker aparte | Contenedor, VM, PaaS; serverless con límites | Python, ML y datos | Agente con tools, RAG, evals y modelos locales |
| **Node / TypeScript** | Amplio en web y agentes: Vercel AI SDK, LangChain.js, SDKs de proveedores y MCP | Estático (TypeScript), útil para contratos de tools | Event loop excelente para I/O; pobre para CPU sostenida | Serverless, edge y contenedores | Frontend y fullstack TypeScript | Producto web, streaming de UI y serverless |
| **Go** | Moderado: SDKs de proveedores y MCP; menos ecosistema de evals y ML | Estático y explícito | Goroutines excelentes para concurrencia de I/O | Binario único, contenedor, bajo consumo | Backend e infraestructura | Gateway u orquestador de alta concurrencia contra APIs externas |
| **Java / Kotlin** | Empresarial: Spring AI, LangChain4j, SDKs de nube | Estático | Hilos virtuales (Java) o corrutinas (Kotlin) | JVM en contenedor; plataformas empresariales | Equipos JVM y enterprise | Integración con sistemas corporativos, gobierno e IAM existente |

| Stack | Usar cuando | Evitar cuando |
|---|---|---|
| Python / FastAPI | El equipo ya es Python; hay RAG, evals, modelos locales o ciencia de datos | El equipo no mantiene Python ni quiere operar dependencias pesadas |
| Node / TypeScript | La interfaz y el streaming son el producto; el equipo es TS; el deploy es serverless | Hay inferencia local pesada o un pipeline de datos/ML |
| Go | Importan el volumen, la latencia predecible y un binario simple de operar | Se itera rápido sobre prompts y evals, o se necesita NLP/ML nativo |
| Java / Kotlin | La organización ya vive en JVM, Spring, IAM y compliance | Es un prototipo pequeño, el equipo no es JVM o se busca el despliegue más liviano |

**Nota de honestidad:** el stack no decide la arquitectura. Un workflow con reglas y una llamada single-shot se implementa en cualquiera; el lenguaje pesa en el ecosistema de evals, en la disponibilidad de SDKs y en quién puede mantenerlo. "Ecosistema IA" es una observación cualitativa: verifica el SDK y el modelo que piensas usar, no la existencia de una carpeta `examples/`.

**Evidencia en los cuatro proyectos:** los cuatro usan Python/FastAPI. AgroVoz y copiloto lo combinan con modelos locales y servicios de dominio; ManttoAI con FastAPI y un frontend React/Vite; Wenuke con serverless y Pydantic v2. Ninguno eligió Node, Go o Java. Eso no convierte a Python en una regla: describe un autor y cuatro contextos donde el ecosistema de IA y el equipo pesaron más que el lenguaje.

### Cómo decidir en 5 preguntas

1. ¿En qué lenguaje puede mantener el sistema el equipo actual, sin contratar?
2. ¿La inferencia es local o API? Si es local, ¿qué runtime y cuánta CPU/RAM hay?
3. ¿El cuello de botella es I/O de red o CPU sostenida?
4. ¿El despliegue objetivo es contenedor, PaaS o serverless?
5. ¿Necesitas evals, embeddings y herramientas de datos en el mismo lenguaje?

## 2. Bases de datos

| Base | Escala | Concurrencia | Serverless | Operación | Costo | Mejor para |
|---|---|---|---|---|---|---|
| **SQLite** | Baja/media en un nodo; el límite es la escritura, no el volumen | Un escritor; lectores con WAL | Deficiente con disco efímero; solo con volumen persistente | Casi nula: un archivo, backup e `integrity_check` | Muy bajo, incluido en el host | Demo, piloto, un tenant, modelos locales |
| **PostgreSQL** | Alta; vertical y con réplicas | MVCC y pool de conexiones | Gestionado (Neon, RDS, Supabase; verificar) | Media: backups, upgrades, pool, observabilidad | Variable por instancia y almacenamiento | Producción, multi-tenant, transacciones y pgvector |
| **MySQL** | Alta | Alta con pool | Gestionado y opciones serverless compatibles (verificar) | Media | Variable | Equipos que ya operan MySQL o stacks PHP/Laravel |
| **Turso / libSQL** | Media; lecturas distribuidas y escritura en primario (verificar modelo vigente) | HTTP; verificar transacciones multi-statement | Nativa para serverless y edge | Baja: gestionado | Bajo en planes pequeños; verificar | Serverless con estado pequeño (Wenuke) |
| **Redis** | Alta en memoria; limitada por RAM | Alta por instancia; clúster para escalar | Gestionado (Upstash, ElastiCache; verificar) | Baja/media | Variable por memoria | Caché, rate limit, sesiones y colas ligeras; no es fuente de verdad |

| Base | Usar cuando | Evitar cuando |
|---|---|---|
| SQLite | Hay un solo nodo, pocos usuarios y el backup es un archivo | Hay varias réplicas, escrituras concurrentes o serverless sin volumen |
| PostgreSQL | Hay producción, multi-tenant, transacciones o búsqueda vectorial | No hay equipo ni servicio gestionado para operarla |
| MySQL | Ya existe MySQL, experiencia operativa o un stack que lo asume | Necesitas extensiones específicas de PostgreSQL y no las verificaste |
| Turso / libSQL | El deploy es serverless y el estado es pequeño, con lecturas cercanas | Hay transacciones complejas o escritura intensiva; verifica límites |
| Redis | Necesitas caché, rate limit, sesión o cola efímera | Necesitas durabilidad como fuente de verdad o no puedes perder datos |

**Nota de honestidad:** SQLite en un serverless con `/tmp` efímero no es una base de datos: es una carpeta temporal. La decisión no es "cuál es mejor", sino **dónde vive el estado y qué pasa si el proceso muere**. El proyecto AgroVoz documenta SQLite para menos de 1.000 usuarios y PostgreSQL recién por encima de 10.000; son cifras de su contexto, no una regla universal.

**Evidencia en los cuatro proyectos:** AgroVoz usa SQLite con WAL y un solo escritor. copiloto usa SQLite para el estado del copiloto y PostgreSQL/Redis para Chatwoot. ManttoAI usa MySQL en local y PostgreSQL en Neon para el deploy público. Wenuke usa Turso/libSQL en producción y `aiosqlite` en local. Los cuatro evitan una base vectorial; el estado y el despliegue, no la moda, explican cada elección.

### Cómo decidir en 5 preguntas

1. ¿Cuántas escrituras concurrentes necesitas y cuántas réplicas tendrás?
2. ¿El despliegue es serverless con disco efímero?
3. ¿Necesitas transacciones multi-statement y claves foráneas?
4. ¿Quién hace backups, restores y migraciones?
5. ¿Necesitas extensiones como pgvector o búsqueda de texto completo?

## 3. Retrieval

| Estrategia | Tamaño de corpus | Frescura | Costo | Explicabilidad | Mejor para |
|---|---|---|---|---|---|
| **Sin RAG (reglas o contexto)** | Nulo o muy pequeño y estructurado | La del dato inyectado; alta si se calcula por turno | Muy bajo | Alta | FAQ, políticas, dashboard y datos ya calculados |
| **TF-IDF / BM25** | Decenas a cientos de documentos; vocabulario exacto | Corpus versionado con TTL; reindexar al cambiar | Bajo (CPU) | Alta: se ve el término que coincide | Corpus YAML pequeño o mediano (AgroVoz) |
| **Embeddings + vector store** | Miles a millones de fragmentos no estructurados | Depende del pipeline de reindexado; puede quedar viejo | Medio: embeddings, índice y operación | Media/baja: la similitud no siempre se explica | Preguntas semánticas sobre documentos |
| **Híbrido** | Grande y heterogéneo | Pipeline de indexación y TTL | Alto: dos recuperadores y reranking | Media: combina señal léxica y densa | Corpus grande con nombres, códigos y sinónimos |
| **API en vivo** | Sin corpus; el dato vive en el sistema fuente | Máxima, con hora de lectura | Por llamada: latencia, cuota y disponibilidad externa | Alta si la fuente es autoritativa | Precios, clima y disponibilidad (Wenuke, PMS) |

| Estrategia | Usar cuando | Evitar cuando |
|---|---|---|
| Sin RAG | El dato ya está calculado o cabe en una regla | La pregunta es abierta y el corpus cambia |
| TF-IDF / BM25 | El corpus es pequeño, estable y usa términos exactos | Hay sinónimos, paráfrasis o un corpus grande |
| Embeddings + vector store | El corpus es no estructurado y la semántica importa | El corpus es pequeño, hay PII sin control o no puedes medir retrieval |
| Híbrido | Hay corpus grande y mezcla de códigos, nombres y lenguaje natural | No hay evals de retrieval y el costo/latencia ya es un problema |
| API en vivo | El dato cambia por minuto o por transacción | La fuente no tiene SLA ni caché y el turno no puede depender de ella |

**Nota de honestidad:** RAG no es sinónimo de base vectorial. AgroVoz resuelve su corpus con TF-IDF top-3 y citas; copiloto resuelve FAQ con keywords; Wenuke lee clima en vivo; ManttoAI inyecta un resumen SQL. Ninguno de los cuatro usa embeddings. Si agregas un vector store, el costo no es la demo: es el reindexado, el aislamiento por tenant, la evaluación de retrieval y la operación del índice.

**Evidencia en los cuatro proyectos:** AgroVoz indexa YAML con TF-IDF, top-3 y score mínimo; copiloto hace match de keywords sobre `hotel.yaml`; ManttoAI concatena totales del dashboard; Wenuke consulta OpenMeteo y evalúa reglas. La lección no es "no uses vectores": es que el corpus pequeño y estructurado se resuelve antes de pagar la operación de un índice.

### Cómo decidir en 5 preguntas

1. ¿Cuántos documentos hay y qué tan estructurados son?
2. ¿El dato cambia por minuto o puede vivir versionado durante semanas?
3. ¿Necesitas citar fuente y fecha en cada respuesta?
4. ¿La coincidencia exacta de términos resuelve la mayoría de las consultas?
5. ¿Puedes medir recall y precisión antes de agregar reranking o embeddings?

## 4. Proveedores LLM

| Proveedor | Calidad | Latencia | Costo | Privacidad | Tool calling | Disponibilidad | Lock-in | Mejor para |
|---|---|---|---|---|---|---|---|---|
| **OpenAI** | Alta/frontera; varía por modelo y tarea | Baja/media según modelo y región | Medio/alto; verificar precio vigente | Depende de plan, región y retención | Maduro y ampliamente soportado | Alta, con límites por tier | Medio/alto por formato y ecosistema | Uso general, tools y prototipo rápido |
| **Anthropic** | Alta/frontera en razonamiento y contexto largo | Media | Medio/alto; verificar | Depende de plan y región | Maduro (tool use) | Alta, con límites | Medio | Razonamiento, contexto largo y documentos |
| **Google** | Alta (familia Gemini; verificar modelo) | Baja/media | Medio; verificar | Depende de AI Studio o Vertex y región | Bueno; verificar modelo | Alta vía Vertex o AI Studio | Medio/alto si usas Vertex | GCP, grounding e integración empresarial |
| **Groq** | Depende del modelo abierto hospedado; media/alta | Muy baja en modelos soportados | Bajo/medio; verificar | Del proveedor; verificar retención | Variable por modelo; verificar | Límites por tier; el catálogo puede cambiar | Bajo/medio (API compatible) | Chat de baja latencia y alto throughput (Wenuke) |
| **OpenRouter** | La del modelo upstream; variable | Variable por proveedor | Variable, con posible fee; verificar | Depende del upstream; los modelos gratuitos pueden tener condiciones distintas | Depende del modelo | Multi-proveedor, pero catálogo rotativo y límites | Bajo | Experimentar modelos y fallback multi-proveedor (AgroVoz free) |
| **Local (Ollama / llama.cpp)** | Limitada por hardware y tamaño; verificar con evals propias | Alta en CPU; baja con GPU | Fijo (hardware y operación); marginal bajo | Alta: los datos no salen del servidor | Depende del runtime y del modelo | Autogestionada | Bajo, con costo operativo | Privacidad, volumen bajo y offline (AgroVoz, ManttoAI) |

| Proveedor | Usar cuando | Evitar cuando |
|---|---|---|
| OpenAI | Necesitas tool calling maduro, ecosistema y un equipo sin infraestructura ML | La región o la retención no cumplen, o el costo por token domina |
| Anthropic | El caso exige razonamiento o contexto largo sobre documentos | Necesitas modelo local o el precio no cierra con tu volumen |
| Google | Ya estás en GCP, usas Vertex o necesitas grounding | El equipo no quiere operar GCP o necesitas portabilidad total |
| Groq | La latencia es la restricción y el modelo abierto soportado alcanza | Necesitas el modelo más capaz o un catálogo estable a largo plazo |
| OpenRouter | Quieres probar varios modelos y tener fallback multi-proveedor | La privacidad de los modelos gratuitos no es aceptable o necesitas SLA |
| Local | La privacidad manda, el volumen es bajo y hay quien opere el servidor | No hay hardware, no hay operación o la calidad no pasa tus evals |

**Nota de honestidad:** no hay precios a propósito. Cualquier tarifa cambia y una tabla de este manual quedaría vieja antes de publicarse. "Calidad" es contextual: el modelo que gana en razonamiento abierto puede perder en extracción barata y en latencia. **Verifica precios, cuotas, retención y capacidades vigentes** en la página del proveedor, con fecha de consulta.

**Evidencia en los cuatro proyectos:** Wenuke usa Groq con un modelo abierto; AgroVoz usa Qwen2.5-3B local y OpenRouter free como opción; copiloto usa DeepSeek o un modelo local compatible con OpenAI; ManttoAI usa Ollama con `qwen2.5:0.5b` y lo apaga en el deploy público por memoria. No hay uso directo documentado de OpenAI, Anthropic o Google en los cuatro handoffs. La decisión de cada proyecto fue por restricción operativa —costo, privacidad, latencia o hardware—, no por un ranking.

### Cómo decidir en 5 preguntas

1. ¿Qué tarea concreta debe resolver y cuál es la calidad mínima que pasa tus evals?
2. ¿Cuál es el p95 de latencia que el canal tolera?
3. ¿Los datos pueden salir del país o del servidor? ¿Qué retención acepta el proveedor?
4. ¿Necesitas tool calling y salida estructurada en el modelo elegido?
5. ¿Cuánto cuesta cambiar de proveedor: formato, prompts, evals y SDK?

## 5. Frameworks de agentes

**Comparativa secundaria.** La tabla se basa en fuentes de terceros y documentación pública consultada el 2026-11-04; no es una medición propia ni un ranking. "No consta" significa que la fuente consultada no lo destaca, no que la capacidad no exista. Verifica la versión vigente antes de decidir.

| Framework | Modelo mental | Durabilidad | HITL | MCP | Tracing | Mejor para | Costo de adopción |
|---|---|---|---|---|---|---|---|
| **LangGraph** | Grafo de estado con nodos y aristas | Checkpoints e interrupts; ejecución durable | Explícito en el grafo | Sí | Según integración | Workflows complejos con ramas, ciclos y aprobación | Medio/alto: más integración |
| **Pydantic AI** | Agentes tipados con validación Pydantic | Vía Temporal, DBOS o Prefect | Según integración | Sí | Según integración | Equipos Python/FastAPI que ya viven en tipos | Medio: ecosistema Pydantic |
| **OpenAI Agents SDK** | Minimalista: agents, tools, handoffs, guardrails, sessions | Sessions; durabilidad no destacada | Guardrails y handoffs | Sí | Por defecto | Empezar rápido en el ecosistema OpenAI | Bajo |
| **Google ADK** | Workflow agents (sequential, parallel, loop) y grafo 2.0 | Según despliegue en Vertex AI | Según integración | No consta en la fuente | Evals y despliegue gestionado | Google Cloud y Gemini | Medio: acopla al stack Google |
| **CrewAI** | Equipos de roles que colaboran | No destacada; estado menos explícito | No consta en la fuente | No consta en la fuente | No consta en la fuente | Prototipado rápido de equipos | Bajo para demo; alto para producción |
| **Mastra / Vercel AI SDK** | Workflows y agentes en TypeScript | Workflows y memoria | Según integración | Sí | Según integración | Equipos TypeScript/Next.js | Bajo/medio |
| **Claude Agent SDK** | Sesiones, hooks y permisos para Claude | Sesiones | Hooks y permisos | No consta en la fuente | No consta en la fuente | Automatización con Claude | Bajo si ya usas Claude |

| Framework | Usar cuando | Evitar cuando |
|---|---|---|
| LangGraph | Hay ramas, ciclos, checkpoints o HITL explícito | Es un FAQ simple o el equipo no tiene tiempo de integración |
| Pydantic AI | El equipo es Python/FastAPI y quiere tipos y validación | El flujo no necesita framework o el equipo no es Python |
| OpenAI Agents SDK | Quieres empezar rápido con agents, handoffs y guardrails | Necesitas durabilidad fuerte o independencia estricta de proveedor |
| Google ADK | El stack es GCP/Gemini y quieres workflow agents | No usas Google Cloud o MCP es un requisito |
| CrewAI | Prototipas equipos de roles y priorizas velocidad | Producción con estado, durabilidad y HITL exigentes |
| Mastra / Vercel AI SDK | El producto es TypeScript/Next.js y necesitas streaming | Hay Python/ML o modelos locales en el camino crítico |
| Claude Agent SDK | Ya usas Claude y necesitas sesiones, hooks y permisos | Necesitas multi-proveedor o estás fuera del ecosistema Claude |

**La regla que ordena la tabla:** el framework no es la arquitectura. Elige por forma del workflow, durabilidad requerida, modelo y proveedor, lenguaje del equipo y observabilidad. Para un bot de FAQ con reglas y una llamada single-shot, cualquiera de estos frameworks es sobreingeniería: agrega una dependencia, oculta el prompt que necesitas depurar y suma una superficie de actualización.

**Evidencia en los cuatro proyectos:** ninguno usa un framework de agentes. copiloto y AgroVoz implementan el loop a mano; ManttoAI y Wenuke ni siquiera necesitan loop. copiloto tiene máquina de estados, tools y HITL sin LangGraph; AgroVoz tiene whitelist y loop acotado sin SDK. Si tu caso se parece a estos, el framework no es el primer problema: la arquitectura y la validación lo son.

### Cómo decidir en 5 preguntas

1. ¿Puedes dibujar la ruta en código o el plan depende de lo que devuelve el mundo?
2. ¿Necesitas checkpoints, reanudación y durabilidad, o una sola llamada alcanza?
3. ¿Hay una persona que aprueba en medio del flujo?
4. ¿El equipo domina el lenguaje y el ecosistema del framework?
5. ¿Puedes depurar el turno sin leer el código interno del framework?

## 6. Canales

| Canal | Costo | Aprobación | Límites | Latencia | Mejor para | Riesgo |
|---|---|---|---|---|---|---|
| **WhatsApp Cloud API** | Por conversación o mensaje según categoría; verificar tarifa vigente | Negocio en Meta, número y plantillas | Ventana de servicio y plantillas para iniciar; calidad del número | Segundos | Usuarios que ya viven en WhatsApp | Rechazo de plantillas, cambios de política y calidad |
| **WhatsApp no oficial (OpenWA)** | Infraestructura y número; sin tarifa oficial | Sin aprobación de Meta, pero fuera de sus términos | Depende de WhatsApp Web; sesión frágil | Baja/media | Demo o prototipo interno | Bloqueo o suspensión del número; incumplimiento |
| **Telegram** | Bot API sin costo directo; verificar | Token de BotFather, sin revisión de negocio | Límites de tasa y longitud por mensaje; verificar | Baja | Comunidades técnicas y alertas internas | Alcance limitado en el público objetivo |
| **Web widget** | Infraestructura y LLM; sin costo por mensaje | Sin aprobación externa; autenticación propia | Sesión, CORS, cuotas y accesibilidad | Baja | SaaS, demo y usuarios autenticados | XSS, accesibilidad y privacidad de cookies |
| **Voz (STT/TTS)** | Por minuto o audio más cómputo; verificar | Proveedor telefónico y consentimiento de grabación | Duración, ruido, latencia y ausencia de salida visual | Alta: tres modelos en serie | Manos libres, campo y baja alfabetización digital | Privacidad del audio, calidad y costo por minuto |
| **IVR** | PSTN por minuto e infraestructura | Proveedor telefónico | DTMF, menús rígidos y sin contexto | Baja | Usuarios solo teléfono y routing simple | Callejón sin salida y experiencia rígida |

| Canal | Usar cuando | Evitar cuando |
|---|---|---|
| WhatsApp Cloud API | Producción, alcance y usuarios que ya usan WhatsApp | No puedes cumplir políticas y plantillas, o el costo por conversación no cierra |
| WhatsApp no oficial (OpenWA) | Una demo controlada, con un número desechable | Producción o cualquier número que no puedas perder |
| Telegram | Comunidad técnica, alertas internas o prototipo | El público no técnico no usa Telegram |
| Web widget | El producto es tu web y puedes autenticar y controlar la sesión | Necesitas notificaciones proactivas o el usuario no visita tu web |
| Voz | Manos libres, accesibilidad o campo | Respuestas largas, datos visuales o presupuesto ajustado |
| IVR | Usuarios solo teléfono y routing simple | Conversación abierta o datos complejos |

**Nota de honestidad:** canal completo o promesa honesta. Sin webhook de entrada no hay chatbot conversacional, solo notificaciones: Wenuke envía por Graph y no recibe; su chat real es la demo web. OpenWA es un cliente no oficial y puede suspender el número; úsalo para demo, no para operación. Las tarifas y políticas de WhatsApp cambian: verifica la página vigente antes de prometer un costo por conversación.

**Evidencia en los cuatro proyectos:** AgroVoz usa OpenWA, demo web y un spike de IVR con Asterisk; copiloto usa Chatwoot (web/WhatsApp vía OpenWA), voz y demo web, sin Telegram implementado; ManttoAI usa widget web y API HTTP, sin WhatsApp; Wenuke solo envía por WhatsApp Graph y su chat real es la web. Ninguno implementa inbound de WhatsApp Cloud API. El canal que se promete y el canal que existe no siempre coinciden.

### Cómo decidir en 5 preguntas

1. ¿Dónde ya está el usuario y qué canal abre todos los días?
2. ¿El mensaje lo inicia el usuario o el negocio? Si lo inicia el negocio, ¿hay plantilla aprobada?
3. ¿Necesitas voz, o el texto alcanza?
4. ¿Puedes asumir la aprobación, la ventana de servicio y la calidad del número?
5. ¿Qué pasa si el canal se cae o cambia de política: hay fallback y canal alternativo?

## 7. Despliegue

| Opción | Control | Estado | Costo | Operación | Mejor para |
|---|---|---|---|---|---|
| **Docker Compose** | Total | Volúmenes locales; tú haces backup | Fijo bajo/medio | Media: host, parches, TLS y backups | Piloto con modelos locales y un tenant |
| **PaaS (Render, Railway, Fly.io)** | Medio | Efímero salvo volumen o servicio gestionado | Bajo; crece con el uso | Baja | Demo o MVP de tráfico bajo |
| **Serverless (Vercel, Lambda, Cloud Run)** | Bajo | Efímero; el estado va a una base u objeto externo | Casi cero en reposo; por invocación | Baja, con límites | API sin estado, webhooks y frontend |
| **Kubernetes** | Alto | Volúmenes, operadores y CRDs | Alto operacional | Alta: SRE o plataforma | Varios servicios, multi-tenant y equipo con operación |
| **Edge** | Muy bajo | Sin estado durable local | Bajo por request | Baja | Auth, routing, caché y normalización; no pipeline LLM |

| Opción | Usar cuando | Evitar cuando |
|---|---|---|
| Docker Compose | Hay modelos locales, control total y un solo host | Hay multi-región, alta disponibilidad o equipo sin operación |
| PaaS | Es un MVP, el tráfico es bajo y quieres poca operación | Hay modelos locales grandes o estado persistente sin servicio gestionado |
| Serverless | La API es stateless, hay webhooks y el tráfico es variable | Hay modelos locales, schedulers, estado en memoria o procesos largos |
| Kubernetes | Hay muchos servicios, tenants y un equipo de plataforma | Hay un servicio, un cliente y ninguna guardia |
| Edge | Necesitas firma, routing, caché o normalización cerca del usuario | Necesitas inferencia, ffmpeg o estado durable |

**Nota de honestidad:** el estado es la decisión, no el proveedor. Un scheduler en el proceso, un rate limit en memoria o una sesión local no sobreviven a serverless ni a un reinicio. Los cuatro proyectos muestran los cuatro arquetipos: AgroVoz y copiloto en Compose, ManttoAI en tres gratuitos encadenados, Wenuke en serverless puro. Ninguno demuestra que su arquetipo sea universal.

**Evidencia en los cuatro proyectos:** AgroVoz corre Docker Compose en un VPS con un worker y volúmenes para modelos y SQLite; copiloto levanta Chatwoot, Postgres, Redis, PMS y puentes en Compose; ManttoAI encadena Vercel, Render y Neon; Wenuke usa dos proyectos Vercel y Turso por HTTP. Los cuatro tienen en común una decisión explícita sobre el estado y una deuda declarada sobre durabilidad o escalado.

### Cómo decidir en 5 preguntas

1. ¿Hay modelos locales o dependencias pesadas que no caben en un tier?
2. ¿Dónde vive el estado y qué pasa si el proceso muere en medio del turno?
3. ¿El tráfico es estable o variable, y cuánto cuesta el reposo?
4. ¿Quién opera, parchea y responde a las 3 de la mañana?
5. ¿Cuánto cuesta una caída y cuánto tarda un rollback?

## 8. Observabilidad

**Comparativa secundaria.** No se probaron estas herramientas en los cuatro proyectos. La columna "qué responde" describe la categoría, no una certificación de features. Verifica en la documentación vigente qué incluye cada plan, si exporta a OTel y dónde almacena el contenido.

| Señal o herramienta | Qué responde | Costo | Lock-in | Mejor caso |
|---|---|---|---|---|
| **Logs** | Qué pasó en este turno o servicio | Bajo de almacenamiento; alto si guardas contenido | Bajo | Depuración y auditoría |
| **Métricas** | Cómo va el sistema en agregado | Bajo | Bajo | SLO, costo y alertas |
| **Trazas** | Dónde se fue el tiempo y qué falló | Medio | Bajo/medio | Latencia, tools y errores compuestos |
| **OTel** | Cómo instrumento sin atarme a un proveedor | Medio de adopción | Bajo | Portabilidad; convenciones GenAI en estado Development (2026-10) |
| **Langfuse** | Trazas, evals y prompts de LLM | Medio (nube o autoalojado) | Medio | Ver el turno y evaluar; verificar plan y features |
| **Arize Phoenix** | Trazas y evals sobre OTel | Medio | Bajo/medio | Equipo que ya usa OTel; verificar features |
| **LangSmith** | Trazas y evals en el ecosistema LangChain | Medio | Medio/alto | Si ya usas LangChain; verificar |
| **Logfire** | Observabilidad Python/OTel | Medio | Medio | Equipos Pydantic/FastAPI; verificar |
| **Sentry** | Errores y performance, con trazas de AI | Medio | Medio | Monitoreo de errores; verificar alcance AI |

| Señal o herramienta | Usar cuando | Evitar cuando |
|---|---|---|
| Logs | Siempre, con redacción y `request_id` | Es la única señal y no correlaciona nada |
| Métricas | Necesitas SLO, costo o alertas de tendencia | Quieres explicar la causa de un turno concreto |
| Trazas | Necesitas depurar latencia, tools o errores compuestos | No tienes `request_id` ni `trace_id` para correlacionar |
| OTel | Quieres portabilidad y un vocabulario común | El equipo no puede operar collector y backend |
| Langfuse / Phoenix / LangSmith / Logfire / Sentry | Necesitas trazas y evals de LLM en una herramienta | El lock-in o el costo no cierran; verifica antes de migrar |

**Nota de honestidad:** la observabilidad mínima no empieza con una plataforma: empieza con `request_id`, `trace_id`, modelo, tokens de entrada y salida, latencia por etapa, tools, costo estimado, resultado —`ok`, `fallback`, `error`— y versión de prompt. Si no tienes esos campos, ninguna herramienta los inventa. El contenido —prompts, respuestas, argumentos de tools— es opt-in por privacidad y costo; guárdalo aparte y registra una referencia.

**Evidencia en los cuatro proyectos:** AgroVoz tiene `X-Request-ID` y métricas por etapa; copiloto registra eventos sin texto y separa liveness de readiness; ManttoAI expone `fuente` como contrato de observabilidad; Wenuke devuelve `offline: true` y lo muestra en la interfaz, pero no tiene traza por turno. Las señales existen en grados distintos: el hueco común es la correlación entre turno, tool y costo.

### Cómo decidir en 5 preguntas

1. ¿Qué pregunta necesitas responder: qué pasó, cuánto cuesta, dónde se fue el tiempo o por qué falló?
2. ¿Puedes guardar contenido o solo metadatos y hashes?
3. ¿Necesitas un estándar abierto para no quedar atado a un proveedor?
4. ¿Cuál es el presupuesto mensual de observabilidad y retención?
5. ¿Vas a autoalojar la herramienta o necesitas un servicio gestionado?

## 9. Controles de seguridad

**No es un ranking.** Es una guía de combinación. La eficacia es cualitativa —alta, media, baja— y depende del atacante, del canal y de la implementación; no es un porcentaje medido. El costo incluye latencia, operación y falsos positivos, no solo dinero.

| Control | Qué ataca | Eficacia esperada | Costo | Límite |
|---|---|---|---|---|
| **Filtro de input** | Inyección directa y patrones conocidos | Media/baja ante un ataque dirigido | Bajo | Se evade con paráfrasis, otro idioma o contenido indirecto; bloquea consultas legítimas |
| **Allowlist de tools** | Agencia excesiva y tools inventadas | Alta para el alcance de acciones | Bajo: es código | No valida argumentos ni intención; una tool permitida puede ser mal usada |
| **Aprobación humana** | Acciones irreversibles y financieras | Alta | Alto: latencia y operación | No escala; la fatiga de confirmación degrada la atención |
| **Sandbox** | Contención del blast radius | Alta para efectos y datos aislados | Medio | No sustituye autenticación; puede tener copias de datos reales |
| **Validación de salida** | XSS, SQL, shell y enlaces maliciosos | Alta si se aplica en el borde correcto | Bajo/medio | No corrige una alucinación factual ni una decisión de negocio |
| **Mínimo privilegio** | Permisos amplios y movimiento lateral | Alta para reducir el blast radius | Medio: inventario y revisión | Requiere mantener permisos y rotarlos |

**Cómo combinar:** allowlist de tools + mínimo privilegio + aprobación humana para lo irreversible + validación de salida en cada borde. El filtro de input es una capa extra, nunca la garantía. El sandbox sirve para demos y código no confiable; no reemplaza la autorización. La regla que resume el capítulo 8: **el prompt pide, el código dispone**.

**Nota de honestidad:** un control que no se prueba en CI no existe. Cada fila necesita al menos un caso de eval: tool no permitida, inyección directa e indirecta, PII, acción irreversible sin confirmación, salida que llega a HTML o SQL. La eficacia esperada no se mide con una demo feliz.

**Evidencia en los cuatro proyectos:** copiloto es el más maduro en combinación —HMAC, sandbox, allowlist, aprobación en el texto del huésped y validación de salida—; AgroVoz tiene HMAC, whitelist y rate limit, pero no confirmación explícita para escrituras; ManttoAI delimita la pregunta y permite chat a la cuenta demo; Wenuke loggea el teléfono completo y no tiene inbound que firmar. Ninguno cubre todos los controles con la misma madurez, y esa brecha es la lección: se combinan, no se eligen.

### Cómo decidir en 5 preguntas

1. ¿Cuál es el activo que no puedes permitirte perder: datos, dinero, cuentas o reputación?
2. ¿Qué tools escriben y cuáles son irreversibles?
3. ¿Quién confirma una acción irreversible y en qué turno?
4. ¿Qué datos entran al contexto y cuáles nunca deberían entrar?
5. ¿Qué control puedes verificar hoy en CI, con un caso que falle si se rompe?

## Errores frecuentes al comparar

| Error | Síntoma | Corrección |
|---|---|---|
| Elegir por popularidad | La opción gana porque "todos la usan" | Medir la restricción dominante: latencia, privacidad, operación o equipo |
| Comparar precio por token | El costo por turno se dispara por tools, reintentos y contexto | Calcular costo por turno y por conversación, no por tarifa aislada |
| Framework antes de arquitectura | Se adopta LangGraph o CrewAI sin estado, tools ni HITL | Dibujar la ruta más simple y justificar cada capa |
| Vector store para un corpus pequeño | Se paga reindexado e infraestructura para doce FAQs | Medir corpus y ambigüedad; probar keywords o TF-IDF primero |
| Canal sin webhook de entrada | Se promete conversación y solo hay envío saliente | Nombrar el sistema por lo que hace y completar el inbound |
| Serverless con estado en memoria | Rate limit y scheduler se reinician en cada invocación | Mover estado a base, caché o cron externo |
| Observabilidad sin `trace_id` | Hay logs, pero no se puede reconstruir el turno | Instrumentar `request_id`, `trace_id` y spans por etapa |
| Benchmarks de otra persona | El número no se reproduce en tu corpus ni en tu tráfico | Medir con tu dataset, tu modelo y tu presupuesto |

Una comparativa se usa para **descartar opciones con justificación**, no para delegar la decisión. Si dos alternativas siguen empatadas después de la tabla, la diferencia no está en la tecnología: está en el equipo, en el costo de cambio o en una prueba que todavía no hiciste.

## Antes de cerrar la decisión

Una decisión comparativa se registra, no se recuerda. Deja constancia de:

- [ ] La restricción dominante y por qué las demás son secundarias.
- [ ] La opción elegida y las dos que descartaste, con el motivo.
- [ ] El costo por turno y el costo de operación estimados.
- [ ] La prueba que hiciste con tu corpus o tu tráfico.
- [ ] La fecha de la próxima revisión y la señal que la dispara.

Sin ese registro, la próxima persona vuelve a comparar desde cero y probablemente elige distinto.

## Cierre

Ninguna comparativa reemplaza una prueba con tu corpus, tu tráfico y tu presupuesto. La regla es siempre la misma: **elige la opción más simple que pasa tus evals y cambia cuando una restricción medida lo exija**, no cuando una tabla te lo sugiera.

Si una decisión sigue abierta, vuelve al [Capítulo 12](12-arquitecturas.md) para la forma de la arquitectura, al [Capítulo 10](10-costos-modelos.md) para el costo por turno y al [Capítulo 7](07-evaluacion.md) para la evidencia que debe respaldarla. El glosario de [A — Glosario](A-glosario.md) define los términos que aparecen en estas tablas.
