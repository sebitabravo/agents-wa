<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Capítulo 5 — Datos y RAG: corpus versionado, TF-IDF local frente a API en vivo

> **Tipo:** how-to (tarea) con explicación mínima del porqué.
> **Audiencia:** desarrolladores que agregan conocimiento factual a un agente.
> **Meta:** al terminar, decides si un dato va a un corpus YAML o a una API en
> vivo, y lo sirves con frescura verificable.

El patrón transversal de los cuatro proyectos es el mismo: **ninguno usa una
base vectorial pesada**. AgroVoz recupera con TF-IDF sobre YAML, copiloto
responde con coincidencia de palabras clave sobre `hotel.yaml`, Wenuke evalúa
umbrales contra la API viva de OpenMeteo sin RAG, y ManttoAI inyecta un resumen
del dashboard en el prompt. AgroVoz conserva la fecha de la fuente en el corpus
y copiloto el sello de hora del PMS; Wenuke marca `offline: true` y ManttoAI no
adjunta fuente ni fecha.

## 1 — Decidir: corpus estático frente a API en vivo

La primera decisión no es tecnológica, es sobre la naturaleza del dato.
Si el dato cambia por minuto o por transacción, pertenece a una API.
Si es factual y estable durante semanas, pertenece a un corpus versionado.

| Dato | Destino | Evidencia |
|------|---------|-----------|
| Precios ODEPA del boletín de junio de 2026 | Corpus YAML + TF-IDF | `AgroVoz/backend/corpus/odepa_papa.yaml:8-16`, `AgroVoz/backend/app/services/rag_service.py:1-5` |
| Datos del hotel, políticas, FAQ | YAML + coincidencia de palabras clave | `copiloto/src/copiloto/hotel.py:51` (`match_faq`), `copiloto/src/copiloto/ai/tools.py:73` (specs) |
| Pronóstico horario, lluvia, viento | API viva OpenMeteo, sin RAG | `backend/reglas.py:173` (`evaluar_reglas`), `backend/clima.py:13` |
| Disponibilidad y precios de habitaciones | PMS en cada turno | `copiloto/src/copiloto/ai/tools.py:190` (`_availability`) |
| Estado operativo de equipos | Resumen del dashboard inyectado | `backend/app/services/chat_service.py:90` (`consultar_ollama`), `backend/app/routers/chat.py:90` |

Regla práctica: si el dato tiene fecha de emisión oficial (boletín, tarifa
publicada, política firmada), va al corpus con su fecha. Si el dato depende de
la hora actual (clima, cupos, telemetría), se lee de la API en cada turno y se
rotula con su hora de lectura. Mezclar ambos caminos es un error común: servir
un precio de boletín de hace tres meses como si fuera cotización de hoy.

## 2 — Formato YAML versionado

El corpus es un conjunto de archivos YAML con revisión humana, no un volcado
automático. Cada documento declara quién lo emitió y cuándo; el manifiesto de
fuentes añade hasta cuándo es válido. Este es el formato real de AgroVoz en
`backend/corpus/odepa_papa.yaml:8`:

```yaml
documentos:
  - titulo: "Boletín de la papa, junio 2026"
    fuente: "ODEPA — Boletín de la papa"
    fecha: "junio 2026"
    url: "https://www.odepa.gob.cl/publicaciones/boletines/boletin-de-la-papa-junio-2026"
    chunks:
      - texto: >
          El precio promedio mensual para mercado mayorista de la papa
          en mayo 2026 disminuyó 2,1% respecto al mes anterior,
          llegando a $9.890 por saco de 25 kilos con IVA incluido.
```

El manifiesto declara `verificado_el` y `revisar_antes_de`
(`AgroVoz/backend/corpus/fuentes_datos.yaml:19-20`); el validador los exige por
fuente (`AgroVoz/backend/app/services/data_hub_service.py:190-194`). El cargador
legacy, en cambio, los lee como opcionales (`rag_service.py:113-126`) y `odepa_papa.yaml` no los declara: por eso
el formato mostrado arriba es el mínimo documental, no un corpus con sellos. Si
el manifiesto existe y no valida, el RAG queda vacío en lugar de servir hechos
sin procedencia (`backend/app/services/rag_service.py:224-233`).

