<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Capítulo 15 — Anti-patrones: las decisiones que funcionan en demo y fallan en producción

> **Tipo:** catalog (qué evitar) + how-to (cómo detectarlo, arreglarlo y priorizarlo).
> **Audiencia:** desarrolladores, PM, QA, seguridad y operaciones que ya tienen un agente
> funcionando o están a punto de exponerlo a usuarios reales.
> **Meta:** al terminar, puedes auditar un agente existente, nombrar sus fallos con precisión,
> elegir el arreglo correcto y decidir qué corregir primero según el contexto.

Un anti-patrón no es "código feo". Es una decisión que funciona en la demo porque el camino
feliz está limpio, el usuario coopera y nadie mira los bordes; y que falla en producción
cuando el canal se cae, el modelo alucina, el dato vence, el webhook se reintenta o el costo
se dispara. La diferencia entre demo y producción no es la calidad del código: es si el
contrato alrededor del modelo cubre los fallos.

La tesis cabe en una línea: **la mayoría de los agentes no fallan por el modelo, fallan por
el contrato alrededor del modelo**. El modelo elige palabras; el contrato decide qué datos
entran, qué acciones se permiten, qué se guarda, qué se mide y qué pasa cuando algo falla.

## La respuesta primero — top 10 anti-patrones que te morderán primero

| # | Anti-patrón | Síntoma | Costo | Arreglo | Capítulo |
|---|---|---|---|---|---|
| 1 | Vender "IA" sin canal de entrada | Promete conversar; el código solo envía | Producto que no cumple su promesa | Webhook entrante o renombrar el producto | [06](06-canales-memoria.md) |
| 2 | Confiar en el texto del modelo para autorizar | El modelo declara "confirmó" y el servidor obedece | Acción sin consentimiento real | Verificar sobre el texto del usuario | [04](04-orquestacion-tools.md) |
| 3 | Efecto irreversible sin confirmación | Registra, borra o envía en el mismo turno | Datos y dinero sin vuelta atrás | Doble confirmación en dos turnos | [04](04-orquestacion-tools.md) |
| 4 | Datos vencidos como actuales | Fecha vieja presentada como vigente | Decisión económica equivocada | `review_before` y fallo cerrado | [05](05-datos-rag.md) |
| 5 | Loop sin límite | Sin `MAX_STEPS`, deadline ni tokens | Latencia y costo impredecibles | Cotas independientes y fallback | [04](04-orquestacion-tools.md) |
| 6 | Webhook sin firma | Cualquier POST entra como mensaje | Inyección y acciones no autorizadas | HMAC, timestamp y límite de cuerpo | [08](08-seguridad.md) |
| 7 | Guardar filas y llamarlo memoria | Hay tabla, pero el modelo no ve el historial | El agente repite preguntas | Pasar turnos estructurados con límites | [06](06-canales-memoria.md) |
| 8 | Evals que no corren en CI | El set existe y se ejecuta a mano | Regresiones que pasan el pipeline | Runner en CI con casos bloqueantes | [07](07-evaluacion.md) |
| 9 | `BackgroundTasks` como cola | El ACK responde 200 y el trabajo se pierde | Mensajes sin procesar | Cola durable e idempotencia | [11](11-despliegue.md) |
| 10 | Cifras copiadas entre documentos | Tests y costos cambian según el archivo | Decisiones sobre datos falsos | Generar cifras desde el runner | [09](09-observabilidad.md) |

## Cómo leer este catálogo

Cada ficha tiene severidad, patrón correcto, síntoma, por qué duele, ejemplo, arreglo y
detección. La severidad se interpreta así: **crítico** = puede causar daño, pérdida de dinero
o caída del canal; **alto** = degrada fiabilidad, costo o calidad al escalar; **medio** =
fricción o deuda que conviene pagar antes de crecer.

Regla de evidencia: un `path:line` identifica código o documento verificado en lectura de
AgroVoz, copiloto-recepción, ManttoAI o Wenuke, sin ejecución de runtime. Si la ficha dice
**observado en la industria**, esos cuatro proyectos no ilustran el anti-patrón y no se le
atribuye a ninguno. Un "caso cercano" es una práctica relacionada que no coincide con el
defecto exacto.

---

## Producto y alcance

### P1 · Chatbot sin caso de uso

**Severidad:** alto · **Patrón correcto:** [Cap. 12](12-arquitecturas.md)
**Síntoma.** El chat existe porque el dashboard "necesitaba IA"; nadie definió qué decisión mejora, quién lo usa ni qué pasa si responde mal. **Por qué duele.** Sin criterio de aceptación se mide que responde, no que el operador decida mejor; cualquier respuesta fluida parece un éxito.
**Ejemplo.** ManttoAI lo agregó fuera del alcance: los entregables listan IoT, pipeline, ML, dashboard, manuales y QA, sin chat (`ManttoAI/docs/alcance/06-enunciado-alcance.md:6-12`), mientras el servicio ya responde preguntas (`ManttoAI/backend/app/services/chat_service.py:61-87`). **Arreglo.** Una frase de valor y una métrica ("la causa de una alerta en menos de 2 minutos"). **Detección.** Preguntar qué decisión cambia si responde bien; si no hay, es adorno.

### P2 · Agente para todo y planner universal

**Severidad:** alto · **Patrón correcto:** [Cap. 12](12-arquitecturas.md)
**Síntoma.** Un solo agente recibe soporte, ventas, datos y acciones; un planner descompone cada turno aunque la ruta ya sea conocida. **Por qué duele.** Cada capacidad amplía el espacio de fallos y permisos; la ruta fija se vuelve no determinista y el costo sube sin mejorar la tarea.
**Ejemplo.** Observado en la industria: agentes que responden FAQ, consultan pedidos y ejecutan reembolsos con el mismo prompt y la misma whitelist. Los cuatro proyectos usan un solo workflow acotado; ninguno documenta multi-agente. **Arreglo.** Un agente por trabajo verificable; workflow con etapas si la ruta es fija. **Detección.** Contar tools y permisos; si una tool no se usa en la tarea principal, sobra.

### P3 · Feature sin ADR

**Severidad:** alto · **Patrón correcto:** [Cap. 13](13-casos-de-estudio.md)
**Síntoma.** La feature entra por una rama, sin decisión escrita, alternativas, criterios de aceptación ni manual. **Por qué duele.** Sin ADR no hay registro de qué se sacrificó ni qué se puede cambiar sin romper una promesa; el fallo se resuelve improvisando.
**Ejemplo.** En ManttoAI, `docs/decisiones/` tiene ADRs de MQTT, Random Forest, email y rate limiting, pero ninguno del chat (`ManttoAI/docs/decisiones/`); el asistente tampoco aparece en el alcance (`ManttoAI/docs/alcance/06-enunciado-alcance.md:6-12`) ni en el manual. **Arreglo.** Un ADR de una página: contexto, decisión, alternativas, consecuencias y aceptación. **Detección.** Buscar la feature en `docs/decisiones/`; si solo vive en código y README, es deuda.

### P4 · Vender "IA" sin canal de entrada

**Severidad:** crítico · **Patrón correcto:** [Cap. 06](06-canales-memoria.md)
**Síntoma.** El marketing promete un asistente conversacional 24/7; el código solo tiene salida. El usuario responde y nadie recibe la respuesta. **Por qué duele.** No es un chatbot: es un notificador con interfaz de chat. La promesa se rompe en el primer mensaje.
**Ejemplo.** Wenuke envía por WhatsApp Graph (`Wenuke/backend/whatsapp.py:53-64`), pero no implementa webhook de entrada, `hub.challenge`, firma `X-Hub-Signature` ni mensajes entrantes; su `llms.txt` vende "IA conversacional 24/7" (`Wenuke/llms.txt:3`). **Arreglo.** Ciclo completo —webhook, verificación, firma, deduplicación y respuesta— o renombrar a "alertas y recomendaciones". **Detección.** Enviar un mensaje desde el teléfono del usuario; si no hay receptor, no hay conversación.

### P5 · Prometer autonomía sin evals

