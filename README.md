# GMA Consultores — copia estática y plan de modernización

Este repositorio contiene una copia estática de [gmaconsultores.com.ar](https://gmaconsultores.com.ar/), originada en WordPress/Avada. **No es una instalación funcional de WordPress:** enviar formularios Elementor y ejecutar llamadas AJAX puede requerir el servidor original.

## Cambios de la rama de modernización

- Portada y nueve páginas institucionales mejoradas sin retirar información.
- Estilos compartidos `assets/gma-modern.css` y accesibilidad básica.
- Búsqueda local: [`/buscar/`](buscar/index.html).
- Concepto de rediseño: [`/propuesta/`](propuesta/index.html) (no indexable).
- Revisión de sitemap y robots, más chequeos automatizados.

Ver [auditoría completa](docs/AUDITORIA-2026-10-22.md).

## Vista previa local

```bash
python3 -m http.server 8000
```

Abrir `http://localhost:8000/` y la propuesta en `http://localhost:8000/propuesta/`. Ejecutar validaciones:

```bash
python3 scripts/audit_static.py
python3 scripts/inspect_archive.py
```

**No publicar este espejo sobre la web activa** hasta resolver backend, formularios, sitemap, SEO y reversión.
