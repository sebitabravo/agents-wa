<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Capítulo 10 — Costos y selección de modelos: el costo se diseña por turno

> **Tipo:** explanation (por qué cuesta) + how-to (cómo medirlo y acotarlo).
> **Audiencia:** fundadores, responsables de producto y desarrolladores que ya
> tienen un agente funcionando y necesitan ponerle precio, presupuesto y límites.
> **Meta:** al terminar, puedes calcular el costo de un turno y de una
> conversación, elegir el modelo por tarea, fijar cuotas con límite duro y
> explicar la economía unitaria con supuestos explícitos.

El costo de un agente no es el precio del token. Es la suma de tokens, llamadas
a herramientas, recuperación de datos, infraestructura, reintentos y personas.
Un modelo barato con tres round-trips por turno puede costar más que uno caro
con una sola llamada; un prototipo de $0 puede esconder el costo de operación
que aparece cuando hay usuarios reales. La tesis del capítulo es una sola:
**el costo se diseña por turno y por conversación, no por factura mensual
sorpresa**. La factura es el resultado; el diseño es la unidad.

## La respuesta primero

| # | Regla | En una frase |
|---|-------|--------------|
| R1 | Diseñar por turno y conversación | El turno es la unidad de consumo; la conversación, la de negocio. |
| R2 | Separar fijo de variable | La infraestructura se paga igual con cero usuarios; los tokens no. |
| R3 | Modelo por tarea | Clasificar y extraer no necesitan el modelo más caro; razonar sí puede. |
| R4 | Presupuesto con límite duro | Sin tope por usuario, canal y tenant, un bug es una factura abierta. |
| R5 | Medir antes de optimizar | Sin tokens, cache hit rate y costo por turno, "optimizar" es adivinar. |

Si solo recuerdas una cosa: **un costo que no se mide por turno no se controla;
solo se descubre a fin de mes**.

---

## 10.1 Anatomía del costo: fijo, variable y por turno

### Fijo y variable

| Tipo | Componentes | Comportamiento | Cómo se controla |
|---|---|---|---|
| Fijo | VPS o serverless reservado, base de datos, dominio y SSL, observabilidad, personas de guardia y soporte | Se paga con cero o con mil usuarios | Derecho de uso, tamaño mínimo, revisión mensual |
| Variable | Tokens de entrada y salida, round-trips de tools, retrieval y embeddings, STT/TTS, mensajes de canal, reintentos | Crece con turnos, tools y errores | `max_tokens`, `max_steps`, caché, cuotas, routing |
| Semifijo | Una instancia, base o número de WhatsApp por tenant | Escala por cliente, no por turno | Arquitectura multi-tenant y contrato por cliente |

La distinción cambia la decisión. Un agente local tiene costo variable casi nulo
y fijo alto; uno con API tiene fijo bajo y variable que crece con cada usuario.
AgroVoz documenta el primer extremo: "El costo es enteramente fijo. No hay costo
variable por agricultor" (`AgroVoz/docs/negocio/07-estructura-de-costos.md:13`),
con CLP 14.364/mes (`:15-23`) y marginal ~0 (`:25`). Wenuke documenta el
segundo: USD 0–10/mes de infraestructura más Groq por token
(`Wenuke/README.md:40`; `Wenuke/docs/ARCHITECTURE.md:71,79`).

### Fórmula por turno

Un turno puede incluir una o varias generaciones si hay tools. La fórmula
separa lo que se cobra por token de lo que se cobra por llamada:

```text
C_turno = C_entrada + C_salida + C_tools + C_retrieval + C_voz + C_canal
C_entrada = T_uncached × p_in + T_cached × p_in_cache
C_salida  = T_out × p_out
C_tools   = Σ (round-trips de tools × C_round-trip)
C_turno_total = C_turno + F_mes / N_turnos_mes
```

`C_round-trip` no es un precio de proveedor: es el costo de la generación extra
que consume la respuesta de la herramienta. Si el orquestador llama tres tools
en secuencia, el prompt crece y se paga tres veces. El costo marginal excluye
`F_mes / N_turnos_mes`; el total lo incluye. No mezclar ambos: un turno de
$0,002 con $500 de infraestructura y cien turnos al mes cuesta $5,002 en total.

### Fórmula por conversación

```text
C_conversación = Σ C_turno(t) + C_sesión + C_handoff + C_muestreo_eval
C_conversación_total = C_conversación + F_mes / N_conversaciones_mes
```

`C_sesión` incluye almacenamiento e índices; `C_handoff`, el tiempo de una
persona si la conversación se deriva; `C_muestreo_eval`, el costo de evaluar una
muestra. Una conversación que se deriva a las tres preguntas cuesta menos tokens
que una que intenta resolver todo, pero puede costar más en personas. La
economía unitaria debe incluir ambas.

