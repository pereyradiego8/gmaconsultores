# Avances de modernización de GMA — fase 2 (octubre de 2026)

**Rama:** `refactor/auditoria-modernizacion-20261022` — PR #1 en borrador. **Sin cambios en producción, sin deploy y sin merge a `main`.**

## Implementación concreta

1. **Rediseño preparado**: `propuesta/` contiene seis páginas modernas, con hoja común `assets/gma-preview.css`, identidad GMA, navegación responsive, enlaces accesibles y datos comerciales obtenidos del sitio original. Se conservan los enlaces a publicaciones y formularios WordPress sin reproducir envíos ficticios. Todas las páginas se marcan `noindex`.
2. **Buscador ampliado**: `buscar/index.html` ahora permite filtrar publicaciones/institucional, utiliza relevancia por título, descripción y contenido (no solo slug), muestra paginación y mensajes accesibles. Solo usa `textContent` para representar contenido externo, evitando HTML inyectado. No recopila búsquedas en un backend propio.
3. **Build aislado**: `scripts/build_static.py` genera `dist/` a partir de archivos fuente. Aplica CSS compartido, enlaces de salto, descripciones heredadas de `og:description` o párrafos reales y redirige búsquedas locales al motor estático. Los aliases `index.html@p=...` se declaran `noindex`, sin eliminar sus páginas.
4. **Integridad**: copia también `wp-includes/css/dist` y `wp-includes/js/dist` (rutas reales de WordPress), sin confundir estas carpetas de distribución de dependencias con la salida `dist/` del proyecto.
5. **Calidad verificable**: auditoría de todos los HTML, comprobación de rutas locales, comprobación estricta de las seis páginas de propuesta y regresión de formularios/imágenes en las diez páginas institucionales.

## Resultados observados en GitHub Actions

En una compilación sin despliegue ya verificada, se generaron:
- 786 archivos HTML procesables (el resto de los 1.132 archivos `.html` son en buena parte feeds o formatos que no contienen HTML de página).
- 776 inserciones del CSS compartido; 769 metadescripciones obtenidas de fuentes del propio espejo; 1.536 correcciones de acciones de búsqueda.
- 354 aliases marcados `noindex`.
- 355 páginas incluidas en el índice de búsqueda, con título, descripción y texto extraído; unos 351 KB de JSON sin comprimir.
- 355 URLs del sitemap, excluyendo búsqueda y preview noindex.

**Corrección de los informes:** el primer conteo de recursos ausentes incluía falsos positivos (atributos `data-*`, enlaces a carpetas sin resolver `index.html`) y tres recursos `wp-includes/*/dist` omitidos accidentalmente del build. Tras corregirlo, la auditoría global residual mostró 105 referencias que requieren análisis, sobre todo enlaces antiguos `themes.php?page=optionsframework` en copias de publicaciones `index.html@p=...`. Las seis páginas de la propuesta no tenían enlaces locales faltantes según la verificación posterior. Esto **no comprueba el funcionamiento de enlaces externos ni de formularios**.

Los resultados de `Lighthouse`, Core Web Vitals, navegación visual, lectores de pantalla, flujos comerciales y anti-spam **no se han medido**; no se asignan puntuaciones supuestas.

## Riesgos pendientes por prioridad

| Prioridad | Limitación | Próximo control |
|---|---|---|
| P0 | `robots.txt` original apunta a sitemaps PHP atípicos (`wzy.php`, `wpadmin/wpadmin.php`) | Revisar origen real, archivos, extensiones y Search Console para descartar SEO spam/compromiso |
| P0 | Formularios Elementor/WordPress AJAX, correo, newsletter y postulaciones no garantizados en un espejo estático | Comprobar backend real y decidir integración funcional antes de publicar |
| P1 | Rediseño multipágina todavía separado de las plantillas antiguas | Validar visualmente en navegador; decidir migración o actualización del WordPress editable |
| P1 | Referencias residuales a `themes.php` en exports de artículos `@p` | Confirmar que son enlaces administrativos heredados e impedir enlaces al admin en una publicación estática |
| P1 | HTML heredado y plugins duplicados/obsoletos | Medir Lighthouse, estructura JS/CSS y cargas antes de eliminar |
| P2 | Tracking por GTM/MonsterInsights y servicios externos | Revisar política de privacidad y consentimiento aplicable |
| P2 | Noticias y vacantes archivadas | Confirmar vigencia editorial antes de mostrarlas como actuales |

## Condiciones para ver el sitio online

Sin autorización previa **no se crea un deployment**, ni siquiera un preview temporal. La preparación técnica queda disponible en la rama y la compilación puede revisarse desde el artefacto de índice/reporte o de manera local. Una futura preview debería usar un subdominio aislado, configuraciones `noindex`/bloqueo de rastreo, y evitar ejecutar formularios no conectados.

El código fuente original y el WordPress público permanecen sin cambios.
