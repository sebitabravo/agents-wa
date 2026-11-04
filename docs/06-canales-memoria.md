<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Capítulo 6 — Canales y memoria: WhatsApp, voz y web

> **Tipo:** explanation (por qué) con patrones aplicables.
> **Audiencia:** desarrolladores que exponen un agente en uno o más canales.
> **Meta:** al terminar, decides qué canal usa cada caso, cómo acotar la sesión,
> cuándo deriva a un humano y qué tres métricas vigilar desde el día uno.

El modelo responde igual en todos lados; lo que cambia es el canal. WhatsApp
limita el formato, la voz suma segundos de audio por turno y la web permite el
historial más largo y costoso. Este capítulo fija una regla por decisión con
evidencia de los cuatro proyectos, citada con `path:line`.

## La respuesta primero

| # | Regla | En una frase |
|---|-------|--------------|
| R1 | Un canal, un contrato | Cada canal declara formato, latencia esperada y autenticación antes del primer mensaje. |
| R2 | Sesión acotada siempre | Historial con límite fijo de turnos y caracteres; lo viejo se trunca. |
| R3 | Proactividad con permiso | Solo el scheduler con opt-in vigente inicia contacto; el resto reacciona. |
| R4 | Handoff con contexto | Derivar es transferir el resumen, no el problema. |
| R5 | Tres métricas desde el día uno | Latencia, tasa de fallback y costo por consulta. |

Si solo recuerdas una cosa: **la memoria del agente es un presupuesto, no un
archivo: cada turno guardado se paga en latencia, tokens y riesgo de filtrar
datos**.

---

## R1 — Matriz de canales: WhatsApp, voz y web

### Principio

Cada canal impone restricciones distintas de formato, tiempo y costo. Un mensaje
válido en la web puede ser inválido o impagable en WhatsApp o en voz.

### Matriz

| Dimensión | WhatsApp (Cloud API) | Voz (STT → LLM → TTS) | Web / API |
|---|---|---|---|
| Formato | Texto plano, sin botones salvo plantillas | Audio; respuesta breve y hablable | Texto libre, Markdown posible |
| Latencia esperada | Segundos (red + API de Meta) | Un orden de magnitud sobre texto (tres modelos en serie) | Cientos de ms si el pipeline es solo texto |
| Autenticación | Token del remitente por mensaje | Sesión de llamada + opt-in de grabación | Bearer token o sesión web |
| Estado | Stateless por request; la sesión vive en tu BD | Efímera; el staging de audio se elimina | Sesión en BD con TTL |
| Inicio permitido | Solo plantillas o respuesta a mensaje entrante | Solo llamada iniciada por el usuario o con consentimiento | Cualquiera autenticado |
| Costo dominante | Por mensaje enviado | Cómputo de audio (STT + TTS) | Tokens del LLM |

### Ejemplo real: envío WhatsApp

Wenuke envuelve la WhatsApp Business Cloud API en un cliente liviano con pool
de conexiones y normalización a E.164, en `backend/whatsapp.py:20-51`:

```python
class WhatsAppClient:
    """Thin wrapper over the WhatsApp Business Cloud API (Meta)."""

    def __init__(self):
        self.token = config.whatsapp_token
        self.phone_number_id = config.whatsapp_phone_number_id
        self.base_url = "https://graph.facebook.com/v21.0"
        self._client: httpx.AsyncClient | None = None

    @property
    def activo(self) -> bool:
        return bool(self.token and self.phone_number_id)
```

El envío (`backend/whatsapp.py:42-75`) retorna un dict explícito
`{"enviado": True, "wa_message_id": ...}` o `{"enviado": False, "error": ...}`
en lugar de lanzar excepciones: el llamador decide si reintenta. Sin
`WHATSAPP_TOKEN` el cliente se declara inactivo y el envío se rechaza con un
error descriptivo, no con un timeout críptico. La autenticación de usuarios es
stateless por token: cada request trae `Authorization: Bearer <token>`, se
compara el hash SHA-256 contra la BD y se verifica expiración
(`backend/main.py:88-117`, `backend/db.py:190-202`).

### Ejemplo real: voz como pipeline, no como canal gratis