### Reintentos, fallback y desperdicio

Un reintento no es gratis: se paga el intento fallido y el nuevo. Un fallback
tampoco es gratis si ocurre después de un intento pagado. La fórmula esperada
es:

```text
C_esperado = C_primario + r × C_reintento + f × C_fallback
C_por_éxito = C_total / (1 - f)
```

Donde `r` es la tasa de reintento y `f` la tasa de conversaciones que terminan
en fallback. Si el 10% falla después de consumir el 30% del costo, el costo por
conversación exitosa sube alrededor de 3,3%: se pagó el intento incompleto y se
dividió por menos éxitos. Un fallback determinista cuesta casi $0 en tokens,
pero baja la calidad y puede costar una persona o una venta perdida. El
circuit breaker de AgroVoz corta el modelo 90 segundos tras un fallo
(`AgroVoz/backend/app/services/llm_service.py:138-142`, `:1020-1030`) para no
seguir pagando intentos condenados.

---

## 10.2 Selección de modelo: cuatro ejes, una decisión por tarea

Elegir modelo es un problema de restricciones, no de ranking. Los cuatro ejes
son capacidad, costo, latencia y privacidad; casi nunca se optimizan los cuatro
a la vez. Un modelo local de 3B puede bastar para redactar con datos de tools y
fallar en razonamiento abierto; uno grande puede resolver lo segundo y ser
demasiado caro para clasificar mil mensajes por hora. La regla práctica es:
**el modelo más pequeño que pasa las evaluaciones de la tarea, no el más grande
que existe**.

| Tarea | Modelo recomendado | Por qué | Evidencia |
|---|---|---|---|
| Clasificar intención, extraer campos, enrutar | Modelo pequeño, reglas o clasificador determinista | La salida es corta y verificable; no requiere razonamiento abierto | AgroVoz clasifica la consulta antes del LLM y recorta tools por intención (`AgroVoz/backend/app/services/llm_service.py:762-795`) |
| FAQ con datos estructurados | Búsqueda por keywords o modelo pequeño | El corpus es pequeño y la respuesta ya existe | copiloto resuelve FAQ por keywords, sin embeddings (`copiloto-recepcion copiloto/src/copiloto/hotel.py:51-62`) |
| Redactar una respuesta a partir de tools | Modelo mediano, temperatura baja, salida acotada | El dato viene de la herramienta; el modelo solo redacta | AgroVoz Qwen2.5-3B local con `max_tokens=128` (`AgroVoz/backend/app/services/llm_service.py:1762-1768`; `AgroVoz/backend/app/services/llm_worker.py:182-186`) |
| Razonamiento abierto o multi-paso | Modelo grande, pocas llamadas, presupuesto por turno | La calidad justifica el costo; el volumen debe ser bajo | Wenuke usa Llama 3.1 70B vía Groq con `max_tokens=500` (`Wenuke/backend/llm.py:144-152`) |
| Voz (STT/TTS) | Local si la privacidad manda; API si la latencia manda | El audio se cobra por minuto, no por token | AgroVoz usa Whisper + Piper locales (`AgroVoz/docs/negocio/07-estructura-de-costos.md:22`) |
| Embeddings y retrieval | Modelo de embeddings pequeño; a veces ningún modelo | Indexar y consultar tienen costo propio | AgroVoz usa TF-IDF, sin embeddings (`AgroVoz/backend/app/services/rag_service.py:281-304`) |

El routing aplica esta tabla en ejecución: una llamada barata clasifica y deriva
solo lo difícil al modelo grande. El riesgo es el costo del clasificador y sus
errores; se mitiga con reglas deterministas y una salida "desconocido" que no
finja certeza. Anthropic recomienda empezar por la solución más simple y aumentar
complejidad solo cuando mejora el resultado
(https://www.anthropic.com/research/building-effective-agents, 2024-12-19,
consultado 2026-11-04).

**No uses el modelo más caro para todo.** Un modelo grande en el camino de FAQ
multiplica el costo por un dato que ya estaba en una tabla; un modelo pequeño en
el camino de razonamiento abierto multiplica los reintentos y las respuestas
malas. La decisión correcta casi siempre es mixta.

---

## 10.3 Técnicas de reducción de costo

