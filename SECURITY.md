<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->

# Reportar un error o un problema de seguridad

## Qué reportar aquí y qué no

- **Errores de evidencia `path:line`**: una cita que no resuelve, una línea que dice otra cosa, un dato cuyo repositorio cambió.
- **Errores de contenido**: una recomendación contradicha por el código o por una fuente externa fechada.
- **Problemas de seguridad en la guía misma**: comandos o plantillas del manual que inducen a una configuración insegura, o contenido que filtre secretos o datos personales.

No es canal para soporte de frameworks o proveedores citados como referencias: los problemas de un tool de terceros se reportan en su propio repositorio.

## Cómo reportar en privado

1. Contacta al mantenedor por correo y declara en el asunto que es un reporte de seguridad o de evidencia sensible.
2. Describe el hallazgo con el máximo detalle reproducible: capítulo, archivo citado, `path:line` o URL con fecha de consulta.
3. Da un plazo razonable antes de publicar nada. No abras un issue público ni publiques el detalle mientras el reporte esté en revisión.

No inventes datos de contacto: si no conoces el correo del mantenedor, pídelo a través de un issue en blanco que no contenga el detalle del hallazgo y continúa en privado desde allí.

## Qué no publicar jamás

- Secretos, tokens, credenciales ni URLs privadas de los cuatro proyectos citados.
- Datos personales de clientes o usuarios reales de esos proyectos.

Para errores públicos y correcciones de contenido ordinarias, el canal es un issue siguiendo [`CONTRIBUTING.md`](CONTRIBUTING.md) y la plantilla de reporte del [Capítulo 16](docs/16-comunidad.md#si-encuentras-un-error).