AgroVoz declara la voz como dependencias pesadas y opcionales:
`faster-whisper==1.2.1` para STT y `piper-tts==1.7.0` para TTS
(`backend/requirements-docker.txt:14-23`), con importación diferida para que
CI funcione sin ellas (`backend/app/services/tts_service.py:14-15`). El script
de modelos descarga Piper + Qwen por defecto
(`backend/scripts/download_models.sh:230-232`).

La consecuencia: un turno de voz encadena tres modelos (STT → LLM → TTS)
donde uno de texto usa uno solo. Como referencia operativa — a medir en tu
despliegue, no como constante del código — espera al menos un orden de
magnitud más de latencia en voz que en texto. Diseña la UX en consecuencia:
confirma recepción de inmediato y reserva la voz para consultas que valen la
espera. El servicio de audio además solo copia el historial con
consentimiento y elimina siempre el staging transitorio
(`backend/app/services/audio_service.py:72-83`).

---

## R2 — Sesiones acotadas y truncado

### Principio

El historial mejora la conversación hasta que la rompe: más turnos implican
más tokens, más latencia y más superficie de filtración. La solución común es
**límite fijo de turnos, de caracteres por turno y expiración por inactividad**.

### Ejemplo real: historial acotado en SQLite

copiloto-recepción modela la sesión como un dataclass con truncado destructivo,
en `copiloto/src/copiloto/ai/sessions.py:12-22`:

```python
@dataclass
class AiSession:
    session_id: str
    history: list[dict] = field(default_factory=list)
    state: dict = field(default_factory=dict)
    msg_count: int = 0
    created_at: float = 0.0

    def add(self, role: str, text: str, limit: int) -> None:
        self.history.append({"role": role, "content": text[:MAX_TEXT]})
        del self.history[:-limit]
```

Tres decisiones en diez líneas: cada texto se recorta a `MAX_TEXT = 1200` al
entrar, el historial nunca supera `limit` entradas (`ai_max_history = 12` en
`copiloto/src/copiloto/config.py:68`) y el borrado es por slice, sin segunda
pasada. La persistencia es un upsert en `ai_sessions` y la expiración un
`DELETE` por prefijo e inactividad (`copiloto/src/copiloto/ai/sessions.py:33-51`);
el esquema base se cubre en el [Capítulo 2](02-stack-base.md).

Patrón reutilizable:

```python
MAX_TURNS = 12
MAX_CHARS_PER_TURN = 1200

def append_turn(history: list[dict], role: str, text: str) -> list[dict]:
    """Append one turn and enforce the fixed budget in place."""
    history.append({"role": role, "content": text[:MAX_CHARS_PER_TURN]})
    del history[:-MAX_TURNS]
    return history
```

### Ejemplo real: máquina de estados y consentimientos separados

AgroVoz convierte la conversación en una máquina de estados explícita con
transiciones válidas y terminales, en `backend/app/services/conversation_state.py:26-82`:

```python
class ConversationState(Enum):
    ESPERANDO_CONSULTA = "esperando_consulta"
    CONSULTA_RECIBIDA = "consulta_recibida"
    BUSCANDO_DATOS = "buscando_datos"
    ACLARANDO = "aclarando"
    RESPONDIENDO = "respondiendo"
    CERRADO = "cerrado"
    DERIVADO = "derivado"
```

`CERRADO` y `DERIVADO` son terminales: no aceptan más transiciones
(`conversation_state.py:77-82`). La activación está tras el flag
`USE_CONVERSATION_STATE=false` (`backend/app/core/config.py:217`) y el registro
conserva solo `phone_hash` en memoria — nunca teléfonos planos ni contenido
(`backend/app/services/conversation_state.py:1-7`). Los consentimientos son
independientes por propósito y están desactivados por defecto: alertas
(`backend/migrations/versions/b7c3e91a4d28_add_alert_consent.py:20-38`),
historial (`AgroVoz/backend/migrations/versions/f2a8c1d7e4b6_add_history_consent.py:19-33`), gastos
(`AgroVoz/backend/migrations/versions/a7c4e9b2d1f6_add_expenses_and_consent.py:19-33`) y parcelas
(`AgroVoz/backend/migrations/versions/b3f8e2a91c47_add_parcelas_and_consent.py:19-33`).

### Ejemplo real: historial reactivo y admin-only

