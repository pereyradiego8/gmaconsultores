# Auditoría y modernización de GMA Consultores — 22/10/2026

## 1. Alcance y origen

Repositorio: `pereyradiego8/gmaconsultores`. Rama de trabajo: `refactor/auditoria-modernizacion-20261022`.

El contenido corresponde a una **exportación estática** del sitio institucional basado en WordPress (Avada / Elementor). No contiene el código fuente ejecutable completo del CMS ni la base de datos. No corresponde desplegar este espejo sobre el WordPress activo sin un proceso de migración y validación.

Inventario obtenido de GitHub para la base `main`: **3.154 archivos**, aproximadamente **362 MB** en los blobs declarados, **1.130 HTML**, **35 CSS**, **348 PNG**, **456 JPG**; hay HTML duplicado en variantes `index.html@p=...`, archivos de feeds, medios originales y recursos estáticos de plugins. Se inspeccionaron directamente los HTML de las **10 páginas institucionales principales**, además de `robots.txt` y rutas/activos del repositorio. El inventario es integral, pero no se ha verificado manualmente la ejecución de cada una de las 1.130 páginas.

### Público, contenido e identidad

Sitio institucional para empresas y organizaciones en Argentina. Se preservan rutas y contenido de Consultoría, Auditoría, Impuestos, Outsourcing, RRHH, Back-office, oportunidades laborales, novedades y contacto. La identidad visual roja de GMA y los archivos multimedia originales permanecen disponibles.

## 2. Hallazgos clasificados

| Prioridad | Hallazgo comprobado | Acción / estado |
|---|---|---|
| Crítica — investigación | `robots.txt` original anuncia `wzy.php?sitemap.xml` y `wpadmin/wpadmin.php?sitemap.xml`, rutas que no corresponden a un sitemap estándar y requieren evaluación de posible SEO spam o compromiso del WordPress origen | Retiradas **solo de la rama del espejo estático**. No se ha verificado si siguen presentes en el servidor activo |
| Alta | Formularios Elementor, AJAX de WordPress y búsqueda `?s` son dependencias de backend; una copia estática no puede garantizar su procesamiento | Se conservan formularios originales. Se incorporó un buscador local para rutas del espejo, sin falsificar envíos |
| Alta | CSS/JS legado del tema y plugins, con HTML de hasta más de 1 MB por página | Mejora progresiva; pendiente consolidación/refactor real sobre fuentes de WordPress |
| Alta | Posible desactualización de oportunidades laborales, noticias históricas y datos | Se conservan sin proclamar vigencia; pendiente verificación editorial |
| Media | En portada se utilizaba H1 para «Clientes con los que trabajamos», sin un H1 que describa la propuesta principal | H1 semántico de página + H2 para clientes |
| Media | Falta de capa uniforme de foco, espaciados y accesibilidad | CSS compartido, navegación al contenido y estilos responsive en 10 rutas |
| Media | Metadescripciones no presentes en páginas institucionales inspeccionadas | Metadescripciones contextuales en 10 rutas |
| Media | Paginaciones y rutas redundantes entre contenidos exportados | Índice estático y sitemap sin listados paginados |

**No se detectó ni confirmó una intrusión activa.** Las referencias PHP de `robots.txt` justifican una revisión del servidor de origen, archivos de WordPress, usuarios, plugins, base de datos y Search Console.

## 3. Implementación de esta rama

- `assets/gma-modern.css`: diseño incremental responsive con identidad conservada; foco visible, enlaces de salto, controles más cómodos y movimiento reducido.
- `index.html`, `quienes-somos/index.html`, `consultoria/index.html`, `outsourcing/index.html`, `impuestos/index.html`, `auditoria/index.html`, `rrhh/index.html`, `oportunidades/index.html`, `novedades/index.html`, `contacto/index.html`: integración del CSS y metadatos, navegación accesible y buscador compatible con el espejo estático.
- `assets/gma-search-index.json`: rutas reales existentes, excluyendo feeds y paginaciones. La búsqueda compara slugs/títulos derivados de rutas; **no indexa el cuerpo completo** de cada nota.
- `buscar/index.html`: búsqueda sin servidor, sin dependencias externas, con mensajes de error y sin resultados.
- `sitemap.xml` y `robots.txt`: sitemap del espejo basado en rutas presentes y limpieza de referencias sospechosas.
- `propuesta/index.html`: propuesta visual más profunda y **no indexable** para evaluar antes de sustituir la portada, sin formularios simulados.
- `scripts/audit_static.py` y `scripts/inspect_archive.py`: chequeos y reporte automatizado. `.github/workflows/static-audit.yml`: pipeline en PR y rama principal.