| Técnica | Mecanismo | Cuándo conviene | Límite o riesgo | Evidencia |
|---|---|---|---|---|
| Prompt caching | Prefijo estable (system prompt + tools) primero; lo variable al final | El prefijo se repite en cada turno | El proveedor debe soportarlo y el prefijo debe ser idéntico | AgroVoz ensambla el prompt en secciones estables (`AgroVoz/backend/app/services/prompt_builder.py:88-103`) |
| Ocultar tools apagadas | No anunciar una tool que el servicio va a rechazar | Feature gates y tools no disponibles | Hay que sincronizar gate y prompt | AgroVoz ahorra 809 caracteres de prefijo y un round-trip (`AgroVoz/docs/ARCHITECTURE-DECISIONS.md:223-227`; `AgroVoz/backend/app/services/llm_service.py:799-809`) |
| Recortar tools por intención | Enviar solo el subconjunto del dominio consultado | La intención se conoce antes del LLM | Si la clasificación falla, se pierde capacidad | AgroVoz separa tools de precio, clima y agronomía (`AgroVoz/backend/app/services/llm_service.py:762-795`) |
| Caché de respuestas | Guardar respuestas exactas o casi exactas con TTL | Preguntas repetidas y datos que no cambian | Nunca cachear datos sensibles a frescura sin invalidación | No implementado en los cuatro proyectos; aplicable a FAQ |
| Caché de datos externos | TTL por fuente; coordenadas redondeadas como clave | Clima, precios, catálogos | Un TTL largo sirve datos viejos | Wenuke cachea clima 1 h (`Wenuke/backend/config.py:20`; `Wenuke/backend/clima.py:29-41`) y ODEPA 6 h (`Wenuke/backend/odepa.py:57-62`) |
| Batching | Agrupar embeddings, evals o tareas offline | Trabajo no interactivo | No reduce la latencia de un chat | Aplicable a indexación y evaluación, no al turno |
| Truncar historial | Límite de mensajes y de caracteres por mensaje | Conversaciones largas | Se pierde contexto útil | copiloto: 12 mensajes, 1.200 caracteres (`copiloto-recepcion copiloto/src/copiloto/config.py:68`; `copiloto-recepcion copiloto/src/copiloto/ai/sessions.py:9-22`) |
| Resumir contexto | Reemplazar turnos viejos por un resumen | El historial supera el límite | El resumen puede omitir un dato crítico | Requiere evaluar calidad, no solo ahorro |
| Tools que devuelven poco | Top-k y campos acotados, no el payload crudo | Toda tool con respuesta grande | Menos datos puede significar menos precisión | AgroVoz usa RAG top-3 (`AgroVoz/backend/app/services/rag_service.py:83-88`) |
| `max_tokens` y `max_steps` | Tope de salida y de iteraciones en código | Siempre | Un tope bajo trunca respuestas legítimas | copiloto `MAX_STEPS=5` (`copiloto-recepcion copiloto/src/copiloto/ai/agent.py:19`); ManttoAI `num_predict=250` (`ManttoAI/backend/app/services/chat_service.py:147`) |
| Streaming solo si aporta | Enviar tokens mientras se generan | La latencia percibida es el problema | No reduce el precio por token | copiloto y ManttoAI usan `stream=False` (`copiloto-recepcion copiloto/src/copiloto/ai/llm.py:49-50`; `ManttoAI/backend/app/services/chat_service.py:142-148`) |

El orden importa: primero se mide, después se optimiza. Recortar el historial
antes de saber cuántos tokens consume puede ahorrar poco y romper la
conversación; activar caché sin un prefijo estable puede no acertar nunca. La
técnica más rentable suele ser la que elimina trabajo, no la que comprime el
trabajo que ya se hace.

---

## 10.4 Local vs API: el TCO honesto

El costo total de propiedad incluye hardware, RAM y CPU, latencia, operación,
energía, privacidad y calidad. Comparar solo el precio por token es una parte
del cálculo.

| Dimensión | Local | API |
|---|---|---|
| Costo marginal | Casi $0 por token; se paga CPU y energía | Por token, tool y a veces por request |
| Costo fijo | Servidor, GPU o CPU, disco, backups | Casi cero; se paga por uso |
| Latencia | Depende del hardware; puede ser alta en CPU | Depende del proveedor y de la red |
| Calidad | Limitada por el modelo que cabe en el equipo | Acceso a modelos mayores |
| Privacidad | Los datos no salen del servidor | Sale el prompt, salvo contrato o despliegue privado |
| Operación | Modelos, versiones, crashes, capacidad | Gestión del proveedor; quedan cuotas y caídas |
| Escalabilidad | Vertical y costosa; una instancia por modelo | Elástica, con límites de rate |
| Actualización | Manual y con riesgo de regresión | El proveedor puede retirar el modelo sin aviso |

**Cuándo conviene local:** el volumen es bajo y estable, la privacidad es un
requisito, el modelo pequeño pasa las evaluaciones y hay alguien que opera el
servidor. **Cuándo conviene API:** el volumen es variable, se necesita calidad
de frontera, no hay equipo de operación o el tiempo de ingeniería vale más que
el ahorro. **Cuándo conviene mixto:** camino principal barato y fallback local,
o clasificación local y razonamiento remoto.

La evidencia de los cuatro proyectos no es una recomendación universal, sino
cuatro respuestas a restricciones distintas:

