#!/usr/bin/env python3
"""Build a lightweight Cloudflare Pages review site from the approved proposal.

Only the six 'propuesta/' pages and required local assets are published.
Historic WordPress pages/forms are *not* deployed. Links to such material
explicitly open the original gmaconsultores.com.ar. No authentication is
implemented here: use Cloudflare Access if private access is required.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from build_static import title_from, description_from, plain

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL="https://gmaconsultores.com.ar"
PREVIEW_PAGES=("index.html","nosotros/index.html","servicios/index.html",
               "novedades/index.html","oportunidades/index.html","contacto/index.html")
ASSETS=("assets/gma-preview.css","wp-content/uploads/2020/07/GMA.-Web.-Favicon.png",
       "wp-content/uploads/2020/08/GMA.-Web.-Logo2.png",
       "wp-content/uploads/2020/09/GMA.-Slider.-Asesoramiento.jpg")

def internal_to_live(page:str, markup:str)->str:
    """Retarget original-site hyperlinks only; keep proposal navigation local."""
    if page=="index.html":
        markup=markup.replace('href="../index.html"',f'href="{ORIGINAL}/"')
        markup=markup.replace('href="../buscar/"','href="/buscar/"')
    else:
        markup=markup.replace('href="../../buscar/"', 'href="/buscar/"')
        markup=markup.replace('href="../../index.html"',f'href="{ORIGINAL}/"')
        markup=re.sub(r'href="../../(?!wp-content|assets)([^"#?]+)"'
                      lambda m:'href="'+ORIGINAL+'/'+m.group(1)+'"',markup)
        # Original site's contact page is an external link, not the new preview.
    return markup

def render_search(src:str)->str:
    src=src.replace('href="../index.html"', 'href="../propuesta/"')
    src=src.replace('href="../novedades/"','href="../propuesta/novedades/"')
    src=src.replace('href="../contacto/"','href="../propuesta/contacto/"')
    src=src.replace("link.href='..'+item.url", "link.href='https://gmaconsultores.com.ar'+item.url")
    return src

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="preview-dist")
    args=p.parse_args()
    if args.output not in {"preview-dist","preview-test"}:
        p.error("Only isolated preview output directories are supported")
    dest=ROOT/args.output
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir()
    for asset in ASSETS:
        infile=ROOT/asset
        if not infile.is_file():
            raise RuntimeError("Missing source asset: "+asset)
        target=dest/asset
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(infile,target)
    for page in PREVIEW_PAGES:
        infile=ROOT/"propuesta"/page
        if not infile.is_file(): raise RuntimeError("Missing preview page: "+page)
        target=dest/"propuesta"/page
        target.parent.mkdir(parents=True,exist_ok=True)
        page_src=internal_to_live(page,infile.read_text(encoding="utf-8"))
        target.write_text(page_src,encoding="utf-8")
    search=ROOT/"buscar/index.html"
    target=dest/"buscar/index.html"
    target.parent.mkdir(exist_ok=True)
    markup=render_search(search.read_text(encoding="utf-8"))
    # Externalize inline CSS/JS for a strict, no-unsafe-inline CSP.
    style=re.search(r"<style>(.*?)</style>",markup,re.S)
    script=re.search(r"<script>(.*?)</script>",markup,re.S)
    if not style or not script:
        raise RuntimeError("Missing expected search CSS/JS: update build when templates change")
    stylesheet=style.group(1)+"\n.brand-accent{color:#b80a13}\n.visually-hidden{position:absolute;clip:rect(0 0 0 0);clip-path:inset(50%);width:1px;height:1px;overflow:hidden;white-space:nowrap}\n"
    (dest/"assets/gma-search.css").write_text(stylesheet,encoding="utf-8")
    (dest/"assets/gma-search.js").write_text(script.group(1),encoding="utf-8")
    markup=markup.replace(style.group(0),'<link rel="stylesheet" href="../assets/gma-search.css">')
    markup=markup.replace(script.group(0),'<script src="../assets/gma-search.js" defer></script>')
    markup=markup.replace('style="color:#b80a13"','class="brand-accent"')
    markup=markup.replace('style="position:absolute;clip:rect(0,0,0,0)"','class="visually-hidden"')
    if re.search(r"\\sstyle=|<style>|<script>(?!\\s*<)",markup,re.I):
        raise RuntimeError("Inline style/script remains in generated search")
    target.write_text(markup,encoding="utf-8")
    index=json.loads((ROOT/"assets/gma-search-index.json").read_text(encoding="utf-8"))
    records=[]
    for item in index:
        url=item["url"]
        if url=="/buscar/" or not url.endswith("/"):continue
        src=ROOT/url.lstrip("/")/"index.html"
        if not src.is_file():continue
        markup=src.read_text(encoding="utf-8",errors="replace")
        title=title_from(markup,item["title"])
        desc=description_from(markup,title)
        main_match=re.search(r'<main\b[^>]*>(.*?)</main>',markup,re.I|re.S)
        excerpt=plain(main_match.group(1))[:650] if main_match else ""
        records.append({"title":title,"url":url,"description":desc,
                        "body":excerpt,"type":item["type"]})
    out=dest/"assets/gma-search-index.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(records,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    (dest/"index.html").write_text('''<!doctype html><html lang="es"><head>
<meta charset="utf-8"><meta name="robots" content="noindex,nofollow">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="0;url=/propuesta/">
<title>Vista previa de GMA Consultores</title></head>
<body><p>Ver <a href="/propuesta/">la propuesta de GMA Consultores</a>.</p></body></html>''',encoding="utf-8")
    (dest/"_headers").write_text('''/*
  X-Robots-Tag: noindex, nofollow, noarchive
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: DENY
  Strict-Transport-Security: max-age=31536000
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
  Content-Security-Policy: default-src 'none'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'
''',encoding="utf-8")
    (dest/"404.html").write_text('''<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Página no encontrada | GMA Consultores</title>
<link rel="stylesheet" href="/assets/gma-preview.css"></head>
<body><main class="section"><div class="container"><p class="kicker">Error 404</p>
<h1>Página no encontrada</h1><p>El enlace que buscás no existe en esta vista previa.</p>
<a class="button primary" href="/propuesta/">Volver al inicio</a></div></main></body></html>''',encoding="utf-8")
    (dest/"robots.txt").write_text("User-agent: *\nDisallow: /\n",encoding="utf-8")
    (dest/"_redirects").write_text("/ /propuesta/ 302\n",encoding="utf-8")
    print(json.dumps({"preview_pages":len(PREVIEW_PAGES),"searchable_original_pages":len(records),
                      "file_count":sum(1 for f in dest.rglob("*") if f.is_file()),
                      "bytes":sum(f.stat().st_size for f in dest.rglob("*") if f.is_file())}))
    print("Local preview only: no Cloudflare Access or deploy performed.")

if __name__=="__main__":
    main()
