<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Capítulo 11 — Despliegue: el agente es un sistema, no un script

> **Tipo:** how-to + explanation.
> **Audiencia:** desarrolladores con un agente funcionando en local y responsables
> de operación que deben ponerlo en producción sin perder mensajes ni datos.
> **Meta:** elegir un arquetipo con criterio, ubicar el estado fuera del proceso,
> definir colas y webhooks durables, escribir un pipeline con rollback y ejecutar
> cinco runbooks sin improvisar.

En local hay un proceso, un archivo SQLite, un `.env` a mano y un solo usuario. En
producción hay varios procesos, una base gestionada, secretos inyectados por la
plataforma, un proxy, un proveedor que impone timeouts y un usuario que reintenta el
mensaje cuando no ve respuesta. El agente no cambió; el entorno sí.

Los cinco fallos son siempre los mismos: **estado** que vivía en memoria y
desaparece, **timeouts** que el cliente no tolera, **cold starts** que convierten el
primer mensaje en error, **secretos** que no llegan al contenedor y **colas** que se
pierden en un reinicio. Ninguno se detecta con tests unitarios; todos se detectan
con una prueba de despliegue.

La tesis es una sola: **desplegar un agente es desplegar un sistema con estado,
dependencias externas y fallos parciales**. Recibe un webhook, guarda una sesión,
llama a un modelo, ejecuta una tool, escribe en una base y responde por otro canal.
Cada salto puede fallar por separado. Las rutas de evidencia son relativas a la
raíz de cada proyecto y se prefijan con el nombre del repo cuando hace falta
desambiguar.

## La respuesta primero

| # | Regla | En una frase |
|---|-------|--------------|
| R1 | El estado vive fuera del proceso | Si el reinicio borra la conversación, no está desplegado. |
| R2 | El webhook se persiste antes del 200 | Un ACK sin escritura durable es una promesa que el reinicio rompe. |
| R3 | La cola es un servicio, no `BackgroundTasks` | El trabajo en vuelo debe sobrevivir al proceso que lo aceptó. |
| R4 | Cada artefacto tiene versión y rollback | Prompt, modelo, imagen y esquema se revierten por separado. |
| R5 | El despliegue se prueba contra el entorno real | Los tests locales no ejercitan proxy, secretos, cold start ni DNS. |
| R6 | Nada entra sin backup probado | Un respaldo que nunca se restauró es una hipótesis. |

**Un agente en un solo proceso con estado en memoria es una demo; uno que sobrevive
a un reinicio es un producto.**

## 11.1 Arquetipos de despliegue

| Arquetipo | Costo | Control | Estado | Límites | Mejor caso |
|---|---|---|---|---|---|
| VM + Docker Compose | Fijo bajo o medio | Total | Volúmenes locales | Un host que parchear; escalado manual | Piloto con modelos locales y un tenant (AgroVoz, copiloto) |
| PaaS (Render, Railway, Fly.io) | Bajo; crece con el uso | Medio | Efímero salvo volumen o servicio gestionado | Cold start, memoria y CPU del plan | Demo o MVP de tráfico bajo (ManttoAI) |
| Serverless (Vercel, Lambda, Cloud Run) | Casi cero en reposo | Bajo | Efímero; sin proceso persistente | Timeout, memoria, disco de solo lectura, scheduler no garantizado | API sin estado, frontends, webhooks livianos (Wenuke) |
| Kubernetes | Alto operacional | Total | Volúmenes, operadores, CRDs | Complejidad, costo de plataforma, necesidad de SRE | Varios servicios, multi-tenant, equipo con operación propia |
| Edge | Bajo por request | Muy bajo | Sin estado durable local | CPU y memoria acotadas; sin runtimes pesados | Normalización, auth, caché y enrutamiento |

**Kubernetes, sí:** varios servicios, tenants con cuotas y un equipo que ya opera un
clúster. **No:** un servicio, un cliente y sin guardia. **Edge** sirve para firma,
tamaño, routing y caché, no para el pipeline: no alcanza para modelos ni ffmpeg.

## 11.2 Los cuatro proyectos como casos

### AgroVoz — Docker Compose en VPS, landing en Vercel

El backend corre en un VPS con un solo worker de uvicorn
(`AgroVoz/docker-compose.prod.yml:126-136`): los modelos viven en un volumen
montado en el contenedor.

- Volúmenes para modelos, SQLite y caché de Whisper (`AgroVoz/docker-compose.prod.yml:137-140`).
- Sin root, `read_only`, `cap_drop: ALL`, `no-new-privileges` (`:182-188`; `AgroVoz/backend/Dockerfile:51,78`).
- Límites 3 CPU / 8 GB y `start_period` de 10 min por descarga de modelos (`:148-162,170-181`).
- Webhook con ACK inmediato y procesamiento en background (`AgroVoz/backend/app/api/webhooks.py:126-146,185-194`).

