# Integración del sitio WordPress original en el rediseño GMA

**Fecha:** 22 de octubre de 2026  
**Entorno:** https://gmaconsultores-preview.pages.dev/propuesta/  
**GitHub:** rama `refactor/auditoria-modernizacion-20261022`, PR #1 (borrador).

## Contenido migrado

El repositorio es una copia exportada del sitio WordPress/Avada/Elementor, **no el servidor WordPress ni su base de datos**. Para preservar contenido real sin arrastrar temas, plugins o formularios rotos, el generador `scripts/import_original.py` obtiene los artículos y secciones del espejo y los transforma a plantillas HTML modernas, con tipografía y navegación GMA.

Una compilación de prueba verificó:
- **427 rutas importadas**, desglosadas en **347 páginas individuales** y **80 listados de archivo o categorías**.
- **707 imágenes y otros recursos públicos** de `wp-content/uploads`, aproximadamente **103,5 MB** (se excluyeron JS/CSS de plugins y entradas duplicadas por su formato, no imágenes).
- **354 resultados del buscador** vinculados a páginas de la nueva versión en esa primera compilación. Los alias de WordPress, feeds y archivos duplicados `index.html@p=...` no se presentan como páginas independientes; sus rutas canónicas sí están conservadas.
- Se mantienen las seis secciones nuevas de `/propuesta/`, junto con `/consultoria/`, `/impuestos/`, `/auditoria/`, `/outsourcing/`, `/rrhh/`, `/quienes-somos/`, `/novedades/`, `/oportunidades/`, noticias, vacantes históricas y archivos de categorías y paginación.

La compilación **no carga ni ejecuta código PHP, widgets de WordPress, plugins ni JavaScript ajeno**. Preserva en HTML estático los párrafos, encabezados, listas, enlaces, tablas e imágenes del material original. Utiliza un sanitizador que omite código ejecutable y elementos de envío de datos.

Los vínculos del contenido conservado ahora apuntan al sitio renovado cuando la página está migrada. Enlaces a archivos no incluidos o funciones dinámicas continúan en `https://gmaconsultores.com.ar`. El buscador también dirige a las rutas importadas y no a otra web.

## Secciones y funcionamiento

- **Servicios:** `/propuesta/servicios/` sirve como índice visual; los seis servicios enlazan a páginas interiores importadas con el detalle original.
- **Institucional:** `/propuesta/nosotros/` enlaza a `/quienes-somos/` con la información histórica.
- **Noticias:** `/propuesta/novedades/` incluye seis noticias recientes obtenidas de la API pública de WordPress en el momento de cada build, junto con acceso local al archivo completo `/novedades/`. Los artículos presentes en el espejo se leen sin salir del preview.
- **Oportunidades:** `/propuesta/oportunidades/` exhibe avisos procedentes del archivo histórico y permite acceder a los detalles; **no se afirma que estén abiertos**.
- **Contacto y postulaciones:** las interfaces de WordPress con envíos reales necesitan backend (captcha, correo, almacenamiento y seguridad). En lugar de simular un formulario, se ofrece un enlace directo al formulario oficial correspondiente y se indican explícitamente estas limitaciones.
- **Imágenes:** los recursos se copian localmente; las galerías históricas de logos se muestran en una cuadrícula adaptable para reducir la altura en celulares.

## Qué falta para reemplazar realmente la producción

1. Obtener acceso al servidor WordPress, base de datos o exportación completa de contenidos y configuración de formularios, si se pretende migrar sus envíos a un backend nuevo. El espejo no contiene credenciales ni lógica del servidor.
2. Definir integración de los formularios de contacto, postulaciones y newsletter (Cloudflare Workers/Pages Functions más un proveedor de correo o API oficial) y verificar entregas en pruebas con consentimiento.
3. Confirmar vigencia editorial de vacantes y enlaces históricos. Las noticias nuevas se incorporan a la portada de noticias **en la siguiente compilación**, no en tiempo real sin recargar el sitio.
4. Activar Cloudflare Access si se requiere privacidad: la cuenta aún no tiene Access habilitado. `noindex` no es autenticación.
5. Revisar SEO y dominio al momento del lanzamiento; **noindex** sigue activado en Pages para impedir competencia con el WordPress público.
6. No modificar `main` ni apuntar `gmaconsultores.com.ar` al preview sin una nueva autorización para despliegue a producción.

## Construcción local y controles

Requiere Python 3.10+ y conexión para obtener las seis noticias recientes de WordPress (si la API no está disponible, el archivo local igualmente se genera):

```bash
python3 scripts/build_preview.py --output preview-dist
python3 scripts/verify_integrated.py
python3 scripts/check_links.py --root preview-dist --focus propuesta/ --strict
python3 -m http.server 8765 --directory preview-dist
```

Las comprobaciones Chrome/axe de GitHub Actions prueban páginas nuevas e integradas. Para la ruta 404 y las cabeceras CSP, verificar el despliegue real en Cloudflare Pages, no únicamente `http.server` de Python.