- **AgroVoz:** Qwen2.5-3B local y OpenRouter free (`AgroVoz
  backend/app/core/config.py:136-147`). El prompt ronda 2.771 tokens y obliga a
  `n_ctx=4096`; la latencia en el VPS no está validada (`AgroVoz
  backend/app/services/llm_service.py:145-159`). El router gratuito traslada el
  costo a la privacidad (`AgroVoz/docs/ARCHITECTURE-DECISIONS.md:100-108`).
- **copiloto-recepción:** DeepSeek o llama.cpp/Qwen local; sin `LLM_API_KEY` el
  bot sigue determinista (`copiloto-recepcion copiloto/src/copiloto/config.py:149-152`).
  La latencia local ronda 18 s frente a 0,3 s del flujo guiado: el ahorro se
  paga en espera (`copiloto-recepcion docs/caso-de-estudio.md:112`).
- **ManttoAI:** Ollama con qwen2.5:0.5b en local (`ManttoAI
  backend/app/config.py:132-134`), pero el deploy público lo apaga porque 800 MB
  exceden los 512 MB del tier (`ManttoAI/render.yaml:52-53`;
  `ManttoAI/docs/auditoria/deploy.md:59`). El chat sin reglas cae a fallback.
- **Wenuke:** Groq de bajo costo y fallback offline (`Wenuke/backend/llm.py:130-159`).
  El estimado USD 0–10/mes es de infraestructura, no una medición de tokens
  (`Wenuke/README.md:40`).

---

## 10.5 Comparativa de proveedores

Esta tabla compara criterios, no precios. Cualquier tarifa exige **consultar
precio vigente** y tratarla como **precio vigente a verificar** en la página del
proveedor, con la fecha de consulta; los precios cambian y los modelos se retiran.

| Proveedor | Rol típico | Qué verificar antes de elegir | Evidencia en los cuatro proyectos |
|---|---|---|---|
| OpenAI | Modelo general y tool calling | Precio vigente, caching, límites, región, retención de datos | Sin uso directo documentado |
| Anthropic | Razonamiento y contexto largo | Precio vigente, caching de prompt, tool use, región | Sin uso directo documentado |
| Google | Gemini y Vertex AI | Precio vigente, cuotas, región, grounding | Sin uso directo documentado |
| Groq | Modelos abiertos con baja latencia | Precio vigente, catálogo de modelos, límites del tier | Wenuke usa `llama-3.1-70b-versatile` (`Wenuke/backend/config.py:10`) |
| OpenRouter | Router multi-proveedor | Precio vigente, catálogo rotativo, rate limits, política de datos | AgroVoz usa `openrouter/free` (`AgroVoz/backend/app/core/config.py:136-147`) |
| Local (llama.cpp/Ollama) | Privacidad y costo marginal cero | Hardware, RAM, latencia, calidad, operación | AgroVoz, copiloto y ManttoAI tienen un camino local |

Dos cifras documentadas por los proyectos, con su alcance: Wenuke registra
"$0.59/M tokens" para Groq (`Wenuke/docs/ARCHITECTURE.md:71`), sin fecha de
cotización ni verificación externa; copiloto enlaza la página de precios de
DeepSeek y aclara que no fue verificada (`copiloto-recepcion docs/costos.md:11`).
Ninguna es una tarifa vigente certificada por este manual: el resto se compara
por criterios y se cotiza al momento de decidir.

---

## 10.6 Presupuestos y cuotas

Un presupuesto sin límite duro es una intención. El límite duro se aplica en
código, antes de llamar al modelo, y devuelve un error o un fallback explícito.

| Ámbito | Límite de ejemplo | Dónde se aplica | Señal |
|---|---|---|---|
| Turno | `max_tokens`, `max_steps`, timeout | Cliente LLM y orquestador | Respuesta truncada o fallback |
| Conversación | Turnos, tokens y tool calls | Sesión | Handoff o menú determinista |
| Usuario/día | Mensajes o tokens | Rate limit por identidad | `429` con `Retry-After` |
| Canal/hora | Mensajes por número o por IP | Gateway o middleware | `429` y alerta |
| Tenant/mes | Gasto o tokens acumulados | Contabilidad por tenant | Alerta al 80%, corte al 100% |
| Global/mes | Gasto total | Presupuesto de la organización | Kill switch |

Un ejemplo de política, no un estándar: 12 turnos y 15.000 tokens por
conversación; 30 mensajes por usuario/día; USD 50 por tenant/mes; USD 500
globales/mes con alertas al 50%, 80% y 100%. Se calibran con el costo medido.
copiloto acota la demo a 30 mensajes por sesión, 20/min por IP y 300/h global
(`copiloto-recepcion copiloto/src/copiloto/config.py:68-75`;
`copiloto-recepcion docs/demo-api.md:33-85`); AgroVoz limita el chat a 5/min y el clima a 30/min
(`AgroVoz/backend/app/core/config.py:166-171`).