La landing en Vercel no ejecuta el agente: reescribe `/api/v1/*` al backend
(`AgroVoz/landing/vercel.json:3-32`). **El fracaso del slim:** el entrypoint recortado
no cupo con 2,5 GB de modelos y `config.py` hacía `mkdir` en un filesystem de solo
lectura (`docs/ARCHITECTURE-DECISIONS.md:320-379,345-350`; verificar plan vigente).
Lección: se arregla cambiando el runtime, no con un entrypoint.

### copiloto — Compose con Chatwoot, PMS y puentes

Seis servicios: Postgres con pgvector, Redis, Chatwoot, Sidekiq, copiloto y PMS
simulado, la landing y los puentes opcionales
(`copiloto-recepcion/infra/docker-compose.yml:26-84,86-134`).

- Puertos solo en `127.0.0.1`; un proxy externo termina TLS (`:59,106,181`).
- Sin root, `read_only`, `cap_drop`; liveness separado de readiness (`:98-104,173-188`).
- Respaldo con `pg_dump` y SQLite verificado con `PRAGMA integrity_check` (`docs/despliegue.md:35-46`).
- Webhook firmado, deduplicado por `msg:{id}` y con lock por conversación (`copiloto/src/copiloto/flow.py:95-136`).

Los webhooks corren en `BackgroundTasks`: un reinicio pierde el trabajo en vuelo y
no hay cola durable (`docs/escalabilidad.md:18-24`; `copiloto/src/copiloto/app.py:171-180`). El
procesamiento es **a lo más una vez** y los locks son locales, así que no coordinan
réplicas (`copiloto-recepcion/README.md:138-140`; `docs/despliegue.md:114-120`).

### ManttoAI — tres gratuitos encadenados

Vercel sirve la SPA y reescribe `/api/*` hacia Render; Render ejecuta FastAPI en
Docker; Neon mantiene PostgreSQL (`ManttoAI/docs/despliegue-render.md:10-29`;
`ManttoAI/frontend/vercel.json:7-16`).

- Blueprint con plan, región y healthcheck (`ManttoAI/render.yaml:4-11`).
- Scheduler de inferencia dentro del proceso (`:40-45`; `backend/app/main.py:86-99`).
- Ollama fuera por memoria del tier (`:52-53`; `docs/auditoria/deploy.md:49-60`).
- Timeout de 60 s en el cliente por el despertar de Render (`frontend/src/api/client.js:21-26`).

Render puede dormir, Neon puede escalar a cero y la retención se corta a 30 días
(`docs/despliegue-render.md:39-46`; verificar plan vigente). Las `VITE_*` quedan
visibles en el bundle y por eso la demo usa una cuenta de solo lectura (`:47-49`).
`ALLOW_RUNTIME_SCHEMA_CHANGES=true` sirve para una demo desechable y es peligroso en
producción: convierte el arranque en una migración no revisada.

### Wenuke — serverless puro

Dos proyectos Vercel sobre el mismo repositorio: frontend estático y backend Python
con un `catch-all` a `Wenuke/backend/main.py` (`Wenuke/backend/vercel.json:1-14`). La base es Turso
por HTTP en producción y `aiosqlite` en local; en Vercel el fallback usa
`/tmp/wenuke.db` (`Wenuke/backend/config.py:11-17`).

- Scheduler lanzado en `lifespan` (`Wenuke/backend/main.py:131-135`).
- Duerme 6 h antes del primer chequeo (`Wenuke/backend/scheduler.py:10-11,32-37,56`).
- Transacciones no-op en Turso: cada sentencia es atómica por HTTP (`Wenuke/backend/db.py:107-115`).

El scheduler en `lifespan` no tiene garantía: la instancia se congela o se destruye
sin tráfico, y el primer chequeo llega seis horas después de arrancar. Las alertas
pueden no enviarse nunca; un cron externo autenticado es la alternativa correcta.

## 11.3 Estado: dónde vive y qué pasa al reiniciar

Un servicio es **stateless** cuando cualquier instancia atiende cualquier request
con la misma información. Un agente casi nunca lo es: la conversación, la sesión, la
propuesta de reserva y el lock por conversación son estado.

