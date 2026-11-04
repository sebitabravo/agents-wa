<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Capítulo 4 — Orquestación y tools: loop acotado, validación en servidor, doble confirmación

> **Tipo:** how-to con explicación (cómo orquestar herramientas y por qué acotar el loop).
> **Audiencia:** desarrolladores que agregan function calling o tools a un agente o chatbot.
> **Meta:** al terminar, decides entre loop con tools y single-shot, implementas un loop
> acotado por plazo y pasos, validas cada argumento en el servidor y exiges doble
> confirmación en dos turnos antes de cualquier efecto irreversible.

Un agente con tools no es un chatbot que habla: es un programa que ejecuta
acciones a partir de texto generado. El texto del modelo es una sugerencia; la
decisión de actuar vive en tu código.

## La respuesta primero

| # | Regla | En una frase |
|---|-------|--------------|
| R1 | Loop solo cuando hay acción verificable | Si el modelo solo redacta, usa single-shot; si consulta o modifica datos, usa loop con tools. |
| R2 | Loop siempre acotado | Todo loop tiene plazo máximo, número máximo de pasos y traza de cada llamada. |
| R3 | El servidor valida, el modelo sugiere | Fechas, cupo, nombres y permisos se verifican en código, nunca en el prompt. |
| R4 | Doble confirmación en dos turnos | Ningún efecto irreversible se ejecuta en el mismo turno donde se propuso. |

Si solo recuerdas una cosa: **el modelo propone, el servidor dispone**.

---

## R1 — Cuándo usar loop con tools y cuándo usar single-shot

### El contraste real

Los cuatro proyectos usan dos arquitecturas distintas, y la elección depende de si
el agente actúa sobre datos o solo redacta texto.

**Single-shot: reglas deterministas primero, LLM solo para redactar.** ManttoAI
procesa cada mensaje en `backend/app/services/chat_service.py:61`: primero busca
una palabra clave en `REGLAS_MANTENIMIENTO` y, solo si ninguna coincide, delega a
Ollama en una única llamada sin herramientas. No hay loop porque no hay nada que
iterar: o la respuesta está prearmada o el modelo redacta una respuesta de texto.
Wenuke usa reglas deterministas para alertas (`backend/reglas.py:173-255`) y, en
`/preguntar`, una sola llamada al LLM con el contexto climático ya calculado
(`backend/main.py:555-572`); no hay loop de tools. Cuando el dato ya está resuelto
por reglas, el modelo solo redacta; cuando el usuario pregunta, responde una vez
con ese contexto.

**Loop real: el modelo necesita observar antes de responder.** Solo dos proyectos
implementan un loop de herramientas: copiloto-recepción y AgroVoz. En
`copiloto/src/copiloto/ai/agent.py:116-145`, `respond` construye el historial,
resuelve el modo (`full` o `assisted`), guarda el texto crudo del huésped en
`session.state["last_user_text"]` y obtiene los `tool_specs` antes de entrar al
bucle `for step in range(MAX_STEPS)` con `MAX_STEPS = 5` (`agent.py:19`). El loop
existe porque la respuesta correcta depende de datos que solo aparecen tras
llamar herramientas: disponibilidad del PMS, precio, estado de la reserva.
AgroVoz declara un catálogo amplio de herramientas permitidas en
`backend/app/services/llm_service.py:81-103` (`WHITELIST_TOOLS`, 19
herramientas de lectura, cálculo y registro) con un texto de fallback fijo cuando
el modelo intenta algo fuera de la lista. El loop existe porque el modelo debe
encadenar observaciones: precio, clima, calendario agrícola, registro. El
principio fail-closed y el fallback por causa están en el
[Capítulo 1](01-principios-fail-closed.md).

### Criterio de decisión

Usa esta tabla antes de escribir código:

| Situación | Patrón | Ejemplo |
|-----------|--------|---------|
| Respuesta prearmada o redactada, sin datos externos | Single-shot (reglas-first + fallback LLM) | ManttoAI `chat_service.py:61-87` |
| Decisión determinista sobre datos ya disponibles | Reglas en código + LLM solo para texto | Wenuke `Wenuke/backend/reglas.py:173`, `Wenuke/backend/main.py:555-572` |
| La respuesta exige consultar un sistema externo | Loop con tools de lectura | copiloto `agent.py:116`, AgroVoz `WHITELIST_TOOLS` |
| La acción modifica estado (reserva, registro, pago) | Loop + validación en servidor + doble confirmación | copiloto `tools.py:243-336` |

