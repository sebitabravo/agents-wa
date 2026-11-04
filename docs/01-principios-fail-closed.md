<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Capítulo 1 — Principios fail-closed y costo $0: cuando NO responder

> **Tipo:** explanation (por qué) con checklists aplicables.
> **Audiencia:** desarrolladores que construyen agentes o chatbots con LLM.
> **Meta:** al terminar, decides en qué casos tu agente debe NO responder con datos
> generados y qué mecanismo usar en su lugar.

La regla de este capítulo cabe en una línea: **ante la duda, el agente se cierra,
no inventa**. Todo lo demás — fallbacks, whitelists, modo offline — son formas
de implementar esa regla. Los tres principios siguientes vienen de código real de
los proyectos AgroVoz, Wenuke y copiloto-recepción, citados con `path:line`.

## La respuesta primero

| # | Principio | En una frase |
|---|-----------|--------------|
| P1 | Falla cerrado, nunca inventes | Sin dato verificado no hay respuesta con datos: hay fallback explícito. |
| P2 | Whitelist de herramientas | Toda acción fuera de la lista permitida se rechaza con el mismo fallback. |
| P3 | Degradación a costo $0 | Si el LLM falla o sale caro, responde un camino determinista y gratis. |

Si solo recuerdas una cosa: **un "no sé" explícito siempre es mejor que un dato
inventado que parece real**.

---

## P1 — Falla cerrado: sin dato verificado no hay respuesta con datos

### Principio

El agente solo afirma datos que obtuvo de una fuente verificada (herramienta,
corpus aprobado o API). Cuando no tiene el dato — porque el LLM falló, no
respondió o intentó salirse del guion — devuelve un texto de fallback fijo y
acotado, nunca una improvisación.

### Por qué

Un LLM siempre puede generar texto fluido; esa fluidez es el peligro. En un
contexto agrícola, un precio o un pronóstico inventado se lee igual que uno
real y provoca decisiones económicas equivocadas. El fallo silencioso (responder
cualquier cosa) es peor que el fallo visible (admitir que no se sabe). Por eso
los fallbacks se definen como **constantes**, no como texto generado: son
predecibles, revisables y testeables.

### Ejemplo real

AgroVoz define textos de fallback como constantes separadas según la causa del
fallo, en `backend/app/services/llm_service.py:66-78`:

```python
# Texto de fallback cuando el LLM intenta una tool fuera del whitelist.
FALLBACK_TEXT = "No tengo ese dato, pero puedo consultarte el precio en ODEPA o el clima."

# Texto cuando el LLM no genera respuesta.
NO_RESPONSE_TEXT = "No entendí tu consulta. ¿Podrías reformularla?"

# Un mock con precios fijos solo sirve en pruebas. En runtime sería
# indistinguible de un dato real para el agricultor.
LLM_UNAVAILABLE_TEXT = "No puedo procesar esa consulta en este momento. ¿Podrías intentarlo de nuevo más tarde?"

# No se reinyecta un fallo de herramienta al modelo: podría repetir tags o
# instrucciones internas en vez de comunicar una falla pública y acotada.
TOOL_EXECUTION_ERROR_TEXT = "No pude consultar ese dato en este momento. ¿Probamos más tarde?"
```

Observa tres decisiones deliberadas en ese fragmento:

1. **Un fallback por causa** (`FALLBACK_TEXT`, `NO_RESPONSE_TEXT`,
   `LLM_UNAVAILABLE_TEXT`, `TOOL_EXECUTION_ERROR_TEXT`). Cada uno describe lo
   que pasó sin filtrar detalles internos.
2. **Nunca reinyectar el error crudo al modelo.** El comentario de la línea 76
   lo dice explícito: reinyectar el fallo podría hacer que el modelo repita
   tags o instrucciones internas en lugar de una falla pública acotada.
3. **El comentario sobre mocks** (líneas 72-73): un precio falso en producción
   es indistinguible de uno real para el usuario final. Los datos de prueba
   nunca salen del entorno de pruebas.

### Checklist P1

- [ ] Cada camino de fallo (sin respuesta, tool denegada, servicio caído, error
      de ejecución) tiene su propio texto de fallback constante.
- [ ] Ningún fallback contiene datos que parezcan reales (precios, fechas,
      pronósticos, IDs de reserva).
- [ ] Los errores internos nunca se reinyectan al modelo ni se muestran al
      usuario tal cual.