| Estado | Dónde debería vivir | Al reiniciar | Multi-instancia |
|---|---|---|---|
| Historial conversacional | Base de datos por `session_id` | Sobrevive | Correcto si la escritura es transaccional |
| Estado de flujo y propuestas | Base de datos o Redis con TTL | Se pierde en memoria | Requiere almacén compartido |
| Locks por conversación | Redis con expiración | Se liberan; el turno en vuelo se pierde | Un lock local no coordina réplicas |
| Rate limit y cuotas | Redis o tabla con ventana | Contador a cero | En memoria se multiplica por réplica |
| Caché de datos externos | Redis o tabla con TTL | Se pierde; se repuebla | Aceptable si el costo lo tolera |
| Adjuntos y audio | Object storage o volumen | Sobrevive solo con volumen | Requiere storage compartido |

La base es la opción por defecto: auditable, respaldable y consultable. Redis sirve
para lo efímero —locks, TTL corto, rate limit—, no para el historial que hay que
reconstruir tras un incidente. **Sticky sessions no son una solución:** fijan un
usuario a una instancia y funcionan hasta el próximo deploy o la próxima caída.

Al reiniciar se pierden las tareas en vuelo de `BackgroundTasks`, los locks
huérfanos, los contadores de rate limit y los leases en memoria; lo que está en
`/tmp` no sobrevive (`Wenuke/backend/config.py:11-14`). Con dos réplicas, cada una
ejecuta su scheduler, su rate limit y su lock: alertas duplicadas y carreras que en
un proceso no existían. La regla es **externalizar el estado antes de agregar la
réplica**. AgroVoz lo trata con cuidado: el estado conversacional está apagado por
defecto (`USE_CONVERSATION_STATE=false`) y, al activarse, usa lease y timeout de 30
minutos que rechaza turnos concurrentes
(`AgroVoz/backend/app/core/config.py:214-218`).

## 11.4 Base de datos

SQLite primero, Postgres o MySQL después. El [Capítulo 2](02-stack-base.md) cubre
configuración y PRAGMAs; aquí importa la operación.

**Cuándo migrar y cómo.** Con réplicas, escrituras concurrentes sostenidas o un
runtime sin disco; ManttoAI rechaza SQLite fuera de desarrollo
(`ManttoAI/backend/app/config.py:151-174`).
Cambian `DATABASE_URL`, el pool y el plan de respaldo, no el modelo. La migración es
un paso del pipeline —`alembic upgrade head` antes de desplegar—, con la versión
anterior todavía capaz de leer el esquema nuevo: AgroVoz mantiene 26 versiones
(`AgroVoz/backend/migrations/versions/`) y ManttoAI tiene su árbol
(`ManttoAI/backend/alembic/versions/`). El patrón seguro es **expandir y contraer**:
columnas nullable, código que escribe en ambas, migración de datos y recién después
la eliminación; así el rollback de la app no revierte el esquema.

**Backups y restore drills.** Se definen por frecuencia, retención y prueba de
restauración. El copiloto genera `pg_dump` y copias consistentes de SQLite con
`PRAGMA integrity_check` (`copiloto-recepcion/docs/despliegue.md:35-46`). El drill es
trimestral, en un entorno aislado, comparando conteos y ejecutando un turno completo.

**Retención.** Por tipo de dato: audio 24 horas (`AgroVoz/docker-compose.prod.yml:100`),
telemetría 30 días (`ManttoAI/render.yaml:38-39`), historial de consultas 28 días
(`AgroVoz/docker-compose.prod.yml:63-64`). Ese archivo configura el TTL; no
acredita la ejecución ni la auditoría de un job de limpieza.

**Conexiones.** En servidor clásico, `pool_size`, `max_overflow` y `pool_pre_ping=True`
evitan conexiones muertas. En serverless cada instancia abre su pool y el total se
multiplica: usa el pooler del proveedor o una conexión HTTP (verificar plan vigente).

**Transacciones.** El handoff del copiloto es una sola transacción antes de abrir la
conversación a recepción (`copiloto/src/copiloto/flow.py:622-643`): estado, evento y
SLA se escriben juntos o no se escriben. En Turso `begin`, `commit` y `rollback` son
no-op y cada sentencia es atómica por HTTP (`Wenuke/backend/db.py:107-115`): una
operación de negocio debe caber en una sentencia o compensarse explícitamente.

**Aislamiento multi-tenant.** Instancia por cliente (copiloto,
`docs/escalabilidad.md:7-10`), base por cliente, o base compartida con `tenant_id` en
cada tabla. La tercera escala mejor y falla peor: un `WHERE` olvidado expone datos de
otro cliente. El filtro se aplica en la capa de repositorio.

## 11.5 Colas y durabilidad

