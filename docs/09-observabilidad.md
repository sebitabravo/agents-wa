<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Capítulo 9 — Observabilidad: cada turno es una transacción

> **Tipo:** how-to + explanation.
> **Audiencia:** desarrolladores y responsables de operación que ya tienen un
> agente respondiendo y necesitan saber por qué falla, cuánto cuesta y cuándo
> degradarlo.
> **Meta:** al terminar, cada turno produce una traza correlacionada con
> metadata suficiente para diagnosticar latencia, fallback, tools y costo sin
> guardar el contenido de las conversaciones.

Un agente falla en silencio: no lanza una excepción cuando responde mal, inventa
un dato, tarda ocho segundos o cae al fallback; sigue respondiendo. Sin trazas,
el operador no distingue una respuesta correcta de una degradada. La tesis es una
sola: **cada turno es una transacción observable, no un log suelto**. Observar no
es coleccionar todo: es registrar lo mínimo para responder qué entró, qué decidió
el sistema, qué salió y cuánto costó. El contenido es la parte más sensible y la
menos necesaria para operar; se separa de la metadata y se captura solo con
opt-in.

## La respuesta primero

| # | Regla | En una frase |
|---|-------|--------------|
| R1 | Una traza por turno | El turno es la transacción; los spans dicen dónde se fue el tiempo. |
| R2 | Metadata antes que contenido | Identificadores, tokens, latencias y resultados; prompts y respuestas fuera por defecto. |
| R3 | Medir las tres del capítulo 6 | Latencia, fallback y costo son el piso; tools y entrega completan el cuadro. |
| R4 | Alertar por síntoma | Se alerta cuando el usuario sufre; se diagnostica con la causa en la traza. |
| R5 | Todo incidente deja una prueba | Kill switch, rollback y postmortem con un caso de evaluación nuevo. |

Si solo recuerdas una cosa: **un log sin `request_id` es una anécdota; una traza
sin `outcome` es una caja negra**.

---

## 9.1 La unidad de observabilidad: una traza por turno

Un turno empieza cuando el mensaje entra por el canal y termina cuando la
respuesta se entrega o se marca como fallida. La traza agrupa todos los pasos con
el mismo `trace_id`; cada paso es un span con inicio, fin, estado y atributos.
El orden es estable para que cualquier herramienta muestre el mismo árbol:

```text
turn (invoke_agent)                          trace_id = 7f3c...
├─ input          receive: channel, message_id, received_at
├─ normalize      trim, language, phone_hash, session_hash
├─ guardrails     rate_limit, injection_check, pii_redact
├─ retrieval      query, top_k, scores, sources
├─ llm            model, tokens_in/out, finish_reason
├─ tools          execute_tool × N: name, args_hash, status
├─ validate       schema, groundedness, policy
├─ output         render, redact, length
└─ deliver        send, delivery_status, delivered_at
```

Reglas del árbol:

1. **Un `trace_id` por turno.** Se genera al entrar y se propaga a logs, tools y
   llamadas salientes; si el canal trae otro identificador, se guarda aparte.
2. **Un span por etapa.** Si no aplica (por ejemplo, `retrieval` sin RAG), se
   marca `skipped` con `reason`; no se omite en silencio.
3. **El estado vive en el span.** `ok`, `error`, `timeout`, `blocked` o
   `fallback`; el `outcome` se deriva de los spans, no de un print.
4. **La entrega es parte del turno.** Una respuesta generada pero no entregada
   no es un turno exitoso; `delivery_status` cierra la transacción.

El `invoke_agent` es el span raíz. Los spans `chat` y `execute_tool` son hijos
directos cuando ocurren en el mismo turno; si hay varias llamadas al modelo, hay
varios `chat`, uno por intento. Esa estructura permite responder “¿fue el modelo
o la tool?” sin leer el prompt.

## 9.2 Esquema mínimo de campos

La metadata mínima se guarda por turno, no por mensaje suelto. La tabla prioriza
lo que permite diagnosticar y atribuir costo; la columna PII indica qué exige
seudonimización o prohibición.