- [ ] Los mocks con datos fijos están marcados y confinados al entorno de
      pruebas.
- [ ] Cada fallback ofrece un siguiente paso útil ("puedo consultarte…",
      "¿probamos más tarde?", "¿podrías reformularla?").

### Anti-patrón

> **El fallback generativo.** Capturar la excepción y pedirle al LLM que
> "responda algo amable de todas formas". Eso convierte un fallo controlado en
> una invención con tono seguro. Si el modelo ya falló una vez, no le pidas que
> improvise: sirve la constante.

---

## P2 — Whitelist de herramientas: lo no permitido no existe

### Principio

El agente solo puede ejecutar las herramientas de una lista explícita y
cerrada. Cualquier intento del modelo de llamar a otra herramienta — exista o
no — se rechaza y termina en el `FALLBACK_TEXT` de P1, no en un error técnico
expuesto al usuario.

### Por qué

El modelo propone llamadas a herramientas como texto; nada le impide proponer
una que no existe o una de escritura cuando solo debía leer. Sin whitelist, el
orquestador debe decidir caso por caso qué es válido, y cada olvido es una vía
de abuso o de corrupción de datos. Con whitelist, la regla es una sola línea:
**lo que no está en la lista no se ejecuta**. Además separa lectura de
escritura: las operaciones con efectos persistentes reciben un tratamiento más
estricto (sin reintentos a ciegas que duplicarían registros).

### Ejemplo real

AgroVoz declara el conjunto permitido como `frozenset` en
`backend/app/services/llm_service.py:81-103`, y documenta la separación
lectura/escritura en el comentario de la línea 105:

```python
# Tool names permitidas. Cualquier otra -> fallback.
WHITELIST_TOOLS = frozenset(
    {
        "get_price",
        "get_price_history",
        "calculate_sale_value",
        "get_weather",
        "search_corpus",
        # ... (lista cerrada, ver archivo completo)
    }
)

# En el intento remoto primario solo se anuncian tools de lectura. Si una
# request OpenRouter vence justo despues de ejecutar una escritura y el caller
# reintenta con Qwen, se podria duplicar el registro.
```

El complemento está en copiloto-recepción. En
`copiloto/src/copiloto/ai/agent.py:127-129` las herramientas no confían en lo
que el modelo afirma: el "sí" del huésped se verifica contra su propio texto,
no contra la interpretación del modelo:

```python
# Las herramientas no confían en el modelo: el «sí» del huésped se verifica sobre su propio texto.
session.state["last_user_text"] = user_text
specs = tool_specs("full" if settings.autonomous_booking else "assisted")
```

Y el modo más restrictivo se impone por bandera, no por prompt, en
`copiloto/src/copiloto/ai/agent.py:119-121`:

```python
# Por voz el reconocimiento puede errar nombres y fechas: nunca se reserva solo, sea cual sea el modo global
denied = hooks.extra.get("sandbox_only") is True and hooks.extra.get("sandbox_authorized") is not True
settings = replace(self.settings, ai_mode="assisted") if voice or denied else self.settings
```

Tres mecanismos distintos, un mismo principio: **el permiso vive en código
(datos y banderas), no en instrucciones en lenguaje natural**. El prompt puede
pedir lo que sea; la whitelist, el `sandbox_only` y la verificación sobre el
texto del usuario son los que mandan. La mecánica del loop y la validación de
argumentos se detalla en el [Capítulo 4](04-orquestacion-tools.md).

### Checklist P2

- [ ] Existe una lista cerrada de herramientas permitidas, definida en código
      (`frozenset`, enum o equivalente), no solo mencionada en el prompt.
- [ ] Toda llamada fuera de la lista termina en fallback de usuario, no en un
      stack trace ni en silencio.
- [ ] Las herramientas de escritura están separadas de las de lectura y no se
      reintentan automáticamente a ciegas.
- [ ] Las confirmaciones del usuario (un "sí", una fecha, un nombre) se
      verifican contra el texto original del usuario, no contra el resumen del
      modelo.
- [ ] Los modos restringidos (`sandbox_only`, voz, asistido) se imponen con
      banderas de código que degradan el modo global, sin importar lo que el
      modelo sugiera.

### Anti-patrón

> **La blacklist.** Definir "herramientas prohibidas" en el system prompt y
> asumir que el modelo obedecerá. Todo lo nuevo queda permitido por defecto, y
> una instrucción en lenguaje natural no es un control de acceso. Permite por
> defecto lo que el modelo proponga y terminarás ejecutando algo que nunca
> revisaste.