**Severidad:** alto · **Patrón correcto:** [Cap. 07](07-evaluacion.md)
**Síntoma.** El README dice "autónomo" o "experto"; no hay golden set, tasas de error ni casos bloqueantes. **Por qué duele.** La autonomía es una promesa de tasa de acierto; sin evals, el usuario descubre los límites en producción y el equipo no distingue mejora de regresión.
**Ejemplo.** Observado en la industria. Caso cercano: ManttoAI presenta el chat como "experto en mantenimiento predictivo" (`ManttoAI/backend/app/services/chat_service.py:129-140`), pero sus métricas son del Random Forest sobre datos sintéticos (`ManttoAI/backend/reports/ml-evaluation-latest.md:25-37`), no del asistente. **Arreglo.** 20-30 conversaciones con expectativa pass/fail contra el modelo real. **Detección.** Pedir la tasa de éxito por tarea y la fecha de la última corrida.

---

## Arquitectura

### A1 · Multi-agente para un FAQ

**Severidad:** alto · **Patrón correcto:** [Cap. 12](12-arquitecturas.md)
**Síntoma.** Varios agentes —router, investigador, redactor, crítico— para responder horarios, precios o políticas que caben en una tabla. **Por qué duele.** Cada salto agrega latencia, costo, puntos de fallo y un contrato nuevo; la calidad no sube porque el problema era de datos, no de razonamiento.
**Ejemplo.** Observado en la industria. Los cuatro proyectos usan un solo agente con loop acotado o single-shot (`AgroVoz/backend/app/services/llm_service.py:127`; `copiloto-recepcion copiloto/src/copiloto/ai/agent.py:19`). **Arreglo.** Reglas o single-shot para FAQ; tools solo cuando el dato vive fuera y cambia. **Detección.** Contar saltos por turno; si el 80% se resuelve con una regla, sobra arquitectura.

### A2 · Framework-first

**Severidad:** medio · **Patrón correcto:** [Cap. 02](02-stack-base.md)
**Síntoma.** El equipo elige LangGraph, CrewAI o un orquestador de moda antes de saber si hay estado, tools o human-in-the-loop. **Por qué duele.** El framework impone abstracciones, versiones y curvas de aprendizaje para un problema que quizá se resuelve con un `switch` y tres funciones.
**Ejemplo.** Observado en la industria. AgroVoz y copiloto implementan el loop a mano sobre FastAPI: AgroVoz con `MAX_TOOL_ITERATIONS = 3` y copiloto con `MAX_STEPS = 5` (`AgroVoz/backend/app/services/llm_service.py:127`; `copiloto-recepcion copiloto/src/copiloto/ai/agent.py:19`). **Arreglo.** Escribir el flujo en pseudocódigo; si cabe en un `switch`, no necesita framework. **Detección.** Preguntar qué primitiva se usa y qué se haría sin ella.

### A3 · Loop sin límite

**Severidad:** crítico · **Patrón correcto:** [Cap. 04](04-orquestacion-tools.md)
**Síntoma.** `while True` alrededor del modelo, sin máximo de pasos, deadline único ni presupuesto de tokens. **Por qué duele.** Una tool que repite, un error ambiguo o un proveedor lento convierten un turno en una factura y una espera sin techo; el usuario abandona antes de que el sistema decida.
**Ejemplo.** Observado en la industria. Los dos proyectos con loop lo acotan: AgroVoz corta a 3 iteraciones con deadline compartido (`AgroVoz/backend/app/services/llm_service.py:127-141`); copiloto corta a 5 pasos (`copiloto-recepcion copiloto/src/copiloto/ai/agent.py:19`). **Arreglo.** Cotas independientes de pasos, tiempo y tokens; fallback al agotar cualquiera. **Detección.** Buscar `while`, `for` y recursión alrededor del modelo; si el límite no está en código, no existe.

### A4 · Orquestación por prompt

**Severidad:** alto · **Patrón correcto:** [Cap. 04](04-orquestacion-tools.md)
**Síntoma.** El system prompt dice "decide qué herramienta usar", "si es urgente deriva" o "respeta las reglas". La secuencia vive en lenguaje natural. **Por qué duele.** El prompt no es scheduler ni control de acceso; el modelo puede saltarse un paso o ignorar una regla y no hay forma determinista de reproducir el fallo.
**Ejemplo.** Wenuke calcula alertas y recomendaciones, pero las pasa al LLM como contexto sin override duro (`Wenuke/backend/main.py:566-571`); el prompt solo pide "avisar riesgos" (`Wenuke/backend/llm.py:135-141`). **Arreglo.** Routing y decisiones críticas en código: reglas, máquina de estados, guards. **Detección.** Listar las decisiones que el prompt "debe" tomar; cada una con consecuencia de negocio falta en código.

### A5 · Estado implícito

**Severidad:** alto · **Patrón correcto:** [Cap. 06](06-canales-memoria.md)
**Síntoma.** El "estado" es el historial del prompt, una variable de React o una fila suelta; nadie sabe en qué paso está la conversación. **Por qué duele.** Con dos réplicas o una recarga, el flujo se reinicia o se duplica; los tests solo cubren un turno porque el estado no se puede montar de forma determinista.
**Ejemplo.** ManttoAI persiste cada intercambio como fila independiente, sin `conversation_id` (`ManttoAI/backend/app/models/chat.py:15-32`), y el router ignora el historial que envía el cliente (`ManttoAI/backend/app/routers/chat.py:96`); el estado real vive en el navegador. **Arreglo.** Enum de estados, transiciones, terminales y persistencia con clave. **Detección.** Dibujar el grafo; si no puedes nombrar el estado actual, no hay estado.

---

## Prompt

### PR1 · Prompt gigante

**Severidad:** medio · **Patrón correcto:** [Cap. 03](03-system-prompts.md)
**Síntoma.** Miles de tokens de instrucciones, ejemplos duplicados, políticas copiadas y casos históricos; cada incidente agrega un párrafo y nadie borra. **Por qué duele.** Aumenta latencia y costo, diluye reglas importantes, rompe la caché del proveedor y hace imposible atribuir un cambio de comportamiento.
**Ejemplo.** Observado en la industria. Caso cercano: AgroVoz ensambla seis secciones y coloca las tools después del prompt fijo para mantener estable el prefijo (`AgroVoz/backend/app/services/prompt_builder.py:88-103`), disciplina que evita el crecimiento accidental. **Arreglo.** Presupuesto por sección, una regla por línea, ejemplos mínimos y diff del prompt como código. **Detección.** Medir tokens por turno; si crece sin subir la tasa de éxito, es grasa.

### PR2 · Reglas contradictorias

**Severidad:** alto · **Patrón correcto:** [Cap. 03](03-system-prompts.md)
**Síntoma.** El prompt dice "sé breve" y "explica todos los pasos"; el chat dice un umbral y el motor de alertas usa otro. El modelo elige una regla y el operador recibe dos verdades. **Por qué duele.** La contradicción no aparece en el camino feliz; aparece cuando el operador compara chat y dashboard y no sabe cuál creer.
**Ejemplo.** ManttoAI afirma ">0.5 G es inusual y >1.0 G es riesgo alto" (`ManttoAI/backend/app/services/chat_service.py:25`), mientras el umbral evalúa `max(abs(x),abs(y),abs(z))` contra 0–9.9 (`ManttoAI/backend/app/services/alerta_service.py:54-58`; `ManttoAI/scripts/seed_db.py:127-128`). **Arreglo.** Una constante para cada umbral, importada por prompt, alertas, dashboard y tests. **Detección.** Buscar el mismo número en dos archivos con semánticas distintas.

### PR3 · Instrucciones sin ejemplos