## 4. Comparación verificable

| Antes | En rama propuesta |
|---|---|
| Portada y páginas institucionales usan estilos Avada sin una capa de mejoras compartida | Diez rutas incluyen `gma-modern.css`; HTML original y contenidos preservados |
| Búsqueda de WordPress dependiente del backend | Búsqueda local por títulos/slugs sobre rutas reales; capacidad de búsqueda por texto completo pendiente |
| `robots.txt` incluye rutas PHP no reconocidas | Eliminadas y reemplazadas por un sitemap XML de rutas del espejo |
| Portada usa H1 centrado en clientes | H1 descriptivo en portada y clientes pasan a H2 |
| Sin chequeo automatizado propio en el espejo | Scripts de auditoría y workflow CI en PR |
| Sin página de propuesta visual | `/propuesta/` ofrece un rediseño autónomo sin afectar portada ni backend |

## 5. Pruebas y limitaciones

**No afirmar 90+ de Lighthouse ni LCP/INP/CLS sin medirlos.** Esta revisión no dispone de un navegador automatizado ejecutando el espejo ni acceso al WordPress/backend de producción. Los tests CI validan estructura, enlaces de búsqueda y archivos mínimos; la inspección integral adicional genera un JSON de inventario y alertas. Deben verificarse manualmente 320/375/768/1024/1440 px, accesibilidad con teclado y lector de pantalla, SEO live, tiempo de carga, formularios de contacto, newsletter, ofertas laborales e integraciones reales.

Para validar localmente desde la raíz:
```bash
python3 scripts/audit_static.py
python3 scripts/inspect_archive.py --output reports/gma-static-audit.json
python3 -m http.server 8000
```
Luego abrir `http://localhost:8000/`, `/buscar/` y `/propuesta/` (no usar `file://`, porque `fetch` del buscador requiere HTTP).

## 6. Despliegue seguro y reversión

1. Revisar primero este pull request y su pipeline; **no fusionar sin revisión**.
2. Publicar preview en hosting estático aislado, apuntando al directorio raíz del repositorio, evitando el dominio activo.
3. Comprobar páginas, imágenes, rutas, vistas responsive, accesibilidad y búsquedas. La versión estática no reemplaza automáticamente las funciones WordPress.
4. Verificar en el servidor WordPress real que el `robots.txt` y el sitemap sean legítimos; investigar las rutas sospechosas.
5. Decidir estrategia final: mantener WordPress y trasladar cambios al tema hijo/bloques, o migrar con backend de formularios, administración de contenidos, redirecciones 301 e integraciones verificadas.
6. Mantener backup/commit de referencia y permitir rollback del despliegue previo.

## 7. Próximas prioridades

1. **P0:** auditoría del WordPress en vivo y de los sitemaps PHP no reconocidos.
2. **P0:** probar contacto, newsletter y datos/capacidad de postulación con backend real.
3. **P1:** validación automatizada de páginas y recursos completos, Lighthouse/PageSpeed y axe.
4. **P1:** decidir si se adopta la propuesta visual y aplicarla a todas las plantillas con fuente editable.
5. **P2:** optimizar medios, limpiar duplicados **sin borrar originales ni cambiar URLs indexadas**, configurar caché y compresión.
6. **P2:** revisar privacidad/cookies y confirmar analítica con consentimiento conforme a la jurisdicción.

El reporte diferencia deliberadamente lo comprobado en código de lo pendiente por validar en producción.