El **kill switch** debe ser una bandera de configuración, no un despliegue:
apaga la IA, sirve el camino determinista y deja el sistema respondiendo.
copiloto ya tiene esa propiedad: sin `LLM_API_KEY` o con `AI_MODE=off` sigue
guiado (`copiloto-recepcion copiloto/src/copiloto/config.py:149-152`). El
procedimiento de activación y rollback está en el [Capítulo 11](11-despliegue.md).

Rate limit y presupuesto no son lo mismo. Un límite de 1.500 requests/hora
protege la disponibilidad, pero no impide que un usuario gaste el presupuesto
mensual en una tarde. ManttoAI tiene límite global y ningún rate limit por
endpoint de chat ni presupuesto por usuario (`ManttoAI
backend/app/middleware/rate_limit.py:71-84`; `ManttoAI/backend/app/routers/chat.py:88-109`).

---

## 10.7 Economía unitaria

La economía unitaria responde cuánto cuesta entregar una unidad de valor: una
conversación, un ticket resuelto, un usuario activo, una hectárea monitoreada,
un equipo o una habitación. El numerador es el costo del período; elegir bien el
denominador importa más que la precisión del cálculo.

```text
Costo variable unitario = V_período / Q_unidades
Costo total unitario    = (F_período + V_período) / Q_unidades
Margen bruto            = (Precio - Costo variable unitario) / Precio
Punto de equilibrio     = F_período / (Precio - Costo variable unitario)
Costo por resultado     = Costo total / Resultados resueltos
```

`Costo por resultado` usa resultados, no intentos: una conversación que se
deriva o falla también costó y debe repartirse entre los casos que sí se
resolvieron. Si solo se divide por los exitosos, el número se ve mejor de lo que
es.

**Ejemplo aritmético ilustrativo.** Las tarifas son supuestos, no precios de
ningún proveedor; reemplázalas por tu precio vigente.

Supuestos: 1.000 conversaciones/mes; 4 turnos por conversación; 1.500 tokens
de entrada (900 cacheados) y 200 de salida por turno; tarifas supuestas USD
1,00/M de entrada, USD 0,25/M cacheada y USD 4,00/M de salida; USD 0,00085 por
turno de overhead (tools, retrieval, canal); USD 20 de costo fijo mensual.

```text
C_turno = (600 × 1,00 + 900 × 0,25 + 200 × 4,00) / 1.000.000 + 0,00085
        = 0,001625 + 0,00085 = 0,002475 USD
C_conversación = 4 × 0,002475 = 0,0099 USD
C_total_mes = 1.000 × 0,0099 + 20 = 29,90 USD
C_por_conversación_total = 29,90 / 1.000 = 0,0299 USD
```

| Resultado | Valor |
|---|---|
| Costo variable mensual | USD 9,90 |
| Costo por conversación (variable) | USD 0,0099 |
| Costo por conversación (con fijo) | USD 0,0299 |
| Margen bruto a precio USD 0,06 | 83,5% |
| Punto de equilibrio | 399 conversaciones/mes |

Sin caché, la entrada costaría 1.500 unidades en vez de 825 y la línea de
tokens subiría cerca de 29% en este ejemplo. Ese es el tipo de afirmación que
solo se puede hacer con supuestos explícitos: "ahorra 29%" sin decir de qué
tarifa, qué proporción de prefijo y qué tasa de acierto no significa nada.

El punto de equilibrio se calcula sobre el margen de contribución, no sobre el
margen bruto contable. Si el precio es CLP 600 y el costo variable es CLP 12,
cada conversación aporta CLP 588 a los fijos. Con CLP 500.000 de fijos, el
equilibrio son 851 conversaciones/mes. Cambiar el precio o el volumen mueve el
resultado más que optimizar unos pocos tokens.

---

## 10.8 Costos ocultos

| Costo oculto | Cómo aparece | Cómo se mide |
|---|---|---|
| Reintentos | Una llamada falla por 429/5xx y se repite; el primero ya se pagó | `retry_rate × costo del intento` |
| Tool calls | Cada tool es otra generación con prompt más largo | Round-trips por turno y tokens por round-trip |
| Embeddings | Indexar documentos y consultar; reindexar al cambiar el corpus | Costo por documento y por query |
| Almacenamiento | Base, adjuntos, backups, índices vectoriales | GB-mes y crecimiento mensual |
| Logs y trazas | Volumen, retención y exportación a un proveedor | GB-mes y costo de ingesta |
| Egress | Tráfico de salida, sobre todo en self-hosted | GB transferidos |
| WhatsApp | Conversaciones de servicio vs marketing, plantillas y calidad del número | Precio vigente por categoría y país |
| STT/TTS | Minutos de audio, no tokens; en local es CPU | Minutos y costo de CPU/energía |
| Cold starts | El primer request tarda; el usuario reintenta o abandona | Latencia p95 y tasa de abandono |
| Tiempo de ingeniería | Mantener prompts, evals, modelos y guardrails | Horas/mes del equipo |
| Evals | Llamadas al juez, revisión humana y datasets | Costo por corrida y por caso |
| Soporte | Handoffs, incidentes y reclamos | Minutos de persona por conversación |

