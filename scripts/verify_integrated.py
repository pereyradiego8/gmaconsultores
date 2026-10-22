#!/usr/bin/env python3
"""Guardrail for complete public archive import in the renewed GMA site."""
from __future__ import annotations
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"preview-dist"
def fail(message:str)->None:
    raise SystemExit("Integración incompleta: "+message)
if not DEST.is_dir():fail("no se creó preview-dist")
assets=list((DEST/"wp-content/uploads").rglob("*"))
assets=[f for f in assets if f.is_file()]
if len(assets)<700:fail("faltan imágenes y archivos originales: "+str(len(assets)))
html_files=list(DEST.rglob("index.html"))
if len(html_files)<430:fail("faltan páginas conservadas: "+str(len(html_files)))
must_have=[
 "consultoria/index.html","impuestos/index.html","auditoria/index.html",
 "outsourcing/index.html","rrhh/index.html","quienes-somos/index.html",
 "novedades/index.html","oportunidades/index.html","category/newsletter/index.html",
 "analista-de-impuestos-sr/index.html","propuesta/index.html","buscar/index.html"
]
for path in must_have:
    if not (DEST/path).exists():fail("falta una ruta esencial: "+path)
    text=(DEST/path).read_text(encoding="utf-8")
    if 'lang="es"' not in text:fail("falta idioma en "+path)
    if '<meta name="viewport"' not in text:fail("no responsive: "+path)
    if 'gma-preview.css' not in text and path not in {"buscar/index.html"}:
        fail("estilos del sitio nuevo no encontrados en "+path)
    if '<main' not in text:fail("falta landmark main: "+path)
    if not re.search(r'<h1[\s>]',text):fail("falta H1: "+path)

original_pages=[f for f in html_files if len(f.relative_to(DEST).parts)>1 and
               f.relative_to(DEST).parts[0] not in {"buscar","propuesta"}]
invalid=[]
missing_images=set()
for f in original_pages:
    content=f.read_text(encoding="utf-8")
    if '<form ' in content.lower() or '<script ' in content.lower():
        invalid.append(f.relative_to(DEST).as_posix())
    if "gma-content" not in content:
        invalid.append(f.relative_to(DEST).as_posix()+" [sin contenido integrado]")
    for src in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"',content,re.I):
        parsed=urlsplit(src)
        path=parsed.path
        if not parsed.netloc and path.startswith("/") and not (DEST/unquote(path).lstrip("/")).is_file():
            missing_images.add(path)
if invalid:fail("formularios/scripts originales activos o páginas incompletas: "+", ".join(invalid[:8]))
if missing_images:fail("faltan archivos de imagen referenciados: "+", ".join(sorted(missing_images)[:8]))
index=json.loads((DEST/"assets/gma-search-index.json").read_text(encoding="utf-8"))
if len(index)<345:fail("faltan resultados de búsqueda: "+str(len(index)))
no_target=[item["url"] for item in index if not (
    DEST/item["url"].lstrip("/")/"index.html").is_file()]
if no_target:fail("índice apunta a rutas ausentes: "+", ".join(no_target[:10]))
search=(DEST/"assets/gma-search.js").read_text(encoding="utf-8")
if "link.href='..'+item.url" not in search:fail("el buscador no enlaza a las páginas importadas")
if "https://gmaconsultores.com.ar'+item.url" in search:fail("el buscador todavía redirige contenido importado")
first=(DEST/"category/newsletter/index.html").read_text(encoding="utf-8")
second=(DEST/"category/newsletter/page/2/index.html").read_text(encoding="utf-8")
if 'href="/category/newsletter/page/2/"' not in first:
    fail("la paginación newsletter no apunta a la página 2 local")
if 'href="/category/newsletter/"' not in second:
    fail("la página 2 de newsletter no tiene acceso a la primera página local")
# User-facing forms must exist and never submit personal data to a
# nonexistent or logging endpoint: they explicitly hand off to email clients.
contact=(DEST/"propuesta/contacto/index.html").read_text(encoding="utf-8")
jobs=(DEST/"propuesta/oportunidades/index.html").read_text(encoding="utf-8")
news=(DEST/"propuesta/novedades/index.html").read_text(encoding="utf-8")
for content,form_id,to in [
    (contact,"gma-contact-form","info@gmaconsultores.com.ar"),
    (jobs,"gma-application-form","rrhh@gmaconsultores.com.ar"),
    (news,"gma-newsletter-form","info@gmaconsultores.com.ar")
]:
    if 'id="'+form_id+'"' not in content:
        fail("falta formulario "+form_id)
    if 'action="mailto:'+to+'"' not in content:
        fail("el formulario no utiliza el contacto verificado: "+form_id)
    if 'type="email"' not in content or 'required' not in content:
        fail("faltan controles de validación: "+form_id)
    if "gma-forms.js" not in content or "gma-forms.css" not in content:
        fail("faltan recursos de formularios: "+form_id)
if '<section class="section"><div class="container">' not in jobs:
    fail("falta el listado de oportunidades de trabajo")
if 'Seleccioná una oportunidad' not in jobs:
    fail("falta selector de puestos")
if 'GMA_JOB_OPTIONS' in jobs:
    fail("no se generaron opciones de puestos")
if 'href="/propuesta/oportunidades/?puesto=' not in jobs and 'API pública de vacantes no disponible' not in jobs:
    # A zero-post WP category is also legitimate; don't imply active jobs.
    if 'No hay avisos publicados' not in jobs and 'No fue posible confirmar' not in jobs:
        fail("faltan botones de postulación relacionados a vacantes")
formjs=(DEST/"assets/gma-forms.js").read_text(encoding="utf-8")
if 'mailto:' not in formjs or 'fetch(' in formjs:
    fail("formulario cliente envía datos sin backend autorizado")
headers=(DEST/"_headers").read_text(encoding="utf-8")
if "form-action 'self' mailto:" not in headers:
    fail("CSP bloquea el fallback seguro de los formularios")
for file in ["404.html","_headers","robots.txt","assets/gma-content.css"]:
    if not (DEST/file).exists():fail("falta recurso de producción: "+file)
print(json.dumps({
    "public_original_pages":len(original_pages),
    "uploaded_public_assets":len(assets),
    "search_entries":len(index),
    "local_image_references_missing":len(missing_images),
    "unsafe_interactive_original_pages":len(invalid)
},ensure_ascii=False))
