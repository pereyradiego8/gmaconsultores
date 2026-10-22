#!/usr/bin/env python3
"""Migrate the readable public HTML archive into the GMA redesign.

No WordPress PHP/plugin execution. All form submissions, applications, and
newsletter flows continue at the official origin until a real backend exists.
Use only Python stdlib. The original repository files remain untouched.
"""
from __future__ import annotations

import html
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://gmaconsultores.com.ar"
HEAD = re.compile(r"</head\s*>", re.I)
ARTICLE = re.compile(r"<article\b[^>]*>.*?</article\s*>", re.I | re.S)
MAIN = re.compile(r"<main\b[^>]*>.*?</main\s*>", re.I | re.S)
TAG = re.compile(r"<[^>]+>", re.S)
TITLE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.I | re.S)
HEADING = re.compile(r"<h[1234]\b[^>]*>(.*?)</h[1234]>", re.I | re.S)
A_TAG = re.compile(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>", re.I | re.S)
BODY_TEXT = re.compile(r"<div\b[^>]*class=[\"'][^\"']*\bpost-content\b[^\"']*[\"'][^>]*>", re.I)
CONTROL = {"script", "style", "noscript", "iframe", "form", "input", "select",
           "option", "textarea", "button", "svg", "canvas", "video", "audio"}
CONTROL_VOID = {"input", "br", "hr", "img", "source", "track", "embed"}
ALLOWED = {"h2", "h3", "h4", "p", "strong", "b", "em", "i", "u", "ul", "ol", "li",
           "blockquote", "figure", "figcaption", "table", "thead", "tbody",
           "tfoot", "tr", "td", "th", "br", "hr", "code", "pre", "a", "img",
           "sup", "sub", "small"}
EMPTY = {"img", "br", "hr"}
ARCHIVE_EXCLUDE = {".git", ".github", "scripts", "docs", "reports", "dist",
                   "preview-dist", "preview-test", "propuesta", "buscar",
                   "node_modules", "wp-content", "wp-includes", "wp-admin"}


def clean_text(source: str) -> str:
    return " ".join(html.unescape(TAG.sub(" ", source)).split())


def get_attr(source: str, name: str) -> str:
    m = re.search(r'\b' + re.escape(name) + r'\s*=\s*(["\'])(.*?)\1', source, re.I | re.S)
    return html.unescape(m.group(2)) if m else ""


def public_path(relative: str) -> str:
    return "/" + relative[:-10] if relative.endswith("index.html") else "/" + relative


def safe_target(raw: str, current: str, local_routes: set[str], assets: set[str]) -> str | None:
    value = html.unescape(raw.strip())
    if not value or value.startswith(("javascript:", "data:", "vbscript:", "blob:")):
        return None
    if value.startswith("#"):
        return value
    if value.lower().startswith(("mailto:", "tel:")):
        return value
    url = urlsplit(urljoin(ORIGIN + current, value))
    if url.scheme not in ("http", "https"):
        return None
    if url.netloc.lower() in ("gmaconsultores.com.ar", "www.gmaconsultores.com.ar"):
        path = unquote(url.path)
        if path.startswith("/wp-content/uploads/") and path.lstrip("/") in assets:
            return url.path + (("?" + url.query) if url.query else "")
        if path in local_routes and not url.query:
            return path + ("#" + url.fragment if url.fragment else "")
        # Dynamic endpoints and uncopied article URLs must stay functional on WP.
        return ORIGIN + url.path + (("?" + url.query) if url.query else "") + \
            (("#" + url.fragment) if url.fragment else "")
    return url.geturl()


def first_post_content(markup: str) -> str:
    m = BODY_TEXT.search(markup)
    if not m:
        return ""
    begin = m.end()
    depth = 1
    for tag in re.finditer(r"</?div\b[^>]*>", markup[begin:], re.I):
        if tag.group(0).startswith("</"):
            depth -= 1
        else:
            depth += 1
        if depth == 0:
            return markup[begin:begin + tag.start()]
    return markup[begin:]


class ContentSanitizer(HTMLParser):
    """Semantic, safe subset; strip WP JavaScript, forms, builders, embeds."""
    def __init__(self, route: str, valid: set[str], assets: set[str]):
        super().__init__(convert_charrefs=True)
        self.route, self.valid, self.assets = route, valid, assets
        self.parts: list[str] = []
        self.stack: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        if self.skip:
            if tag not in CONTROL_VOID:
                self.skip += 1
            return
        if tag in CONTROL:
            if tag not in CONTROL_VOID:
                self.skip = 1
            return
        if tag not in ALLOWED:
            return
        props = dict(attributes)
        if tag == "img":
            raw = props.get("src") or props.get("data-src") or ""
            target = safe_target(raw, self.route, self.valid, self.assets)
            if not target or not target.startswith(("https://", "/")):
                return
            image = f'<img src="{html.escape(target, quote=True)}" alt="{html.escape(props.get("alt") or "", quote=True)}" loading="lazy" decoding="async"'
            for dim in ("width", "height"):
                if (props.get(dim) or "").isdigit():
                    image += f' {dim}="{props[dim]}"'
            self.parts.append(image + ">")
            return
        if tag == "a":
            target = safe_target(props.get("href") or "", self.route, self.valid, self.assets)
            if target:
                self.parts.append(f'<a href="{html.escape(target, quote=True)}">')
                self.stack.append("a")
            else:
                self.stack.append("")
            return
        self.parts.append("<" + tag + ">")
        if tag not in EMPTY:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if self.skip:
            if tag not in CONTROL_VOID:
                self.skip -= 1
            return
        if tag not in ALLOWED or tag in EMPTY:
            return
        if not self.stack:
            return
        if tag in self.stack:
            # Malformed source HTML should not produce unclosed nested tags.
            while self.stack:
                open_tag = self.stack.pop()
                if open_tag:
                    self.parts.append("</" + open_tag + ">")
                if open_tag == tag:
                    break

    def handle_data(self, text: str) -> None:
        if not self.skip and text.strip():
            self.parts.append(html.escape(text))

    def handle_entityref(self, name: str) -> None:
        if not self.skip:
            self.parts.append(html.escape(html.unescape("&" + name + ";")))

    def handle_charref(self, name: str) -> None:
        if not self.skip:
            self.parts.append(html.escape(html.unescape("&#" + name + ";")))

    def result(self) -> str:
        while self.stack:
            tag = self.stack.pop()
            if tag:
                self.parts.append("</" + tag + ">")
        return "".join(self.parts)


def name_image_only_links(content: str) -> str:
    """Supply discernible names for old linked logos with empty alt text."""
    def fix(match: re.Match[str]) -> str:
        opening, interior = match.group(1), match.group(2)
        if clean_text(interior):
            return match.group(0)
        alt = re.search(r'<img\b[^>]*\balt=["\']([^"\']+)', interior, re.I)
        if alt and html.unescape(alt.group(1)).strip():
            return match.group(0)
        href = get_attr(opening, "href")
        parsed = urlsplit(href)
        short = parsed.netloc.replace("www.", "") or parsed.path.strip("/").split("/")[-1]
        short = re.sub(r"[^a-zA-Z0-9áéíóúñÁÉÍÓÚÑ ._-]", " ", short).strip()[:62]
        label = "Abrir enlace relacionado" + (": " + short if short else "")
        if "aria-label=" in opening:
            return match.group(0)
        return opening[:-1] + ' aria-label="' + html.escape(label, quote=True) + '">' + interior + "</a>"
    return re.sub(r'(<a\b[^>]*href=["\'][^"\']+["\'][^>]*>)(.*?)</a>', fix,
                  content, flags=re.I | re.S)


def listing_from_articles(markup: str, route: str, valid: set[str], assets: set[str]) -> str:
    cards = []
    seen = set()
    for match in ARTICLE.finditer(markup):
        article = match.group(0)
        header = HEADING.search(article)
        if not header:
            continue
        title = clean_text(header.group(1))
        anchor = A_TAG.search(header.group(1)) or A_TAG.search(article)
        if not anchor or not title:
            continue
        href = safe_target(anchor.group(1), route, valid, assets)
        if not href or href in seen:
            continue
        seen.add(href)
        cards.append('<article class="simple-item"><h3>' +
                     html.escape(title) + '</h3><a class="button secondary" href="' +
                     html.escape(href, quote=True) + '">Leer publicación →</a></article>')
    if not cards:
        return ""
    # Source pagination may use a generated permalink to the next archive page.
    pagination = []
    for a in re.finditer(r'<a\b[^>]*class=["\'][^"\']*(?:pagination|next|prev)[^"\']*["\'][^>]*>.*?</a>', markup, re.I | re.S):
        href = get_attr(a.group(0), "href")
        dest = safe_target(href, route, valid, assets)
        label = clean_text(a.group(0))
        if dest and (dest not in pagination) and len(pagination) < 14:
            pagination.append(dest)
    nav = "".join('<a class="button secondary" href="' +
                  html.escape(h, quote=True) + '">Más publicaciones →</a>' for h in pagination)
    return '<div class="simple-list">' + "".join(cards) + '</div>' + \
        ('<nav class="actions archive-pages" aria-label="Páginas del archivo">' + nav + '</nav>' if nav else "")


def chrome(title: str, route: str, description: str, content: str,
           form_notice: bool) -> str:
    esc = html.escape
    clean_title = re.sub(r"\s*[|–-]\s*GMA(?:\s+Consultores)?\s*$","",title or "Contenido",flags=re.I).strip()
    label = esc(clean_title[:170])
    root_title = esc(clean_title[:150])
    notice = (
        '<aside class="archive-note"><p>Las consultas, postulaciones y suscripciones '
        'se procesan en el sitio oficial. Para enviar datos o completar un formulario '
        'utilizá <a href="' + ORIGIN + esc(route, quote=True) +
        '">el formulario original de GMA ↗</a>.</p></aside>'
    ) if form_notice else ""
    nav = (('<a href="/propuesta/nosotros/">Nosotros</a>'
            '<a href="/propuesta/servicios/">Servicios</a>'
            '<a href="/propuesta/novedades/">Novedades</a>'
            '<a href="/propuesta/oportunidades/">Oportunidades</a>'
            '<a href="/buscar/">Buscar</a>'
            '<a class="top-cta" href="/propuesta/contacto/">Contacto ↗</a>'))
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,follow">
<meta name="description" content="{esc(description[:160], quote=True)}">
<title>{label} | GMA Consultores</title>
<link rel="icon" href="/wp-content/uploads/2020/07/GMA.-Web.-Favicon.png">
<link rel="stylesheet" href="/assets/gma-preview.css">
<link rel="stylesheet" href="/assets/gma-content.css"></head><body>
<a class="skip" href="#contenido">Saltar al contenido</a>
<header><div class="container head-inner">
<a class="brand" href="/propuesta/" aria-label="GMA Consultores, volver al inicio">
<img width="135" height="55" src="/wp-content/uploads/2020/08/GMA.-Web.-Logo2.png" alt="GMA Consultores"></a>
<nav class="desktop-nav" aria-label="Navegación principal">{nav}</nav>
<details class="mobile-nav"><summary>Menú</summary>
<nav aria-label="Navegación móvil">{nav}</nav></details></div></header>
<main id="contenido">
<section class="subhero"><div class="container">
<div class="breadcrumb"><a href="/propuesta/">Inicio</a> / Archivo del sitio</div>
<p class="eyebrow">GMA Consultores · contenido conservado</p>
<h1>{root_title}</h1></div></section>
<section class="section"><div class="container two-columns">
<article class="text-panel gma-content">{content}{notice}
<div class="archive-actions"><a class="button primary" href="/buscar/">Buscar otros contenidos →</a>
<a class="button secondary" href="{ORIGIN}{esc(route, quote=True)}">Consultar en la web oficial ↗</a></div></article>
<aside class="aside"><h3>Explorá GMA</h3>
<a href="/propuesta/servicios/">Servicios <span>→</span></a>
<a href="/propuesta/novedades/">Novedades <span>→</span></a>
<a href="/propuesta/oportunidades/">Oportunidades <span>→</span></a>
<a href="/propuesta/contacto/">Contacto <span>→</span></a>
<a href="/buscar/">Buscador <span>→</span></a></aside>
</div></section></main>
<footer><div class="container foot"><div>GMA Consultores · Archivo histórico integrado</div>
<nav aria-label="Enlaces del pie"><a href="/propuesta/">Inicio</a>
<a href="/propuesta/contacto/">Contacto</a><a href="{ORIGIN}">Sitio original</a></nav>
</div></footer></body></html>'''


def import_archive(dest: Path) -> dict:
    # Build a route set before processing, so old internal links can be kept.
    sources = []
    for file in ROOT.rglob("index.html"):
        rel = file.relative_to(ROOT)
        if rel.parts[0] in ARCHIVE_EXCLUDE or len(rel.parts) < 2:
            continue
        if "embed" in rel.parts or "feed" in rel.parts:
            continue
        sources.append((file, public_path(rel.as_posix())))
    valid = {route for _, route in sources}
    valid.update({"/propuesta/", "/propuesta/servicios/", "/propuesta/novedades/",
                  "/propuesta/contacto/", "/propuesta/nosotros/",
                  "/propuesta/oportunidades/", "/buscar/"})
    assets = set()
    total_bytes = 0
    image_count = 0
    for asset in (ROOT/"wp-content/uploads").rglob("*"):
        if not asset.is_file() or asset.suffix.lower() not in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".pdf"}:
            continue
        if asset.stat().st_size > 25 * 1024 * 1024:
            print("AVISO: archivo demasiado grande para Pages:", asset)
            continue
        rel = asset.relative_to(ROOT)
        target = dest/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset, target)
        assets.add(rel.as_posix())
        image_count += 1
        total_bytes += asset.stat().st_size
    created = 0
    indexed = 0
    archived = 0
    no_content = []
    for src, route in sources:
        document = src.read_text(encoding="utf-8", errors="replace")
        match = MAIN.search(document)
        if not match:
            continue
        main = match.group(0)
        heading = re.search(r"<h1\b[^>]*>(.*?)</h1>", main, re.I | re.S)
        title = clean_text(heading.group(1)) if heading else ""
        if not title:
            t = TITLE.search(document)
            title = clean_text(t.group(1)) if t else route.strip("/").replace("-", " ").title()
        if not title:
            title = "GMA Consultores"
        description = title + " — publicaciones y servicios profesionales de GMA Consultores."
        articles = list(ARTICLE.finditer(main))
        is_listing = (len(articles) >= 2)
        if is_listing:
            body = listing_from_articles(main, route, valid, assets)
        else:
            post_content = first_post_content(main)
            if not post_content and articles:
                post_content = articles[0].group(0)
            if post_content:
                sanitizer = ContentSanitizer(route, valid, assets)
                sanitizer.feed(post_content)
                body = name_image_only_links(sanitizer.result())
            else:
                body = ""
        plain = clean_text(body)
        if len(plain) < 30:
            no_content.append(route)
            continue
        has_forms = bool(re.search(r'<form\b[^>]*(?:elementor|newsletter|contact)', main, re.I))
        if route.startswith(("/oportunidades/", "/contacto/", "/base-de-talentos/")):
            has_forms = True
        target = dest / route.lstrip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(chrome(title, route, description, body, has_forms), encoding="utf-8")
        created += 1
        indexed += int(not is_listing)
        archived += int(is_listing)
    print(json.dumps({"imported_public_pages":created,
                      "single_pages":indexed, "archive_listings":archived,
                      "skipped_empty_pages":len(no_content),
                      "assets_copied":image_count,"asset_bytes":total_bytes,
                      "empty_examples":no_content[:20]},ensure_ascii=False))
    return {"pages":created, "assets":image_count, "missing":no_content}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="preview-dist")
    args = parser.parse_args()
    report = import_archive(ROOT/args.output)
    if report["pages"] < 300:
        raise SystemExit("Se esperaba conservar cientos de páginas del sitio original")
