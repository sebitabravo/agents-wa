<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Contribuir

Esta guía es un manual con un estándar de evidencia propio. Para proponer un cambio:

1. **Abre un issue primero.** Describe el problema concreto con ubicación (`archivo:capítulo:sección`), afirmación actual y la evidencia que la contradice, si la tienes. Un cambio sin problema identificado no parte con buena base.
2. **Un tema por issue y un PR por tema.** Un cambio de una frase corrige un error; un cambio que mezcla corrección, estilo y contenido nuevo es difícil de revisar y de revertir.
3. **Respeta el estándar de evidencia** definido en el [Capítulo 16](docs/16-comunidad.md#estándar-de-evidencia):
   - Afirmación sobre uno de los cuatro proyectos citados: `path:line` relativo a la raíz de ese proyecto. La referencia de cada repositorio se registra en [`SOURCES.md`](SOURCES.md).
   - Fuente externa: URL, fecha de publicación y fecha de consulta. No se inventan fechas ni SHAs; lo desconocido se declara pendiente.
   - Opinión: marcada como **recomendación de esta guía**, nunca presentada como hecho.
4. **Verifica antes de enviar.** El runner del repositorio comprueba estructura, enlaces, rutas, marcadores pendientes, cabeceras SPDX y resolución de citas:

   ```bash
   python3 scripts/check_docs.py
   ```

   Cuando los cuatro repos citados no están presentes, el runner informa la resolución de citas como omitida; usa `--repos-root` para apuntarlos.

5. **Preserva el estilo**: español neutro y profesional, segunda persona singular, sin emojis ni adjetivos de marketing. Los detalles completos están en el [Capítulo 16](docs/16-comunidad.md).

Errores de seguridad o de evidencia sensible: no abras un issue público; sigue [`SECURITY.md`](SECURITY.md).