`BackgroundTasks` ejecuta trabajo después de responder, dentro del mismo proceso.
Sirve para tareas cortas y prescindibles; no es una cola: no reintenta, no persiste,
no tiene visibilidad y no sobrevive al reinicio (`docs/escalabilidad.md:18-24`).

| Mecanismo | Persistencia | Reintento | Visibilidad | Cuándo usarlo |
|---|---|---|---|---|
| `BackgroundTasks` | No | No | No | Tareas idempotentes y descartables |
| Redis (RQ, Celery, arq) | Sí, con AOF o RDB | Sí | Parcial | Volumen medio; ya hay Redis |
| SQS / Cloud Tasks / Pub/Sub | Sí, gestionado | Sí, con DLQ | Sí | Producción sin operar el broker |
| Outbox en base de datos | Sí | Sí, con un worker | Sí | Webhooks que no se pueden perder |

| Modo | Garantía | Consecuencia | Requisito |
|---|---|---|---|
| At-least-once | Una o más entregas | Puede duplicar efectos | Idempotencia real en cada efecto |
| At-most-once | Cero o una entrega | Puede perder trabajo | Aceptar la pérdida y medirla |

El copiloto opera a lo más una vez (`copiloto-recepcion/README.md:138-140`). AgroVoz hace ACK y procesa
en background, también sin cola durable
(`AgroVoz/backend/app/api/webhooks.py:141-146,185-194`). Ambos son correctos para su
escala y ambos pierden trabajo en un reinicio. Wenuke ni siquiera tiene cola: su
scheduler vive en `lifespan` (`Wenuke/backend/main.py:131-135`). Si el mensaje no se
puede perder, la cola es obligatoria.

**Idempotencia.** La llave es el identificador del evento, no el contenido. El
copiloto marca `msg:{id}` antes de procesar (`copiloto/src/copiloto/flow.py:124-127`);
la implementación mínima es una tabla con `event_id TEXT PRIMARY KEY` e `INSERT ... ON
CONFLICT DO NOTHING`, y si `changes() = 0` se responde 200 y se sale.

**DLQ y backoff.** Todo mensaje que falla N veces termina en una DLQ (dead letter queue) con payload,
error y timestamp; sin ella se pierde o bloquea la cola. El backoff es exponencial con
jitter, tope de intentos y presupuesto total. **Webhooks que no se pueden perder:** el
orden es **persistir, hacer ACK, procesar**. Si el ACK llega antes de la escritura, el
proveedor deja de reintentar y el evento se pierde con el proceso; el patrón outbox
escribe el evento en la misma base y deja que un worker lo consuma.

## 11.6 Webhooks e ingreso

El webhook es la frontera de confianza: todo lo que entra puede ser un mensaje
legítimo, un reintento, un duplicado o un ataque.

1. **Firma sobre el cuerpo crudo**, antes de parsear JSON: si se parsea y se vuelve a
   serializar, deja de coincidir. AgroVoz usa HMAC-SHA256 con `hmac.compare_digest`
   (`AgroVoz/backend/app/core/security.py:283-330`).
2. **Timestamp y tolerancia.** El copiloto firma `<timestamp>.<body>` y rechaza fuera
   de 300 segundos (`copiloto/src/copiloto/app.py:45-56`;
   `copiloto-recepcion/copiloto/src/copiloto/config.py:50`): sin él, un
   cuerpo capturado se reenvía indefinidamente (replay).
3. **Comparación en tiempo constante.** `==` filtra información por temporización.
4. **Límite de cuerpo antes de autenticar.** El copiloto lee con tope de 256 KB
   (`copiloto-recepcion/copiloto/src/copiloto/config.py:27`; `app.py:63-79`);
   AgroVoz corta en 10 MB y responde 413
   (`AgroVoz/backend/app/core/security.py:30,331-366`).
5. **Deduplicación por identificador de evento**, no por hash del contenido.
6. **2xx solo si aceptaste el evento.** Un 2xx dice "no reintentes"; un 5xx dice "reintenta".
7. **Respuesta rápida.** AgroVoz apunta a menos de 5 segundos para Open-WA
   (`AgroVoz/backend/app/api/webhooks.py:144-145`).
8. **Handshake de canal.** En WhatsApp Cloud API, el `GET` compara `hub.verify_token` antes de devolver `hub.challenge`.

**Idempotency keys.** Cuando el proveedor las ofrece, se persisten con el resultado
para devolver la misma respuesta ante un reintento; cuando no, se usa el identificador
del evento más el del destinatario. Meta, Chatwoot y Open-WA reintentan con políticas
distintas: tolera duplicados, no asumas una sola entrega.

## 11.7 CI/CD

El pipeline es la única puerta entre un cambio y un usuario.