Los tres últimos suelen ser los más grandes en un piloto y los únicos que no
aparecen en la factura del proveedor. Un agente "barato" que exige dos horas
semanales de ajuste de prompt y una persona revisando derivaciones puede costar
más que uno caro que casi nunca se toca.

---

## 10.9 Evidencia real de los cuatro proyectos

| Proyecto | Escenario y fecha | Costo fijo | Costo variable | Unidad declarada | Cita |
|---|---|---|---|---|---|
| AgroVoz | Piloto con VPS propio; tipo de cambio jul-2026 | CLP 14.364/mes | ~CLP 0 por agricultor | 20 consultas/usuario/mes como supuesto | `AgroVoz/docs/negocio/07-estructura-de-costos.md:13-34`, `:36-38` |
| copiloto-recepción | Escenario EVA2, supuesto no cotización; sin fecha en el repo | CLP 90.000/mes | M + tokens; ~2.500 tokens por conversación de reserva en la prueba | Costo por consulta en `/metricas` | `copiloto-recepcion docs/costos.md:11-22`; `copiloto/src/copiloto/metrics.py:72-84` |
| ManttoAI | Plan comercial may-2026, nota de vigencia ago-2026 | CLP 187.100/mes | No desagregado | Precio CLP 88.000/mes por rubro | `ManttoAI/docs/costos/12-plan-gestion-costos.md:64-74`, `:123-125`; `ManttoAI/docs/costos/13-estimacion-costos-detallada.md:40` |
| Wenuke | MVP serverless; sin fecha de cotización en el repo | USD 0–10/mes | Groq por token; USD 0,59/M sin verificación externa | No declarada | `Wenuke/README.md:40`; `Wenuke/docs/ARCHITECTURE.md:71,79` |

**No son comparables directamente.** AgroVoz mide infraestructura y excluye
sueldos; separa el equilibrio de infraestructura (29 usuarios a CLP 500) del
equilibrio con retiro de socios (~985 usuarios) (`AgroVoz
docs/negocio/07-estructura-de-costos.md:46-54`). copiloto usa un supuesto
académico de CLP 90.000, no una cotización (`copiloto-recepcion docs/costos.md:22`).
ManttoAI mezcla infraestructura con contador, abogado y domicilio comercial
(`ManttoAI/docs/costos/12-plan-gestion-costos.md:64-74`). Wenuke estima
infraestructura y no mide tokens (`Wenuke/README.md:40`). Fechas, monedas y
alcances distintos: la tabla da órdenes de magnitud, no un ranking.

Lo que enseña cada uno: en AgroVoz el margen cero depende de que el modelo local
aguante latencia y calidad; en copiloto la IA es opcional y el costo por consulta
se calcula (`copiloto-recepcion copiloto/src/copiloto/metrics.py:84`); en
ManttoAI el modelo local no cabe en el hosting gratuito (`ManttoAI
render.yaml:52-53`); en Wenuke el precio bajo no sustituye la medición
(`Wenuke/README.md:40`).

---

## 10.10 Cómo medir

| Métrica | Fórmula | Dónde vive | Para qué |
|---|---|---|---|
| Tokens por turno | `input_tokens + output_tokens` (con cached aparte) | Cliente LLM o respuesta del proveedor | Dimensionar prompt y salida |
| Cache hit rate | `cached_input_tokens / total_input_tokens` | Log del proveedor o gateway | Verificar que el prefijo es estable |
| Costo por turno | Fórmula de 10.1 con la tarifa vigente | Agregación de trazas | Detectar turnos anómalos |
| Costo por conversación | Suma de turnos + sesión + handoff | Tabla de conversaciones | Economía unitaria |
| Costo por tenant | Suma del costo de las conversaciones del tenant en el mes | Contabilidad por tenant | Cuota y margen por cliente |
| Costo de fallback | Costo de intentos que terminaron en fallback / costo total | Traza con `outcome` | Cuantificar desperdicio |
| Tasa de reintento | `reintentos / llamadas` | Cliente LLM | Detectar 429, timeouts o prompts frágiles |
| Tool calls por turno | `Σ tool_calls / turnos` | Orquestador | Explicar el costo que no es token |
| Costo por resultado | `costo total / resultados resueltos` | Cruce de costo y negocio | Precio y punto de equilibrio |

