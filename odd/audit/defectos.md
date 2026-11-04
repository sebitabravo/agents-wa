<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Auditoría de citas `path:line` — 2026-11-04

Método: 19 verificadores read-only (uno por shard de 35–70 citas) sobre 945 citas resueltas.
Cobertura: 921 citas inspeccionadas. Defectos: 18 `FALSE`, 26 `RANGE`, 70 `UNSUPPORTED`.

- `FALSE`: el código contradice la afirmación.
- `RANGE`: la afirmación es cierta pero la línea citada no la contiene (rango obsoleto o demasiado ancho).
- `UNSUPPORTED`: el archivo existe, pero la línea citada no prueba la afirmación.

Causa raíz dominante: nombres de archivo ambiguos entre repos (`llm.py`, `config.py`,
`pytest.ini`, `requirements.txt`, `vercel.json`, `docker-compose.yml`) citados sin prefijo de
proyecto, y rangos de línea que quedaron obsoletos al cambiar los repos.

## docs/00-introduccion.md

| Línea | Cita | Veredicto | Corrección |
|---|---|---|---|
| 86 | `backend/app/services/llm_worker.py:182-186` | UNSUPPORTED | Fija `temperature=0.0`, pero `max_tokens=command.max_tokens`; el 128 viene de la config, no de esas líneas. |
| 204 | `backend/whatsapp.py:26-26` | RANGE | `Wenuke/backend/whatsapp.py:1-102` es un módulo de envío saliente sin ruta ni handler de recepción. |
| 217 | `copiloto/src/copiloto/ai/sessions.py:8-22` | UNSUPPORTED | Esas líneas describen sesiones e historial; no sostienen la fila de operación, canales ni tools. |
| 218 | `backend/app/routers/chat.py:60-63` | UNSUPPORTED | No identifica al usuario como operador de pyme. |
| 219 | `backend/vercel.json:1-14` | UNSUPPORTED | El archivo configura `app/vercel_demo.py` de AgroVoz; no acredita el deploy de Wenuke. |
| 225 | `backend/app/services/llm_worker.py:182-186` | UNSUPPORTED | Muestra la llamada al modelo local, no la justificación de la elección. |
| 235 | `backend/app/services/llm_service.py:81-103` | RANGE | La whitelist está ahí; el rechazo de tools fuera de lista está en `1833-1842`. |
| 239 | `copiloto/src/copiloto/ai/sessions.py:8-22` | UNSUPPORTED | Fija `MAX_TEXT=1200` y recorta al límite recibido; no establece 12 mensajes ni tope de 60. |
| 268 | `backend/app/core/security.py:284-347` | UNSUPPORTED | El rango cubre HMAC y límite de body; el rate limit global está en `RateLimitMiddleware`. |
| 269 | `backend/app/services/pipeline_service.py:1803-1872` | UNSUPPORTED | Guarda métricas y devuelve `AudioResponse`; no muestra estados `pending`/`delivered`. |
| 304 | `backend/app/services/pipeline_service.py:912-938` | UNSUPPORTED | Trata revocación y borrado de historial; no acredita el flujo de escrituras. |
| 304 | `backend/app/services/parcela_service.py:82-99` | UNSUPPORTED | Muestra gates, identidad y consentimiento; no demuestra la ausencia de confirmación. |
| 310 | `backend/app/services/lectura_service.py:54-73` | UNSUPPORTED | Trata lecturas telemétricas, no la retención del historial de chat. |

## docs/02-stack-base.md

| Línea | Cita | Veredicto | Corrección |
|---|---|---|---|
| 46 | `ManttoAI/backend/app/config.py:128-131` | RANGE | El rechazo de credenciales demo está en `169-174`; las líneas citadas configuran Redis. |
| 263 | `backend/app/main.py:65-104` | UNSUPPORTED | Muestra middleware que propaga `request_id`; no dos endpoints ni su formato de log. |

## docs/03-system-prompts.md

| Línea | Cita | Veredicto | Corrección |
|---|---|---|---|
| 71 | `llm.py:11` | UNSUPPORTED | Cita ambigua: el archivo resuelto es el cliente LLM de copiloto. Debe apuntar a `Wenuke/backend/llm.py` con línea verificada, o pierde la cita. |
| 99 | `llm.py:135-141` | UNSUPPORTED | Mismo caso; verificar contexto climático en `Wenuke/backend/llm.py`. |
| 105 | `llm.py:17` | UNSUPPORTED | Mismo caso; la frase exacta debe citarse de `Wenuke/backend/llm.py`. |
| 109 | `llm.py:150-151` | UNSUPPORTED | Rango fuera del archivo resuelto (95 líneas). |
| 167 | `llm.py:37`, `llm.py:157` | UNSUPPORTED | Groq y marca offline deben citarse de `Wenuke/backend/llm.py`, no del archivo de copiloto. |

