#!/usr/bin/env python3
"""Regression tests comparing original WordPress HTML to the local static build."""
from __future__ import annotations
from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"dist"
KEY=[
"index.html","quienes-somos/index.html","consultoria/index.html",
"impuestos/index.html","auditoria/index.html","outsourcing/index.html",
"rrhh/index.html","novedades/index.html","oportunidades/index.html",
"contacto/index.html"]
errors=[]
def expect(ok,msg):
 if not ok: errors.append(msg)

for page in KEY:
 original=(ROOT/page).read_text(encoding="utf-8",errors="replace")
 built=(DEST/page).read_text(encoding="utf-8",errors="replace")
 expect(original.count("<form")==built.count("<form"),"Cambió cantidad de formularios: "+page)
 expect(original.count("<img")==built.count("<img"),"Cambió cantidad de imágenes: "+page)
 expect("gma-modern.css" in built,"Falta CSS de modernización: "+page)
 expect("gma-skip-link" in built,"Falta navegación accesible: "+page)
 expect("buscar/index.html" in built,"Falta búsqueda estática: "+page)
 if page=="index.html":
  expect(built.count("<h1")==1,"La portada debe tener un H1 único")
for name in [
 "wp-includes/css/dist/block-library/style.min.css@ver=7.0.7.css",
 "wp-includes/js/dist/hooks.min.js@ver=7496969728ca0f95732d",
 "wp-includes/js/dist/i18n.min.js@ver=781d11515ad3d91786ec",
 "assets/gma-preview.css"
]:
 expect((DEST/name).is_file(),"Asset requerido no copiado: "+name)
for name in ["index.html","servicios/index.html","nosotros/index.html",
             "novedades/index.html","oportunidades/index.html","contacto/index.html"]:
 page=DEST/"propuesta"/name
 expect(page.is_file(),"Falta la propuesta multipágina: "+name)
 if page.is_file():
  h=page.read_text(encoding="utf-8")
  expect(bool(re.search(r'noindex',h,re.I)),"La propuesta debe permanecer noindex: "+name)
index=json.loads((DEST/"assets/gma-search-index.json").read_text(encoding="utf-8"))
expect(len(index)>=300,"Índice de búsqueda incompleto")
expect(any(len(item.get("description",""))>30 for item in index),"Índice no contiene descripciones reales")
for item in index:
 path=(DEST/item["url"].lstrip("/")/"index.html") if item["url"].endswith("/") else DEST/item["url"].lstrip("/")
 expect(path.is_file(),"Entrada de búsqueda apunta a recurso ausente: "+item["url"])
summary={"institutional_pages":len(KEY),"preview_pages":6,"search_entries":len(index),"errors":len(errors)}
print(json.dumps(summary,ensure_ascii=False))
if errors:
 for msg in errors[:25]:print("ERROR:",msg)
 raise SystemExit(1)