copiloto ya expone `ai_tokens`, `ai_tools` y `cost_per_query_clp` desde eventos
(`copiloto-recepcion copiloto/src/copiloto/metrics.py:22`, `:43`, `:84`, `:91`).
ManttoAI expone `fuente` pero no mide tokens (`ManttoAI
backend/app/services/chat_service.py:61-88`); Wenuke devuelve `offline` pero no
registra consumo (`Wenuke/backend/llm.py:130-159`). El costo es un atributo de
la traza, no un reporte aparte: eso se detalla en el [Capítulo
9 — Observabilidad](09-observabilidad.md). OpenTelemetry estandariza la captura
con `gen_ai.client.token.usage`, `gen_ai.usage.input_tokens` y
`gen_ai.usage.output_tokens`
(https://github.com/open-telemetry/semantic-conventions-genai, estado
Development 2026-10, consultado 2026-11-04); el contenido no se captura por
defecto, por privacidad y costo de almacenamiento.

---

## 10.11 Anti-patrones

**Mirar solo el precio por millón.** Es la parte visible y la menos decisiva. Un
modelo con salida larga, tres tools y reintentos puede costar más que uno con
precio por token mayor y una sola llamada.

**Ignorar reintentos y tools.** Cada tool es otra generación y cada reintento
duplica el intento; sin `max_steps`, un loop consume el presupuesto en una
conversación. AgroVoz limita a 3 iteraciones (`AgroVoz
backend/app/services/llm_service.py:127`) y copiloto a 5 (`copiloto-recepcion
copiloto/src/copiloto/ai/agent.py:19`).

**No medir.** Si no se registran tokens, tools y `outcome`, la primera señal es
la factura. Para entonces ya se pagó el mes. La métrica mínima es costo por
turno y por conversación con fecha y modelo.

**No presupuestar.** Un límite global de requests no protege el presupuesto de
un usuario ni de un tenant. Sin cuota por identidad y por mes, un abuso o un bug
gasta lo que haya. El límite duro se aplica antes de la llamada.

**Usar el modelo grande para todo.** Clasificar, extraer y responder FAQ con el
modelo más caro es pagar razonamiento que no se usa. La tabla de decisión de
10.2 existe para evitarlo.

**Comparar prototipo con producción.** ManttoAI costó USD 98 en hardware y VPS;
su plan comercial declara CLP 187.100/mes (`ManttoAI
docs/costos/12-plan-gestion-costos.md:123-125`, `:64-74`). copiloto costó $0;
su escenario EVA2 declara CLP 90.000/mes (`copiloto-recepcion docs/costos.md:3-22`).
Una prueba de concepto no incluye soporte, evals, personas ni crecimiento.

**Optimizar antes de medir.** Recortar historial, cachear o bajar tokens sin
línea base puede ahorrar poco y romper la calidad. Primero se mide el turno
típico y el p95; después se ataca la línea más grande.

---

## 10.12 Checklist de 12 puntos antes de lanzar

- [ ] 1. Separo costo fijo y variable, con una fuente y una fecha por cada línea.
- [ ] 2. Calculo el costo por turno con entrada, salida, tools y retrieval.
- [ ] 3. Defino costo por conversación y costo por resultado resuelto.
- [ ] 4. Elijo el modelo por tarea y tengo una evaluación que lo justifica.
- [ ] 5. Fijo `max_tokens`, `max_steps`, timeout y máximo de turnos en código.
- [ ] 6. Mantengo un prefijo estable y mido el cache hit rate.
- [ ] 7. Trunco o resumo el historial con un límite duro y probado.
- [ ] 8. Las tools devuelven payloads acotados y las apagadas no se anuncian.
- [ ] 9. Tengo cuota por usuario, canal, tenant y día, con `429` y `Retry-After`.
- [ ] 10. Tengo presupuesto mensual con alertas al 50/80/100% y kill switch.
- [ ] 11. Mido reintentos, fallback y gasto desperdiciado, no solo el total.
- [ ] 12. Documento economía unitaria, margen y equilibrio con supuestos y fecha.

---

## Cierre

El costo de un agente se decide en el diseño del turno: qué modelo, cuántos
pasos, qué tools, qué historial y qué pasa cuando algo falla. La factura solo
confirma esa decisión. Un sistema con costo por turno medido, presupuesto con
límite duro y un camino determinista de respaldo puede crecer sin sorpresas;
uno que solo mira el precio por millón está apostando a que nada falle.

## Siguiente lectura

- [Capítulo 9 — Observabilidad](09-observabilidad.md): tokens, tools y `outcome` en la traza.
- [Capítulo 11 — Despliegue](11-despliegue.md): flags, kill switch y rollback.
- [Capítulo 12 — Arquitecturas](12-arquitecturas.md): routing, cascadas y multi-tenant.
- [Capítulo 14 — Plantillas](14-plantillas.md): hoja de costos y política de cuotas.

