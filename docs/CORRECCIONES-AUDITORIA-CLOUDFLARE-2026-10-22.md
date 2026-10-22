# Correcciones de auditoría — GMA Consultores / Cloudflare Pages

**Fecha:** 22/10/2026
**Preview:** https://gmaconsultores-preview.pages.dev/propuesta/
**Repositorio:** `pereyradiego8/gmaconsultores`
**Rama aislada:** `refactor/auditoria-modernizacion-20261022` · PR #1 como borrador.
**Sin cambios en la web original, en el DNS corporativo ni en `main`.**

## Errores resueltos en la versión de prueba

| Hallazgo | Remediación implementada | Cómo comprobarlo |
|---|---|---|
| Resultados de búsqueda en páginas inexistentes | `build_preview.py` transforma `link.href` para apuntar a `https://gmaconsultores.com.ar` y no al subdominio Pages. | Buscar `impuestos`, abrir resultados y verificar el dominio de destino. |
| «Versión original» enviaba a `/index.html` (404 en WordPress) | Todos los enlaces de regreso a la portada original ahora van a `https://gmaconsultores.com.ar/`. | Abrir pie de página de las seis secciones. |
| «Buscar publicaciones» enviaba a `https://gmaconsultores.com.ar/buscar/` (404) | En la demo enlaza a `/buscar/`, que sí se publica. | Novedades → Buscar publicaciones. |
| Rutas desconocidas devolvían HTTP 200 | Se genera `404.html` con navegación al inicio y `noindex`. | Abrir una ruta inexistente y verificar HTTP 404. |
| Push automático omitido (`path_config`) | Configuración de Cloudflare Pages corregida con `source.config.path_includes=["*"]`, `production_deployments_enabled=true`, `preview_deployment_setting="none"`. | Historial de Deployments: `github:push` marcado `success`, sin disparar deploys de otras ramas. |
| CSP inexistente e inline scripts/styles | El buscador extrae sus CSS/JS a archivos propios; se bloquean scripts externos salvo el beacon de Cloudflare Web Analytics; se restringe `base-uri`, frames, objetos y conexiones. | Inspeccionar `/_headers` del artefacto construido y las cabeceras HTTP. |
| Ausencia de HSTS / Permissions-Policy | Se añadieron `Strict-Transport-Security: max-age=31536000` y restricciones a cámara, micrófono, geolocalización y pagos. | Inspeccionar cabeceras de las páginas. |
| Ausencia de  medición de usuarios | Se registró `gmaconsultores-preview.pages.dev` en Cloudflare Web Analytics, habilitando su integración con Pages y CSP apropiada. | Cloudflare → Web Analytics; las métricas requieren visitas y un intervalo de recopilación. |
| Publicaciones solo históricas | Novedades incorpora las 6 publicaciones más recientes obtenidas de la API REST pública de WordPress durante la compilación; títulos y URLs se validan y se escapan para evitar HTML externo. | Novedades → «Publicaciones recientes», con enlace al artículo oficial. |
| Falta de pruebas de accesibilidad | CI ejecuta axe-core con criterios WCAG 2.1 A/AA en las siete páginas y dos tamaños de pantalla, y Playwright a 320, 360, 390, 768, 1024 y 1440 píxeles. | GitHub Actions → artefactos `reports/accessibility/axe.json` y `reports/responsive/`. |
| Espacios excesivos del hero móvil | Menor separación vertical, imagen con proporción más horizontal y botones que conservan altura táctil. | Comparar vista móvil de 320 y 390 px. |
| Cargas repetidas de recursos | Caché moderada en CSS, JavaScript e índice (5 minutos) e imágenes (1 hora), manteniendo HTML revalidable. | Respuestas de `/assets/*` y `/wp-content/*`. |

## Qué depende de acciones adicionales

1. **Privacidad de la vista previa:** Cloudflare Access sigue sin habilitarse a nivel de cuenta (API responde `403 access.api.error.not_enabled`). No es posible convertirla en privada sin activar el producto en el panel, definir organización/identidad y crear una regla para quienes deban acceder. Los encabezados `noindex` y `robots.txt` no protegen la URL. No simular autenticación con JavaScript.
2. **Seguridad de la cuenta:** la organización no exige MFA globalmente; habilitar esa política afecta a todos los usuarios y requiere coordinación para evitar pérdida de acceso. No se cambia sin decisión del administrador.
3. **Migración de WordPress:** el preview es estático; Elementor, postulaciones, newsletter, formularios y sus bases de datos se mantienen en la web original. Migrar estos procesos requiere integración de backend y pruebas de envío real; no se han enviado mensajes de prueba ni copiado credenciales.
4. **Novedades:** la API pública se consulta **al compilar** la vista previa. No constituye actualización diaria independiente de un nuevo deployment; las búsquedas laborales deben confirmarse como vigentes desde el origen.
5. **Indexación en dominio definitivo:** este proyecto permanece `noindex`; no debe eliminarse la protección SEO ni cambiar el dominio corporativo sin autorizar y completar la migración.
6. **Protección de WordPress:** las referencias atípicas a sitemaps PHP detectadas en el mirror no demuestran por sí solas una intrusión. Revisar WordPress/servidor original y Search Console con acceso administrativo.
7. **Rendimiento real:** las ejecuciones de Chrome en CI verifican ausencia de imágenes rotas, overflow y controles muy pequeños; Web Analytics empieza a recopilar datos desde su habilitación, pero esto no constituye certificación integral WCAG ni garantía de puntuaciones Lighthouse en todos los dispositivos.

## Probar localmente

```bash
python3 scripts/build_preview.py --output preview-dist
python3 -m http.server --directory preview-dist 8765
# Otra consola, con NODE_PATH apuntando a playwright-core y axe-core instalados:
node scripts/check_responsive.cjs
node scripts/check_accessibility.cjs
```

La página 404 y las cabeceras especiales se verifican en Cloudflare Pages: el servidor HTTP básico de Python no reproduce por sí solo todas las reglas de Pages.

## Cloudflare Access: configuración requerida en el panel

Ingresar en Cloudflare Zero Trust, activar Access, definir la identidad corporativa permitida y crear una aplicación de tipo **Self-hosted** que proteja el hostname `gmaconsultores-preview.pages.dev`; crear una política `Allow` limitada a identidades autorizadas y verificar acceso anónimo denegado. No proteger ni cambiar `gmaconsultores.com.ar` por error. Es una operación administrativa que no se completó desde esta conexión.