| Campo | Tipo | Por qué | PII |
|---|---|---|---|
| `request_id` | string | Correlaciona la petición HTTP y los logs del canal. | No |
| `trace_id` | string | Une todos los spans del turno. | No |
| `session_id_hash` | string | Agrupa turnos de una conversación sin guardar el identificador. | Seudónimo |
| `channel` | enum | Separa latencia, costo y fallback por WhatsApp, voz o web. | No |
| `user_hash` / `tenant_hash` | string | Atribuye uso y costo sin identificar a la persona. | Seudónimo |
| `model` | string | Compara proveedores y detecta cambios de modelo. | No |
| `prompt_version` | string | Reproduce una respuesta y permite rollback de prompt. | No |
| `tokens_in` / `tokens_out` | int | Calcula costo y detecta prompts que crecen. | No |
| `latency_ms` | map | Desglose por etapa: input, retrieval, llm, tools, deliver. | No |
| `tool_calls` | array | Nombre, `args_hash`, estado y duración de cada tool. | Args hash |
| `finish_reason` | enum | `stop`, `length`, `tool_calls`, `content_filter`. | No |
| `fallback_reason` | enum | `no_key`, `timeout`, `provider_error`, `guardrail`, `rate_limit`. | No |
| `cost_estimate` | float | Costo del turno con la tabla de precios vigente. | No |
| `outcome` | enum | `ok`, `refusal`, `handoff`, `error`, `blocked`. | No |
| `delivery_status` | enum | `pending`, `delivered`, `failed`. | No |
| `app_version` | string | Correlaciona regresiones con despliegues. | No |

Dos decisiones importantes. Primera: `args_hash` es un hash estable de los
argumentos de la tool, no los argumentos; alcanza para detectar patrones y evita
guardar direcciones, nombres o teléfonos. Segunda: el `session_id` se guarda
hasheado con sal por entorno; el hash permite continuidad analítica sin permitir
reconstruir el identificador original.

## 9.3 OpenTelemetry GenAI: el vocabulario estándar