## Referencias verificadas

- `AgroVoz/docs/negocio/07-estructura-de-costos.md:13-34` — costo fijo CLP 14.364/mes, marginal ~0 y tabla por usuarios; `:36-38` — supuesto de 20 consultas/usuario/mes; `:46-54` — equilibrio; `:60-74` — riesgo Open-WA y API oficial.
- `AgroVoz/docs/negocio/04-solucion-y-stack.md:31-38` — estimación de US$400-580/mes con APIs comerciales para 1.500 consultas/mes.
- `AgroVoz/docs/ARCHITECTURE-DECISIONS.md:100-108` — costos de privacidad y rate limits de `openrouter/free`; `:223-227` — 809 caracteres de prefijo por anunciar tools apagadas.
- `AgroVoz/backend/app/services/llm_service.py:127-159` — máximo de iteraciones, presupuesto de 10 s, circuit breaker y `n_ctx`; `:762-795` — tools por intención; `:799-809` — tools ocultas por gate.
- `AgroVoz/backend/app/services/llm_worker.py:182-186` — `temperature=0.0`, `max_tokens=command.max_tokens`; `backend/app/core/config.py:136-147` — OpenRouter, salida 120 tokens y deadlines.
- `AgroVoz/backend/app/services/prompt_builder.py:88-103` — ensamblado estable del system prompt.
- `copiloto-recepcion docs/costos.md:3-22` — prototipo $0, DeepSeek por token, ~2.500 tokens por reserva, CLP 90.000/mes y fórmula de costo por consulta.
- `copiloto-recepcion copiloto/src/copiloto/metrics.py:72-84` — `fixed_monthly_clp`, `usage_m_clp` y `cost_per_query_clp`; `:22`, `:43`, `:91` — tokens y tools por evento.
- `copiloto-recepcion copiloto/src/copiloto/config.py:68-75` — 12 mensajes de historial y límites de demo; `:149-152` — `ai_active` y modo guiado sin clave.
- `copiloto-recepcion copiloto/src/copiloto/ai/llm.py:47-50` — `max_tokens=500`, `temperature=0.3`, `stream=False`; `ai/agent.py:19` — `MAX_STEPS=5`; `ai/sessions.py:9-22` — `MAX_TEXT=1200` y recorte de historial.
- `copiloto-recepcion docs/caso-de-estudio.md:112` — latencia local ~18 s vs 0,3 s del flujo guiado.
- `ManttoAI/docs/costos/12-plan-gestion-costos.md:64-74` — costo operacional CLP 187.100/mes; `:123-125` — prototipo USD 98; `:10-21` — nota de vigencia; `docs/costos/13-estimacion-costos-detallada.md:40` — precio CLP 88.000/mes por rubro.
- `ManttoAI/backend/app/config.py:132-134` — `qwen2.5:0.5b`; `backend/app/services/chat_service.py:143-156` — payload Ollama, `num_predict=250`, `temperature=0.2`, timeout 60 s.
- `ManttoAI/render.yaml:52-53` — `OLLAMA_URL` vacío en el deploy público; `ManttoAI/docs/auditoria/deploy.md:59` — Ollama de 800 MB excede los 512 MB del tier.
- `ManttoAI/backend/app/middleware/rate_limit.py:71-84` — límite global 1.500/h en producción.
- `Wenuke/README.md:40` — costo operativo USD 0–10/mes; `docs/ARCHITECTURE.md:71,79` — Groq USD 0,59/M tokens y estimado operativo.
- `Wenuke/backend/llm.py:130-159` — fallback offline y contrato `respuesta`/`offline`; `:144-152` — `max_tokens=500`, `temperature=0.3`.
- `Wenuke/backend/config.py:20` — TTL de caché 3.600 s; `backend/clima.py:29-41` — coordenadas redondeadas y caché; `backend/odepa.py:57-62` — caché de 6 h.
- OWASP GenAI LLM Top 10 2026, LLM06 Unbounded Consumption, https://genai.owasp.org/llm-top-10/, publicado 2026-08-04, consultado 2026-11-04.
- OpenTelemetry GenAI Semantic Conventions, https://github.com/open-telemetry/semantic-conventions-genai, estado Development 2026-10, consultado 2026-11-04.
- OpenTelemetry, “Inside the LLM Call: GenAI Observability with OpenTelemetry”, https://opentelemetry.io/blog/2026/genai-observability/, consultado 2026-11-04.
- Anthropic, “Building effective agents”, https://www.anthropic.com/research/building-effective-agents, 2024-12-19, consultado 2026-11-04.
- DeepSeek, precios, https://api-docs.deepseek.com/quick_start/pricing, enlazado por `copiloto-recepcion docs/costos.md:11`; no verificado en este manual.