Copiloto aplica la misma idea a menor escala: cada nodo de `data/hotel.yaml`
(raíz del repo, no `copiloto/data/`) lleva `source` y `status`
(`verificado | pendiente_validar`), y los conflictos conocidos se declaran en el
propio archivo en vez de ocultarse (`data/hotel.yaml:14-20`, direcciones en
disputa Km 12.5 frente a Km 2.5). Los precios y el horario de turno se marcan
como simulados o por validar (`data/hotel.yaml:1-3`).

Campos del formato:

- `titulo`, `fuente`, `fecha`: identificación y fecha de emisión de la fuente.
- `url` o `fuente_url`: enlace verificable por el usuario.
- `chunks`: lista de textos factuales cortos, sin recomendaciones mezcladas.
- `verificado_el` y `revisar_antes_de`: obligatorios por fuente en el manifiesto;
  el cargador legacy los admite ausentes y entonces no aplica vencimiento.

## 3 — Pipeline TF-IDF mínimo (sin vectores densos)

Para un corpus de decenas de documentos, TF-IDF con similitud coseno supera en
precisión a los embeddings en términos exactos del dominio (precios, "papa",
"Traiguén", "ODEPA") y responde en menos de 2 ms en CPU, según el propio
módulo (`backend/app/services/rag_service.py:14-16`). La configuración real es:

```python
self._vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    stop_words=_SPANISH_STOP_WORDS,
    lowercase=True,
    strip_accents="unicode",
)
```

Tres decisiones merecen atención. Primera, `ngram_range=(1, 2)` captura
bigramas como "precio papa" o "ferias libres" (`rag_service.py:277-280`).
Segunda, scikit-learn solo trae stop words en inglés, así que el proyecto
mantiene una lista manual en español (`rag_service.py:44-77`). Tercera, el
ranking es determinista ante empates (`np.argsort` con `kind="stable"`,
`rag_service.py:336-341`), requisito para respuestas reproducibles y pruebas
estables.

El retrieval devuelve como máximo 3 chunks (`_TOP_K = 3`) y descarta todo lo
que puntúe bajo `_MIN_SCORE = 0.05`:

```python
query_vec = self._vectorizer.transform([query.strip()])
scores = cosine_similarity(query_vec, self._tfidf_matrix)[0]
```

Cada resultado conserva su procedencia (`text`, `source`, `date`, `title`,
`source_url`, `score`), de modo que la capa de respuesta puede citar fuente y
fecha sin pasos adicionales (`rag_service.py:343-360`).

Por debajo de TF-IDF existe un nivel cero válido: la coincidencia de palabras
clave. Copiloto puntúa cada FAQ por cantidad de palabras clave presentes y
desempata por la palabra más larga (`hotel.py:51-62`); ManttoAI prueba primero
su diccionario `REGLAS_MANTENIMIENTO` y solo si nada coincide delega a Ollama
(`chat_service.py:61-87`). Usa palabras clave cuando el corpus cabe en un
archivo y las preguntas son previsibles; sube a TF-IDF cuando el vocabulario
crece o las consultas usan sinónimos que las palabras clave no cubren.

## 4 — TTL y frescura: cada dato declara su edad

Un dato sin edad es un dato inventado a medias. La frescura se marca en tres
lugares: caché con TTL, vencimiento del corpus y sello en la respuesta.

Wenuke cachea el pronóstico horario en memoria con TTL de una hora
(`Wenuke/backend/config.py:20`, `cache_ttl_segundos: int = 3600`) y el histórico con
24 veces ese TTL (`backend/clima.py:113-118`). Si OpenMeteo falla, sirve el
caché vencido como fallback antes que inventar un pronóstico
(`Wenuke/backend/clima.py:61-66`). Los precios de referencia de ODEPA se cachean
6 horas (`backend/odepa.py:58-62`). A nivel HTTP, los endpoints climáticos
envían `Cache-Control` con 1 hora de caché y 10 minutos de
stale-while-revalidate (`backend/main.py:206-209`).