ManttoAI muestra el extremo opuesto y válido: chat reactivo `POST /chat` que
procesa un mensaje y persiste el par pregunta-respuesta
(`backend/app/routers/chat.py:88-110`). El historial (`GET /chat/historial`) y
la exportación del dataset (limitada a 10 000 filas) exigen rol `admin`
(`backend/app/routers/chat.py:112-137`; el tope de 10 000 está en `:54`). Sin memoria entre turnos: cada
request es independiente y la trazabilidad vive en la BD, no en el prompt.

Regla práctica: elige un nivel y decláralo. Nivel 0 (ManttoAI): sin memoria
entre turnos, historial solo para auditoría. Nivel 1 (copiloto): ventana fija
de N turnos con TTL. Nivel 2 (AgroVoz): máquina de estados con terminales
explícitos y consentimientos separados por propósito.

---

## R3 — Proactividad: scheduler con permiso vs. SLA reactivo

### Principio

El **scheduler** inicia contacto y exige consentimiento previo más ventana de
envío. El **SLA reactivo** mide cuánto tarda un humano en responder lo que el
bot no resolvió. Confundirlos produce spam o guardias fantasma.

### Ejemplo real: scheduler periódico (Wenuke)

Wenuke ejecuta un `AlertScheduler` en background cada 6 horas
(`backend/scheduler.py:32-56`), con lógica compartida con el dispatch manual
(`backend/servicio_alertas.py:1`). La selección de destinatarios filtra solo por
cultivo (`backend/db.py:518-529`) y el registro inserta siempre
(`backend/db.py:538-545`): no hay columna de consentimiento ni deduplicación.
Este caso sirve como esqueleto de scheduler, no como modelo de permiso. Las
condiciones mínimas para un scheduler que inicia contacto son: opt-in vigente y
revocable, intervalo y ventana horaria declarados, deduplicación de la misma
alerta, y resultado de envío registrado.

### Ejemplo real: SLA reactivo con semáforo (copiloto)

copiloto-recepción no inicia contacto comercial; mide la derivación con dos
umbrales (`copiloto/src/copiloto/config.py:47-48`):

```python
sla_amber_s: int = 120
sla_red_s: int = 180
```

Verde bajo 120 s desde el traspaso, ámbar a los 120 s, rojo a los 180 s con
nota de alerta (`docs/manual-recepcion.md:21-23`). El piloto exige ≥ 90 % de
consultas comerciales con primera respuesta humana bajo 180 s
(`docs/piloto.md:18`). El bot no presiona al humano; el tablero sí.

Regla práctica: si tu agente envía el primer mensaje, implementa scheduler con
las cuatro condiciones. Si solo responde, implementa el semáforo SLA sobre el
handoff y publica el cumplimiento. Ambos, nunca ninguno.

---

## R4 — Handoff humano con contexto armado

### Principio

Derivar es el camino diseñado para lo que el bot debe no resolver (fuera de
turno, PMS caído, petición explícita, tercer fallo de comprensión). Un buen
handoff transfiere el resumen y la causa; uno malo transfiere al usuario a una cola vacía.

### Ejemplo real: causas explícitas y cola visible

El flujo de copiloto deriva con causa tipificada; las razones reales están en
el mapa de `_note` (`copiloto/src/copiloto/flow.py:572-575`): `human_requested`,
`commercial`, `pms_down`, `error`, `ai_handoff`. Los disparadores, por ejemplo,
están en `:190` (falla técnica), `:212`/`:689` (pidió humano), `:469` (PMS caído),
`:483`/`:551` (consulta comercial) y `:745` (derivación de la IA). Persiste el
momento (`handoff_at`), registra el evento y decide qué ve el huésped según el
turno humano (`SHIFT_START` / `SHIFT_END`). `night` no es una causa de `_handoff`:
fuera de turno se registra `night_capture` y la etiqueta `nocturna`
(`flow.py:622-642`, `:198-199`). Los disparadores están listados, no
adivinados (`copiloto/src/copiloto/flow.py:52`): "recepción", "humano",
"persona", "agente", "ejecutivo", "operador", "hablar con alguien".

Del lado de AgroVoz, la derivación es un estado terminal
(`DERIVADO` en `backend/app/services/conversation_state.py:35`): una
conversación derivada no vuelve al bot por accidente. Ese detalle evita el
peor bug de handoff: el bot que interrumpe al humano que ya tomó el caso.

Checklist del handoff:

