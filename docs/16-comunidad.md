<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Capítulo 16 — Comunidad, versionado y contribución

> **Tipo:** explanation (por qué una guía abierta se sostiene en evidencia y versiones) + how-to (cómo usarla, adaptarla, citarla y contribuir).
> **Audiencia:** equipos que adoptan la guía, autores de casos de estudio, mantenedores de documentación, revisores técnicos y cualquier persona que quiera corregir o extender el manual.
> **Meta:** al terminar, puedes adaptar la guía a otro stack sin romper sus invariantes, proponer un cambio con evidencia verificable, versionarlo y citarlo sin ambigüedad.

## La respuesta primero

**Un estándar sirve si se puede citar, discutir y mejorar; si no, es una opinión con formato.**

Esta guía no es una norma formal, una certificación ni un framework. Es un conjunto de decisiones verificadas en cuatro proyectos reales: AgroVoz, copiloto-recepción, ManttoAI y Wenuke. Lo que la vuelve útil no es la prosa, sino que cada afirmación se puede rastrear hasta un archivo, una línea, una URL o una salida de comando. Lo que la vuelve un estándar es que otra persona puede discutirla con la misma evidencia y proponer una mejora.

| Pregunta | Respuesta corta |
|---|---|
| ¿Qué es esta guía? | Un conjunto de invariantes, plantillas y criterios de evidencia, no una norma ISO. |
| ¿Qué la hace estándar? | Que sus reglas se pueden auditar, citar y refutar con evidencia. |
| ¿Qué puedo copiar? | Las ideas y los invariantes; el código, solo si su licencia lo permite. |
| ¿Cómo la mejoro? | Con un caso, una corrección o una fuente; no con una opinión. |

> **Estado de gobernanza:** este manual no tiene todavía un comité, un release etiquetado ni un canal oficial de discusión. El proceso de este capítulo es una **propuesta** para cuando el repositorio se abra a contribuciones externas. Lo que ya existe es el método de evidencia del manual.

## Qué es esta guía y qué no es

Un manual escrito desde cuatro proyectos tiene una ventaja y un límite. La ventaja: las decisiones no salieron de una pizarra, salieron de código que se ejecutó, falló y se corrigió. El límite: cuatro proyectos no son una muestra representativa de la industria. Por eso la guía distingue tres tipos de afirmación:

| Tipo | Cómo se reconoce | Ejemplo |
|---|---|---|
| **Hecho verificado** | Lleva `path:line` o URL con fecha de consulta. | Una whitelist de 19 tools en AgroVoz (`backend/app/services/llm_service.py:81-103`). |
| **Recomendación de esta guía** | Se declara como tal y no se atribuye a una fuente. | Empezar por fail-closed antes que por tools. |
| **Límite declarado** | Dice qué no se probó y por qué. | No se ejecutaron las suites durante la exploración. |

Si una afirmación no cae en ninguna de las tres categorías, no debería estar en el manual. Esa es la regla editorial que sostiene todo lo demás.

## Cómo usar la guía

### Rutas por rol

