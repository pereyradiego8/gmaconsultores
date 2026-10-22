# Cloudflare Pages — vista previa de GMA

**Proyecto:** `gmaconsultores-preview` (cuenta de Cloudflare asociada a GitHub `pereyradiego8`).

**URL asignada:** https://gmaconsultores-preview.pages.dev/

**Repositorio y rama:** `pereyradiego8/gmaconsultores`, `refactor/auditoria-modernizacion-20261022` (independiente de `main`).

**Build:** `python3 scripts/build_preview.py --output preview-dist` — **salida:** `preview-dist`.

**Contenido del preview:** seis páginas del rediseño en `/propuesta/`, buscador estático y recursos estrictamente necesarios (aprox. 490 KB). Enlaces al archivo WordPress original abren el sitio original, sin copiar formularios ni backend.

**SEO:** `/_headers` aplica `X-Robots-Tag: noindex, nofollow, noarchive`; `robots.txt` indica `Disallow: /`. Son controles antiindexación, **no autenticación**.

**Acceso:** Cloudflare Access no estaba habilitado en la cuenta al configurar este proyecto; el subdominio `pages.dev` es público hasta implementar un control de acceso real. No incluir datos privados ni utilizarlo como almacenamiento confidencial.

**Automatización:** GitHub conecta únicamente la rama de trabajo. El proyecto Pages despliega los cambios de esa rama; las ramas de vista previa están deshabilitadas y no se modifica el dominio empresarial.

**Pendientes antes de reemplazar el sitio original:** autenticación privada opcional mediante Zero Trust / Cloudflare Access, mediciones en navegador, verificación de búsquedas y rutas externas, integraciones WordPress y aprobación expresa para pasar a producción.