**Severidad:** medio · **Patrón correcto:** [Cap. 03](03-system-prompts.md)
**Síntoma.** El prompt enumera reglas abstractas —"sé claro", "no inventes", "deriva cuando corresponda"— sin un par entrada/salida que muestre el comportamiento. **Por qué duele.** El modelo interpreta con su criterio: "breve" puede ser una frase o un párrafo; "deriva" puede ser cualquier cosa.
**Ejemplo.** El prompt de ManttoAI define tono y delimitadores, pero no incluye ejemplos (`ManttoAI/backend/app/services/chat_service.py:129-140`); el de copiloto tiene cuatro casos de comportamiento (`copiloto-recepcion copiloto/src/copiloto/ai/prompts.py:32-37`). **Arreglo.** Dos o tres ejemplos: caso normal, borde y rechazo. **Detección.** Preguntar si puedes mostrar la respuesta esperada con un ejemplo; si no, la regla es ambigua.

### PR4 · Prompt que promete más que el contexto

**Severidad:** alto · **Patrón correcto:** [Cap. 03](03-system-prompts.md)
**Síntoma.** El prompt pide "analiza los próximos 7 días" o "compara el histórico", pero el orquestador entrega el día actual o un resumen truncado. **Por qué duele.** El modelo no puede cumplir; improvisa, se contradice o responde con una generalidad que parece un dato.
**Ejemplo.** Wenuke pide "DATOS DEL CLIMA PARA LA PARCELA (próximos 7 días)" (`Wenuke/backend/llm.py:136`), pero el contexto es el resumen del día y las alertas del forecast (`Wenuke/backend/servicios.py:34-41`). **Arreglo.** Generar el prompt desde el mismo contrato que arma el contexto; si el dato no está, decirlo. **Detección.** Comparar las variables que el prompt nombra con las que el orquestador inyecta.

### PR5 · No versionar el prompt

**Severidad:** medio · **Patrón correcto:** [Cap. 03](03-system-prompts.md)
**Síntoma.** El prompt vive en un `f-string` o una constante; la respuesta no incluye versión y los logs no permiten saber qué prompt generó qué respuesta. **Por qué duele.** Cuando la calidad cambia no se puede atribuir al modelo, al prompt o a los datos; el rollback es intuición y el eval no distingue la causa.
**Ejemplo.** ManttoAI construye el prompt inline (`ManttoAI/backend/app/services/chat_service.py:129-140`) y Wenuke lo define en una constante (`Wenuke/backend/llm.py:11-20`); ninguno devuelve `prompt_version` (`ManttoAI/backend/app/schemas/chat.py:18-22`). **Arreglo.** `prompt_version` en respuesta y traza; prompt en archivo versionado con changelog. **Detección.** Preguntar qué prompt produjo una respuesta y exigir un ID, no una fecha.

---

## Tools

### T1 · Tool sin contrato: schema y descripción vaga

**Severidad:** alto · **Patrón correcto:** [Cap. 04](04-orquestacion-tools.md)
**Síntoma.** La tool se describe en prosa, acepta un objeto libre y el servidor interpreta con `getattr` o `dict.get`; "busca datos" no dice qué datos, formato ni límites. **Por qué duele.** El modelo rellena los huecos con suposiciones y el servidor no distingue un argumento válido de uno inventado.
**Ejemplo.** Observado en la industria. El contraste es copiloto: cuatro tools con `additionalProperties: false`, enums, rangos y campos requeridos (`copiloto-recepcion copiloto/src/copiloto/ai/tools.py:73-106`). **Arreglo.** Schema cerrado, descripción con cuándo usarla y cuándo no, ejemplos y errores tipificados. **Detección.** Llamar con un argumento inventado; si se acepta o falla con 500, no hay contrato.

### T2 · Tool sin validación

**Severidad:** alto · **Patrón correcto:** [Cap. 04](04-orquestacion-tools.md)
**Síntoma.** El servidor hace `json.loads` y pasa los argumentos al handler; confía en que el modelo respetó el schema porque el schema estaba en el prompt. **Por qué duele.** El modelo no ejecuta el schema: lo lee. Un producto inventado, una fecha pasada o un monto negativo llegan al handler.
**Ejemplo.** AgroVoz parsea JSON y filtra `kwargs` contra la firma real, con campos requeridos (`AgroVoz/backend/app/services/llm_service.py:1398-1428`), pero no aplica un JSON Schema completo; la validación es pragmática. **Arreglo.** Validar tipo, rango, formato, pertenencia y reglas de negocio antes de ejecutar. **Detección.** Enviar un argumento fuera de rango; si el error sale del handler, la validación llegó tarde.

### T3 · Efecto irreversible sin confirmación

**Severidad:** crítico · **Patrón correcto:** [Cap. 04](04-orquestacion-tools.md)
**Síntoma.** El agente registra un gasto, crea una parcela, envía un correo o borra un dato en el mismo turno en que el usuario lo menciona; no hay "¿confirmas?". **Por qué duele.** Un error de interpretación se vuelve un hecho persistente; si la acción se reintenta, se duplica, y si el usuario se arrepiente no hay vuelta atrás.
**Ejemplo.** AgroVoz registra gastos y parcelas tras gate y consentimiento, sin confirmación explícita (`AgroVoz/backend/app/services/expense_service.py:254-272`); los comandos cerrados de borrado se ejecutan directo (`AgroVoz/backend/app/services/pipeline_service.py:912-938`). **Arreglo.** Propuesta, resumen del servidor, confirmación en el turno siguiente, idempotencia y TTL. **Detección.** Buscar escrituras en la tool; si no hay estado `pending`, el efecto es irreversible.

### T4 · Tool que devuelve demasiado

**Severidad:** medio · **Patrón correcto:** [Cap. 04](04-orquestacion-tools.md)
**Síntoma.** La tool devuelve el JSON crudo de la API, cien filas o el forecast completo "por si acaso". **Por qué duele.** Aumenta tokens, latencia y costo; entierra el dato relevante y facilita que el modelo copie campos internos. La tool deja de ser interfaz y se vuelve un dump.
**Ejemplo.** Wenuke devuelve `raw_forecast` en `/clima` siempre, aunque el schema dice "solo presente si se solicita" (`Wenuke/backend/main.py:548`; `Wenuke/backend/models.py:75-78`). **Arreglo.** Devolver solo los campos necesarios; el crudo va en un endpoint aparte o detrás de un flag. **Detección.** Medir tokens del resultado; si supera al prompt, devuelve de más.

### T5 · Whitelist ausente

**Severidad:** crítico · **Patrón correcto:** [Cap. 04](04-orquestacion-tools.md)
**Síntoma.** El agente puede llamar cualquier tool registrada, incluidas las de escritura, sin lista cerrada por modo, canal o usuario; la única barrera es el prompt. **Por qué duele.** Un modelo manipulado propone una tool que nunca debió existir para ese contexto y el orquestador la ejecuta.
**Ejemplo.** Observado en la industria. El contraste es AgroVoz: `WHITELIST_TOOLS` es un `frozenset` de 19 nombres y el intento remoto solo anuncia las de lectura (`AgroVoz/backend/app/services/llm_service.py:81-103`). **Arreglo.** Lista cerrada por modo y canal; lo no permitido termina en fallback, no en stack trace. **Detección.** Pedir una tool inexistente o de escritura en modo lectura.

### T6 · Tool declarada pero no conectada

**Severidad:** alto · **Patrón correcto:** [Cap. 04](04-orquestacion-tools.md)
**Síntoma.** Existe un archivo de `tool_definitions` con nombres, descripciones y schemas, pero el cliente del LLM nunca recibe `tools=` ni hace function calling. **Por qué duele.** El equipo cree que el agente consulta clima, precios o parcelas; en realidad solo redacta con el contexto que le pasaron. La brecha aparece en la primera integración.
**Ejemplo.** Wenuke declara cinco tools con `input_schema` (`Wenuke/tool_definitions.json:1-149`), pero la llamada a Groq no pasa `tools` ni interpreta tool calls (`Wenuke/backend/llm.py:144-152`). **Arreglo.** Una sola fuente de verdad: si no está conectada, no se publica como tool. **Detección.** Buscar `tools=` en el cliente; si no aparece, es documentación.

---

## Datos y RAG

### D1 · RAG vectorial para 20 FAQs