La tabla canónica de rutas por rol vive en el [Capítulo 0](00-introduccion.md#cómo-leer-esta-guía-según-tu-rol). Este capítulo no la duplica para evitar que las rutas deriven.

### Cuánto tiempo tienes

| Tiempo | Qué leer | Qué debes producir |
|---|---|---|
| **1 hora** | [0](00-introduccion.md), [1](01-principios-fail-closed.md) y la síntesis del [13](13-casos-de-estudio.md). | Una frase con tu nivel N0-N5, tu fallback y la acción irreversible que no vas a automatizar. |
| **1 día** | Bloques de fundamentos y datos: [0](00-introduccion.md) a [6](06-canales-memoria.md), más [13](13-casos-de-estudio.md). | Un esqueleto ejecutable con una regla, una tool de lectura, un fallback y tres evals. |
| **1 semana** | El manual completo, los apéndices disponibles y una plantilla adaptada a tu caso. | Un documento de arquitectura, un set de evals y un runbook revisados por otra persona. |

El orden de lectura no es el orden de los archivos: primero el canal y el fallback, después los datos, luego las tools y al final el prompt.

## Cómo adaptarla a otro stack

### Lo que no se negocia

Los invariantes no dependen de FastAPI, de Python ni de Chile. Si cambias el lenguaje, el proveedor del modelo o el canal, estos controles siguen siendo exigibles.

La lista canónica de los 10 invariantes, con evidencia en los cuatro proyectos y capítulo dueño de cada uno, está en el [Capítulo 0](00-introduccion.md#los-10-invariantes-del-estándar). Esta tabla no la redeclara: recoge los controles que sobreviven a un cambio de stack.

| Invariante | Qué significa en cualquier stack | Cómo se verifica |
|---|---|---|
| **Fail-closed** | Sin dato verificado no hay respuesta con datos; hay un fallback constante. | Un test que fuerza el fallo y compara el texto exacto. |
| **Validación en servidor** | Fechas, permisos, montos y cupos se validan en código, no en el prompt. | Un test por regla, con un payload inválido que debe ser rechazado. |
| **Whitelist de tools** | El modelo solo puede invocar tools declaradas y habilitadas. | Una tool fuera de la lista devuelve un error controlado. |
| **Frescura y procedencia** | Cada dato declara fuente, fecha y vigencia. | Un dato vencido no aparece en la respuesta ni en el retrieval. |
| **Memoria como presupuesto** | Historial y contexto tienen tope, TTL y consentimiento. | El turno N+1 no crece sin límite ni persiste sin opt-in. |
| **Fallback observable** | La respuesta degradada se marca, se registra y se mide. | El flag y la métrica aparecen en el log y en el dashboard. |
| **Confirmación humana** | Toda escritura irreversible se confirma en un turno distinto. | Un test de doble confirmación y otro de rechazo. |
| **Evals y regresión** | Cada incidente se convierte en un caso reproducible. | El caso falla antes del fix y pasa después. |
| **Límites honestos** | Lo no probado se declara como no probado. | El README y el capítulo listan lo que falta, con fecha. |

### Lo que sí es específico

La guía usa Python y Chile porque los cuatro proyectos lo hacen. Eso es una coincidencia del corpus, no una prescripción: conserva el contrato y cambia la implementación.

| Pieza de la guía | Por qué es específica | Equivalente funcional en Node/TypeScript | Equivalente funcional en Go |
|---|---|---|---|
| FastAPI, Pydantic, `pydantic-settings` | Stack de los cuatro proyectos. | Fastify o Express, Zod para esquemas, validación de entorno al arrancar. | `net/http` o chi, validación explícita, configuración con `envconfig`. |
| `pytest`, `httpx` | Herramientas usadas en los repos. | Vitest o Jest, `fetch` o supertest. | `testing`, `net/http/httptest`. |
| SQLite primero | Decisión operativa, no de lenguaje. | SQLite con `better-sqlite3` o Postgres gestionado. | SQLite con `modernc.org/sqlite` o Postgres. |
| Open-WA | Canal no oficial usado en los demos. | Cloud API oficial de WhatsApp; cualquier bridge no oficial es un riesgo, no un atajo. | El mismo contrato HTTP, sin importar el lenguaje. |
| ES-CL y CLP | Idioma, moneda y normativa del caso chileno. | Cambia el locale, no la arquitectura. | Cambia el locale, no la arquitectura. |

### Otros canales

Cambiar de WhatsApp a Telegram, web, voz o correo no cambia los invariantes del capítulo 6, pero sí cambia el contrato del canal. Antes de escribir código, responde:

- ¿Cuál es el evento de entrada, cómo se autentica y cuál es la clave de idempotencia?
- ¿Qué se responde de inmediato y qué se procesa después?
- ¿Cómo se distingue "generado" de "entregado"?
- ¿Qué mensaje ve el usuario cuando falla y qué se retiene?

Un canal de voz agrega presupuesto de latencia, turnos solapados y consentimiento para grabar. Un canal de correo agrega hilos, adjuntos y respuestas parciales. Ninguno de esos problemas se resuelve con un prompt más largo.

### Otros países

Chile no es el estándar; es el caso de los cuatro proyectos. Al adaptar la guía a otro país, reemplaza las fuentes de datos, la moneda, la zona horaria, el formato de teléfono y la ley de privacidad aplicable. Conserva la disciplina: fuente, fecha, vigencia y fallo cerrado cuando el dato no está. La referencia a la Ley 21.719 es un aviso técnico, no asesoría legal: revisa el marco aplicable con un profesional antes de publicar.

## Versionado de la guía

### Semver para documentación

La guía propone usar versionado semántico adaptado a documentación. No es una norma del proyecto; es una convención para que un lector sepa si un cambio rompe lo que ya implementó.

| Cambio | Bump | Ejemplo |
|---|---|---|
| Se corrige una cita, un enlace o una errata que no cambia la regla. | **PATCH** | Una línea de código se movió y el `path:line` se actualiza. |
| Se agrega un capítulo, un caso, una plantilla o una fuente sin invalidar lo anterior. | **MINOR** | Nuevo caso de estudio con evidencia y límites. |
| Se cambia un invariante, se elimina un capítulo o se invalida una recomendación central. | **MAJOR** | Se retira la regla de "un solo agente" por evidencia en contra. |

Antes de 1.0.0, la convención de SemVer permite cambios incompatibles en versiones menores. Esta edición usa la etiqueta de trabajo **0.1.0-draft** porque el conjunto todavía no está completo ni revisado por una persona externa. El 1.0.0 se declara cuando todos los capítulos, apéndices y plantillas estén publicados y el conjunto haya pasado una revisión de coherencia.

### Metadatos de capítulo

Cada capítulo debería declarar `status`, `version`, `last_reviewed`, `valid_until` y `supersedes` al inicio. Los capítulos actuales no usan ese bloque; se propone para la siguiente edición, no como requisito retroactivo.

### Fecha de revisión y "vigente al"

Una guía con fechas no promete que el mundo no cambie. Promete que alguien volvió a mirar la evidencia en una fecha concreta.

- `last_reviewed` es la fecha en que se verificaron las citas y los enlaces.
- `valid_until` es la fecha después de la cual hay que volver a verificar, no la fecha en que el consejo caduca.
- Las fuentes externas se revisan cada **6 meses**; las citas de código, cada **12 meses** o en el siguiente cambio del repositorio citado.
- Un capítulo vencido pasa a `needs_review`. No se borra ni se marca como falso: se declara desactualizado.

La expresión "vigente al 2026-11-04" significa "la evidencia se consultó en esa fecha". No significa "la arquitectura sigue siendo la mejor para siempre".

### Changelog

El registro de cambios propuesto vive en un `CHANGELOG.md` en la raíz y usa las categorías habituales: `Added`, `Changed`, `Fixed`, `Deprecated`, `Removed`, `Security`. Una entrada por release, no una por commit. Cada entrada dice qué capítulo cambió y por qué. Un changelog que solo lista archivos no sirve para decidir si conviene actualizar.

### Deprecación de capítulos

Un capítulo no se borra cuando deja de ser válido: se depreca. El procedimiento propuesto es:

1. Marcar el capítulo con `status: deprecated` y la versión en que ocurrió.
2. Agregar un aviso al inicio con el capítulo que lo reemplaza.
3. Conservarlo durante un ciclo **MAJOR** completo para no romper enlaces externos.
4. Eliminarlo en el siguiente **MAJOR**, dejando una entrada en el changelog.

```markdown
> **Deprecado en 2.0.0.** Reemplazado por [Capítulo 4](04-orquestacion-tools.md).
> Se conserva hasta 3.0.0 para no romper enlaces externos.
```

## Proceso de contribución

### Flujo propuesto

El proceso tiene cinco etapas. Cada una tiene un criterio de salida; sin ese criterio, el cambio no avanza.

| Etapa | Qué produce | Criterio de salida |
|---|---|---|
| **1. Issue** | Un problema concreto, con ubicación y evidencia inicial. | Se entiende qué está mal y a quién afecta. |
| **2. Propuesta** | Una página con el cambio, su impacto y los capítulos afectados. | El cambio cabe en el alcance del manual. |
| **3. Evidencia** | `path:line`, URL con fecha o salida de comando. | Otra persona puede reproducir la afirmación. |
| **4. Revisión** | Comentarios de al menos una persona que no escribió el cambio. | Los comentarios están resueltos o justificados. |
| **5. Integración** | El cambio en la rama principal y la entrada de changelog. | El capítulo cumple su Definition of Done. |

### Estándar de evidencia

| Afirmación | Evidencia mínima | Qué la invalida |
|---|---|---|
| Comportamiento de un proyecto | `path:line` relativo a la raíz del proyecto, con fecha o commit. | La línea ya no existe o dice otra cosa. |
| Fuente externa | URL, fecha de publicación y fecha de consulta. | El enlace devuelve 404 o el contenido cambió. |
| Cifra de tests, latencia o costo | Salida del runner o documento fechado; nunca copiada a mano entre archivos. | No tiene fecha ni comando que la reproduzca. |
| Comportamiento en runtime | Log o traza con `request_id`, no una inferencia. | No se puede reproducir ni con el mismo payload. |
| Opinión del autor | La etiqueta **recomendación de esta guía**. | Se presenta como hecho o como norma. |
| Afirmación legal | Ley, artículo y fecha, más el aviso de que no es asesoría legal. | Generaliza a otra jurisdicción sin fuente. |

Cada cita `path:line` es relativa al commit del proyecto registrado en [`SOURCES.md`](../SOURCES.md); fijar esos commits es una tarea pendiente de esta edición, y así se declara cuando no lo está.

### Estilo

- Español neutro y profesional, segunda persona singular, presente.
- Código, identificadores, comandos y nombres de archivo en inglés.
- Una idea por párrafo; párrafos de tres a cinco líneas.
- Tablas para comparar, listas para enumerar, checklists para actuar.
- Sin emojis, sin adjetivos de marketing, sin "obviamente", "simplemente" ni "fácil".
- Cada capítulo abre con una tesis que se puede citar sola.
- Los enlaces internos son relativos; los externos llevan fecha de consulta.
- Las rutas de código son relativas a la raíz del proyecto citado.

### Qué se acepta

- Correcciones de hecho con evidencia reproducible.
- Casos de estudio nuevos que declaren problema, usuarios, canal, stack, fallos y límites.
- Plantillas con un ejemplo ejecutable o con la etiqueta explícita de no probado.
- Contraejemplos que refuten un invariante con evidencia, no con preferencia.
- Traducciones con una persona que pueda revisar la lengua y el contenido técnico.

### Qué no se acepta

- Promoción de un proveedor, un framework o un curso sin comparación ni límites.
- "Soluciones" de prompt injection que solo agregan frases al system prompt.
- Benchmarks sin método, sin dataset y sin fecha.
- Precios sin proveedor, región, fecha y unidad.
- Código copiado sin verificar la compatibilidad de licencias.
- Datos personales, credenciales, nombres de clientes o capturas con información real.
- Texto generado por IA presentado como evidencia sin verificación humana.

### Revisión por pares

El revisor no reescribe el capítulo: verifica que la evidencia sostenga la afirmación y que un lector nuevo pueda seguir el argumento. Para cambios normativos —los que tocan un invariante— se proponen dos revisores, y al menos uno debe haber operado un sistema en producción. El autor no aprueba su propio cambio. Si hay desacuerdo, se documenta la decisión con el formato de un ADR breve; la evidencia gana a la antigüedad.

## Definition of Done de un capítulo

Un capítulo está terminado cuando cumple estos criterios. No es una lista de deseos: cada uno se puede verificar.

| Criterio | Cómo se verifica |
|---|---|
| **Tesis** | La primera sección responde la pregunta central en una frase citable. |
| **Evidencia** | Toda afirmación sobre un repositorio tiene `path:line`; toda fuente externa tiene URL y fecha. |
| **Ejemplos** | Hay al menos un ejemplo copiable, o una justificación explícita de por qué no aplica. |
| **Checklist** | El lector puede convertir el capítulo en acciones verificables. |
| **Fuentes** | Las referencias están listadas con publicación, consulta y, si aplica, licencia. |
| **Enlaces** | Los enlaces relativos resuelven y el capítulo tiene entrada y salida en el índice. |
| **Revisión** | Una persona distinta del autor revisó evidencia, claridad y límites. |
| **Límites** | El capítulo dice qué no se probó, qué puede cambiar y qué no cubre. |

## Licencia

### Split de licencia

| Material | Licencia | Por qué | Advertencia |
|---|---|---|---|
| Prosa, tablas y checklists | **CC BY-SA 4.0** | Permite citar, adaptar y traducir con atribución; la cláusula share-alike mantiene abiertas las derivaciones. | No se recomienda para código. |
| Código original de plantillas y scripts | **MIT** | Fricción mínima y compatibilidad amplia. | Exige conservar el aviso de copyright. |
| Alternativa para código con interés en patentes | **Apache-2.0** | Agrega una concesión explícita de patentes. | No es la licencia actual; el autor puede adoptarla en el futuro. |

El precedente de la prosa es OWASP: el **OWASP GenAI LLM Top 10 2026** se publica bajo **CC BY-SA 4.0** (https://genai.owasp.org/llm-top-10/, publicado 2026-08-04, consultado 2026-11-04). Ese precedente no obliga a nadie, pero muestra que una referencia técnica abierta puede usar share-alike sin perder adopción.

La licencia está en vigor desde el 2026-11-04. El repositorio incluye `LICENSE`, `LICENSES/CC-BY-SA-4.0.txt`, `LICENSES/MIT.txt` y `NOTICE`; los documentos de `docs/` y el README declaran su identificador SPDX, y los textos de licencia se rigen por su propio contenido. La prosa, las tablas y los checklists son CC BY-SA 4.0; el código original de las plantillas y los scripts es MIT. Los fragmentos citados de los cuatro proyectos no se relicencian: conservan su licencia original y se detallan en `NOTICE`.

### Licencias reales de los cuatro proyectos

Verificado el 2026-11-04 en los archivos de cada repositorio. No se infiere una licencia a partir del README ni de las dependencias.

| Proyecto | Archivo verificado | Licencia | Qué implica para quien copia |
|---|---|---|---|
| **AgroVoz** | `LICENSE` | **GNU Affero General Public License v3.0** (AGPL-3.0). | Copyleft fuerte con cláusula de red: si ofreces una versión modificada como servicio, debes ofrecer el código fuente correspondiente. Revisa el texto completo y consulta a un profesional antes de reutilizar código. |
| **Wenuke** | `LICENSE` | **MIT License**, Copyright (c) 2026 Werken-mapu. | Permite usar, copiar, modificar y distribuir, incluso comercialmente, conservando el aviso de copyright y la licencia. |
| **copiloto-recepción** | Sin `LICENSE` en la raíz. | **Sin licencia de proyecto declarada.** `docs/stack-abierto.md:8-15` lista licencias de dependencias; `:10` describe el código propio como "código propio del proyecto", que no es una concesión de licencia. | Por defecto, derechos reservados. No copies código sin permiso escrito del autor. |
| **ManttoAI** | Sin `LICENSE` en la raíz. | **Sin licencia de proyecto declarada.** El README se declara "open-source" (`README.md:9`), pero no hay archivo de licencia. | "Open source" sin licencia no concede derechos. El único archivo `LICENSE` observado en el repositorio pertenece a una skill de terceros incluida en `.agents/skills/frontend-design/`, no al proyecto. |

La disparidad es material. Un mismo manual que cita cuatro repos no puede tratar el código de los cuatro como si tuviera la misma licencia. La sección de contribución exige verificar la licencia antes de copiar, y la revisión de pares debe rechazar un ejemplo sin procedencia.

### Reglas prácticas

- **Copiar una idea no es copiar código.** Puedes adoptar el patrón de fallback por causa sin copiar la implementación.
- **AGPL no es MIT.** Si tu producto es un servicio de red, una copia de código AGPL puede obligarte a publicar tu fuente. No lo decidas por intuición.
- **Sin licencia no significa "libre".** Significa que el autor conserva los derechos, salvo la excepción legal que aplique.
- **La licencia de una dependencia no licencia el proyecto.** Chatwoot, FastAPI o Postgres tienen sus propias licencias; el código del proyecto sigue la suya.
- **Las plantillas de esta guía deben ser originales o compatibles.** Si un capítulo extrae código de un proyecto, debe declarar la fuente y la licencia, y no puede relicenciarlo como MIT sin permiso.
- **Citar un marco no es redistribuir su texto.** Los estándares ISO suelen requerir compra y no se reproducen; los marcos NIST se consultan en su sitio. Esta guía no reproduce su contenido.

## Cómo citar la guía

Una cita útil incluye título, capítulo, edición y fecha. Sin edición, el lector no sabe qué versión de la regla está leyendo.

```text
Guía estándar para crear agentes de IA y chatbots.
Capítulo 16: Comunidad, versionado y contribución.
Edición 0.1.0-draft, 2026-11-04. Repositorio agents-wa.
```

Cita en línea:

```text
(Guía de agentes IA, cap. 16, ed. 2026-11-04)
```

Entrada BibTeX:

```bibtex
@misc{guia-agentes-ia-2026,
  title        = {Guía estándar para crear agentes de IA y chatbots},
  year         = {2026},
  edition      = {0.1.0-draft},
  howpublished = {Repositorio agents-wa},
  note         = {Capítulo 16: Comunidad, versionado y contribución. Consultado 2026-11-04}
}
```

Cuando exista una URL pública, se agrega al campo `url` y al texto de la cita. No se inventa una URL antes de publicar.

### Cómo enlazarla

- Enlaza al archivo, no al ancla: `[Capítulo 16](16-comunidad.md)`. Los títulos cambian; los archivos, menos. Si usas un ancla, que sea una sección estable del contrato del capítulo.
- Al citar código, incluye proyecto, `path:line` y fecha o commit. Una línea sin commit envejece mal; una cifra de tests sin comando y fecha, también.
- Si traduces un capítulo, conserva el título original y declara la edición base.

## Roadmap

La prioridad se decide por impacto, no por novedad: primero lo que desbloquea decisiones caras o evita fallos frecuentes. No hay fechas comprometidas; un roadmap con fechas inventadas es marketing.

| Prioridad | Entrega | Por qué | Señal de terminado |
|---|---|---|---|
| **P0** | Dataset de eval reproducible | Convierte las recomendaciones en una medición. Es lo que más falta en los cuatro proyectos. | 20-30 conversaciones doradas, con criterio pass/fail, licencia limpia y comando de ejecución. |
| **P0** | Guía multi-tenant | El nivel L4 es donde se rompen aislamiento, cuotas y facturación. | Checklist de aislamiento por tenant, roles, cuotas y evals por tenant. |
| **P1** | Plantillas por stack (Node/TypeScript y Go) | Reduce la fricción de adopción sin cambiar los invariantes. | Las mismas plantillas con contrato equivalente y ejemplos ejecutables. |
| **P1** | Guía de voz | Voz agrega latencia, turnos solapados y consentimiento de grabación. | Presupuesto de latencia, manejo de barge-in y política de retención. |
| **P1** | Más casos de estudio, con fallos | Cuatro casos no cubren la variedad de canales y restricciones. | Cada caso declara problema, usuarios, stack, fracasos y límites. |
| **P2** | Traducciones (inglés y portugués) | Amplía el alcance, pero solo tiene sentido cuando el contenido esté estable. | Traducción revisada por una persona bilingüe y enlazada a la edición base. |

## Comunidad

### Dónde discutir

Esta guía no tiene todavía un foro propio, un chat ni una lista de correo. Mientras no exista, el canal es el repositorio:

- **Issues** para errores, preguntas y propuestas de caso.
- **Pull requests** para cambios concretos con evidencia.
- **Discusiones** solo si el repositorio las habilita; si no, un issue que indique la categoría en el título.

Si se crea un canal oficial, debería anunciarse en el README. No se promete un espacio que no existe.

Si el repositorio adopta etiquetas, la categoría del issue debe indicarla en el título: `error`, `propuesta`, `caso-de-estudio`, `licencia` o `traduccion`. Todavía no existen como etiquetas oficiales.

### Cómo proponer un caso de estudio

Un caso sirve si muestra una decisión, no si muestra un producto. El issue debe incluir:

1. Problema y usuarios reales.
2. Canal y restricción operativa principal.
3. Stack y modelo, con versiones.
4. Qué funcionó, con evidencia.
5. Qué falló, con evidencia. Un caso sin fallos no se acepta.
6. Límites: qué no se probó, qué datos son ficticios.
7. Permiso y licencia para publicar el material.

### Código de conducta propuesto

- Critica la afirmación, no a la persona.
- Trae evidencia o etiqueta tu opinión como opinión.
- Declara conflictos de interés: proveedor, empleador o trabajo pagado.
- No publiques datos personales, credenciales ni nombres de clientes.
- Respeta las licencias y la atribución.
- El acoso y la discriminación no tienen lugar en este espacio.

El mantenedor puede cerrar un hilo o rechazar una contribución, y debe dejar la razón por escrito. Todavía no existe un comité de apelaciones; decirlo es parte de la honestidad del proceso.

## Si encuentras un error

Un error no se reporta con una captura y una frase. Se reporta con evidencia y una propuesta.

1. **Verifica que sea un error.** Revisa la edición, la fecha y el archivo citado. Una diferencia de opinión no es un error; una línea que dice otra cosa, sí.
2. **Reproduce o localiza la evidencia.** Abre el archivo y la línea, o la URL y la fecha. Si la fuente cambió, adjunta la versión anterior.
3. **Busca un reporte existente y reporta con la plantilla.** Si ya existe un hilo, agrega tu evidencia allí. Separa el hecho observado de la interpretación.
4. **Propón el fix mínimo.** Un cambio de una frase es preferible a un rediseño del capítulo. Si el problema es de diseño, abre una propuesta aparte.

Plantilla de reporte:

```text
Capítulo:
Edición o fecha:
Ubicación (archivo:línea):
Afirmación actual:
Evidencia esperada:
Evidencia observada:
Impacto: corrección | cambia una decisión | invalida un capítulo
Propuesta:
```

Si no puedes reproducir el error, dilo. "No reproducible" es un dato útil, no una vergüenza. Si el error afecta una decisión de seguridad o una licencia, márcalo como prioritario y evita publicar datos sensibles en el issue.

## Checklist de contribución

- [ ] 1. El cambio responde a un problema concreto, no a una preferencia de estilo.
- [ ] 2. La tesis del capítulo cabe en una frase y aparece al inicio.
- [ ] 3. Cada afirmación sobre un repositorio tiene `path:line` con fecha o commit.
- [ ] 4. Cada fuente externa tiene URL, fecha de publicación y fecha de consulta.
- [ ] 5. El ejemplo se copió y se ejecutó, o se marcó explícitamente como no verificado.
- [ ] 6. Los enlaces relativos resuelven y el capítulo tiene entrada y salida en el índice.
- [ ] 7. La licencia del código copiado es compatible y está declarada.
- [ ] 8. El capítulo declara sus límites y lo que no se probó.
- [ ] 9. Otra persona revisó la evidencia y la claridad.
- [ ] 10. El changelog y la versión reflejan el tipo de cambio.

## Cierre

Esta guía se sostiene en una idea simple: la confiabilidad de un agente vive en el código que lo rodea, y la confiabilidad de una guía vive en la evidencia que la respalda. Si puedes citar una regla, discutirla con un `path:line` y mejorarla con un caso, el estándar existe. Si no, es una opinión con formato.

Continúa con:

- [Capítulo 0 — Introducción](00-introduccion.md): la tesis, el mapa de decisión y los diez invariantes.
- [Capítulo 13 — Casos de estudio](13-casos-de-estudio.md): qué funcionó, qué falló y qué copiar de los cuatro proyectos.
- [Capítulo 14 — Plantillas](14-plantillas.md): las estructuras copiables para prompts, tools, evals y runbooks.
- [Capítulo 15 — Anti-patrones](15-anti-patrones.md): el catálogo de fallos recurrentes y sus antídotos.
- [Apéndice C — Referencias](C-referencias.md): las fuentes externas con URL, fecha y licencia.
