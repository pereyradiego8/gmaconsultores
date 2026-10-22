# GMA Consultores — modernización sobre copia estática de WordPress

Este repositorio conserva una exportación completa del sitio público [GMA Consultores](https://gmaconsultores.com.ar/) (WordPress + Avada/Elementor). **No incluye el backend de WordPress ni garantiza que formularios, AJAX, postulaciones o suscripciones procesen datos en un hosting estático.** Los originales se mantienen como referencia.

## Estado de la rama de desarrollo

- CSS institucional compartido en diez páginas existentes.
- **Propuesta visual moderna de seis páginas** en `propuesta/`: inicio, servicios, nosotros, novedades, oportunidades y contacto. Se conserva la identidad GMA y se enlaza contenido original.
- Buscador `buscar/` con relevancia, filtros, paginación y resultados accesibles. La compilación genera un índice de texto extraído de páginas reales.
- Generador de versión independiente: `scripts/build_static.py`. Aplica mejoras a cientos de páginas del espejo **sin alterar sus archivos originales**: metadescripciones de fuente real, estilos, búsqueda y bloqueo de indexación en aliases.
- Comprobaciones estáticas, auditoría de enlaces, pruebas de regresión y GitHub Actions.

## Compilar y probar localmente

Requiere Python 3.10+ y no necesita instalar paquetes.

```bash
python3 scripts/audit_static.py
python3 scripts/build_static.py --output dist
python3 scripts/audit_static.py --root dist
python3 scripts/verify_build.py
python3 scripts/check_links.py --root dist --output reports/gma-links.json
python3 scripts/check_links.py --root dist --focus propuesta/ --strict --output reports/gma-preview-links.json
python3 -m http.server 8000 --directory dist
```

Abrir `http://localhost:8000/propuesta/` (propuesta visual), `http://localhost:8000/buscar/` (buscador) o `http://localhost:8000/` (espejo). **No abrir como `file://`**: el índice del buscador se obtiene mediante HTTP.

El directorio `dist/` es generado, no se commitea, y no se publica automáticamente. Los informes quedan en `reports/`; GitHub Actions publica únicamente un artefacto de auditoría y el índice, **no el sitio**.

## Seguridad y despliegue

**No se realizó despliegue ni se alteró `main`**. No configurar un host público de vista previa sin autorización expresa. Si se autoriza un preview, exigir protección contra indexación, HTTPS y acceso a una rama aislada; revisar el dominio canónico y las rutas originales.

Los formularios de Elementor dependen de WordPress. No enviar consultas mediante endpoints inexistentes ni simular éxitos de envío.

Consultar [auditoría inicial](docs/AUDITORIA-2026-10-22.md) y [reporte de continuación](docs/AVANCES-MODERNIZACION.md).


## Integración del sitio original

La versión de Cloudflare Pages ahora importa contenido WordPress al diseño moderno: **427 páginas de contenido y listados (347 páginas individuales y 80 archivos)** más **707 imágenes y recursos públicos**, según la compilación inicial. Los duplicados del mirror y los feeds no se despliegan como páginas independientes.

Los servicios detallados, artículos, búsquedas laborales históricas y páginas de archivo están dentro del preview con las mismas rutas de las páginas canónicas. El buscador dirige a esas páginas y la sección moderna de oportunidades muestra enlaces al archivo de vacantes; las noticias recientes se obtienen de la API pública de WordPress durante cada compilación.

Los formularios Elementor, suscripciones y postulaciones siguen ejecutándose **solo en el sitio WordPress original**; el frontend estático no puede reproducir los envíos sin su backend. La nueva versión enlaza a sus formularios originales en vez de simular una operación exitosa.

Construcción: `python3 scripts/build_preview.py --output preview-dist`; validación: `python3 scripts/verify_integrated.py`. Informe: [Integración completa de contenidos](docs/INTEGRACION-CONTENIDO-ORIGINAL.md).

**No se fusionó `main`, no se cambió el DNS y no se sustituyó la producción original.**
