#!/usr/bin/env python3
"""Build a lightweight Cloudflare Pages review site from the approved proposal.

Only the six 'propuesta/' pages and required local assets are published.
Historic WordPress pages/forms are *not* deployed. Links to such material
explicitly open the original gmaconsultores.com.ar. No authentication is
implemented here: use Cloudflare Access if private access is required.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from build_static import title_from, description_from, plain
from import_original import import_archive, listing_from_articles, MAIN, ARTICLE

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
        def migrated_link(m):
            url="/"+m.group(1)
            # Publication detail and static archive pages now exist in the preview.
            if url in {
                "/consultoria/","/auditoria/","/impuestos/","/outsourcing/",
                "/rrhh/","/soluciones-de-back-office/","/quienes-somos/",
                "/novedades/","/oportunidades/","/base-de-talentos/",
                "/category/novedades-especiales/","/category/novedades-contables/",
                "/category/newsletter/"}:
                return 'href="'+url+'"'
            return 'href="'+ORIGINAL+url+'"'
        markup=re.sub(r'href="../../(?!wp-content|assets)([^"#?]+)"',migrated_link,markup)
        # Original site's contact page is an external link, not the new preview.
    return markup

def render_search(src:str)->str:
    src=src.replace('href="../index.html"', 'href="../propuesta/"')
    src=src.replace('href="../novedades/"','href="../propuesta/novedades/"')
    src=src.replace('href="../contacto/"','href="../propuesta/contacto/"')
    # Search results now open the imported pages on the renewed site.
    return src

def recent_public_news():
    """Read public WordPress posts at build time, without scraping private data.

    The original news archive remains linked if WordPress is unavailable.
    Content is escaped rather than injected as HTML from another origin.
    """
    uri=ORIGINAL+"/wp-json/wp/v2/posts?per_page=6&_fields=date,link,title"
    try:
        request=urllib.request.Request(uri,headers={
            "User-Agent":"GMA-Preview-Build/1.0 (+https://gmaconsultores-preview.pages.dev)",
            "Accept":"application/json"})
        with urllib.request.urlopen(request,timeout=7) as response:
            if response.status!=200:
                raise ValueError("WordPress returned HTTP "+str(response.status))
            entries=json.loads(response.read(100000).decode("utf-8"))
        valid=[]
        print("Noticias públicas recibidas de WordPress:",len(entries) if isinstance(entries,list) else "formato inválido")
        for item in entries[:6]:
            title=html.unescape(re.sub(r"<[^>]+>"," ",item.get("title",{}).get("rendered","")))
            title=" ".join(title.split())[:170]
            url=item.get("link","")
            date=item.get("date","")[:10]
            if not title or not url.startswith(ORIGINAL+"/") or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",date):
                continue
            valid.append((title,url,date))
        print("Noticias públicas validadas:",len(valid))
        return valid
    except (OSError,ValueError,KeyError,TypeError,UnicodeError) as exc:
        print("Aviso: no se pudo consultar noticias públicas de WordPress:",type(exc).__name__)
        return []

def recent_jobs_section(dest: Path) -> str:
    """Show six archived job listings within the renovated careers section.

    This is an archive, never an assertion that hiring is currently open.
    """
    source=ROOT/"oportunidades/index.html"
    text=source.read_text(encoding="utf-8",errors="replace")
    main=MAIN.search(text)
    if not main:
        return ""
    articles=ARTICLE.findall(main.group(0))[:6]
    valid={"/"+p.relative_to(dest).as_posix().removesuffix("index.html")
           for p in dest.rglob("index.html")}
    cards=listing_from_articles("".join(articles),"/oportunidades/",valid,set())
    if not cards:
        return ""
    return ('<section class="section"><div class="container">'
            '<div class="section-head"><div><p class="kicker">Archivo laboral</p>'
            '<h2>Búsquedas profesionales publicadas</h2></div>'
            '<p class="section-intro">Estos avisos provienen del archivo institucional; '
            'su vigencia debe consultarse en cada publicación.</p></div>'
            + cards + '</div></section>')


def news_section(items, dest: Path):
    if not items:
        return ""
    cards=[]
    for title,url,date in items:
        path=urlsplit(url).path
        href=path if (dest/path.lstrip("/")/"index.html").is_file() else url
        cards.append('<article class="simple-item"><p class="kicker">Publicación · '+
                     html.escape(date)+'</p><h3>'+html.escape(title)+'</h3>'+
                     '<a class="button secondary" href="'+html.escape(href,quote=True)+
                     '">Leer en la web oficial ↗</a></article>')
    return '<section class="section"><div class="container">'+\
           '<div class="section-head"><div><p class="kicker">Actualizaciones del sitio original</p>'+\
           '<h2>Publicaciones recientes</h2></div>'+\
           '<p class="section-intro">Obtenidas de la API pública de GMA durante la última compilación; verificá vigencia y fechas en la fuente.</p></div>'+\
           '<div class="simple-list">'+"".join(cards)+'</div></div></section>'

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
    imported=import_archive(dest)
    if imported["pages"]<300 or imported["assets"]<700:
        raise RuntimeError("Incomplete public archive import; aborting deploy")
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
        if page=="novedades/index.html":
            extra=news_section(recent_public_news(),dest)
            if extra:
                page_src=page_src.replace("</main>",extra+"</main>")
        if page=="oportunidades/index.html":
            extra=recent_jobs_section(dest)
            if extra:
                page_src=page_src.replace("</main>",extra+"</main>")
        if page=="servicios/index.html":
            page_src=page_src.replace("Ver contenido original ↗","Ver servicio completo →")
        if page=="nosotros/index.html":
            page_src=page_src.replace("Ver la página institucional original ↗","Conocer nuestra trayectoria →")
        if page=="novedades/index.html":
            page_src=page_src.replace("Explorar las novedades originales →","Ver archivo completo →")
        if page=="oportunidades/index.html":
            page_src=page_src.replace("Consultar oportunidades originales →","Ver archivo completo →")
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
    if re.search(r"\sstyle=|<style>|<script>(?!\s*<)",markup,re.I):
        raise RuntimeError("Inline style/script remains in generated search")
    target.write_text(markup,encoding="utf-8")
    index=json.loads((ROOT/"assets/gma-search-index.json").read_text(encoding="utf-8"))
    records=[]
    for item in index:
        url=item["url"]
        if url=="/buscar/" or not url.endswith("/"):continue
        src=ROOT/url.lstrip("/")/"index.html"
        if not src.is_file() or not (dest/url.lstrip("/")/"index.html").is_file():continue
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
  Content-Security-Policy: default-src 'none'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; script-src 'self' https://static.cloudflareinsights.com; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self' https://cloudflareinsights.com https://*.cloudflareinsights.com

/assets/*
  Cache-Control: public, max-age=300

/wp-content/*
  Cache-Control: public, max-age=3600
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
    print(json.dumps({"preview_pages":len(PREVIEW_PAGES),"imported_original_pages":imported["pages"],
                      "imported_assets":imported["assets"],"searchable_original_pages":len(records),
                      "file_count":sum(1 for f in dest.rglob("*") if f.is_file()),
                      "bytes":sum(f.stat().st_size for f in dest.rglob("*") if f.is_file())}))
    print("Local preview only: no Cloudflare Access or deploy performed.")

if __name__=="__main__":
    main()
