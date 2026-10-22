#!/usr/bin/env python3
"""Non-destructive validation for GMA's archived static WordPress pages.
Usage: python3 scripts/audit_static.py
No packages or network access required.
"""
from __future__ import annotations
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

ROOT=pathlib.Path(__file__).resolve().parents[1]
CRITICAL=[
 "index.html","quienes-somos/index.html","consultoria/index.html",
 "outsourcing/index.html","impuestos/index.html","auditoria/index.html",
 "rrhh/index.html","oportunidades/index.html","novedades/index.html",
 "contacto/index.html"]
failures=[]
warnings=[]
paths=list(ROOT.rglob("*.html"))
for path in CRITICAL:
 f=ROOT/path
 if not f.is_file():
  failures.append("Página institucional ausente: "+path)
  continue
 source=f.read_text(encoding="utf-8",errors="replace")
 prefix="../" if path!="index.html" else ""
 if '<main id="main"' not in source: warnings.append("No se detectó main: "+path)
 if 'href="'+prefix+'assets/gma-modern.css"' not in source:
  failures.append("No se carga CSS institucional: "+path)
 if 'class="gma-skip-link"' not in source:
  failures.append("Falta enlace para saltar al contenido: "+path)
 if 'action="'+prefix+'buscar/index.html"' not in source:
  failures.append("Búsqueda estática no integrada: "+path)
 if "<form class=\"elementor-form\"" not in source:
  warnings.append("Revisar formulario original: "+path)
if not (ROOT/"assets/gma-modern.css").is_file():
 failures.append("Falta CSS compartido")
try:
 data=json.loads((ROOT/"assets/gma-search-index.json").read_text(encoding="utf-8"))
 for item in data:
  target=ROOT/item["url"].lstrip("/")
  file=target/"index.html" if item["url"].endswith("/") else target
  if not file.is_file(): failures.append("Búsqueda referencia ruta inexistente: "+item["url"])
except (FileNotFoundError,ValueError,KeyError) as exc: failures.append("Índice inválido: "+str(exc))
try:
 doc=ET.parse(ROOT/"sitemap.xml")
 urls=[e.text for e in doc.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
 if not urls: failures.append("Sitemap vacío")
except (FileNotFoundError,ET.ParseError) as exc: failures.append("Sitemap inválido: "+str(exc))
robots=(ROOT/"robots.txt").read_text(encoding="utf-8")
if "wzy.php" in robots or "wpadmin.php" in robots:
 failures.append("robots.txt todavía contiene rutas PHP no aprobadas")
print(f"Archivos HTML presentes: {len(paths)}")
print(f"Entradas de búsqueda: {len(data) if 'data' in locals() else 0}")
print(f"Rutas sitemap: {len(urls) if 'urls' in locals() else 0}")
for x in warnings[:25]: print("ADVERTENCIA:",x)
for x in failures[:50]: print("ERROR:",x)
if len(failures)>50: print(f"... y {len(failures)-50} errores adicionales")
sys.exit(1 if failures else 0)