La regla práctica: si puedes escribir la respuesta correcta sin llamar a nada, no
uses tools. Empieza sin loop y migra a loop cuando una respuesta real lo exija.

---

## R2 — Receta del loop acotado: plazo, pasos y herramienta forzada

Un loop sin cotas es un riesgo operativo: un modelo indeciso puede encadenar
llamadas hasta agotar el presupuesto o el tiempo del turno. La receta de
copiloto-recepción combina cuatro cotas independientes.

### Los cuatro límites

**1. Plazo del turno (`deadline`).** En `agent.py:118`, `respond` calcula
`deadline = time.monotonic() + self.settings.ai_turn_timeout_s` antes de
cualquier llamada. Cada iteración verifica `if deadline <= started: raise
LlmUnavailable("plazo del turno agotado")` (`agent.py:175-176`) y cada llamada al
LLM corre dentro de `asyncio.timeout` contra el tiempo restante
(`agent.py:178-182`). El plazo cubre el turno completo, no una sola llamada:
cinco llamadas rápidas y una lenta consumen el mismo presupuesto.

**2. Número máximo de pasos (`MAX_STEPS`).** El bucle es
`for step in range(MAX_STEPS)` con `MAX_STEPS = 5` (`agent.py:19,173`). Cinco
pasos alcanzan para consultar, validar, proponer y confirmar; más pasos indican
que el modelo está dando vueltas y hay que cortar con un fallback, no seguir
intentando.

**3. Sin `tool_choice="required"`.** El código documenta por qué no fuerza
llamadas a nivel de API: el servidor local (llama.cpp) ignora ese parámetro y el
modelo tiende a narrar la llamada en texto en vez de emitirla (`agent.py:177`).
En su lugar, fuerza la herramienta que importa con lógica determinista previa al
loop: si el mensaje parece pregunta del hotel o intención de reserva, ejecuta
`get_hotel_info` antes de la primera llamada al modelo (`agent.py:134-153`). La
lección: no confíes en un parámetro del proveedor para garantizar una llamada;
ejecútala tú cuando la intención sea clara.

**4. Respaldo determinista cuando el modelo no llama.** Si en el paso cero el
modelo responde texto sin herramientas pero el mensaje trae intención de
reserva, el código parsea fechas y huéspedes del texto del usuario y consulta
`check_availability` igualmente (`agent.py:186-208`). La lectura del PMS no
depende de que el modelo decida llamar. El loop tolera un modelo perezoso porque
la ruta crítica (fechas dichas por el usuario → disponibilidad real) no pasa por
su criterio.

### Traza y carga acotada

Cada llamada queda registrada en `result.events` con nombre, argumentos,
milisegundos y estado (`agent.py:218-222`), y la carga de cada herramienta se
trunca a `MAX_TOOL_PAYLOAD` antes de volver al historial (`agent.py:227`).

### Receta mínima (verificar contra `agent.py:116-234`)

```python
MAX_STEPS = 5
MAX_TOOL_PAYLOAD = 3500

async def respond(session, user_text):
    deadline = time.monotonic() + settings.turn_timeout_s
    state["last_user_text"] = user_text  # raw text, for server-side checks
    specs = tool_specs("full" if settings.autonomous else "assisted")
    messages = [system_prompt, *session.history, user_message]
    maybe_run_forced_tool(user_text)
    for step in range(MAX_STEPS):
        if time.monotonic() >= deadline:
            raise TurnTimeout("turn deadline exceeded")
        reply = await llm.chat(messages, specs, timeout=deadline - now())
        if not reply.tool_calls:
            maybe_run_fallback_tool(step, user_text)
            break
        messages.append(reply.message)
        for call in reply.tool_calls:
            outcome = await run_tool(call.name, call.arguments)
            record_event(call.name, outcome)  # name, args, ms, ok
            messages.append(tool_message(call.id, outcome.data[:MAX_TOOL_PAYLOAD]))
    return finish(session, result, text)
```

---

## R3 — Validación en servidor: el modelo sugiere, el código decide

Las herramientas de copiloto no confían en el modelo: el "sí" del huésped se
verifica sobre su propio texto, no sobre el argumento que el modelo envía
(`agent.py:127`). Toda la función `_booking` en
`copiloto/src/copiloto/ai/tools.py:243-336` es una secuencia de validaciones en
código que ningún prompt podría garantizar:

1. **Permiso del canal.** Si la sesión es `sandbox_only` sin autorización, o la
   lectura previa no es simulada, la reserva se rechaza de inmediato
   (`tools.py:245-249`). El modo demo no puede tocar datos reales por ningún
   camino, ni siquiera si el modelo lo pide.