| Etapa | Pregunta | Herramienta | Evidencia |
|---|---|---|---|
| Lint | ¿El código es consistente? | `ruff` | `AgroVoz/.github/workflows/ci.yml:67-69` |
| Typecheck | ¿Los tipos cierran? | `mypy --strict` | `AgroVoz/.github/workflows/ci.yml:71-73` |
| Tests | ¿Se comporta como se espera? | `pytest` | `copiloto-recepcion/.github/workflows/ci.yml:23` |
| Evals | ¿La calidad se mantiene? | set dorado | [Capítulo 7](07-evaluacion.md) |
| Build | ¿La imagen y el frontend compilan? | Docker, Vite | `AgroVoz/.github/workflows/ci.yml:179+` |
| Smoke | ¿Arranca con las restricciones reales? | `docker compose` | `copiloto-recepcion/.github/workflows/ci.yml:32-36` |
| Migración | ¿El esquema avanza sin romper? | `alembic upgrade` | `AgroVoz/backend/migrations/versions/` |
| Deploy | ¿Llegó al entorno? | plataforma | `ManttoAI/docs/despliegue-render.md:128-164` |
| Rollback | ¿Se puede volver? | imagen anterior | `11.11` |

Desarrollo, staging y producción con bases, secretos y dominios distintos. Un staging
que comparte base con producción no es staging: es producción con otro nombre. La
configuración se inyecta por entorno y nunca se commitea (12-factor, III Config,
https://12factor.net, consultado 2026-11-04). Los secretos van en el vault de la
plataforma: AgroVoz los inyecta desde Dokploy y falla el arranque si faltan
(`AgroVoz/docker-compose.prod.yml:23-25,48-56`); el copiloto deja `.env` y
`.env.runtime` fuera de git (`docs/despliegue.md:59-62`).

**Migraciones y feature flags.** La migración es un job previo. Los flags permiten desplegar
código apagado y encenderlo sin rebuild: AgroVoz los usa para tools y capacidades
(`MCP_ENABLED`, `CONSULTATION_HISTORY_ENABLED`,
`AgroVoz/docker-compose.prod.yml:57-80`). Un flag necesita dueño, fecha de expiración
y una prueba de que apagado no rompe nada.

**Canary y blue-green.** Canary manda un porcentaje del tráfico a la versión nueva y
compara error rate, latencia y costo antes de subir; blue-green mantiene dos entornos
y cambia el tráfico de golpe, con rollback instantáneo y costo duplicado durante el
corte. En un agente, el canary debe medir también calidad —fallback, tools,
groundedness—.

## 11.8 Contenedores

| Control | Qué evita | Evidencia |
|---|---|---|
| Usuario no root | Escritura y escalada en el contenedor | `AgroVoz/backend/Dockerfile:51,78`; `copiloto/copiloto/Dockerfile:8-10` |
| `read_only: true` | Modificar binarios y código en runtime | `AgroVoz/docker-compose.prod.yml:186`; `copiloto/infra/docker-compose.yml:173` |
| `tmpfs: /tmp` | Escribir en un FS inmutable | `AgroVoz/docker-compose.prod.yml:187-188` |
| `cap_drop: ALL` | Capacidades del kernel innecesarias | `AgroVoz/docker-compose.prod.yml:182-183` |
| `no-new-privileges` | Escalada vía setuid | `AgroVoz/docker-compose.prod.yml:184-185` |
| Healthcheck | Tráfico a un proceso no listo | `AgroVoz/docker-compose.prod.yml:148-162` |
| Límites de CPU y memoria | Un modelo que consume el host | `AgroVoz/docker-compose.prod.yml:170-181` |
| Imagen pinneada por digest | Cambio silencioso de la imagen | `copiloto-recepcion/infra/docker-compose.yml:195` |
| Volumen para estado | Pérdida de sesión al recrear | `AgroVoz/docker-compose.prod.yml:137-140` |

Un tag mutable es un deploy sorpresa. AgroVoz lo tiene como deuda documentada: Open-WA
usa `:latest` con un pendiente explícito de digest
(`AgroVoz/docker-compose.prod.yml:192-197`). **SBOM y escaneo:** generar un SBOM por
imagen (`syft`, `trivy`) y escanear en el pipeline; es recomendación, no práctica
observada en los cuatro proyectos.

**Liveness no es readiness.** Liveness dice si el proceso vive; readiness, si puede
atender. El copiloto separa ambas sondas (`docs/despliegue.md:53-56`); mezclarlas hace
que Docker reinicie un contenedor sano. Si el arranque descarga modelos o migra, el
`start_period` debe cubrirlo: AgroVoz usa 10 minutos
(`docker-compose.prod.yml:159-162`).

## 11.9 Serverless

| Restricción | Síntoma | Mitigación |
|---|---|---|
| Cold start | El primer mensaje tarda o expira | Timeout mayor; calentamiento; aceptar la latencia |
| Timeout de ejecución | El turno se corta a mitad | Presupuesto explícito; trabajo largo a cola |
| Memoria acotada | El modelo no carga | Sacar el modelo del runtime; API externa |
| Disco efímero y read-only | SQLite se pierde; `mkdir` falla | Base gestionada; `/tmp` solo para caché |
| Estado en memoria | Caché y rate limit por instancia | Redis o tabla compartida |
| Scheduler no garantizado | Alertas que nunca se envían | Cron externo autenticado |
| Límite de bundle | El deploy falla o se recorta | Separar planos; entrypoint mínimo |
| `VITE_*` públicas | Credenciales visibles en el navegador | Solo valores públicos; secretos en servidor |

ManttoAI absorbe el cold start con 60 segundos de timeout en el cliente
(`ManttoAI/frontend/src/api/client.js:21-26`). Wenuke no declara `maxDuration`, memoria
ni región (`Wenuke/backend/vercel.json:1-14`), así que hereda el default de la
plataforma: todo turno con un modelo lento debe caber ahí o ir a una cola.

ManttoAI descartó Ollama porque el tier gratuito no ofrece memoria suficiente
(`ManttoAI/render.yaml:52-53`; `docs/auditoria/deploy.md:49-60`; verificar plan
vigente): el chat sin regla cae al fallback y cambia el producto, no solo la
infraestructura. Wenuke usa `/tmp/wenuke.db` en Vercel (`Wenuke/backend/config.py:11-14`); una
instancia nueva no ve los datos de la anterior, y Turso existe para eso (`:15-17`).

`asyncio.create_task` en `lifespan` vive mientras viva la instancia: Wenuke espera seis
horas antes del primer chequeo (`Wenuke/backend/main.py:131-135`;
`Wenuke/backend/scheduler.py:10-11,32-37,56`), así que lo periódico debe ir en
un cron gestionado. Y como las `VITE_*` se compilan en el bundle,
ManttoAI usa una cuenta demo de solo lectura (`docs/despliegue-render.md:47-49`): nunca
pongas una llave de proveedor ahí.

El intento de AgroVoz de correr el backend completo en Vercel chocó con el tamaño de
los modelos (`docs/ARCHITECTURE-DECISIONS.md:320-379`; verificar plan vigente). La
lección no es "optimizar el bundle": un runtime sin GPU ni disco no sirve para voz.

## 11.10 Escalabilidad

**Vertical primero.** Más CPU y memoria en el mismo proceso resuelve la mayoría de los
pilotos y no cambia el modelo de estado: AgroVoz usa 3 CPU y 8 GB con un solo worker
(`AgroVoz/docker-compose.prod.yml:170-181`). **Horizontal después, con estado
externalizado:** sin eso, cada réplica tiene su scheduler, su rate limit y su lock.

**Servir modelos.** Un modelo en CPU ocupa memoria y compite por núcleos; uno en GPU
exige un proceso que la controle. La decisión práctica es un servicio de inferencia por
modelo, con cola y timeout, y el agente como cliente; AgroVoz mantiene un worker único
por eso (`docker-compose.prod.yml:126-136`).

**Rate limits y cuotas.** Por IP para abuso y por tenant para costo. En memoria
funcionan en un proceso; con réplicas se comparten por Redis. ManttoAI ya soporta Redis
con fallback a memoria (`ManttoAI/backend/app/middleware/rate_limit.py:96-134`).

**Multi-tenant y sharding.** Instancia por cliente, base por cliente o `tenant_id`
compartido. La primera es simple y escala mal; la tercera escala bien y exige
disciplina. Copiloto declara una instancia por hotel y describe qué exigiría el segundo
(`copiloto-recepcion/docs/escalabilidad.md:7-27`). Al particionar, la llave debe estar
en todas las consultas y en el routing.

**Colas y caché.** Un turno interactivo no compite con un job de mantenimiento: colas
separadas por latencia y un worker dedicado. Wenuke cachea clima una hora y ODEPA seis
horas (`Wenuke/backend/clima.py:16-41`; `Wenuke/backend/odepa.py:57-62`); la caché en memoria no se comparte entre
réplicas, así que si el dato es caro, va a Redis.

## 11.11 Rollback y versionado

Un agente cambia por cuatro vías independientes: código, prompt, modelo y esquema.

| Artefacto | Dónde se versiona | Rollback | Riesgo si no se versiona |
|---|---|---|---|
| `app_version` | Imagen o commit | Redeploy de la anterior | No se sabe qué código respondió |
| `prompt_version` | Archivo, tabla o registro | Cambiar la versión activa | Un prompt peor exige deploy |
| `model_version` | ID exacto del modelo | Volver al ID anterior | El proveedor lo retira o actualiza |
| `schema_version` | Alembic u otra herramienta | `downgrade` o expand/contract | Migración irreversible |

**Prompt sin deploy.** Se guarda con versión y se activa por configuración o por fila
en base de datos; el agente registra `prompt_version` y `model_version` en cada turno
([Capítulo 9](09-observabilidad.md)). Si la calidad cae, se cambia la versión activa y
el siguiente turno la usa.

**Modelo.** El ID se fija explícitamente, nunca "el último disponible". Un proveedor
puede retirarlo o cambiar su comportamiento sin aviso; el rollback es volver al ID
anterior y el canary debe detectar la deriva antes de que llegue a todos.

**Migraciones.** Expand/contract permite volver la app sin tocar el esquema: primero se
deja de escribir en la columna, después se elimina. Si la migración la elimina antes,
el rollback falla. Un rollback que nunca se ejecutó es una hipótesis.

## 11.12 Runbooks

**Runbook de deploy**
1. Confirmar que el pipeline pasó lint, typecheck, tests, evals y build.
2. Verificar que la migración es compatible con la versión anterior.
3. Tomar un backup y anotar su identificador.
4. Desplegar a staging y correr smoke de `/health`, `/ready` y un turno real.
5. Desplegar a producción con canary o blue-green y observar error rate, latencia
   p95, fallback y costo durante 30 minutos.
6. Confirmar un turno end-to-end y registrar versión y responsable.

**Runbook de rollback**
1. Declarar el incidente y congelar despliegues nuevos.
2. Identificar la última versión sana y su imagen o commit.
3. Revertir la aplicación; no revertir el esquema si es compatible.
4. Si el esquema es incompatible, ejecutar el `downgrade` probado.
5. Verificar `/health`, `/ready` y un turno real contra la línea base; confirmar que
   la cola no quedó con mensajes de la versión fallida.
6. Abrir un caso de evaluación que reproduzca el fallo.

**Runbook de incidente**
1. Asignar un responsable y un canal único de comunicación.
2. Determinar alcance: canal, tenant, tipo de mensaje y hora de inicio.
3. Revisar la traza del último turno fallido y el estado de las dependencias.
4. Aplicar la mitigación más pequeña: flag, rollback, desvío o degradación.
5. Confirmar que el usuario recibe respuesta o un fallback explícito.
6. Preservar logs y eventos del periodo afectado; escribir el postmortem y convertir
   la acción en test o alerta.

**Runbook de backup y restore**
1. Verificar que el backup más reciente existe y tiene el tamaño esperado.
2. Restaurar en un entorno aislado, nunca sobre producción.
3. Ejecutar `PRAGMA integrity_check` o el equivalente del motor.
4. Comparar conteos de tablas clave contra el origen.
5. Arrancar la aplicación contra la copia y ejecutar un turno completo.
6. Documentar el tiempo de restauración y ajustar frecuencia o retención si el
   ejercicio lo exige.

**Runbook de rotación de secretos**
1. Inventariar el secreto, sus consumidores y su fecha de expiración.
2. Generar el valor nuevo en el vault, sin escribirlo en logs ni en el chat.
3. Desplegar el valor nuevo en staging y verificar.
4. Aplicar el valor en producción con ventana de compatibilidad si aplica.
5. Reiniciar solo los servicios que lo leen al arrancar.
6. Verificar firma de webhooks y healthchecks; revocar el anterior y registrar la
   rotación en el inventario.

## 11.13 Checklist pre-producción

- [ ] **Estado:** sesiones y estado de flujo sobreviven a un reinicio; nada crítico en memoria.
- [ ] **Base de datos:** motor apto para el número de réplicas y pool configurado.
- [ ] **Colas:** lo que no se puede perder está en cola durable con reintentos y DLQ.
- [ ] **Secretos:** inyectados por entorno, fuera del repo, sin defaults válidos.
- [ ] **Salud:** `/health` y `/ready` responden y el healthcheck usa la sonda correcta.
- [ ] **Observabilidad:** traza, `request_id`, `prompt_version`, `model_version` y `outcome` por turno.
- [ ] **Backups:** backup automático y restore drill en los últimos 90 días.
- [ ] **Rollback:** imagen anterior disponible y procedimiento probado en staging.
- [ ] **Límites:** CPU, memoria, timeout, cuerpo y rate limit definidos y probados.
- [ ] **CI/CD:** lint, typecheck, tests, evals, build y smoke en cada cambio.
- [ ] **Evaluación:** set dorado ejecutado contra la versión que se despliega.
- [ ] **Seguridad:** sin root, `read_only`, `cap_drop` y secretos rotables; ver [Capítulo 8](08-seguridad.md).
- [ ] **Costo:** presupuesto por tenant y alerta de gasto configurada.
- [ ] **Documentación:** runbook, arquitectura y variables de entorno actualizados.
- [ ] **On-call:** persona responsable, escalamiento y canal de incidentes definidos.

## 11.14 Anti-patrones

1. **`BackgroundTasks` como cola.** Responde 200 y pierde el trabajo en el reinicio (`copiloto-recepcion/docs/escalabilidad.md:18-24`).
2. **Scheduler en serverless.** `asyncio.create_task` en `lifespan` no garantiza ejecución (`Wenuke/backend/main.py:131-135`).
3. **Estado en memoria.** Locks, propuestas y sesiones que desaparecen o se duplican con dos réplicas.
4. **SQLite en multi-instancia.** Cada réplica ve un archivo distinto (`copiloto-recepcion/docs/despliegue.md:114-120`).
5. **Secretos en el repositorio.** `.env` versionado, tokens en compose o credenciales en `VITE_*`.
6. **Deploy sin migración.** El código nuevo arranca contra un esquema viejo.
7. **Deploy sin rollback.** No hay imagen anterior ni procedimiento probado.
8. **Sin backup probado.** El respaldo existe hasta que se intenta restaurar.
9. **Cold start ignorado.** El cliente corta antes de que el servicio despierte.
10. **Límites de memoria del modelo.** Correr un modelo que no cabe en el tier o asumir que el proveedor mantendrá el mismo límite (verificar plan vigente).

## Cierre

Desplegar un agente es aceptar que el sistema tiene estado, dependencias y fallos
parciales, y diseñar para que cada uno sea visible y recuperable. La elección del
arquetipo importa menos que la disciplina: estado fuera del proceso, webhook persistido
antes del ACK, cola durable para lo que no se puede perder, versión y rollback para cada
artefacto, y un runbook que se ejecutó al menos una vez. El
[Capítulo 8](08-seguridad.md) define qué contener; el
[Capítulo 9](09-observabilidad.md), cómo saber qué pasó; el
[Capítulo 10](10-costos-modelos.md), cuánto cuesta cada decisión; el
[Capítulo 12](12-arquitecturas.md), cómo cambia el despliegue según la topología; y el
[Capítulo 14](14-plantillas.md), qué copiar para no empezar de cero.

## Referencias verificadas

- `AgroVoz/docker-compose.prod.yml:23-25,48-56,126-147,148-162,170-188,192-197` — secretos, worker, volúmenes, healthcheck, límites y endurecimiento.
- `AgroVoz/backend/app/api/webhooks.py:126-146,185-194`; `backend/app/core/security.py:30,283-330,331-366` — ACK, HMAC y tope de cuerpo.
- `AgroVoz/backend/app/core/config.py:214-218`; `backend/migrations/versions/`; `AgroVoz/.github/workflows/ci.yml:67-73,113-115`; `landing/vercel.json:3-32`; `docs/ARCHITECTURE-DECISIONS.md:320-379`.
- `copiloto-recepcion/infra/docker-compose.yml:26-84,98-104,170-188,195`; `copiloto/src/copiloto/app.py:45-56,63-79,171-180`; `copiloto-recepcion/copiloto/src/copiloto/config.py:27,50`; `flow.py:95-136,622-643`.
- `copiloto-recepcion/docs/despliegue.md:35-46,48-57,114-120`; `docs/escalabilidad.md:7-27`; `copiloto-recepcion/README.md:138-140`; `.github/workflows/ci.yml:23,32-36`.
- `ManttoAI/docs/despliegue-render.md:10-29,39-49,128-164`; `render.yaml:4-11,20-25,32-53`; `frontend/src/api/client.js:21-26`; `backend/app/main.py:86-99`; `ManttoAI/backend/app/config.py:151-173`.
- `Wenuke/backend/vercel.json:1-14`; `Wenuke/backend/main.py:131-135`; `Wenuke/backend/scheduler.py:10-11,32-37,56`; `Wenuke/backend/config.py:11-17`; `Wenuke/backend/db.py:107-115`; `Wenuke/backend/clima.py:16-41`; `Wenuke/backend/odepa.py:57-62`.
- The Twelve-Factor App, https://12factor.net, consultado 2026-11-04 — configuración, procesos y disposabilidad.
