<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Apéndice A — Glosario de agentes, chatbots y operación

> **Tipo:** reference (definiciones operativas).
> **Audiencia:** cualquier persona que lea, construya o revise un agente: desarrollo, producto, QA, seguridad y operaciones.
> **Meta:** al terminar, puedes interpretar los términos del manual en su acepción técnica y reconocer el error más común de cada uno.

Este glosario define los términos **en el uso de este manual**, no en su acepción más amplia. Los términos en inglés se conservan porque aparecen así en SDKs, documentación de proveedores y código. La nota final de cada entrada —"Por qué importa" o "Error común"— es la parte operativa: explica la consecuencia de confundir el concepto.

## Índice alfabético

| Letra | Términos |
|---|---|
| A | [A/B testing](#ab-testing) · [A2A](#a2a) · [agencia excesiva](#agencia-excesiva) · [agente](#agente) · [allowlist](#allowlist) · [alucinación](#alucinacion) · [anonimización y seudonimización](#anonimizacion-seudonimizacion) |
| B | [baseline y noise floor](#baseline-noise-floor) |
| C | [cadena de suministro](#cadena-suministro) · [capability eval y regresión](#capability-regresion) · [chunk](#chunk) · [citación](#citacion) · [consentimiento](#consentimiento) · [contexto](#contexto) · [contexto oculto](#contexto-oculto) · [cuota y rate limit](#cuota-rate-limit) |
| D | [deadline](#deadline) |
| E | [embedding](#embedding) · [envenenamiento de vectores](#envenenamiento-vectores) · [error budget y SLO](#error-budget-slo) · [escalation](#escalation) · [eval](#eval) · [eval offline y online](#eval-offline-online) · [exfiltración](#exfiltracion) |
| F | [fallback, degradación y fail-closed](#fallback-degradacion-fail-closed) |
| G | [golden dataset](#golden-dataset) · [groundedness](#groundedness) · [guardrail](#guardrail) |
| H | [handoff](#handoff) · [HMAC](#hmac) · [human-in-the-loop](#human-in-the-loop) |
| I | [idempotencia](#idempotencia) · [inyección de prompt y jailbreak](#inyeccion-prompt-jailbreak) |
| K | [kill switch](#kill-switch) |
| L | [llamada a herramientas](#llamada-herramientas) · [LLM-as-judge](#llm-as-judge) · [log](#log) · [loop](#loop) |
| M | [manejo de salida](#manejo-salida) · [máquina de estados](#maquina-estados) · [max steps](#max-steps) · [max_tokens](#max-tokens) · [MCP](#mcp) · [memoria](#memoria) · [métrica](#metrica) · [mínimo privilegio](#minimo-privilegio) · [multi-tenant](#multi-tenant) |
| O | [observabilidad](#observabilidad) · [orquestador](#orquestador) · [OTel](#otel) |
| P | [pass^k](#pass-k) · [PII](#pii) · [presupuesto de tokens](#presupuesto-tokens) · [prompt](#prompt) · [prompt de sistema y de usuario](#prompt-sistema-usuario) |
| R | [RAG](#rag) · [reranking](#reranking) · [retención](#retencion) · [retrieval](#retrieval) |
| S | [sandbox](#sandbox) · [sesión](#sesion) · [SLA](#sla) · [streaming](#streaming) |
| T | [temperatura](#temperatura) · [token](#token) · [traza y span](#traza-span) |
| V | [ventana de contexto](#ventana-contexto) · [vector store](#vector-store) |
| W | [webhook](#webhook) · [workflow](#workflow) |

## A
### <a id="ab-testing"></a>A/B testing (A/B testing)

Comparación controlada de dos variantes —prompt, modelo, umbral o flujo— contra una métrica definida antes de mirar el resultado. Sirve para decidir con evidencia, no para elegir la variante que "se siente mejor". **Error común:** cambiar dos cosas a la vez y atribuir la mejora a la que se recuerda. Sin tamaño de muestra ni métrica predefinida, el A/B testing es una anécdota con dos brazos.

### <a id="a2a"></a>A2A (Agent2Agent)

Protocolo para que agentes se comuniquen entre sí: un agente descubre a otro, le delega una tarea y recibe un resultado. No es lo mismo que MCP, que conecta un modelo con tools y datos. **Por qué importa:** este manual no evalúa A2A porque ninguno de los cuatro proyectos lo implementa. Confundir A2A con MCP lleva a diseñar una integración de tools donde hacía falta una comunicación entre agentes, o al revés.

### <a id="agencia-excesiva"></a>agencia excesiva (excessive agency)

Situación en la que el agente tiene más funcionalidad, permisos o autonomía de los necesarios para su tarea. OWASP la clasifica como LLM03 e incluye tools de más, credenciales amplias y escrituras sin confirmación. **Error común:** creer que el modo `full` del modelo es un permiso efectivo. La capacidad real es la intersección de modo, credenciales, sandbox y contexto; cada tool de escritura necesita su propio control.

### <a id="agente"></a>agente (agent)

Sistema en el que el modelo dirige dinámicamente su propio proceso y decide el próximo paso, incluido el uso de herramientas. En este manual, un agente confiable es un **orquestador determinista con un LLM acotado**: el código decide flujo, permisos, datos y fallbacks; el modelo interpreta y redacta. **Error común:** llamar "agente" a un prompt con instrucciones y ninguna tool. Si el sistema no puede actuar ni decidir pasos, es un chatbot o un workflow, y nombrarlo agente solo confunde el modelo de amenazas.

### <a id="allowlist"></a>allowlist (allowlist / whitelist)

Conjunto explícito de elementos permitidos —tools, dominios, modelos, destinos de red— con denegación por defecto. Todo lo que no está en la lista se rechaza, aunque el modelo lo pida con confianza. **Por qué importa:** es el control que convierte "el modelo propone" en "el servidor dispone". Una allowlist de tools vale más que cien instrucciones en el prompt; una blocklist siempre queda un paso atrás del próximo nombre inventado.

### <a id="alucinacion"></a>alucinación (hallucination)

Salida fluida y plausible que no está sustentada por los datos disponibles. No es solo un error factual: también es una cifra inventada, una cita falsa o una acción afirmada que nunca ocurrió. **Error común:** tratarla como un problema de prompt. Se contiene con grounding en tools, citas verificables, validación de salida y un fallback que no invente cuando falta el dato.

### <a id="anonimizacion-seudonimizacion"></a>anonimización y seudonimización (anonymization / pseudonymization)

La **anonimización** vuelve imposible reidentificar a una persona con medios razonables. La **seudonimización** reemplaza el identificador por otro, pero conserva una clave o pepper que permite reidentificar; el dato sigue siendo personal. **Error común:** llamar anónimo a un hash de teléfono con pepper. Es un seudónimo: con el pepper se puede reverificar y atacar por diccionario. La diferencia cambia obligaciones legales y controles de acceso.

## B
### <a id="baseline-noise-floor"></a>baseline y noise floor (baseline / noise floor)

El **baseline** es la referencia contra la que se compara un cambio: el fallback trivial, la versión en producción o el modelo anterior, siempre medido con el mismo dataset y el mismo judge. El **noise floor** es la dispersión de la misma versión repetida varias veces; marca la diferencia mínima que puede considerarse señal. **Error común:** declarar una mejora de dos puntos sin haber medido el ruido. Si la versión se mueve tres puntos entre corridas idénticas, esos dos puntos son varianza, no progreso.

## C
### <a id="cadena-suministro"></a>cadena de suministro (supply chain)

Conjunto de componentes externos que hacen funcionar al agente: modelo, dataset, embeddings, dependencias, imágenes de contenedor y servidores MCP. OWASP la trata como LLM04 y pide procedencia, versión fijada, hash y licencia. **Por qué importa:** un cambio silencioso en el modelo o en un paquete altera el comportamiento sin tocar tu prompt. El pin y el hash son la única forma de reproducir un incidente.

### <a id="capability-regresion"></a>capability eval y regresión (capability eval / regression eval)

La **capability eval** pregunta si el agente puede hacer algo nuevo; se espera que falle al principio y mide el techo. La **regresión** pregunta si sigue haciendo lo que ya hacía; se espera que pase siempre y protege el piso. Una capability estable se gradúa a regresión. **Error común:** mezclar ambas en un solo porcentaje. La mejora de una capability tapa la caída de una regresión, y el promedio se ve estable mientras el sistema empeora en lo que ya funcionaba.

### <a id="chunk"></a>chunk (chunk)

Fragmento de un documento que se indexa y se recupera como unidad. Su tamaño y su solapamiento afectan la precisión: muy grande diluye la señal, muy chico pierde contexto. **Por qué importa:** el chunk es la unidad de citación y de control de acceso. Si un chunk mezcla datos de dos tenants o de dos fechas, el retrieval ya no puede aislarlos después.

### <a id="citacion"></a>citación (citation)

Referencia a la fuente, la fecha y —cuando existe— la URL que sustenta una afirmación. Permite que una persona verifique el dato sin confiar en el modelo. **Error común:** agregar citas decorativas que no corresponden al texto. Una cita falsa es peor que ninguna: simula verificabilidad y multiplica el trabajo de revisión.

### <a id="consentimiento"></a>consentimiento (consent)

Permiso informado, granular y revocable para usar un dato con una finalidad concreta. No es un checkbox global: historial, alertas, ubicación, grabación y entrenamiento son permisos separados. **Por qué importa:** el consentimiento se verifica en código y se registra con fecha y versión del aviso. Si el usuario no puede revocarlo, no hay consentimiento, hay una casilla.

### <a id="contexto"></a>contexto (context)

Todo lo que el modelo recibe en una llamada: prompt de sistema, historial, documentos recuperados, resultados de tools y la pregunta actual. Es la información disponible, no la capacidad máxima del modelo. **Error común:** creer que más contexto siempre mejora la respuesta. El contexto irrelevante compite por atención, aumenta latencia y costo, y puede introducir instrucciones no confiables.

### <a id="contexto-oculto"></a>contexto oculto (hidden context)

Contenido que el usuario no ve pero que el modelo sí: prompt de sistema, memoria, documentos recuperados, estado de la aplicación y resultados de tools. OWASP lo trata como LLM08 porque todo eso puede filtrarse por una respuesta, un log o un error. **Error común:** tratar el prompt de sistema como una bóveda. Si contiene una clave, un endpoint interno o el nombre de otro cliente, ese dato ya está comprometido.

### <a id="cuota-rate-limit"></a>cuota y rate limit (quota / rate limit)

El **rate limit** limita solicitudes por ventana de tiempo; la **cuota** limita el consumo total por periodo, usuario o tenant. El primero evita ráfagas; la segunda evita que un usuario agote el presupuesto del mes. **Error común:** implementar el límite en memoria dentro de un servicio con varias réplicas o serverless. Cada instancia cuenta por su lado y el límite efectivo se multiplica o se reinicia en cada despliegue.

## D
### <a id="deadline"></a>deadline (deadline)

Plazo máximo de pared para completar un turno, incluidas las llamadas al modelo, las tools, los reintentos y el fallback. No es el timeout de una sola llamada. **Por qué importa:** un turno con cinco llamadas rápidas y una lenta consume el mismo presupuesto. El deadline se verifica antes de cada paso y se propaga a cada llamada; al agotarse, se devuelve el fallback, no se sigue intentando.

## E
### <a id="embedding"></a>embedding (embedding)

Representación numérica de un texto —un vector— que permite medir similitud semántica y buscar por cercanía. Se genera con un modelo de embeddings y se almacena en un índice. **Error común:** tratar el embedding como cifrado o anonimización. La inversión de embeddings puede reconstruir parte del texto original; no embebas PII cruda sin necesidad.

### <a id="envenenamiento-vectores"></a>envenenamiento de vectores (vector poisoning)

Manipulación del corpus, de los documentos o de los embeddings para que el retrieval devuelva contenido sesgado o malicioso. OWASP lo agrupa en LLM09 junto con las debilidades de aislamiento y la inversión de embeddings. **Por qué importa:** un documento envenenado no necesita hablar con el agente; basta con que esté en una fuente que el agente consulta. Corpus versionado, revisión, ACL por tenant y evals de retrieval son el control.

### <a id="error-budget-slo"></a>error budget y SLO (error budget / SLO)

El **SLO** es un objetivo medible de nivel de servicio —por ejemplo, porcentaje de turnos bajo el deadline—. El **error budget** es el fallo que ese objetivo permite en una ventana: `1 - SLO`. **Error común:** publicar un SLO sin medirlo o sin dueño. Un SLO sin instrumentación es una intención; un SLO sin error budget no dice cuándo hay que frenar cambios.

### <a id="escalation"></a>escalation (escalation / escalamiento)

Política y disparador para elevar un caso a una persona con más autoridad o a otra cola: riesgo, ambigüedad, fallo repetido, acción irreversible o petición explícita. Es la decisión; el handoff es la transferencia concreta. **Por qué importa:** una escalación sin criterio depende del humor del modelo. Define las causas en código —`human_requested`, `pms_down`, `commercial`— y registra cuál se activó.

### <a id="eval"></a>eval (evaluation)

Caso reproducible con una expectativa verificable sobre una entrada concreta. No es un test unitario: un test pregunta si el código ejecuta la rama correcta; un eval pregunta si el sistema acierta cuando el modelo cambia o improvisa. **Error común:** llamar eval a una conversación mirada a ojo. Si no puedes decir "esto está mal" sin discutir, no hay expectativa y no hay eval.

### <a id="eval-offline-online"></a>eval offline y online (offline / online evaluation)

La **offline** corre contra un dataset fijo en CI: es reproducible, tiene verdad conocida y riesgo de sobreajuste. La **online** corre con tráfico real: detecta deriva, costo y distribución, pero no tiene verdad de referencia y llega tarde. **Error común:** usar métricas online sin etiquetas como si midieran corrección. Sin un conjunto de casos con expectativa, la observación de tráfico es monitoreo, no evaluación de calidad.

### <a id="exfiltracion"></a>exfiltración (exfiltration)

Salida no autorizada de datos privados a través de la respuesta, una tool, un enlace, un correo o un canal externo. El "trilema letal" la habilita cuando coinciden datos privados, contenido no confiable y capacidad de comunicar al exterior. **Por qué importa:** no se evita detectando la frase maliciosa; se evita quitando una pata. El agente que lee documentos no debería poder enviar mensajes, y el que envía no debería leer documentos de terceros.

## F
### <a id="fallback-degradacion-fail-closed"></a>fallback, degradación y fail-closed (fallback / graceful degradation / fail-closed)

El **fallback** es la respuesta determinista y acotada cuando falla el modelo, una tool o la red. La **degradación** es el modo reducido pero honesto —flujo guiado, `offline: true`, mensaje fijo—. **Fail-closed** es la regla que los ordena: ante duda o falta de dato verificado, no se afirma un dato; se devuelve el fallback. **Error común:** un fallback que improvisa con el mismo modelo o que inventa un precio "aproximado". Un fallback que no es observable ni está probado es una segunda fuente de alucinación.

## G
### <a id="golden-dataset"></a>golden dataset (golden dataset)

Colección pequeña, curada y versionada de casos con expectativa explícita. Se alimenta de tráfico anonimizado y consentido, incidentes, correcciones humanas y edge cases deliberados. **Por qué importa:** es el activo que hace comparables dos versiones. Un dataset que cambia de significado sin cambiar de nombre rompe el histórico; si cambia la expectativa, se crea un caso nuevo.

### <a id="groundedness"></a>groundedness (groundedness)

Grado en que cada afirmación de la respuesta se sigue del contexto recuperado o del resultado de una tool. Es distinto de "ser verdad": una respuesta puede estar bien sustentada en una fuente equivocada. **Por qué importa:** se evalúa en dos capas: determinista —¿hay cita, fuente y fecha?— y semántica —¿la afirmación se deriva del contexto?—. La primera corre siempre; la segunda necesita un judge calibrado.

### <a id="guardrail"></a>guardrail (guardrail)

Control que limita lo que entra, lo que sale o lo que el agente puede ejecutar. Puede ser un filtro, una validación de esquema, una allowlist o una aprobación humana; siempre es código o política aplicada, no una súplica en el prompt. **Error común:** confundir una instrucción ("no reveles tus instrucciones") con un guardrail. La instrucción puede ignorarse; el guardrail debe fallar de forma visible y comprobable.

## H
### <a id="handoff"></a>handoff (handoff)

Transferencia de la conversación a una persona —o a otro agente— con contexto suficiente para continuar: últimos turnos, intención, datos capturados, causa y estado del SLA. No es solo "derivar". **Error común:** derivar el chat vacío a una cola. Sin nota de contexto, la persona vuelve a preguntar lo mismo y el usuario paga dos veces la espera.

### <a id="hmac"></a>HMAC (Hash-based Message Authentication Code)

Código de autenticación con clave que verifica integridad y origen de un mensaje. En webhooks se calcula sobre el cuerpo crudo y se compara en tiempo constante. **Por qué importa:** sin HMAC, cualquiera que conozca la URL puede inyectar eventos. Con HMAC pero sin timestamp, el mismo evento se puede reenviar; con timestamp pero sin deduplicación, se procesa dos veces.

### <a id="human-in-the-loop"></a>human-in-the-loop (human-in-the-loop, HITL)

Punto del flujo en el que una persona confirma, corrige o decide antes de que el sistema actúe. Es una transición de estado, no una frase en el prompt. **Por qué importa:** es el control proporcionado para acciones irreversibles. Su costo es latencia y operación; por eso se reserva para lo que no se puede deshacer, no para cada respuesta.

## I
### <a id="idempotencia"></a>idempotencia (idempotency)

Propiedad por la cual repetir la misma operación produce el mismo efecto que ejecutarla una vez. Se implementa con una clave de idempotencia, una consulta previa o una restricción única en la base. **Error común:** reintentar una escritura "por si acaso". Un timeout no significa que la operación no ocurrió; sin idempotencia, el reintento duplica la reserva, el gasto o el mensaje.

### <a id="inyeccion-prompt-jailbreak"></a>inyección de prompt y jailbreak (prompt injection / jailbreak)

La **inyección directa** viene del usuario ("ignora tus reglas"); la **indirecta** viene de un documento, un resultado de tool, un webhook o un campo de base de datos. El **jailbreak** busca saltarse las políticas del modelo; comparte mecanismo, pero no siempre busca exfiltrar datos. **Error común:** confiar en un clasificador de texto como garantía. El lenguaje natural tiene infinitas formulaciones y el modelo no separa instrucciones de datos; la contención vive en la allowlist, los permisos y la validación del servidor.

## K
### <a id="kill-switch"></a>kill switch (kill switch)

Interruptor operativo que desactiva una capacidad —un canal, una tool, el uso del LLM, una integración— sin desplegar código. Debe poder probarse antes del incidente. **Por qué importa:** en un incidente, el tiempo de reacción importa más que la elegancia. Un flag por capacidad y por tenant es más útil que un "apagar todo" que también apaga el negocio.

## L
### <a id="llamada-herramientas"></a>llamada a herramientas (tool calling / function calling)

Mecanismo por el que el modelo emite una llamada estructurada a una función declarada, con nombre y argumentos. El servidor valida los argumentos, aplica permisos y ejecuta; el modelo no ejecuta nada por sí mismo. **Error común:** declarar tools en un JSON y creer que ya existen. Si el runtime no las pasa al modelo y no hay `tool_calls`, son documentación, no capacidad.

### <a id="llm-as-judge"></a>LLM-as-judge (LLM-as-judge)

Uso de un modelo como instrumento de medición para puntuar una salida con una rúbrica. Sirve para semántica a escala, no para verdad absoluta. **Error común:** usar el mismo modelo que produjo la respuesta, con una pregunta vaga y sin calibración. Un judge así prefiere su propio estilo y produce números estables que no correlacionan con humanos.

### <a id="log"></a>log (log)

Registro de eventos con marca de tiempo, nivel y campos estructurados. Responde "qué pasó" en un turno o en un servicio; no reemplaza la traza ni la métrica. **Error común:** loggear el payload completo "para depurar". El log se convierte en una fuga de PII o de secretos y en un costo de almacenamiento que nadie revisa.

### <a id="loop"></a>loop (loop / bucle)

Ciclo en el que el modelo propone una tool, el servidor la ejecuta y el resultado vuelve al modelo como observación. Es la mecánica del agente con tools, no una prueba de autonomía. **Por qué importa:** todo loop necesita deadline, máximo de pasos, traza y truncado del payload. Un loop sin cotas es un riesgo de costo, latencia y errores compuestos.

## M
### <a id="manejo-salida"></a>manejo de salida (output handling)

Tratamiento de la salida del modelo como dato no confiable antes de que otro sistema la use: HTML, SQL, un comando de shell, un enlace o una llamada a otra tool. OWASP lo trata como LLM10. **Error común:** renderizar la respuesta como HTML "porque se ve mejor". Si el modelo puede producir un tag o un enlace, la salida abre XSS, phishing o inyección en el siguiente sistema.

### <a id="maquina-estados"></a>máquina de estados (state machine)

Modelo explícito de estados, transiciones válidas y estados terminales. Reemplaza el "estado implícito en el historial" por un dato que se puede leer, testear y auditar. **Por qué importa:** una máquina de estados no garantiza durabilidad por sí sola. Si el proceso muere en medio del turno, sin checkpoint y almacén durable se pierde igual; el estado explícito y la persistencia son dos decisiones distintas.

### <a id="max-steps"></a>max steps (max steps)

Número máximo de iteraciones del loop de tools. Al agotarse, el sistema devuelve un fallback acotado en lugar de seguir intentando. **Error común:** poner un número alto "para que tenga libertad". Más pasos no significan mejor respuesta: suelen indicar que el modelo da vueltas, y cada vuelta cuesta tokens y latencia.

### <a id="max-tokens"></a>max_tokens (max_tokens)

Tope de tokens de salida que se solicitan al modelo. No limita la entrada ni el costo total del turno, y puede truncar una respuesta válida a mitad de un JSON. **Por qué importa:** es un presupuesto, no una sugerencia. Se fija junto con el formato de salida y se verifica que el contenido quepa; si el modelo necesita más, el problema es el diseño de la respuesta.

### <a id="mcp"></a>MCP (Model Context Protocol)

Protocolo abierto para conectar modelos con datos y tools. Un servidor expone tres primitivas: resources —contexto que controla la aplicación—, prompts —plantillas que elige el usuario— y tools —funciones que invoca el modelo—. **Error común:** creer que MCP resuelve la política de negocio. Estandariza la interfaz, no la autorización: consentimiento, validación, rate limit y aislamiento por tenant siguen siendo de tu aplicación.

### <a id="memoria"></a>memoria (memory)

Información que se conserva entre turnos o sesiones para personalizar o continuar una conversación. Tiene presupuesto, TTL, consentimiento y una finalidad declarada. **Error común:** llamar memoria a una tabla de mensajes. Guardar filas no crea memoria conversacional: si el historial no se envía al modelo de forma estructurada y acotada, es un archivo de auditoría.

### <a id="metrica"></a>métrica (metric)

Serie numérica agregada que describe el comportamiento del sistema: latencia p50/p95, tokens por turno, tasa de fallback, costo, errores por tipo. Se usa para tendencias y alertas. **Por qué importa:** una métrica sin etiquetas de tenant, canal o versión de prompt esconde la causa. La cardinalidad también cuesta: no conviertas cada `session_id` en una dimensión.

### <a id="minimo-privilegio"></a>mínimo privilegio (least privilege)

Principio por el cual cada componente —modelo, tool, servicio, usuario— recibe solo los permisos y datos necesarios para su tarea, durante el tiempo necesario. **Error común:** aplicar el permiso en el router y no en la tool. La autorización debe vivir donde se ejecuta la acción, porque el modelo puede llamar la tool directamente y el router no siempre es el único camino.

### <a id="multi-tenant"></a>multi-tenant (multi-tenant)

Arquitectura en la que varias organizaciones comparten infraestructura, con aislamiento de datos, configuración, cuotas y trazas. No basta con una columna `organizacion_id`. **Error común:** filtrar en la interfaz y devolver todo desde la API. El aislamiento se aplica en la consulta, en el contexto que recibe el modelo, en las claves y en los logs; si el frontend oculta, ya perdiste.

## O
### <a id="observabilidad"></a>observabilidad (observability)

Capacidad de inferir el estado interno del sistema a partir de sus señales: logs, métricas y trazas. No es tener dashboards; es poder responder una pregunta nueva sin desplegar instrumentación nueva. **Error común:** instrumentar solo el error y no el camino feliz. Sin la traza del turno que funcionó, no hay línea base para comparar el que falló.

### <a id="orquestador"></a>orquestador (orchestrator)

Código que decide el flujo, los estados, qué tools existen, qué datos se leen, cuándo se llama al modelo y qué pasa cuando algo falla. Es la parte determinista del sistema. **Por qué importa:** la tesis del manual es "orquestador determinista, LLM acotado". Si el modelo decide permisos o flujo, el orquestador es una ilusión y el sistema no se puede auditar.

### <a id="otel"></a>OTel (OpenTelemetry)

Estándar abierto y conjunto de SDKs para producir trazas, métricas y logs con un vocabulario común, independiente del proveedor de observabilidad. Las convenciones semánticas de GenAI están en estado Development (2026-10). **Por qué importa:** permiten cambiar de herramienta sin reescribir la instrumentación. Se adoptan como vocabulario y se aíslan detrás de una capa propia, porque las convenciones todavía pueden cambiar.

## P
### <a id="pass-k"></a>pass^k (pass^k)

Métrica de fiabilidad: las `k` corridas de un caso deben pasar. Se contrasta con `pass@k`, que mide si al menos una pasa y por eso describe capacidad, no consistencia. **Por qué importa:** un agente que reserva necesita que todas las corridas sean correctas. Si cada corrida acierta con probabilidad 0,9, la probabilidad ilustrativa de cinco aciertos seguidos es 0,9^5 ≈ 0,59; la aritmética no es una medición, pero explica por qué una sola corrida no alcanza.

### <a id="pii"></a>PII (personally identifiable information)

Dato que permite identificar a una persona, sola o combinado con otros: nombre, teléfono, correo, RUT, dirección, coordenadas, identificador de dispositivo. La definición legal varía por jurisdicción. **Error común:** proteger solo la respuesta y olvidar logs, trazas, argumentos de tools, chunks y embeddings. La fuga suele estar en la superficie que nadie revisa.

### <a id="presupuesto-tokens"></a>presupuesto de tokens (token budget)

Tope explícito de tokens de entrada y salida por solicitud, usuario, tenant o día, junto con un umbral de alerta y un límite duro. Se aplica en código, antes de llamar al proveedor. **Por qué importa:** el costo por turno no es solo el precio del token: incluye reintentos, tools, retrieval y contexto que crece. Sin presupuesto, un loop o un usuario insistente se convierte en denial-of-wallet.

### <a id="prompt"></a>prompt (prompt)

Texto o estructura de entrada que se envía al modelo: instrucciones, contexto, ejemplos y la petición del usuario. Es una interfaz, no un programa. **Error común:** hacer crecer el prompt para compensar datos que faltan o validaciones que no existen. Si el prompt tiene que suplicar una regla de negocio, la regla pertenece al código.

### <a id="prompt-sistema-usuario"></a>prompt de sistema y de usuario (system prompt / user prompt)

El **prompt de sistema** define rol, límites, tono y formato; se escribe una vez y se versiona. El **prompt de usuario** es la petición concreta y debe tratarse como dato no confiable, porque puede contener instrucciones maliciosas. **Error común:** esconder secretos en el prompt de sistema y confiar en que el modelo no los repita. El prompt de sistema no es una bóveda; el de usuario no es una orden de confianza.

## R
### <a id="rag"></a>RAG (Retrieval-Augmented Generation)

Patrón que recupera contexto de un corpus y lo entrega al modelo junto con la pregunta, idealmente con cita de fuente y fecha. No es sinónimo de base vectorial ni de embeddings. **Error común:** montar un vector store para un corpus de doce FAQs que se resuelve con keywords. La complejidad de un índice se paga con operación, no con una demo; mide el corpus antes de elegir.

### <a id="reranking"></a>reranking (reranking)

Segunda etapa que reordena los candidatos recuperados con un modelo o criterio más costoso, para mejorar la precisión de los primeros puestos. No recupera documentos que la primera etapa no trajo. **Error común:** usar reranking para tapar un retrieval con baja cobertura. Si el documento correcto no está entre los candidatos, reordenar no lo inventa; primero mide recall.

### <a id="retencion"></a>retención (retention)

Tiempo durante el cual un dato se conserva y las condiciones de su borrado. Incluye la base, los backups, los logs, las trazas y los índices; no solo la tabla principal. **Por qué importa:** una política de retención sin borrado de backups ni de trazas no se cumple. Define TTL, purga, anonimización y quién puede exportar antes de lanzar.

### <a id="retrieval"></a>retrieval (retrieval)

Selección del contexto relevante para una pregunta a partir de un corpus, una API o una base. Puede ser léxica, densa o híbrida; se mide con recall y precisión sobre casos representativos. **Error común:** evaluar solo la respuesta final y no el retrieval. Si el chunk correcto no se recuperó, el modelo no puede fundamentar la respuesta y el problema no se arregla con un prompt mejor.

## S
### <a id="sandbox"></a>sandbox (sandbox)

Entorno aislado con datos, permisos y efectos limitados, usado para demos, pruebas o ejecución de código no confiable. No es un sinónimo de "modo de prueba" si comparte credenciales o base con producción. **Por qué importa:** la capacidad efectiva se calcula por la intersección de modo, credenciales, sandbox y contexto. Un `AI_MODE=full` con sandbox y sin token sigue siendo incapaz de escribir.

### <a id="sesion"></a>sesión (session)

Contexto acotado de una conversación, identificado por un ID y con un TTL. Puede vivir en memoria, en la base o en una cookie firmada; no implica memoria persistente. **Error común:** usar la sesión como almacén ilimitado. El historial tiene tope de mensajes y de caracteres, y se trunca antes de enviarlo al modelo; lo que no entra, no existe para la respuesta.

### <a id="sla"></a>SLA (service level agreement)

Compromiso de nivel de servicio con un cliente o entre áreas: disponibilidad, latencia de respuesta, tiempo de handoff, soporte. Suele tener consecuencias contractuales y se mide con evidencia. **Error común:** prometer un SLA sin instrumentación ni capacidad probada. Un SLA externo se declara cuando hay métricas, error budget y runbook; mientras tanto, es un objetivo interno.

### <a id="streaming"></a>streaming (streaming)

Entrega incremental de la respuesta mientras el modelo genera. Mejora la latencia percibida y la experiencia en respuestas largas, pero no reduce el precio por token ni reemplaza el deadline. **Error común:** activar streaming y creer que el turno es más barato o más rápido de punta a punta. El costo es el mismo y el tiempo total puede no cambiar; solo cambia cuándo empieza a verse el texto.

## T
### <a id="temperatura"></a>temperatura (temperature)

Parámetro de muestreo que controla la aleatoriedad de la salida. Cerca de 0 favorece opciones probables; valores altos aumentan diversidad y variabilidad. **Error común:** asumir que `temperature=0` garantiza la misma respuesta. El proveedor puede cambiar modelo, batching, hardware u orden de tools; la reproducibilidad se mide con `pass^k`, no se promete con un parámetro.

### <a id="token"></a>token (token)

Unidad mínima de texto que el modelo procesa y factura; suele ser un fragmento de palabra, no una palabra completa. La misma frase en español puede consumir más tokens que en inglés. **Por qué importa:** el costo, la ventana de contexto y el truncado se miden en tokens, no en caracteres. Estimar por palabras subestima el presupuesto y produce cortes inesperados.

### <a id="traza-span"></a>traza y span (trace / span)

La **traza** es la historia completa de un turno: request, llamadas al modelo, tools, retrieval, fallback y entrega. El **span** es cada unidad de trabajo dentro de la traza, con duración, estado y atributos. **Error común:** tener logs sin `trace_id` y llamarlo observabilidad. Sin correlación no se puede reconstruir el turno; con demasiados spans de bajo valor, la traza se vuelve ilegible y cara.

## V
### <a id="ventana-contexto"></a>ventana de contexto (context window)

Máximo de tokens que el modelo puede atender en una sola llamada, sumando entrada y salida. Es una restricción del modelo, no un objetivo de diseño. **Error común:** llenar la ventana "porque cabe". El contexto irrelevante cuesta, distrae y puede degradar la precisión; además, lo que está en el medio suele recibir menos atención que el inicio y el final.

### <a id="vector-store"></a>vector store (vector store / base vectorial)

Índice especializado en almacenar vectores y buscar los más cercanos con algoritmos de vecinos aproximados. Añade operación, persistencia, control de acceso y aislamiento por tenant. **Error común:** elegirlo antes de medir el corpus. Para decenas de documentos versionados, TF-IDF o keywords pueden ser más precisos, explicables y baratos; el vector store se justifica por escala y ambigüedad semántica, no por moda.

## W
### <a id="webhook"></a>webhook (webhook)

Llamada HTTP que un sistema externo hace a tu servicio cuando ocurre un evento. Es una puerta pública y, por tanto, una superficie de ataque y de duplicados. **Por qué importa:** todo webhook necesita firma sobre el cuerpo crudo, timestamp con tolerancia, límite de cuerpo, deduplicación por ID y respuesta rápida. Sin esos controles, el agente procesa eventos falsos, viejos o repetidos.

### <a id="workflow"></a>workflow (workflow)

Ruta de etapas definida en código que orquesta LLM y tools; el programador decide el próximo paso, no el modelo. Es previsible, acotado y testeable. **Por qué importa:** la arquitectura correcta suele ser el workflow más simple que resuelve el problema. Un agente solo se justifica cuando el plan depende de lo que devuelve el mundo y no puedes enumerar los pasos antes de ejecutar.

## Cierre

Si un término de este glosario aparece en una discusión sin acuerdo, la definición operativa de esta página es el punto de partida. La pregunta que ordena casi todas las entradas es la misma: **¿quién decide y qué pasa cuando falla?** Si la respuesta es "el modelo" o "nada", el diseño todavía no está cerrado.

Para el detalle de implementación, continúa con [B — Comparativas](B-comparativas.md) y con las referencias de [C — Referencias](C-referencias.md).