## docs/05-datos-rag.md

| Línea | Cita | Veredicto | Corrección |
|---|---|---|---|
| 25 | `backend/app/services/rag_service.py:1` | UNSUPPORTED | La descripción del módulo menciona ODEPA, YAML y TF-IDF; no la periodicidad mensual. |
| 57 | `backend/corpus/fuentes_datos.yaml:19-20` | UNSUPPORTED | Muestra valores de la entrada ODEPA; no establece campos obligatorios por fuente. |
| 134 | `backend/clima.py:62-65` | RANGE | Extrae `precipitation_sum` por día; el cálculo de `lluvia_total_24h` está en otra parte del archivo. |

## docs/07-evaluacion.md

| Línea | Cita | Veredicto | Corrección |
|---|---|---|---|
| 354 | `AgroVoz/.github/workflows/ci.yml:96` | FALSE | El workflow fija `--cov-fail-under=70` (línea 115), no 80. |
| 361 | `ManttoAI/backend/pytest.ini:7` | FALSE | El archivo tiene 5 líneas y solo declara un marker `integration`; no excluye `tests/e2e`. |
| 366 | `backend/tests/e2e/test_e2e_api.py:96` | UNSUPPORTED | La línea pertenece al test de readiness, no a un E2E de auth. |

## docs/08-seguridad.md

| Línea | Cita | Veredicto | Corrección |
|---|---|---|---|
| 136 | `backend/app/services/llm_service.py:81-103` | RANGE | El rechazo de tools fuera de lista está en `1833-1842`. |
| 141 | `backend/app/services/rag_service.py:198-233` | UNSUPPORTED | Filtra hechos vencidos por `review_before`; no muestra aislamiento por tenant. |
| 173 | `copiloto/src/copiloto/ai/tools.py:298-336` | UNSUPPORTED | Usa `settings.prebooking_minutes`; estas líneas no fijan 15 minutos. |
| 242 | `backend/app/services/llm_worker.py:182-186` | UNSUPPORTED | El worker pasa `command.max_tokens`; no establece 128 ni 120. |
| 244 | `copiloto/src/copiloto/ai/llm.py:36-50` | RANGE | El timeout HTTP de 25 s está en `:22`; los 12 s de turno no se acreditan ahí. |
| 250 | `backend/app/core/security.py:214-264` | UNSUPPORTED | El límite MCP de 5/min está en `rate_limiter.py` (`_mcp_limiter`, `check_mcp_rate_limit`). |
| 302 | `copiloto/src/copiloto/events.py:1-21` | FALSE | `inbound` sí documenta `{"text": str}`; solo `ai_reply` declara no guardar texto. |
| 375 | `backend/whatsapp.py:53-64` | UNSUPPORTED | Muestra envío por Graph; no prueba la ausencia de rutas de entrada en todo el módulo. |
| 389 | `backend/app/services/auth_service.py:130-135` | UNSUPPORTED | Usa `getattr(payload, "rol", "visualizador")`; no prueba RBAC ni forzado del registro público. |
| 391 | `backend/app/routers/auth.py:65-76` | UNSUPPORTED | Genera cookies incluida una CSRF; no muestra validación double-submit. |
| 392 | `backend/app/services/auth_service.py:168-188` | UNSUPPORTED | Bloquea el cambio de contraseña de la cuenta demo; no el cambio de perfil. |
| 407 | `Wenuke/backend/config.py:25-30` | RANGE | El mínimo de 16 caracteres aplica a `admin_token` en `32-33`. |
| 411 | `backend/app/main.py:449-463` | UNSUPPORTED | Exige que dos secretos no estén vacíos en producción; no prueba secretos distintos por entorno. |
| 426 | `backend/app/services/consultation_history_service.py:1-14` | UNSUPPORTED | Documenta opt-in y TTL configurable; no fija 28 días. |
| 426 | `copiloto/src/copiloto/store.py:220-249` | UNSUPPORTED | Recibe `retention_days` por parámetro; no fija 90 días. |
| 427 | `backend/db.py:211-249` | UNSUPPORTED | Muestra el esquema de tablas; no acredita la ausencia de borrado o exportación. |
| 428 | `backend/migrations/versions/f2a8c1d7e4b6_add_history_consent.py:20` | RANGE | `20-31` agrega `history_consent` no nula con default false y constraint. |

