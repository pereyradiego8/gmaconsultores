# Formularios y oportunidades reales — GMA Consultores

**Fecha de implementación:** 22/10/2026  
**Entorno:** https://gmaconsultores-preview.pages.dev/propuesta/  
**Rama:** `refactor/auditoria-modernizacion-20261022`.

## Origen verificado de las ofertas

No se inventaron oportunidades de trabajo. La compilación consulta la **API REST pública** del WordPress oficial de GMA:

- `https://gmaconsultores.com.ar/wp-json/wp/v2/categories?slug=busqueda` → categoría `busqueda`, ID 23.
- `https://gmaconsultores.com.ar/wp-json/wp/v2/posts?categories=23&per_page=30&_fields=id,date,modified,link,title,excerpt`.

La consulta del 22/10/2026 devolvió seis publicaciones en esa categoría:

| Aviso real | Publicación original |
|---|---|
| Estudiantes Contador Público | 04/04/2025 |
| Analista de Impuestos SR | 06/03/2025 |
| Base de Talentos | 06/03/2025 |
| Data Analyst | 31/01/2025 |
| Analista de Engagement & Growth JR | 30/01/2025 |
| Estudiantes avanzados o graduados de Ingeniería Industrial | 23/10/2024 |

El WordPress original las incluye en su bloque «Búsquedas activas», **pero eso no constituye una confirmación independiente de que cada vacante siga abierta**. El rediseño muestra las fechas, los requisitos enlazados al aviso original o su copia integrada y un botón de postulación. Verificar la vigencia con RR. HH. antes de presentarse.

**Actualización:** la lista de la web renovada se refresca durante cada build de Cloudflare Pages. Si la API falla, se muestra claramente como *archivo histórico no confirmado*; no se presentan resultados antiguos como búsquedas activas. No existe aún un disparador diario automático para recompilar el proyecto.

## Tres formularios incorporados

1. **Contacto:** `/propuesta/contacto/`. Nombre, email, empresa, servicio y mensaje. Prepara un correo dirigido a `info@gmaconsultores.com.ar`.
2. **Postulación:** `/propuesta/oportunidades/#postulacion`. Selector alimentado por los avisos reales, nombre, email, teléfono y presentación. Prepara correo a `rrhh@gmaconsultores.com.ar`. El candidato **debe adjuntar el CV manualmente en su correo** antes de enviarlo. El aviso original puede requerir remuneración pretendida.
3. **Newsletter:** `/propuesta/novedades/#newsletter`. Prepara una **solicitud de suscripción** a `info@gmaconsultores.com.ar`. No registra una suscripción automáticamente.

Los formularios usan validación HTML nativa y recursos estáticos `assets/gma-forms.js` y `assets/gma-forms.css`. La acción sin JavaScript también dirige a `mailto:`; la CSP permite únicamente `mailto:` y rutas locales. La vista previa **no almacena nombres, CV ni consultas**. La acción abre la aplicación de correo; no afirma que el mensaje ya haya sido enviado. Se mantienen enlaces a los formularios y avisos del WordPress original como alternativa real.

## Pendiente para envío automático desde la página

Todavía **NO** existe un backend autorizado que reciba y entregue los envíos de estos tres formularios desde Cloudflare Pages. Para implementar envío web real hay que:

- Autorizar/verificar el dominio remitente y un proveedor de correo transaccional (por ejemplo, Resend, Mailgun o servicio de correo corporativo).
- Configurar las credenciales del proveedor **exclusivamente como secretos de Cloudflare**, no en GitHub ni en JavaScript.
- Crear endpoint(s) de Pages Functions/Workers con validación del lado del servidor, rate limiting, captcha/Turnstile, políticas de privacidad y manejo de errores.
- Definir dónde deben recibirse los formularios, consentimiento y retención; para candidatos, establecer un destino seguro para CV si se habilita carga de archivos.
- Probar la entrega hasta la bandeja de entrada y los errores reales antes de sustituir el flujo `mailto:`.

No se ha enviado ningún correo de prueba ni capturado CV sin autorización. GMA WordPress original y `main` no se modificaron.

## Validaciones

- `scripts/verify_integrated.py`: verifica los tres formularios, destinos mailto, campos obligatorios, recursos estáticos, CSP y opciones de puestos.
- `scripts/check_responsive.cjs`: comprueba los formularios en Chrome además del responsive de 13 rutas.
- `scripts/check_accessibility.cjs`: ejecuta axe WCAG 2.1 AA sobre las secciones, incluidas las tres páginas con formularios.

Estado: publicado exclusivamente en Cloudflare Pages preview. La prueba de 22/10/2026 con estos cambios pasó GitHub Actions (ver historial de la rama).