1. **Causa tipificada.** Enum cerrado de motivos, cada uno con su mensaje.
2. **Contexto armado.** La nota incluye últimos N turnos, intent y causa.
3. **Turno visible.** Sin humano disponible, dilo y ofrece captura con folio.
4. **Terminal.** Tras derivar, el bot calla hasta que el humano libera el caso.
5. **Medido.** Cada handoff alimenta el semáforo SLA del R3. La validación en
   servidor de la reserva está en el [Capítulo 4](04-orquestacion-tools.md).

---

## R5 — Métricas mínimas: latencia, fallback y costo

### Principio

Tres números sostienen la operación; el resto es decoración hasta que estos
estén verdes. Se definen antes del lanzamiento, con umbral y dueño cada uno.

| Métrica | Definición | Umbral inicial sugerido |
|---|---|---|
| Latencia p50 / p95 por canal | Mensaje entrante → respuesta entregada | Texto p95 < 5 s; voz p95 < 30 s (medir y ajustar) |
| Tasa de fallback | Respuestas fallback / respuestas totales | < 10 % semanal; si sube, revisar corpus o reglas |
| Costo por consulta | (Tokens × precio) + audio + mensajes enviados | Techo mensual; alerta al 80 % |

La cota de cada llamada externa ya existe como timeout (`timeout=15.0` en
`backend/whatsapp.py:32-35`); la latencia y el costo se calculan en
`copiloto/src/copiloto/metrics.py:52-84`, que no incluye una tasa de fallback:
si la necesitas, es un contador nuevo. Reglas: mide por canal separado,
calcula el fallback sobre respuestas, incluye lo no-LLM (mensajes, TTS/STT),
y publica el semáforo 120/180 s junto a estas tres. La frescura y los TTL se
detallan en el [Capítulo 5](05-datos-rag.md); el contrato offline, en el
[Capítulo 1](01-principios-fail-closed.md).

---

## Antipatrones del canal

1. **Historial infinito "por si acaso".** Sin `MAX_TURNS` ni `MAX_TEXT` cada despliegue hereda la factura del anterior.
2. **Voz tratada como texto con micrófono.** Tres modelos en serie no dan latencia de chat.
3. **Scheduler sin opt-in.** Sin consentimiento vigente, la alerta útil es spam denunciable.
4. **Handoff sin contexto.** Derivar el chat vacío es derivar el trabajo al usuario dos veces.
5. **Métricas de vanidad.** Contar mensajes sin latencia, fallback ni costo celebra el tráfico y esconde la calidad.

## Referencias verificadas

- `backend/app/services/conversation_state.py:26-35` — máquina de estados con nombres reales; terminales en `:77-82` (AgroVoz).
- `backend/app/services/conversation_state.py:1-7` — flag `USE_CONVERSATION_STATE=false`, solo `phone_hash` (AgroVoz); flag en `core/config.py:217`.
- `backend/requirements-docker.txt:14-23` — `faster-whisper` + `piper-tts` pesadas (AgroVoz).
- `copiloto/src/copiloto/ai/sessions.py:12-22,33-51` — `AiSession` con truncado fijo y persistencia (copiloto-recepción).
- `copiloto/src/copiloto/config.py:47-48,68` — SLA 120/180 s e `ai_max_history = 12` (copiloto-recepción).
- `copiloto/src/copiloto/flow.py:52,572-575,602-642` — disparadores, razones y persistencia del handoff (copiloto-recepción).
- `backend/whatsapp.py:20-75` — cliente WhatsApp Cloud API con resultado explícito (Wenuke).
- `backend/scheduler.py:32-56` — scheduler de alertas cada 6 h; `db.py:518-529,538-545` — selección y registro sin consentimiento (Wenuke).
- `backend/main.py:88-117` — auth stateless por Bearer con SHA-256 (Wenuke).
- `backend/app/routers/chat.py:54,88-137` — chat reactivo, historial y dataset solo admin (ManttoAI).

## Cierre

Expón primero el canal más simple (casi siempre web o API reactiva), acota la
sesión con dos números (`MAX_TURNS`, `MAX_CHARS_PER_TURN`), y solo después
agrega WhatsApp, voz o scheduler — cada uno con su contrato, su permiso y su
métrica. El handoff no es el fracaso del agente: es lo único que garantiza que
un humano llega a tiempo cuando el agente no debe continuar.