**Severidad:** medio · **Patrón correcto:** [Cap. 05](05-datos-rag.md)
**Síntoma.** El corpus son 14 preguntas frecuentes y tres políticas; la solución es una base vectorial, embeddings y un re-ranker. **Por qué duele.** Los embeddings resuelven recuperación semántica sobre corpus grandes y cambiantes; para un corpus pequeño y estructurado, keywords es más barato, auditable y testeable.
**Ejemplo.** Observado en la industria. El contraste es copiloto: 14 FAQ y 12 tipos de habitación resueltos con `match_faq` por keywords, sin embeddings (`copiloto-recepcion copiloto/src/copiloto/hotel.py:51-62`). **Arreglo.** Empezar por búsqueda léxica; migrar a embeddings cuando el vocabulario no coincida y el volumen lo justifique. **Detección.** Si el corpus cabe en una tabla, el vector store es decorativo.

### D2 · Corpus sin fuente ni fecha

**Severidad:** alto · **Patrón correcto:** [Cap. 05](05-datos-rag.md)
**Síntoma.** El documento tiene texto, pero no `source`, `source_url`, `date`, `verified_on` ni `review_before`. **Por qué duele.** Sin procedencia no se puede auditar una respuesta ni retirar un dato vencido; el modelo cita una afirmación sin dueño con la misma confianza que un dato verificado.
**Ejemplo.** La auditoría del corpus de papa en AgroVoz encontró un rango de temperatura incorrecto, una ventana de siembra incompleta, síntomas faltantes y una fuente sin URL; se corrigió y se exigió `source_url` (`AgroVoz/backend/corpus/inia_papa.yaml:3-9`; `AgroVoz/backend/corpus/reglas_agronomicas.yaml:12-18`). **Arreglo.** Todo chunk declara fuente, URL, fecha y ventana de revisión; el cargador rechaza lo que no cumple. **Detección.** `grep` de `source` y `date`; si faltan, el RAG no es auditable.

### D3 · Datos vencidos servidos como actuales

**Severidad:** crítico · **Patrón correcto:** [Cap. 05](05-datos-rag.md)
**Síntoma.** El precio, el pronóstico o la regla tienen `review_before` vencido, pero otra ruta —endpoint, panel o fallback— los muestra sin fecha ni advertencia. **Por qué duele.** Un dato viejo presentado como actual es peor que un "no sé": el usuario decide con información falsa y el sistema parece confiable.
**Ejemplo.** El manifest de AgroVoz tiene fuentes con `revisar_antes_de` vencido (`AgroVoz/backend/corpus/fuentes_datos.yaml:19-20`, `:33-34`); el RAG las excluye (`AgroVoz/backend/app/services/rag_service.py:198-233`), pero los servicios estructurados de ODEPA y Open-Meteo no dependen de ese filtro. **Arreglo.** Un solo gate de frescura para todas las rutas; si venció, fallback con la fecha del último dato válido. **Detección.** Verificar cada ruta que lee el dato; una sin gate es una fuga.

### D4 · Embeddings sin aislamiento

**Severidad:** crítico · **Patrón correcto:** [Cap. 08](08-seguridad.md)
**Síntoma.** Un índice vectorial compartido por todos los tenants; la búsqueda filtra por texto o por un `WHERE` que se olvida en una ruta. **Por qué duele.** El embedding no tiene permisos; el aislamiento debe estar en la consulta y en el índice. Una fuga es silenciosa y difícil de detectar después.
**Ejemplo.** Observado en la industria. El contraste es ManttoAI: el contexto se filtra por `organizacion_id` en la sesión (`ManttoAI/backend/app/dependencies.py:186`; `ManttoAI/backend/app/services/tenant_scope.py:13-20`), aunque su chat no usa embeddings. **Arreglo.** Namespace por tenant, filtro obligatorio en retrieval y un test que intente leer otro tenant. **Detección.** Buscar el filtro en todas las consultas; si vive en el prompt, falta en código.

### D5 · Contexto crudo volcado

**Severidad:** alto · **Patrón correcto:** [Cap. 05](05-datos-rag.md)
**Síntoma.** El prompt recibe filas de base de datos, nombres de equipo o texto libre sin delimitar ni escapar; datos e instrucciones comparten el mismo canal. **Por qué duele.** Un campo con "ignora las instrucciones anteriores" se vuelve una instrucción; además, el modelo pierde foco y el prompt crece sin control.
**Ejemplo.** ManttoAI interpola nombres de equipo y otros campos de la base directamente en el contexto (`ManttoAI/backend/app/services/chat_service.py:111`, `:124`); el saneamiento solo cubre el mensaje del usuario. **Arreglo.** Serializar en un formato delimitado, escapar caracteres de control y declarar que el bloque es dato, no instrucción. **Detección.** Buscar interpolaciones de base de datos en el prompt; cada una sin delimitador es una superficie de inyección.

---

## Memoria

### M1 · Guardar filas y llamarlo memoria

**Severidad:** alto · **Patrón correcto:** [Cap. 06](06-canales-memoria.md)
**Síntoma.** Hay una tabla `messages` o `chat_history`, pero el modelo recibe solo el turno actual; el equipo dice "tiene memoria" porque la base guarda los mensajes. **Por qué duele.** Persistir para auditoría no es memoria conversacional; el agente repite preguntas y el usuario siente que no lo escuchan.
**Ejemplo.** ManttoAI guarda cada intercambio en `mensajes_chat` (`ManttoAI/backend/app/models/chat.py:15-32`), pero el router llama `procesar_mensaje(payload.mensaje, db)` sin pasar el historial (`ManttoAI/backend/app/routers/chat.py:96`), y el schema lo acepta sin tipar (`ManttoAI/backend/app/schemas/chat.py:13-15`). **Arreglo.** Definir la ventana de turnos que se envía, con límite y truncado; la tabla queda para auditoría. **Detección.** Preguntar si el modelo ve el turno anterior; "está en la base" no es memoria.

### M2 · Historial sin límite

**Severidad:** alto · **Patrón correcto:** [Cap. 06](06-canales-memoria.md)
**Síntoma.** El contrato acepta `historial: list` sin tipo, sin máximo de turnos y sin truncado por caracteres; el cliente decide cuánto contexto manda. **Por qué duele.** Costo y latencia crecen con el cliente; un payload malicioso o un bug del frontend puede meter miles de turnos, y el historial es dato no confiable.
**Ejemplo.** ManttoAI declara `historial: list` sin más restricciones (`ManttoAI/backend/app/schemas/chat.py:13-15`); hoy se ignora, pero el contrato ya admite cualquier tamaño. **Arreglo.** `max_turns`, `max_chars`, tipo por mensaje y validación de roles; el servidor trunca. **Detección.** Enviar 10.000 turnos; si el schema los acepta, no hay límite.

### M3 · Memoria sin consentimiento

**Severidad:** crítico · **Patrón correcto:** [Cap. 06](06-canales-memoria.md)
**Síntoma.** El agente guarda conversaciones, preferencias o ubicación por defecto; no hay opt-in, TTL ni borrado verificable. **Por qué duele.** La memoria revela consultas, ubicación y hábitos; sin consentimiento granular el sistema incumple su promesa de privacidad y el borrado se vuelve manual.
**Ejemplo.** Observado en la industria. El contraste es AgroVoz: historial apagado por defecto, `history_consent` y guardado solo tras entrega confirmada (`AgroVoz/backend/app/core/config.py:214-224`; `AgroVoz/backend/app/services/consultation_history_service.py:1-14`, `:130-176`). **Arreglo.** Opt-in por tipo de dato, TTL, borrado a pedido y evidencia; por defecto, stateless. **Detección.** Revisar el default de cada flag; si guarda sin preguntar, no hay consentimiento.

### M4 · Memoria que filtra PII