---

## P3 — Degradación a costo $0: el offline es una función, no un error

### Principio

Cuando el proveedor de LLM no responde (caída, timeout, sin conexión), el
agente no devuelve un error vacío: sirve una respuesta determinista construida
sin el modelo — reglas, datos locales o plantillas — y marca explícitamente que
está en modo degradado. Esa respuesta cuesta $0 y siempre está disponible.

### Por qué

Un chatbot agrícola se usa en terreno, donde la conectividad falla. Un "error
500, intente más tarde" en época de siembra es una respuesta inútil. El modo
offline convierte una dependencia externa (la API del LLM, con costo por token
y latencia de red) en una degradación elegante: respuesta menos rica, pero
inmediata, gratuita y honesta sobre sus límites. La bandera `offline: true` en
la respuesta permite al llamante distinguir el camino degradado; no hay una
métrica que agregue ese conteo.

### Ejemplo real

Wenuke implementa este patrón en `backend/llm.py:130-159`. El método `preguntar`
retorna siempre el mismo contrato — `{"respuesta", "offline"}` — por tres
caminos:

```python
async def preguntar(self, pregunta: str, contexto_clima: dict, cultivo: str) -> dict:
    """Responde pregunta del agricultor. Retorna dict con 'respuesta' y 'offline'."""
    if self.modo_offline:
        return {"respuesta": self._respuesta_offline(pregunta, cultivo), "offline": True}
    # ... llamada a Groq con max_tokens=500, temperature=0.3 ...
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return {"respuesta": self._respuesta_offline(pregunta, cultivo), "offline": True}
```

El diseño relevante:

1. **Contrato único.** El llamante siempre recibe `respuesta` + `offline`, sin
   importar el camino. No hay excepciones que atrapar arriba ni `None` que
   chequear.
2. **Dos puertas al mismo fallback.** Tanto el modo offline configurado como
   cualquier excepción del proveedor terminan en `_respuesta_offline`, que
   resuelve desde JSON local con diccionario hardcodeado de respaldo.
3. **Límites de costo explícitos.** `max_tokens=500` y `temperature=0.3` acotan
   el gasto por llamada exitosa; el camino offline lo lleva a cero.

### Checklist P3

- [ ] Existe un camino de respuesta que no llama al LLM (reglas, plantillas,
      datos locales) y está probado, no solo escrito.
- [ ] La respuesta degradada se marca como tal (`offline: true` o equivalente)
      para que el llamante la distinga.
- [ ] El contrato de retorno es idéntico en el camino normal y en el
      degradado: el llamante no necesita ramificarse.
- [ ] Las llamadas al proveedor tienen topes (`max_tokens`, timeout) para que
      el costo del camino feliz esté acotado.
- [ ] El error del proveedor se registra en logs (`logger.error`), no se
      expone al usuario.

### Anti-patrón

> **El try/except que retorna el error.** Capturar la excepción del proveedor y
> devolver `"Error: <mensaje de la API>"` al usuario final. Filtra detalles
> internos, no ayuda a decidir nada y cuesta lo mismo que no haber respondido.
> Si ya pagaste el costo de fallar, al menos entrega el camino offline.

---

## Resumen del capítulo

| Principio | Mecanismo en código | Qué evita |
|-----------|---------------------|-----------|
| P1 Falla cerrado | Constantes de fallback por causa; sin reinyectar errores al modelo | Datos inventados con tono seguro |
| P2 Whitelist | Lista cerrada en código; verificación sobre texto del usuario; `sandbox_only` | Ejecución de acciones no revisadas |
| P3 Costo $0 | Contrato `respuesta + offline`; fallback determinista; topes de tokens | Error vacío y gasto sin respuesta |

Los tres principios comparten una idea: **las decisiones de seguridad viven en
código determinista, no en prompts**. El prompt pide, el código dispone. Los
capítulos siguientes construyen sobre esta base: el Capítulo 2 muestra el stack
(FastAPI, configuración, rate-limit y observabilidad) donde estos mecanismos se
montan, y el Capítulo 3 detalla cómo escribir system prompts que asumen desde
el inicio que el modelo puede fallar o ser manipulado.

## Siguiente paso

Continúa con el Capítulo 2 (stack base FastAPI: configuración, base de datos,
rate-limit y observabilidad), donde los fallbacks y la whitelist de este
capítulo se conectan al ciclo de request real.
