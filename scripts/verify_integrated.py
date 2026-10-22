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
for file in ["404.html","_headers","robots.txt","assets/gma-content.css"]:
    if not (DEST/file).exists():fail("falta recurso de producción: "+file)
print(json.dumps({
    "public_original_pages":len(original_pages),
    "uploaded_public_assets":len(assets),
    "search_entries":len(index),
    "local_image_references_missing":len(missing_images),
    "unsafe_interactive_original_pages":len(invalid)
},ensure_ascii=False))