**Severidad:** crítico · **Patrón correcto:** [Cap. 08](08-seguridad.md)
**Síntoma.** El historial guarda teléfonos, nombres o direcciones en claro; los logs incluyen el número completo; no hay exportación ni borrado. **Por qué duele.** La memoria se convierte en una base de PII que nadie diseñó para proteger; un log, un backup o un export la filtran y el usuario no puede ejercer sus derechos.
**Ejemplo.** Wenuke registra el número completo en el error de WhatsApp (`Wenuke/backend/whatsapp.py:74`) y guarda WhatsApp y nombre en claro (`Wenuke/backend/db.py:216-224`), sin borrado ni exportación. **Arreglo.** Seudonimizar la identidad, separar PII de analytics, redactar logs, TTL y endpoints de exportación/borrado. **Detección.** Buscar teléfonos, correos y nombres en logs y tablas de historial.

---

## Seguridad

### S1 · Webhook sin firma

**Severidad:** crítico · **Patrón correcto:** [Cap. 08](08-seguridad.md)
**Síntoma.** El endpoint acepta cualquier POST, sin HMAC, timestamp ni límite de cuerpo; la autenticación depende de una URL secreta o de la buena fe del proveedor. **Por qué duele.** Cualquiera inyecta mensajes, dispara tools o llena la base; la URL se filtra en logs, proxies y repositorios.
**Ejemplo.** Observado en la industria. Los contrastes son copiloto, que valida `sha256(secret, timestamp.body)` con tolerancia de 300 s (`copiloto-recepcion copiloto/src/copiloto/app.py:45-55`), y AgroVoz, que valida HMAC con `hmac.compare_digest` (`AgroVoz/backend/app/core/security.py:284-320`). **Arreglo.** HMAC sobre el cuerpo crudo, timestamp, límite de tamaño y rechazo si falta el secreto. **Detección.** Enviar un POST sin firma; si se procesa, el webhook es público.

### S2 · Secretos en el prompt o en el repositorio

**Severidad:** crítico · **Patrón correcto:** [Cap. 08](08-seguridad.md)
**Síntoma.** La API key, el token del PMS o la contraseña de administración aparecen en el system prompt, en `.env` versionado, en `docker-compose.yml` o en variables `VITE_*`. **Por qué duele.** El prompt se filtra con una inyección o un log; el repo se clona o se publica. Rotar un secreto filtrado no borra el daño.
**Ejemplo.** Observado en la industria. Caso cercano: ManttoAI publica la contraseña de la cuenta demo en el bundle Vite (`ManttoAI/README.md:190-192`); es un `visualizador` de solo lectura, pero muestra el patrón de credencial que viaja al cliente. **Arreglo.** Secret manager, prompt sin secretos, arranque que falla si falta uno y rotación documentada. **Detección.** `grep` de `sk-`, `token`, `password` y `secret` en repo y prompts.

### S3 · Logs con PII

**Severidad:** alto · **Patrón correcto:** [Cap. 09](09-observabilidad.md)
**Síntoma.** El log de errores incluye teléfono, correo, nombre o el texto completo del mensaje; "para depurar" se guarda todo. **Por qué duele.** Los logs tienen otra retención, otro acceso y otro backup que la base principal; una PII que no estaba en el diseño termina en un sistema sin controles.
**Ejemplo.** Wenuke registra el número completo al fallar el envío (`Wenuke/backend/whatsapp.py:74`); ManttoAI guarda el texto completo del chat sin redacción (`ManttoAI/backend/app/models/chat.py:15-32`). **Arreglo.** Redactar en el logger, hashear identificadores y separar metadata de contenido. **Detección.** Buscar patrones de teléfono y correo en una muestra de logs.

### S4 · Panel sin autenticación

**Severidad:** alto · **Patrón correcto:** [Cap. 08](08-seguridad.md)
**Síntoma.** El panel de métricas, el historial o el export están expuestos sin login, con un token único compartido o detrás de una URL "difícil". **Por qué duele.** El panel muestra conversaciones, costos y salud del sistema: es un mapa para atacar. Sin roles, un token filtrado da acceso total y no se revoca por usuario.
**Ejemplo.** copiloto documenta que `/metricas*` no tiene autenticación propia y debe protegerse en el proxy (`copiloto-recepcion/README.md:136-137`; `copiloto-recepcion docs/despliegue.md:88-90`). **Arreglo.** Auth en la aplicación, roles mínimos, tokens revocables y auditoría de acceso. **Detección.** Abrir el panel sin cookie; si responde datos, está abierto.

### S5 · Rate limit global como única defensa

**Severidad:** alto · **Patrón correcto:** [Cap. 08](08-seguridad.md)
**Síntoma.** Hay un límite global por IP o proceso, pero el chat no tiene cuota por usuario, sesión ni tenant; un usuario consume el presupuesto de todos. **Por qué duele.** El límite global protege la infraestructura, no el costo del modelo; un bucle o un script agota la cuota y degrada a los demás.
**Ejemplo.** ManttoAI aplica 1.500/h global (`ManttoAI/backend/app/middleware/rate_limit.py:71-84`), pero el chat no tiene rate limit por endpoint ni presupuesto de tokens. **Arreglo.** Cuota por identidad y tenant, presupuesto por ventana, límite antes de la llamada y 429 con `Retry-After`. **Detección.** Simular 100 mensajes de un usuario; si el global es la única barrera, el costo no está controlado.

### S6 · Confiar en el texto del modelo para autorizar

**Severidad:** crítico · **Patrón correcto:** [Cap. 04](04-orquestacion-tools.md)
**Síntoma.** La tool recibe `confirmed=true`, `user_approved` o `guest_confirmed` como argumento del modelo y ejecuta; el servidor no verifica el texto original del usuario. **Por qué duele.** El modelo puede inventar la confirmación, confundir un "quizá" con un "sí" o ser manipulado; la autorización se delega a la entidad que puede equivocarse.
**Ejemplo.** copiloto v3 reservó con un nombre inventado porque confiaba en la declaración del modelo; la corrección fue verificar el "sí" y el nombre sobre el texto del huésped (`copiloto-recepcion docs/caso-de-estudio.md:68-71`; `copiloto-recepcion copiloto/src/copiloto/ai/tools.py:22-29`, `:303-307`). **Arreglo.** Leer la confirmación del último mensaje con una regla explícita; ejecutar en un turno posterior. **Detección.** Buscar `confirmed` en argumentos; si el servidor lo usa como permiso, la autorización está en el modelo.

---

## Evals

### E1 · Vibe evals con mocks

**Severidad:** alto · **Patrón correcto:** [Cap. 07](07-evaluacion.md)
**Síntoma.** "Probé el chat y responde bien"; los tests mockean el LLM y verifican substrings, sin un set de conversaciones contra el modelo real. **Por qué duele.** El mock prueba que el orquestador llama al cliente, no que la respuesta sea correcta; un cambio de prompt o modelo pasa el test y rompe la calidad.
**Ejemplo.** ManttoAI prueba el chat con `httpx.AsyncClient` mockeado y aserciones de substring (`ManttoAI/backend/tests/test_chat.py:182-190`); no hay eval de groundedness, inyección, PII ni multi-turno. **Arreglo.** Golden set versionado contra el endpoint real, con casos bloqueantes y código de salida. **Detección.** Preguntar cuántos casos corren contra el modelo real; si son cero, son tests de plumbing.

### E2 · Solo promedio

**Severidad:** alto · **Patrón correcto:** [Cap. 07](07-evaluacion.md)
**Síntoma.** El reporte muestra accuracy, F1 o latencia media; no hay segmentos por canal, intención, tenant, dificultad ni tipo de error. **Por qué duele.** El promedio alto esconde el caso que pierde dinero: la reserva sin confirmación, la pregunta de un tenant grande o el fallo de un canal.
**Ejemplo.** ManttoAI reporta accuracy 0.9413 y F1 0.9304 sobre un dataset sintético, sin desagregación por rubro ni tipo de fallo (`ManttoAI/backend/reports/ml-evaluation-latest.md:25-37`). **Arreglo.** Métricas por segmento y lista de fallos bloqueantes; un caso crítico no se compensa con 99 fáciles. **Detección.** Pedir el resultado del peor segmento; si no existe, el promedio es vanidad.

### E3 · Judge sin calibrar