La frescura también se aplica al corpus: `revisar_antes_de` vencido excluye el
chunk en la carga, tanto en el formato histórico como en el manifiesto Data Hub
(`rag_service.py:113-124`, `rag_service.py:205-206`). Y varias respuestas vivas
exponen su referencia temporal: la disponibilidad del PMS se devuelve con sello
de lectura (`tools.py:190-199`), el pronóstico se evalúa punto por punto con su
día y hora (`reglas.py:189-194`), y el contexto de ManttoAI se reconstruye del
dashboard en cada llamada a `consultar_ollama` en lugar de reutilizar un
resumen viejo (`chat_service.py:94-96`).

| Fuente | TTL / vigencia | Qué pasa al vencer |
|--------|----------------|--------------------|
| Pronóstico OpenMeteo (horario) | 1 h en memoria | Sirve caché vencido, luego error |
| Histórico OpenMeteo | 24 h en memoria | Sirve caché vencido, luego error |
| Precios ODEPA (Wenuke) | 6 h en memoria | Usa `PRECIOS_REFERENCIA` (fuente `referencia`), luego error |
| Chunk de corpus AgroVoz | `revisar_antes_de` | Se excluye de la carga |
| Disponibilidad PMS | Por lectura (sello `read_at`) | Nueva lectura por turno |
| Contexto dashboard ManttoAI | Por llamada | Se reconstruye siempre |

La bandera `offline` distingue el motor que respondió: Wenuke retorna
`offline: true` cuando responde el banco offline en lugar de Groq
(`Wenuke/backend/llm.py:131-133`), y su contrato OpenAPI lo documenta como campo
obligatorio (`backend/openapi.yaml:1035-1044`). Eso no indica si el dato de
fondo vino de caché; el TTL y el sello de lectura cubren esa parte. El contrato
del prompt y su variante degradada están en el [Capítulo 3](03-system-prompts.md);
el uso por canal, en el [Capítulo 6](06-canales-memoria.md).

## 5 — Ejemplo bueno frente a ejemplo malo

**Malo:** respuesta sin procedencia ni fecha. Nada de esto es verificable, y el
precio podría venir de un boletín de hace un año o de la imaginación del modelo:

```text
User: ¿A cuánto está la papa en ferias?
Bot:  La papa está a $700 el kilo aproximadamente.
```

**Bueno:** la misma respuesta con fuente, fecha y estado del motor. El usuario
puede abrir el boletín y el operador puede auditar el chunk servido:

```python
result = rag_corpus.search("precio de la papa en ferias")
# [{"text": "el precio promedio por kilo durante mayo 2026 en ferias ...",
#   "source": "ODEPA — Boletín de la papa", "date": "junio 2026",
#   "source_url": "https://www.odepa.gob.cl/...", "score": 0.42}]
```

```text
User: ¿A cuánto está la papa en ferias?
Bot:  Según ODEPA, Boletín de la papa de junio 2026: $700 por kilo
      promedio en ferias de la Región Metropolitana durante mayo 2026.
      [offline: false · fuente: ODEPA, junio 2026]
```

Cuando no hay match (score bajo el umbral o corpus vacío), el camino correcto
es el del capítulo 1: fallback explícito, nunca relleno. Copiloto lo implementa
literalmente: sin FAQ coincidente, devuelve `sin_respuesta` con la instrucción
de admitirlo y ofrecer derivación (`tools.py:174-176`).

## Lista de verificación

- [ ] Cada fuente del manifiesto declara `verificado_el` y `revisar_antes_de`;
      cada documento declara `titulo`, `fuente`, `fecha`, `url` y `chunks`.
- [ ] Los chunks vencidos se excluyen en la carga, no en el ranking.
- [ ] El retrieval devuelve como máximo 3 resultados con score sobre el umbral
      y conserva `source`, `date` y `source_url`.
- [ ] Los datos vivos (clima, PMS, dashboard) se leen por turno; el PMS expone
      sello de lectura y el pronóstico se evalúa con día y hora; los TTL están documentados.
- [ ] Toda respuesta con datos cita fuente y fecha, o declara `offline: true`.
- [ ] Sin match no hay improvisación: fallback explícito o derivación.