OpenTelemetry publicó convenciones semánticas para GenAI que estandarizan spans,
métricas y atributos. Su estado es Development (2026-10), así que se adoptan como
vocabulario y se aíslan detrás de una capa propia para tolerar cambios. Fuente:
repositorio https://github.com/open-telemetry/semantic-conventions-genai y el blog
“Inside the LLM Call: GenAI Observability with OpenTelemetry” (2026-05-14,
https://opentelemetry.io/blog/2026/genai-observability/).

| Señal | Nombre | Uso |
|---|---|---|
| Span | `invoke_agent` | Turno completo del agente. |
| Span | `chat` | Cada llamada al modelo, incluidos reintentos. |
| Span | `execute_tool` | Cada ejecución de tool. |
| Span | `retrieval` | Búsqueda o recuperación de contexto. |
| Métrica | `gen_ai.client.operation.duration` | Latencia de llamadas al modelo. |
| Métrica | `gen_ai.client.token.usage` | Tokens de entrada y salida. |
| Métrica | `gen_ai.invoke_agent.duration` | Duración total del turno. |
| Métrica | `gen_ai.invoke_agent.inference_calls` | Llamadas al modelo por turno. |
| Métrica | `gen_ai.invoke_agent.tool_calls` | Tools por turno. |
| Métrica | `gen_ai.execute_tool.duration` | Latencia por tool. |
| Atributo | `gen_ai.request.model` | Modelo solicitado. |
| Atributo | `gen_ai.usage.input_tokens` / `output_tokens` | Consumo por llamada. |
| Atributo | `gen_ai.response.finish_reasons` | Motivo de finalización. |

La instrumentación mínima se ve así; el contenido no se agrega por defecto:

```python
from opentelemetry import trace
tracer = trace.get_tracer("agent.turn")

async def handle_turn(msg: IncomingMessage) -> TurnResult:
    with tracer.start_as_current_span("invoke_agent") as turn:
        turn.set_attribute("gen_ai.request.model", settings.llm_model)
        turn.set_attribute("app.prompt_version", PROMPT_VERSION)
        turn.set_attribute("app.channel", msg.channel)
        turn.set_attribute("enduser.id_hash", hash_user(msg.user_id))
        # child spans: chat, execute_tool, retrieval
        result = await run_pipeline(msg)
        turn.set_attribute("app.outcome", result.outcome)
        return result
```

**Contenido fuera por defecto.** Las convenciones definen atributos para
mensajes y tools (`gen_ai.system_instructions`, `gen_ai.input.messages`,
`gen_ai.output.messages`), pero capturarlos es opt-in por privacidad y costo. En
producción se recomienda guardar el contenido en un almacén separado con TTL y
registrar en el span solo una referencia. El blog lo dice sin ambigüedad: el
contenido se registra “when opted in”, no como comportamiento base.

## 9.4 Logs: JSON, correlación y redacción

El log es el diario de eventos del turno; la traza es la estructura. Se emiten
logs JSON, una línea por evento, con `ts`, `level`, `event`, `request_id`,
`trace_id` y los campos del evento. `event` es un enum estable (`turn.started`,
`llm.completed`, `tool.failed`, `turn.delivered`), no texto libre.

```json
{"ts":"2026-11-04T12:00:00Z","level":"info","event":"turn.completed","request_id":"a1b2","trace_id":"7f3c","channel":"whatsapp","model":"qwen2.5-3b","prompt_version":"v12","tokens_in":812,"tokens_out":96,"latency_ms":{"total":2410,"llm":1680,"retrieval":35},"tool_calls":[{"name":"check_availability","status":"ok","args_hash":"9d1e"}],"fallback_reason":null,"outcome":"ok","cost_estimate":0.0007,"delivery_status":"delivered","app_version":"1.8.2"}
```

Reglas de operación:

- **Niveles con dueño.** `DEBUG` para desarrollo, `INFO` para el ciclo del turno,
  `WARNING` para degradación recuperable y `ERROR` para fallo que afecta al usuario.
- **Nunca prompts ni respuestas por defecto.** Se registran longitudes, hashes y
  referencias; el contenido va al almacén de contenido con acceso restringido.
- **Redacción antes de emitir.** Teléfonos, correos, tokens y coordenadas se
  redactan en el formatter; un log que sale con PII ya es una filtración.
- **Muestreo declarado.** El 100 % de errores y fallbacks; un porcentaje de
  turnos exitosos si el volumen lo exige. El muestreo se decide por `trace_id`
  para no partir una traza.
- **Retención por tipo.** Logs operativos 7–30 días; agregados 13 meses;
  contenido según consentimiento y finalidad. La retención se configura, no se
  improvisa.

## 9.5 Métricas: las tres del capítulo 6 y las que faltan

Las tres métricas del capítulo 6 siguen siendo el piso: latencia, tasa de
fallback y costo por consulta. A ellas se suman las que explican por qué el piso
se rompe. Todas llevan etiquetas de `channel`, `model`, `prompt_version` y
`tenant_hash`; nunca `user_id` ni `trace_id`, que disparan la cardinalidad.

| Métrica | Fórmula simple | Para qué |
|---|---|---|
| Latencia p50/p95/p99 | percentil de `delivered_at - received_at` por canal | Percibir la espera real del usuario. |
| Tasa de fallback | turnos con `fallback_reason` / turnos totales | Detectar degradación silenciosa. |
| Costo por turno | `(tokens_in × precio_in + tokens_out × precio_out + tools + canal) / turnos` | Presupuesto y atribución. |
| Tasa de error de tools | tool calls con `status=error` / tool calls totales | Aislar la tool que rompe el turno. |
| Groundedness | respuestas con cita verificable y sin claim no soportado / respuestas con datos | Medir invención sobre una muestra. |
| Tasa de rechazo | rechazos / turnos | Distinguir “no sé” de “inventé”. |
| Tasa de handoff | handoffs / conversaciones | Ver si el bot deriva de más o de menos. |
| Profundidad de cola | pendientes y edad del más antiguo | Anticipar el SLA humano. |
| Tasa de entrega | mensajes con `delivery_status=delivered` / intentos | Separar generación de entrega. |
| Tokens por turno | `(tokens_in + tokens_out) / turnos` | Detectar prompts que crecen. |
| Cache hit rate | aciertos de caché / consultas a caché | Medir ahorro y latencia. |

Groundedness y tasa de rechazo no salen de un contador automático: se calculan
sobre una muestra evaluada con el pipeline del capítulo 7. El tablero debe decir
“muestra de N turnos”, no presentarlas como verdad universal.

## 9.6 Dashboards: tres audiencias, tres preguntas

Un tablero por audiencia; si todos miran el mismo, nadie lo usa.

| Tablero | Audiencia | Paneles | Frescura |
|---|---|---|---|
| Ejecutivo | Producto y operación | Volumen, costo total y por canal, resolución, satisfacción | Horaria o diaria |
| Operativo | On-call y soporte | Errores, latencia p50/p95/p99, colas, salud, fallback | 1–5 minutos |
| Calidad | Ingeniería de IA y QA | Evals, groundedness, rechazo, fallback, alucinación, injection blocks | Diaria |

El ejecutivo responde “¿esto sirve y cuánto cuesta?”. El operativo responde
“¿qué se está rompiendo ahora?”. El de calidad responde “¿está empeorando la
respuesta aunque los errores estén estables?”. Cada panel debe enlazar a la traza
del turno que originó el número; un gráfico sin drill-down es decoración.

## 9.7 Alertas: síntoma antes que causa

Se alerta sobre lo que sufre el usuario, no sobre cada métrica interna. La causa
se investiga en la traza. Toda alerta tiene dueño, severidad, runbook y ventana
de silencio; sin esas cuatro cosas, es fatiga garantizada.

| Señal | Umbral de ejemplo | Primera acción |
|---|---|---|
| Tasa de error | > 5 % durante 10 minutos | Revisar proveedor, tools y último deploy. |
| Caída de proveedor | 5xx o timeouts > 10 % durante 5 minutos | Conmutar al fallback y verificar el estado del proveedor. |
| Latencia p95 | > 2× la línea base durante 15 minutos | Mirar el span más lento por etapa. |
| Fallback | > 20 % o 2× la línea base durante 15 minutos | Verificar clave, cuota, modelo y proveedor. |
| Costo diario | > 80 % del presupuesto; 100 % corta | Throttle por tenant o kill switch. |
| Error de tools | > 10 % de las llamadas durante 10 minutos | Deshabilitar la tool y degradar. |
| Cola | edad del más antiguo > SLA | Avisar a recepción o pausar el bot. |
| Entrega | < 95 % de mensajes entregados | Revisar canal y credenciales. |
| Seguridad | pico de `injection_blocked` o `guardrail` | Congelar tools de escritura y revisar. |

Los umbrales son puntos de partida, no constantes universales: se calibran con
el baseline de cada despliegue. Un SLO de ejemplo —99,5 % de turnos exitosos por
mes— define un error budget; la alerta de “burn rate” avisa cuando se consume más
rápido de lo previsto. Sin SLO, el equipo discute opiniones en lugar de datos.

## 9.8 Incident response para agentes: runbook de 8 pasos

Un agente puede degradarse sin caerse. El runbook prioriza contener el daño,
preservar evidencia y aprender; no busca “reiniciar y ver”.

1. **Declarar y asignar.** Nombre del incidente, severidad, incident commander y
   canal único. Congelar despliegues, cambios de prompt y de modelo.
2. **Activar el kill switch.** Un flag detiene nuevos turnos o, al menos, las
   tools de escritura. Debe probarse antes del incidente, no durante.
3. **Degradar a reglas.** Responder con el flujo determinista o el menú seguro;
   mensaje explícito de degradación, sin inventar datos.
4. **Revertir el último cambio.** Prompt, modelo, versión de app o configuración
   de tools; volver a la versión pinneada que funcionaba.
5. **Deshabilitar tools riesgosas.** Escrituras, pagos, reservas y cualquier
   acción irreversible quedan fuera hasta confirmar la causa.
6. **Preservar evidencia.** Exportar trazas y logs por `request_id`, anotar
   `prompt_version`, `model` y `app_version`; snapshot de la configuración. No
   reiniciar antes de capturar lo volátil y no volcar PII al canal del incidente.
7. **Comunicar.** Estado interno, impacto al usuario, workaround y próxima
   actualización. Recepción necesita saber si el bot está en modo reglas.
8. **Postmortem sin culpa.** Línea de tiempo, causa raíz, factores contribuyentes
   y acciones con dueño y fecha. El incidente se convierte en un caso de
   evaluación de regresión del capítulo 7.

## 9.9 Evidencia real en los cuatro proyectos

Los cuatro proyectos tienen observabilidad parcial y distinta madurez. La tabla
resume qué existe y qué falta; las rutas son relativas a cada repositorio.

| Proyecto | Qué ya observa | Evidencia | Qué falta |
|---|---|---|---|
| AgroVoz | `X-Request-ID`, latencia por etapa, entrega, salud | `backend/app/main.py:83-105`, `backend/app/services/metrics_service.py:285-333` | `trace_id`, tokens/costo, tool args, logs JSON |
| copiloto | Eventos sin texto, métricas, panel y SLA | `copiloto/src/copiloto/events.py:1-21`, `copiloto/src/copiloto/metrics.py:12-95` | Spans, `prompt_version`, auth en `/metricas` |
| ManttoAI | Campo `fuente`, dashboard con polling | `backend/app/services/chat_service.py:61-88`, `frontend/src/utils/constants.js:43-47` | Latencia, tokens, modelo, `prompt_version` |
| Wenuke | Flag `offline` visible y fallback determinista | `backend/llm.py:131-159`, `frontend/app.js:238-240` | `request_id`, métricas, redacción de PII |

### AgroVoz: request_id y métricas por etapa

`RequestIDMiddleware` toma o genera un identificador, lo sanitiza contra log
injection y lo devuelve en la respuesta (`backend/app/main.py:83-105`); el
manejador de errores también lo agrega a los 500 (`:665-668`). El pipeline
persiste `whisper_ms`, `llm_ms` y `tts_ms` junto con la latencia total
(`backend/app/services/pipeline_service.py:1247-1258`) y emite un benchmark
agregado (`:1850`). Las métricas calculan p50/p95/p99 y excluyen `is_test`
(`backend/app/services/metrics_service.py:285-301` y `:270`). La entrega tiene
estado propio: `pending`, `delivered` o `failed`
(`backend/app/models/consultation.py:54-59`), y solo se marca `delivered` tras
confirmar el envío (`backend/app/services/audio_service.py:453`). La salud separa
liveness de readiness (`backend/app/api/health.py:40-74`).

Lo que falta: `request_id` no es un `trace_id`; no hay spans ni relación
padre-hijo. No se persisten tokens, costo, `prompt_version` ni `args_hash` de
tools. Los logs son texto con `request_id` (`AgroVoz/backend/app/main.py:437`), no JSON
estructurado. El contenido se guarda solo con opt-in de historial
(`backend/app/services/pipeline_service.py:1238-1258`), lo cual es correcto,
pero no reemplaza una política de contenido separada.

### copiloto: eventos con texto de entrada y panel operativo

La tabla `events` es la fuente de las métricas: el payload de `inbound` guarda
el texto de entrada, mientras que `ai_reply` no guarda texto
(`copiloto-recepcion/copiloto/src/copiloto/events.py:1-21`). `compute_metrics`
deriva latencia, tokens, tools, conversión y costo por consulta
(`copiloto/src/copiloto/metrics.py:12-95`). El panel muestra cola y SLA
(`copiloto/src/copiloto/app.py:230-232` y `:277-285`), y `/metricas/data.json`
expone el cálculo por rango (`:335-340`). El handoff registra una causa tipificada en el
evento (`copiloto/src/copiloto/events.py:14`), lo que permite separar `commercial`, `night`,
`pms_down` y `human_requested`.

Lo que falta: no hay spans ni `trace_id`; el evento no guarda modelo ni
`prompt_version`. `/metricas` no tiene autenticación y debe protegerse en el
proxy (`copiloto-recepcion/README.md:136-137`). El costo se calcula con configuración, no
con tokens reales por proveedor en todos los casos.

### ManttoAI: `fuente` como contrato de observabilidad

`procesar_mensaje` devuelve `fuente` con tres valores: `reglas`, `ollama` o
`fallback` (`backend/app/services/chat_service.py:61-88`). Ese campo se persiste
junto con el mensaje y la respuesta (`backend/app/models/chat.py:24-27`) y se
devuelve en el contrato HTTP (`backend/app/routers/chat.py:88-109`). Es la señal
mínima que permite auditar si la respuesta vino del camino determinista, del
modelo o de la degradación. El dashboard usa polling de 60 segundos
(`frontend/src/utils/constants.js:43-47`) con stale-while-revalidate
(`frontend/src/hooks/usePolling.js:14-26`).

Lo que falta: la fila de chat no guarda latencia, modelo, tokens ni
`prompt_version`; no hay `request_id` ni traza. Tampoco hay evaluación de
groundedness ni de latencia del LLM. `fuente` dice qué camino se usó, pero no
cuánto tardó ni cuánto costó.

### Wenuke: `offline` visible, pero sin traza

`preguntar` devuelve `{"respuesta": ..., "offline": bool}` y activa el flag
cuando no hay clave o cuando el proveedor falla (`backend/llm.py:131-159`). El
frontend lo muestra como “Respuesta sin conexión al asistente”
(`frontend/app.js:238-240`). Es un buen ejemplo de fallback observable para el
usuario: no se disfraza la degradación.

Lo que falta: no hay `request_id`, latencia, tokens ni métricas por turno. El
error de WhatsApp registra el número completo (`backend/whatsapp.py:74`), una
PII que debe redactarse. El logger intenta structlog en producción, pero si no
está instalado cae a texto sin avisar (`backend/logging_config.py:37-56`).

## 9.10 Cost tracking: tokens, tenant y presupuesto

El costo por turno se calcula con la tabla de precios vigente, versionada y
fechada; nunca con números hardcodeados en el código. La fórmula:

```text
cost_turn = tokens_in × price_in
          + tokens_out × price_out
          + tool_cost
          + channel_cost
```

Se agrega por conversación, tenant y canal. El tablero ejecutivo muestra el
costo del día y del mes; el operativo, el costo por turno y su tendencia. El
presupuesto tiene dos niveles: alerta al 80 % y corte al 100 %, con límites por
tenant para que un cliente no consuma el presupuesto de todos. La comparación de
modelos y precios vive en `10-costos-modelos.md`; este capítulo solo fija la
instrumentación que hace posible esa comparación.

## 9.11 Privacidad: metadata separada del contenido

La observabilidad es una superficie de fuga. OWASP LLM02 incluye en la
divulgación de información sensible no solo la respuesta final, sino también
argumentos de tools, trazas, chunks recuperados y logs. El diseño debe asumirlo.

- **Identificadores hasheados.** `user_hash`, `tenant_hash` y `session_id_hash`
  con sal o pepper por entorno; nunca teléfono, correo o documento en claro.
- **Contenido separado.** Prompts y respuestas en un almacén cifrado, con TTL y
  acceso auditado; en la traza solo una referencia.
- **Contenido off por defecto.** La captura de mensajes en OpenTelemetry es
  opt-in por entorno y tenant; se activa para depurar un caso y se apaga al terminar.
- **Redacción antes del export.** El exporter aplica la lista de campos
  prohibidos; no se confía en que el visor oculte lo que ya salió.
- **Retención y derechos.** Trazas 7–30 días, agregados 13 meses, contenido según
  consentimiento. La Ley 21.719 (vigencia diciembre 2026) exige finalidad,
  proporcionalidad y derechos ARCOP; la revisión legal no se reemplaza con un checkbox.

## 9.12 Checklist de observabilidad mínima

Doce puntos verificables antes de decir que el agente “está observado”:

- [ ] Cada turno tiene `request_id` y `trace_id`, y ambos aparecen en logs y respuesta.
- [ ] La traza tiene spans ordenados de input a entrega, con estado por etapa.
- [ ] Se registran `model`, `prompt_version` y `app_version` por turno.
- [ ] Se registran `tokens_in` y `tokens_out` por llamada al modelo.
- [ ] La latencia se desglosa por etapa y se calcula p50/p95/p99 por canal.
- [ ] Cada tool call registra nombre, `args_hash`, estado y duración.
- [ ] `fallback_reason` tiene un enum cerrado y se cuenta por motivo.
- [ ] `outcome` distingue `ok`, `refusal`, `handoff`, `error` y `blocked`.
- [ ] El costo estimado por turno se calcula con una tabla de precios versionada.
- [ ] `delivery_status` confirma o niega la entrega, no solo la generación.
- [ ] Logs y trazas redactan PII; el contenido está off por defecto y es opt-in.
- [ ] Hay retención, control de acceso y un runbook probado para cada alerta.

Si solo puedes medir cinco cosas, mide estas: **latencia p95, tasa de fallback,
costo por turno, tasa de error de tools y tasa de entrega**. Las cinco cubren la
experiencia, la degradación, el dinero, la causa técnica y el último kilómetro.

## Anti-patrones

1. **Logs con PII.** Teléfonos, correos o prompts completos en texto plano; el
   log se convierte en la base de datos que nunca quisiste tener.
2. **Solo `print`.** Sin niveles, sin `request_id`, sin estructura; imposible
   correlacionar un turno entre servicios.
3. **Métricas sin etiquetas.** Un promedio global esconde que WhatsApp va bien y
   voz va mal, o que un tenant consume el 80 % del costo.
4. **Alertas sin runbook.** El on-call despierta, mira un gráfico y no sabe qué
   hacer; a la tercera noche silencia la alerta.
5. **Dashboard que nadie mira.** Paneles de vanidad sin dueño ni decisión asociada; se mantienen por inercia.
6. **No medir el fallback.** El agente “responde siempre”, pero la mitad de las respuestas son la plantilla de degradación.
7. **No correlacionar.** `request_id` en el gateway, otro en el worker y ninguno
   en la tool; la traza se corta justo donde empieza el problema.

## Cierre

Observar un agente es decidir qué historia quieres poder contar después de un
turno: qué entró, qué modelo respondió, qué tools se ejecutaron, cuánto tardó,
cuánto costó y si la respuesta llegó. Esa historia se diseña antes del incidente,
no durante. El capítulo 7 define cómo evaluar la calidad de esa respuesta; el 8,
cómo contener el daño; el 10, cómo comparar el costo; el 11, cómo desplegar los
cambios de prompt y modelo con rollback. La observabilidad es el hilo que une
los cuatro.

## Referencias verificadas

- `AgroVoz/backend/app/main.py:83-105` — `RequestIDMiddleware`, sanitización y header; `:665-668` — header en respuestas 500.
- `AgroVoz/backend/app/api/health.py:40-74` — liveness vs readiness con DB y ffmpeg.
- `AgroVoz/backend/app/services/pipeline_service.py:1247-1258` — `whisper_ms`, `llm_ms`, `tts_ms`; `:1850` — log de benchmark.
- `AgroVoz/backend/app/services/metrics_service.py:285-301` — p50/p95/p99 y exclusión de `is_test`.
- `AgroVoz/backend/app/models/consultation.py:54-59` — `delivery_status` y `delivery_error_code`.
- `AgroVoz/backend/app/services/audio_service.py:453` — marca `delivered` tras confirmar el envío.
- `copiloto-recepcion copiloto/src/copiloto/events.py:1-21` — eventos y `ai_reply` sin texto.
- `copiloto-recepcion copiloto/src/copiloto/metrics.py:12-95` — métricas derivadas de eventos, tokens, tools y costo.
- `copiloto-recepcion copiloto/src/copiloto/app.py:331-340` — `/metricas` y `/metricas/data.json`.
- `ManttoAI/backend/app/services/chat_service.py:61-88` — `fuente`: reglas, ollama o fallback.
- `ManttoAI/backend/app/models/chat.py:24-27` — persistencia de mensaje, respuesta, fuente y fecha.
- `ManttoAI/frontend/src/utils/constants.js:43-47` — polling de 60 s; `frontend/src/hooks/usePolling.js:26-33` — stale-while-revalidate.
- `Wenuke/backend/llm.py:131-159` — flag `offline`; `frontend/app.js:238-240` — aviso visible de respuesta sin conexión.
- `Wenuke/backend/whatsapp.py:74` — PII (número completo) en log de error.
- OpenTelemetry GenAI Semantic Conventions, estado Development (2026-10), https://github.com/open-telemetry/semantic-conventions-genai, consultado 2026-11-04.
- OpenTelemetry blog, “Inside the LLM Call: GenAI Observability with OpenTelemetry”, 2026-05-14, https://opentelemetry.io/blog/2026/genai-observability/, consultado 2026-11-04.

## Siguiente lectura

- [Capítulo 7 — Evaluación](07-evaluacion.md): cómo convertir un incidente en un caso de regresión.
- [Capítulo 8 — Seguridad](08-seguridad.md): injection, PII y containment.
- [Capítulo 10 — Costos y modelos](10-costos-modelos.md): precios, routing y presupuesto.
- [Capítulo 11 — Despliegue](11-despliegue.md): flags, rollback y operación.