**Severidad:** medio · **Patrón correcto:** [Cap. 07](07-evaluacion.md)
**Síntoma.** Un LLM juega de evaluador sin acuerdo con humanos, sin rúbrica y sin casos de control; el puntaje cambia cuando cambia el judge. **Por qué duele.** Se introduce otro modelo no determinista en la cadena de calidad y no se distingue una mejora real de una preferencia del evaluador.
**Ejemplo.** Observado en la industria. Los cuatro proyectos no documentan un judge calibrado; copiloto usa criterios deterministas en su model eval (`copiloto-recepcion scripts/model_eval.py:14-16`), la dirección más segura. **Arreglo.** Rúbrica, muestra etiquetada por humanos, acuerdo inter-evaluador y casos de control. **Detección.** Comparar el judge con una muestra humana; si el acuerdo es bajo, no es confiable.

### E4 · Evals que no corren en CI

**Severidad:** alto · **Patrón correcto:** [Cap. 07](07-evaluacion.md)
**Síntoma.** El set de evals existe, pero se ejecuta a mano, en la máquina de una persona, contra un entorno que ya cambió; el CI solo corre unitarios. **Por qué duele.** Una regresión de calidad no bloquea el merge; el equipo la descubre en producción y el eval pierde valor como red de seguridad.
**Ejemplo.** Wenuke tiene 22 E2E, pero `pytest.ini` y el workflow los excluyen (`Wenuke/backend/pytest.ini:7`; `Wenuke/.github/workflows/test.yml:75`); ManttoAI no tiene eval de calidad del chat en CI. **Arreglo.** Runner en CI contra un endpoint reproducible, con umbral y casos bloqueantes; subconjunto crítico por PR y set completo nightly. **Detección.** Revisar el workflow; si el comando no aparece, no protegen nada.

---

## Observabilidad

### O1 · Logs sin estructura ni correlación

**Severidad:** medio · **Patrón correcto:** [Cap. 09](09-observabilidad.md)
**Síntoma.** `print` o logs de texto libre, sin nivel, `request_id`, tenant ni etapa; cada servicio escribe su formato y nadie sigue un turno. **Por qué duele.** Cuando falla una conversación, la traza se corta entre webhook, orquestador y tool; el on-call adivina y el incidente dura más que el fallo.
**Ejemplo.** Wenuke declara logging JSON, pero `structlog` no está en `requirements.txt` y el formato base es texto (`Wenuke/backend/logging_config.py:37-56`; `Wenuke/backend/requirements.txt:1-18`). AgroVoz sí inyecta `X-Request-ID` (`AgroVoz/backend/app/main.py:83-105`). **Arreglo.** Log JSON con `request_id`, `conversation_id`, `tenant`, `stage`, `outcome`, modelo y prompt. **Detección.** Buscar un turno por su ID en todos los servicios.

### O2 · Métricas sin etiquetas

**Severidad:** medio · **Patrón correcto:** [Cap. 09](09-observabilidad.md)
**Síntoma.** Un contador global de mensajes, errores o latencia, sin etiquetas de canal, intención, tenant, modelo ni versión. **Por qué duele.** El promedio global esconde que WhatsApp va bien y voz va mal, o que un tenant consume el 80% del costo; la alerta se dispara tarde y la causa queda invisible.
**Ejemplo.** Observado en la industria. Las métricas de copiloto son contadores sin autenticación y sin desagregación por canal (`copiloto-recepcion/README.md:136-137`). **Arreglo.** Etiquetas mínimas y p50/p95, no solo promedio. **Detección.** Intentar responder qué canal falla más; si la métrica no lo permite, faltan etiquetas.

### O3 · No medir el fallback

**Severidad:** alto · **Patrón correcto:** [Cap. 09](09-observabilidad.md)
**Síntoma.** El agente "responde siempre", pero una parte de las respuestas es la plantilla de degradación; no hay contador ni tasa por causa. **Por qué duele.** El fallback silencioso parece una respuesta normal; la calidad cae, el equipo no lo ve y el usuario recibe un mensaje genérico.
**Ejemplo.** Wenuke devuelve `offline: true` y lo muestra (`Wenuke/backend/llm.py:130-159`; `Wenuke/frontend/app.js:238-240`), pero no hay métrica que agregue ese conteo. **Arreglo.** Contador por causa —sin modelo, timeout, tool denegada, dato vencido— y tasa por canal con alerta. **Detección.** Preguntar qué porcentaje de respuestas son fallback; si no hay número, no se mide.

### O4 · No medir costo

**Severidad:** alto · **Patrón correcto:** [Cap. 10](10-costos-modelos.md)
**Síntoma.** El costo se estima por tarifa pública, no por tokens reales; no se registran tokens de entrada/salida, tools, reintentos ni modelo por turno. **Por qué duele.** La primera señal es la factura; sin costo por turno y conversación no se puede presupuestar, comparar modelos ni detectar abuso.
**Ejemplo.** Wenuke declara $0–10/mes sin medición de tokens (`Wenuke/README.md:40`); ManttoAI no tiene presupuesto de tokens por usuario y el chat solo hereda el límite global (`ManttoAI/backend/app/middleware/rate_limit.py:71-84`). **Arreglo.** Registrar tokens, modelo, tools y `outcome` por turno; agregar costo por conversación y tenant. **Detección.** Calcular el costo del último día; si no se puede, no hay medición.

---

## Costos

### C1 · Modelo grande para todo

**Severidad:** alto · **Patrón correcto:** [Cap. 10](10-costos-modelos.md)
**Síntoma.** El modelo más caro clasifica, extrae, resume y responde FAQ; no hay ruteo por tarea ni modelo pequeño para el camino simple. **Por qué duele.** Se paga razonamiento que no se usa y se agrega latencia; la tarea simple no mejora y el costo por turno sí.
**Ejemplo.** Wenuke usa `llama-3.1-70b-versatile` (`Wenuke/backend/config.py:10`) para respuestas de máximo tres oraciones (`Wenuke/backend/llm.py:144-152`), un trabajo que un modelo pequeño o una regla pueden resolver. **Arreglo.** Ruteo por tarea: regla o modelo pequeño para clasificar/extraer; modelo mayor solo para razonamiento abierto. **Detección.** Listar tareas y modelo usado; si todas usan el mismo, no hay selección.

### C2 · Presupuesto que ignora reintentos y tools

**Severidad:** alto · **Patrón correcto:** [Cap. 10](10-costos-modelos.md)
**Síntoma.** El presupuesto se calcula por una llamada; no cuenta tools, reintentos ante 429/5xx, generaciones de resumen ni el loop. **Por qué duele.** Una conversación puede costar tres o cinco veces lo presupuestado; el límite se agota en el caso anómalo, justo cuando más importa.
**Ejemplo.** Observado en la industria. Los contrastes son AgroVoz, con máximo 3 iteraciones (`AgroVoz/backend/app/services/llm_service.py:127`), y copiloto, con máximo 5 pasos y un reintento (`copiloto-recepcion copiloto/src/copiloto/ai/agent.py:19`; `copiloto-recepcion copiloto/src/copiloto/ai/llm.py:54-69`). **Arreglo.** Presupuesto por turno que incluya tools, reintentos y fallback; cortar al agotar y registrar la causa. **Detección.** Comparar tokens facturados con la llamada principal.

### C3 · Comparar prototipo con producción

**Severidad:** alto · **Patrón correcto:** [Cap. 10](10-costos-modelos.md)
**Síntoma.** El costo del prototipo —hardware, VPS, free tiers— se presenta como costo del producto; no incluye soporte, evals, personas, redundancia ni crecimiento. **Por qué duele.** La unidad económica parece viable y deja de serlo al primer cliente real; el precio se decide sobre un escenario que nunca se operó.
**Ejemplo.** ManttoAI declara un prototipo de USD 98 y un plan comercial con costo operacional de CLP 187.100/mes (`ManttoAI/docs/costos/12-plan-gestion-costos.md:44-74`, `:123-125`); son escenarios distintos y el documento lo aclara. **Arreglo.** Separar costo de prototipo, piloto y producción, con supuestos escritos. **Detección.** Preguntar qué incluye el número; sin supuestos, es una anécdota.