## docs/09-observabilidad.md

| Línea | Cita | Veredicto | Corrección |
|---|---|---|---|
| 302 | `copiloto/src/copiloto/events.py:1-21` | FALSE | Misma contradicción que 08:302. |
| 323 | `frontend/src/utils/constants.js:43-47` | UNSUPPORTED | Configura el intervalo de polling; no describe stale-while-revalidate. |

## docs/11-despliegue.md

| Línea | Cita | Veredicto | Corrección |
|---|---|---|---|
| 62 | `docker-compose.prod.yml:126-136` | RANGE | Los volúmenes de modelos y datos están en `137-140`. |
| 116, 342, 501 | `backend/scheduler.py:32-37` | RANGE | El intervalo se configura en `10-11` y `56`; el loop en `32-37`. |
| 159 | `ManttoAI/backend/app/config.py:151-173` | UNSUPPORTED | Rechaza SQLite y credenciales demo fuera de dev; no impone un runtime sin disco. |
| 175 | `docker-compose.prod.yml:63-64` | UNSUPPORTED | No demuestra ejecución programada ni auditoría. |

## docs/12-arquitecturas.md

| Línea | Cita | Veredicto | Corrección |
|---|---|---|---|
| 318 | `copiloto/src/copiloto/ai/tools.py:76-105` | FALSE | Las descripciones entran en el schema, pero no expresan uniformemente lo que cada tool no hace. |
| 325 | `copiloto/src/copiloto/pms.py:80-88` | RANGE | El timeout HTTP de 4 s está en `66-78`; ese archivo no acredita el deadline del loop. |

## docs/13-casos-de-estudio.md