2. **Nombre válido.** El nombre se normaliza y debe coincidir con `GUEST_NAME`
   (solo letras) y tener al menos nombre y apellido (`tools.py:257-259`).
3. **Fechas y huéspedes coherentes.** `_date` y `_int` parsean en servidor y
   `_validate_stay` rechaza estadías imposibles (`tools.py:260-264`).
4. **Lectura vigente.** La reserva exige una lectura de disponibilidad fresca
   (`prebooking_minutes`) con exactamente los mismos datos; si algo cambió, se
   invalida la propuesta y se ordena releer (`tools.py:266-273`). Esto impide
   reservar con precios vencidos.
5. **Habitación ofrecida.** El `room_code` debe existir en las opciones de esa
   lectura; si no, se devuelven las opciones vigentes (`tools.py:274-278`). El
   modelo no puede inventar habitaciones.
6. **Nombre aportado por el usuario.** El nombre debe aparecer literalmente en
   el historial de mensajes del usuario más el texto crudo del turno, con
   coincidencia de palabra completa (`tools.py:279-287`). El modelo no puede
   inventar el nombre del huésped.
7. **Doble confirmación en dos turnos.** Ver sección R4 (`tools.py:303-307`).
8. **Conflicto final contra el PMS.** Si el PMS rechaza por falta de cupo, el
   error se traduce en instrucción de reintentar con alternativas, nunca en una
   reserva afirmada (`tools.py:313-316`).

AgroVoz aplica el mismo principio a nivel de catálogo: cualquier herramienta
fuera de `WHITELIST_TOOLS` recibe el `FALLBACK_TEXT` fijo
(`llm_service.py:66-67,81-103`), y las operaciones con efectos persistentes
(`register_expense`, `register_parcela`, reportes) se excluyen del intento remoto
primario para evitar duplicados ante un reintento
(`llm_service.py:105-117`, `OPENROUTER_PRIMARY_READ_ONLY_TOOLS`). La validación
vive en dos capas: qué herramientas existen y cuáles pueden ejecutarse en cada
ruta.

```python
async def run_booking_tool(args, session, hooks, clock):
    if hooks.extra.get("sandbox_only") and not hooks.extra.get("sandbox_authorized"):
        return ToolResult(ok=False, error="sandbox_not_authorized")
    name = normalize(args.get("guest_name"))
    if not VALID_NAME.match(name) or len(name.split()) < 2:
        return ToolResult(ok=False, error="invalid_name")
    stay = validate_stay(args)  # dates, guests, server-side
    if stay.error:
        return ToolResult(ok=False, error=stay.error)
    if not has_fresh_reading(session, args, clock):
        return ToolResult(ok=False, error="stale_reading_reread_first")
    if args["room_code"] not in last_options(session):
        return ToolResult(ok=False, error="room_not_offered")
    if not user_actually_said(session, name):
        return ToolResult(ok=False, error="name_not_provided_by_user")
    if not confirmed_in_later_turn(session, args):
        return proposal_snapshot(args)  # proposal, not a booking
    return await pms.book(**stay, guest=name)  # translate conflicts, never assert
```

---

## R4 — Doble confirmación en dos turnos: propuesta primero, reserva después

La regla más importante para acciones irreversibles: **ninguna herramienta con
efectos se ejecuta en el mismo turno donde se propuso**. Copiloto la implementa
en `tools.py:96-105` (la descripción del spec de `create_booking` lo anuncia al
propio modelo: con `guest_confirmed=false` prepara una propuesta; solo un sí
explícito en un turno posterior puede crear la reserva) y la impone en código en
`tools.py:298-307`:

- Primera llamada: guarda un `snapshot` en `pending_booking` y devuelve la
  propuesta con `"propuesta": True` más la instrucción de pedir confirmación.
- Segunda llamada: solo crea la reserva si el argumento trae
  `guest_confirmed is True`, el texto crudo del usuario confirma
  (`guest_said_yes` sobre `last_user_text`) y la propuesta se presentó en un
  turno anterior (`presented < turn`).

Los tres requisitos son conjuntivos: basta que uno falle para devolver otra
propuesta. Y la confirmación se lee del texto del usuario, no del argumento del
modelo: si el modelo marca `guest_confirmed` pero el huésped no dijo sí, no hay
reserva (`agent.py:128`, `tools.py:303`).

### Ejemplo malo: reserva en un solo turno