---

## Despliegue

### DP1 · `BackgroundTasks` como cola

**Severidad:** alto · **Patrón correcto:** [Cap. 11](11-despliegue.md)
**Síntoma.** El webhook responde 200 y agenda el trabajo en el proceso; si el proceso reinicia, el trabajo en vuelo se pierde y no hay reintento ni visibilidad. **Por qué duele.** El ACK rápido está bien; la falta de durabilidad no. El usuario cree que el mensaje se procesó y el estado queda inconsistente.
**Ejemplo.** copiloto procesa el webhook en `BackgroundTasks` (`copiloto-recepcion copiloto/src/copiloto/app.py:170-181`) y documenta que un reinicio pierde el trabajo en vuelo (`copiloto-recepcion docs/escalabilidad.md:21`). **Arreglo.** Cola durable con reintentos, idempotencia y estado visible; persistir antes de responder. **Detección.** Reiniciar el servicio durante una ráfaga; si se pierden mensajes, no hay cola.

### DP2 · Scheduler en serverless

**Severidad:** crítico · **Patrón correcto:** [Cap. 11](11-despliegue.md)
**Síntoma.** `asyncio.create_task` o un `while True` en el `lifespan` para enviar alertas o sincronizar datos; en serverless, la instancia se congela o se destruye. **Por qué duele.** El scheduler no garantiza ejecución; las alertas se retrasan o no salen, y el primer chequeo puede esperar horas si el loop duerme antes de correr.
**Ejemplo.** Wenuke lanza un scheduler en el `lifespan` (`Wenuke/backend/main.py:130-135`) que duerme antes del primer chequeo (`Wenuke/backend/scheduler.py:32-37`), sobre un backend Vercel serverless. **Arreglo.** Cron externo o cola programada; el proceso ejecuta una unidad idempotente y persiste la última ejecución. **Detección.** Buscar `create_task`, `while True` y `sleep` en el arranque.

### DP3 · Estado local en infraestructura efímera

**Severidad:** alto · **Patrón correcto:** [Cap. 11](11-despliegue.md)
**Síntoma.** Rate limit, sesiones, locks o SQLite viven en memoria o en `/tmp`; con dos réplicas cada una ve un estado distinto y al reiniciar se pierde. **Por qué duele.** Los límites se eluden, las sesiones se duplican y las escrituras se pierden; el bug es intermitente y depende del balanceador.
**Ejemplo.** Wenuke usa un rate limiter en memoria (`Wenuke/backend/main.py:69-80`) y, en Vercel, SQLite en `/tmp/wenuke.db` (`Wenuke/backend/config.py:11-14`); copiloto advierte que los locks locales no sirven con varias réplicas (`copiloto-recepcion docs/despliegue.md:114-120`). **Arreglo.** Store externo para estado compartido y base gestionada para persistencia; proceso stateless. **Detección.** Escalar a dos réplicas y repetir el flujo.

### DP4 · Deploy sin rollback

**Severidad:** alto · **Patrón correcto:** [Cap. 11](11-despliegue.md)
**Síntoma.** Se despliega sobre la versión anterior sin imagen etiquetada, sin migración reversible y sin procedimiento de vuelta; el rollback es "volver a desplegar el commit". **Por qué duele.** Un cambio de prompt o schema rompe producción y la recuperación depende de la velocidad del equipo, no de un botón.
**Ejemplo.** Observado en la industria. El contraste es copiloto, con imágenes fijadas por versión en Compose (`copiloto-recepcion infra/docker-compose.yml:53-84`), una base para volver a la anterior. **Arreglo.** Imágenes inmutables, migraciones compatibles hacia atrás, rollback probado y prompt versionado. **Detección.** Preguntar cuál es el comando de rollback y cuándo se probó.

### DP5 · Backup no probado

**Severidad:** crítico · **Patrón correcto:** [Cap. 11](11-despliegue.md)
**Síntoma.** Hay un script de backup, pero nadie restauró; el backup se considera una copia y la restauración es un supuesto. **Por qué duele.** Un backup que no restaura es una falsa sensación de seguridad; cuando hace falta, faltan permisos, tablas o el formato cambió.
**Ejemplo.** copiloto genera `pg_dump` y copias SQLite con `PRAGMA integrity_check`, pero declara que restaurar es manual y hay que probarlo (`copiloto-recepcion docs/despliegue.md:35-46`); AgroVoz mantiene backup/restore como gate abierto (`AgroVoz/docs/validacion-operativa.md:226-244`). **Arreglo.** Restauración periódica en un entorno limpio, con verificación y tiempo de recuperación medido. **Detección.** Restaurar el último backup; si falla, no hay backup.

---

## Documentación y operación

### DO1 · README que miente

**Severidad:** alto · **Patrón correcto:** [Cap. 13](13-casos-de-estudio.md)
**Síntoma.** El README promete una capacidad que el código no tiene: conversación sin inbound, deploy que no existe, modelo que no corre en el tier. **Por qué duele.** La primera persona que intenta usar el producto descubre la brecha; la confianza se pierde antes de llegar al valor y el soporte explica lo que no hay.
**Ejemplo.** Wenuke se presenta como asistente conversacional (`Wenuke/README.md:3-4`), pero el código solo envía mensajes (`Wenuke/backend/whatsapp.py:53-64`). AgroVoz tiene una disputa documental sobre qué deploy está vigente (`AgroVoz/docs/ARCHITECTURE-DECISIONS.md:312-379`). **Arreglo.** Cada afirmación se prueba con un comando o un enlace al código; lo no implementado es roadmap. **Detección.** Recorrer el README y ejecutar cada promesa.

### DO2 · Cifras copiadas entre documentos

**Severidad:** medio · **Patrón correcto:** [Cap. 09](09-observabilidad.md)
**Síntoma.** Los tests son 375 en el README, 373 en la auditoría y 320 en la línea base; la latencia es 1 s en el caso de estudio y 10 s en el e2e. **Por qué duele.** Las decisiones se toman sobre números que no se pueden reproducir; el equipo discute cifras en vez de problemas.
**Ejemplo.** ManttoAI declara 375/372/3 en el README, 373/370/3 en el estado de implementación y 320/317/3 en QA (`ManttoAI/README.md:137`; `ManttoAI/docs/auditoria/estado-implementacion.md:82-84`; `ManttoAI/docs/auditoria/qa.md:23-33`). copiloto declara 137 y 139 (`copiloto-recepcion docs/caso-de-estudio.md:84`; `copiloto-recepcion docs/escalabilidad.md:34`). **Arreglo.** Generar las cifras desde el runner y publicarlas con fecha y commit; un solo archivo de referencia. **Detección.** Buscar el mismo número en dos documentos.

### DO3 · Operación de una persona y validación solo local

**Severidad:** alto · **Patrón correcto:** [Cap. 11](11-despliegue.md)
**Síntoma.** Una persona mantiene el sistema, no hay runbook y la validación se hizo en la máquina local con SQLite en memoria y mocks; "funciona en mi máquina" es el criterio. **Por qué duele.** El bus factor es uno y el entorno real difiere: cold starts, base gestionada, proxy, cuotas y latencia; el primer incidente se resuelve improvisando.
**Ejemplo.** AgroVoz es una demo de portfolio mantenida por una persona, con benchmark E2E, WER, piloto y revisión legal como gates abiertos (`AgroVoz/docs/validacion-operativa.md:8-20`, `:226-244`); ManttoAI prueba con SQLite en memoria (`ManttoAI/backend/tests/conftest.py:43-56`) y Playwright mockea el backend (`ManttoAI/frontend/tests/fixtures.js:21-36`). **Arreglo.** Runbook, segundo responsable, smoke test contra el entorno real y staging con las mismas dependencias. **Detección.** Preguntar quién responde a las 3 a.m. y con qué documento.

---

## Checklist de auditoría de un agente existente

Responde sí o no. Cada "sí" suma 1 punto; cada "no" suma 0. No hay puntos parciales: si la
evidencia no está, la respuesta es no.