| Línea | Cita | Veredicto | Corrección |
|---|---|---|---|
| 38 | `backend/whatsapp.py:53-64` | UNSUPPORTED | Muestra envío; no prueba que el módulo no tenga recepción. |
| 87 | `backend/app/services/llm_worker.py:1-5` | UNSUPPORTED | Documenta el aislamiento en proceso hijo; no el modelo ni su cuantización. |
| 90 | `backend/app/services/data_hub_service.py:421-445` | UNSUPPORTED | Calcula el estado de una fuente; no el total ni el desglose 8/2. |
| 95 | `backend/app/services/pipeline_service.py:1803-1872` | UNSUPPORTED | Cubre TTS, métricas y `AudioResponse`; no el flujo de tools. |
| 101 | `backend/app/services/llm_worker.py:182-186` | UNSUPPORTED | No aparecen el modelo ni el valor 128. |
| 107 | `backend/app/api/webhooks.py:46-124` | RANGE | El endpoint está en `126-302`; el rango citado contiene helpers. |
| 108, 134, 184, 647 | `backend/app/services/pipeline_service.py:912-938` | UNSUPPORTED | Gestiona revocación y borrado; no el flujo de escrituras ni la ausencia de confirmación. |
| 134 | `backend/app/services/parcela_service.py:82-99` | UNSUPPORTED | Muestra gates y consentimiento; no el flujo de confirmación. |
| 116 | `backend/app/services/llm_service.py:127-141` | RANGE | El comentario dice 60 s → 25 s y la constante actual es 10 s; el deadline compartido está en `1725-1735`. |
| 118 | `backend/app/services/llm_service.py:81-103` | RANGE | El rechazo de tools fuera de lista está en `1833-1842`. |
| 124, 187 | `backend/app/services/pipeline_service.py:1803-1872` | UNSUPPORTED | No muestra estados de entrega ni confirmación de Open-WA. |
| 229 | `pms_mock/src/pms_mock/main.py:243-248` | RANGE | La disponibilidad simulada está en `194-213`. |
| 231 | `wa_bridge/src/wa_bridge/bridge.py:22-35` | RANGE | El filtro de grupos está en `96-106` y el de privados salientes en `132-134`. |
| 248 | `copiloto/src/copiloto/ai/sessions.py:8-22` | UNSUPPORTED | No establece 12 mensajes, tope de 60 ni demo de 24 h. |
| 265, 625 | `copiloto/src/copiloto/events.py:120-125` | RANGE | `mark_processed` con `INSERT OR IGNORE` está en `108-113`. |
| 285 | `AgroVoz/.github/workflows/ci.yml:10-36` | FALSE | El CI también ejecuta pytest del backend, E2E, landing y validación de Compose. |
| 367 | `backend/app/services/mqtt_service.py:40` | UNSUPPORTED | Muestra topics y validación; no persistencia ni evaluación de umbrales. |
| 371, 442 | `docker-compose.yml:9-189` | FALSE | Define `backend`, `openwa` e `ivr`; el backend monta SQLite. No hay MySQL, Mosquitto, Mailpit, Redis ni Ollama. |
| 373 | `render.yaml:32-47` | UNSUPPORTED | Configura MQTT apagado, simulador y retención; no identifica Neon. |
| 375 | `frontend/src/components/chat/ChatBot.jsx:22-50` | UNSUPPORTED | Muestra el POST del mensaje; no acredita JWT ni CSRF. |
| 424 | `AgroVoz/.github/workflows/ci.yml:84-96` | FALSE | `--cov-fail-under=70`. |
| 425 | `ManttoAI/backend/tests/test_chat.py` | UNSUPPORTED | Respalda el recuento de ese archivo, no el total de 46 archivos `test_*.py`. |
| 432 | `backend/tests/conftest.py:43-56` | UNSUPPORTED | Configura una SQLite temporal; no describe servicios ni gates opt-in. |
| 502, 528, 595, 675 | `Wenuke/backend/reglas.py:173-255` | FALSE | `reglas.py:173-175` llama a `cargar_reglas()` y `:35-54` lee YAML desde disco: no es dominio sin I/O. |
| 503 | `backend/clima.py:16-66` | RANGE | El archive está en `112-142`. |
| 504 | `llm.py` (resuelto a copiloto) | UNSUPPORTED | Groq y fallback offline deben citarse de `Wenuke/backend/llm.py`. |
| 519 | `backend/reglas.yaml:12-90` | UNSUPPORTED | Prueba umbrales por cultivo; no el uso de OpenMeteo ni la ausencia de RAG. |
| 521 | `frontend/app.js:60-83` | UNSUPPORTED | Implementa interacción con el mapa; no una demo web de chat. |
| 534 | `backend/reglas.py:35-54` | RANGE | El fallback hardcodeado se define en `35-144`. |
| 542, 595, 631 | `backend/whatsapp.py:53-64` | UNSUPPORTED | Muestra envío a Graph; no la ausencia de entrada. |
| 546 | `llm.py` (resuelto a copiloto) | FALSE | Ese `chat` sí acepta `tools` (`36-40`); la afirmación sobre Wenuke debe citar `Wenuke/backend/llm.py`. |
| 548, 597, 643 | `backend/scheduler.py:32-37` | RANGE | Intervalo en `10-11` y `56`; `asyncio.create_task` en el lifespan. |
| 560 | `ManttoAI/backend/pytest.ini:7` | FALSE | No excluye `tests/e2e`. |
| 567 | `backend/tests/e2e/test_e2e_api.py:7-81` | UNSUPPORTED | Describe tests HTTP con skip si la API no responde; no registro, idempotencia ni cleanup. |
| 575 | `backend/vercel.json:1-14` | FALSE | `3-7` configura `maxDuration: 60`. |
| 589 | `ai-plugin.json` | UNSUPPORTED | Solo configura `api.url`; no muestra generación de `llms.txt` ni `/api/info`. |
| 589 | `llms.txt` | UNSUPPORTED | Contiene documentación y endpoints; no prueba que se generen desde el OpenAPI. |
| 599 | `backend/db.py:456-475` | FALSE | Limita a una parcela solo al plan free; premium no tiene límite en esa función. |
| 625 | `backend/servicio_alertas.py:54-70` | FALSE | Registra cada alerta y vuelve a enviar por WhatsApp; no evita reenvíos. |
| 678 | `backend/vercel.json:1-14` | UNSUPPORTED | Configura una función de AgroVoz; no documenta Turso, Groq ni fallback de Wenuke. |

## docs/14-plantillas.md

| Línea | Cita | Veredicto | Corrección |
|---|---|---|---|
| 100 | `backend/app/main.py:449-463` | FALSE | Falla si los secretos están vacíos; no comprueba que conserven un default público. |

## docs/15-anti-patrones.md

| Línea | Cita | Veredicto | Corrección |
|---|---|---|---|
| 318 | `backend/pytest.ini` | UNSUPPORTED | Solo declara un marker; no informa qué evals corre el CI. |
| 328 | `backend/requirements.txt` | UNSUPPORTED | Es el archivo de ManttoAI; no demuestra las dependencias de Wenuke. |

## docs/C-referencias.md

| Línea | Cita | Veredicto | Corrección |
|---|---|---|---|
| 180 | `landing/vercel.json` | UNSUPPORTED | Solo muestra rewrites y headers; no runtime, variables, healthchecks ni pooling. |