> Usuario: "¿Tienen algo para este finde? Soy Ana."
> Agente: *(llama `create_booking` con `guest_name="Ana"`, fechas inferidas,
> `guest_confirmed=true` porque "suena a que quiere reservar")*
> Agente: "Listo, reservé la suite para ti."

Todo está mal: el nombre no tiene apellido, las fechas se infirieron, la
confirmación la puso el modelo y la reserva se afirmó sin propuesta previa. Cada
uno de esos puntos es rechazado por una validación distinta en `tools.py`.

### Ejemplo bueno: propuesta, confirmación y reserva

> Usuario: "¿Tienen algo del 12 al 14 para 2 adultos? Soy Ana Rojas."
> Agente: *(llama `check_availability`, muestra opciones con precio y hora de
> lectura. Llama `create_booking` con `guest_confirmed=false`.)*
> Agente: "Tengo la doble estándar, $45.000 por noche, total $90.000 del 12 al
> 14. ¿La confirmo a nombre de Ana Rojas?"
> Usuario: "Sí, confírmala."
> Agente: *(verifica el "sí" sobre el texto del usuario y que la propuesta sea
> del turno anterior; recién entonces crea la reserva.)*
> Agente: "Reserva #1234 creada: doble estándar del 12 al 14 a nombre de Ana
> Rojas."

Dos turnos, dos llamadas, una sola escritura: el resumen intermedio es el punto
de control donde el usuario corrige fechas, nombre o habitación antes del efecto.
La operación del handoff —cola, asignación y SLA— se cubre en el
[Capítulo 6](06-canales-memoria.md).

---

## Errores comunes y lista de cierre

| Error | Síntoma | Antídoto en este capítulo |
|-------|---------|---------------------------|
| Loop sin plazo | Turnos colgados cuando el proveedor tarda | `deadline` por turno + `asyncio.timeout` (R2) |
| Loop sin tope de pasos | Modelo que reintenta la misma llamada | `MAX_STEPS = 5` y fallback (R2) |
| Confiar en `tool_choice` | Proveedor local lo ignora, el modelo narra | Llamada forzada determinista previa (R2) |
| Validar en el prompt | "Solo reserva si..." que el modelo ignora | Validación en servidor, 8 puntos (R3) |
| Confirmación en el argumento | Modelo que se autoconfirma | Confirmación sobre texto del usuario + turno posterior (R4) |
| Reinyectar fallos al modelo | El modelo repite tags internos | Fallo público y acotado, sin reintento ciego (AgroVoz `TOOL_EXECUTION_ERROR_TEXT`) |
| Tools de escritura reintentables | Registro duplicado tras timeout | Escrituras fuera de la ruta con reintento (AgroVoz `OPENROUTER_PRIMARY_READ_ONLY_TOOLS`) |

Antes de dar por terminado un agente con tools, verifica:

- [ ] Cada tool con efectos tiene su validación en servidor, no solo en el prompt.
- [ ] El loop tiene plazo, tope de pasos, traza y truncado de carga.
- [ ] Ningún efecto irreversible ocurre en el mismo turno de su propuesta.
- [ ] La confirmación se verifica sobre el texto del usuario, no sobre argumentos.
- [ ] Toda tool fuera del whitelist recibe el mismo fallback fijo.
- [ ] Las escrituras no se reintentan a ciegas desde el orquestador.

## Referencias al código real

- Loop `respond`, plazo, `sandbox_only`, texto crudo del usuario, specs y llamada
  forzada previa: `copiloto/src/copiloto/ai/agent.py:116-145`.
- Tope de pasos, `tool_choice` no usado, respaldo determinista, eventos y
  truncado: `copiloto/src/copiloto/ai/agent.py:19,173-234`.
- Catálogo de specs por modo (`full`/`assisted`) y descripción de
  `create_booking` en dos turnos: `copiloto/src/copiloto/ai/tools.py:73-106`.
- Validación de reserva en servidor (permiso, nombre, fechas, lectura vigente,
  habitación, nombre dicho, doble confirmación, conflicto PMS):
  `copiloto/src/copiloto/ai/tools.py:243-336`.
- Whitelist de 19 herramientas, fallback fijo y exclusión de escrituras del
  intento con reintento: `backend/app/services/llm_service.py:66-67,81-103,105-117`
  (AgroVoz).
- Single-shot reglas-first sin tools: `backend/app/services/chat_service.py:61-87`
  (ManttoAI).
- Reglas deterministas sobre pronóstico + LLM solo para texto:
  `backend/reglas.py:173`, `backend/main.py:555-572` (Wenuke).