| # | Pregunta | Anti-patrón |
|---|---|---|
| 1 | ¿El agente tiene un usuario, una tarea y una decisión de negocio medible? | P1 |
| 2 | ¿Existe un alcance escrito que enumere lo que el agente no hace? | P2, P3 |
| 3 | ¿El canal de entrada está implementado y probado, no solo el de salida? | P4 |
| 4 | ¿Cada dato factual sale de una tool, API o corpus con fuente y fecha? | D2 |
| 5 | ¿Las fuentes vencidas fallan cerrado en todas las rutas? | D3 |
| 6 | ¿El loop tiene máximo de pasos, deadline y presupuesto de tokens? | A3 |
| 7 | ¿Las tools tienen schema cerrado y validación en el servidor? | T1, T2 |
| 8 | ¿Toda escritura irreversible exige confirmación en un turno posterior? | T3 |
| 9 | ¿La confirmación se verifica contra el texto del usuario, no contra el modelo? | S6 |
| 10 | ¿Existe whitelist de tools en código y lo no permitido falla a un texto seguro? | T5 |
| 11 | ¿El prompt está versionado y su versión aparece en logs o respuesta? | PR5 |
| 12 | ¿El contexto inyectado está acotado, delimitado y escapado? | D5, M2 |
| 13 | ¿La memoria es opt-in, con TTL y borrado verificable? | M3, M4 |
| 14 | ¿Los webhooks validan firma, timestamp y tamaño antes de procesar? | S1 |
| 15 | ¿Los secretos viven fuera del repo, del prompt y de los logs? | S2, S3 |
| 16 | ¿Los logs no contienen PII y tienen correlación por turno? | O1 |
| 17 | ¿Se mide fallback, latencia p95 y costo por turno y conversación? | O3, O4 |
| 18 | ¿Hay un golden set con casos bloqueantes que corre contra el modelo real en CI? | E1, E4 |
| 19 | ¿El deploy tiene rollback, backup probado y estado fuera del proceso? | DP3, DP4, DP5 |
| 20 | ¿Las cifras de tests, latencia y costo se generan desde el runner y tienen fecha? | DO2 |

**Puntaje y veredicto**

| Puntaje | Veredicto | Qué significa |
|---|---|---|
| 18–20 | Production-ready con deuda menor | El contrato existe; corrige los "no" restantes antes del próximo cambio de modelo. |
| 14–17 | Pilot-ready | Puede operar con supervisión y un grupo acotado; cierra los críticos antes de escalar. |
| 10–13 | Demo | No lo expongas a usuarios reales sin supervisión; el contrato tiene huecos materiales. |
| 0–9 | No listo | Detén la expansión y corrige canal, autorización, datos y seguridad antes de agregar features. |

Un puntaje alto no absuelve un fallo crítico: si la pregunta 8 o la 14 es "no", el veredicto
baja un nivel aunque el total sea 19. La seguridad y las acciones irreversibles no se
compensan con puntos.

## Cómo priorizar

La prioridad no es "lo más fácil" ni "lo más nuevo". Es impacto × probabilidad: cuánto daño
causa si falla y qué tan probable es que falle con el uso real.

| Impacto \ Probabilidad | Alta | Media | Baja |
|---|---|---|---|
| **Alto** | Arreglar hoy: autorización, datos vencidos, webhook sin firma, pérdida de mensajes. | Arreglar en el sprint: loop sin límite, backup no probado, memoria sin consentimiento. | Planificar: rollback, multi-tenant, costos a escala. |
| **Medio** | Arreglar en el sprint: rate limit por usuario, logs con PII, tool sin schema. | Deuda priorizada: prompt gigante, métricas sin etiquetas, RAG innecesario. | Documentar y revisar: cifras derivadas, README desactualizado. |
| **Bajo** | Corregir si bloquea una demo: tool declarada no conectada. | Aceptar con registro: framework-first en un prototipo. | Ignorar: estilo de prompt sin impacto medido. |

**Qué arreglar primero en una demo**

1. **Canal de entrada real (P4).** Sin inbound no hay producto que demostrar.
2. **Webhook firmado y limitado (S1).** Una demo pública sin firma es una puerta abierta.
3. **Confirmación y autorización (T3, S6).** No ejecutes acciones irreversibles en vivo.
4. **Datos con fuente y fecha (D2, D3).** Un dato vencido destruye la credibilidad.
5. **Fallback visible (O3).** Muestra qué pasa cuando el modelo no responde.

**Qué arreglar primero en un piloto**

1. **Evals en CI con casos bloqueantes (E1, E4).** Sin red de calidad, cada cambio es una apuesta.
2. **Rate limit y presupuesto por usuario (S5, O4).** El piloto ya tiene costo real.
3. **Estado y cola durables (DP1, DP3).** Un reinicio no puede borrar conversaciones.
4. **Memoria con consentimiento y retención (M3, M4).** La privacidad se diseña antes de escalar.
5. **Observabilidad por turno (O1, O2).** Sin traza, el piloto no produce aprendizaje.

**Qué arreglar primero en producción**

1. **Backup y restore probados (DP5).** El restore es el único backup que existe.
2. **Rollback de código y de prompt (DP4, PR5).** La recuperación debe ser un procedimiento.
3. **Panel y métricas con auth (S4).** El panel es un mapa del sistema; protégelo.
4. **Presupuesto y alertas de costo (O4, C2).** La factura no puede ser la primera señal.
5. **Runbook y segundo responsable (DO3).** El sistema no puede depender de una sola persona.

## Cierre

Un anti-patrón no se corrige con más prompt. Se corrige moviendo la decisión al lugar donde
se puede verificar: el contrato del canal, el schema de la tool, el gate de frescura, la
validación del servidor, el eval en CI, la traza del turno. El modelo sigue siendo útil; deja
de ser el chivo expiatorio.

Si este capítulo te deja una sola práctica, que sea esta: **antes de agregar una capacidad,
escribe qué pasa cuando falla y cómo lo vas a detectar**. Si no puedes responderlo con un
`path:line`, una métrica o un test, todavía no está diseñado.

Continúa con:

- [Capítulo 1 — Principios fail-closed](01-principios-fail-closed.md): la regla de oro que
  convierte cada anti-patrón en un fallback explícito.
- [Capítulo 4 — Orquestación y tools](04-orquestacion-tools.md): loop acotado, validación en
  servidor y doble confirmación.
- [Capítulo 7 — Evaluación](07-evaluacion.md): cómo pasar de "responde" a "responde bien".
- [Capítulo 8 — Seguridad](08-seguridad.md): modelo de amenazas, inyección, permisos y
  privacidad.
- [Capítulo 9 — Observabilidad](09-observabilidad.md): trazas, métricas, logs y costo por turno.
- [Capítulo 11 — Despliegue](11-despliegue.md): colas, estado, backups y rollback.
- [Capítulo 13 — Casos de estudio](13-casos-de-estudio.md): los cuatro proyectos, sus fallos
  y sus aciertos con evidencia.
- [Capítulo 14 — Plantillas](14-plantillas.md): las estructuras copiables para prompts, tools,
  evals y runbooks.

## Key Learnings

1. **El contrato alrededor del modelo es el producto.** Canal, schema, validación, frescura,
   permisos y observabilidad deciden la confiabilidad; el modelo solo redacta.
2. **Los anti-patrones más caros se ven como atajos.** `BackgroundTasks` como cola, estado en
   memoria, historial persistido como memoria y tool definitions sin runtime funcionan en
   demo y fallan cuando hay un usuario real.
3. **La autorización no se delega al modelo.** Confirmaciones, permisos y datos se verifican
   en el servidor contra el texto del usuario y las reglas del dominio.
4. **La evidencia cambia la conversación.** Un `path:line`, una métrica o un caso de eval
   convierten "creo que falla" en un arreglo priorizable.
5. **Priorizar es impacto × probabilidad, no novedad.** Primero se cierra lo que puede causar
   daño irreversible; después se paga la deuda que impide escalar.
