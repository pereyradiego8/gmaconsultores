#!/usr/bin/env python3
"""Prepare the static mirror for local preview (no hosting or deployment).

The WordPress export is immutable input. Run:
  python3 scripts/build_static.py --output dist
  python3 -m http.server 8000 -d dist
Requires only Python 3.10+. Never executes WordPress/plugin code.
"""
from __future__ import annotations
import argparse
import html
import json
import re
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CANONICAL="https://gmaconsultores.com.ar"
OMIT={".git",".github",".venv","dist","reports","scripts","docs","__pycache__","node_modules"}
OG_DESC=re.compile(r'<meta\b[^>]*\bproperty=["\']og:description["\'][^>]*>',re.I)
OG_TITLE=re.compile(r'<meta\b[^>]*\bproperty=["\']og:title["\'][^>]*>',re.I)
CONTENT_ATTR=re.compile(r'\bcontent=["\'](.*?)["\']',re.I|re.S)
TITLE=re.compile(r"<title[^>]*>(.*?)</title>",re.I|re.S)
HEAD_END=re.compile(r"</head\s*>",re.I)
BODY_START=re.compile(r"<body\b[^>]*>",re.I)
SEARCH_ACTION=re.compile(r'(\baction=)(["\'])(?:\.\./)*embed/index\.html\2',re.I)
CLEAN_TAGS=re.compile(r"<[^>]+>")
UNWANTED=re.compile(r"<(?:script|style|noscript|iframe)\b[^>]*>.*?</(?:script|style|noscript|iframe)>",re.I|re.S)
SOURCE_PATHS=ROOT/"assets/gma-search-index.json"

def plain(value:str)->str:
    value=UNWANTED.sub(" ",value)
    return " ".join(html.unescape(CLEAN_TAGS.sub(" ",value)).split())

def attr(tag:str)->str:
    m=CONTENT_ATTR.search(tag)
    return plain(m.group(1)) if m else ""

def source_meta(markup:str,regex:re.Pattern)->str:
    match=regex.search(markup)
    return attr(match.group(0)) if match else ""

def title_from(markup:str,default:str)->str:
    m=TITLE.search(markup)
    title=plain(m.group(1)) if m else ""
    return title or source_meta(markup,OG_TITLE) or default

def description_from(markup:str,title:str)->str:
    original=source_meta(markup,OG_DESC)
    if original:
        return original[:157].rsplit(" ",1)[0].rstrip(" ,;:") if len(original)>160 else original
    m=re.search(r"<main\b[^>]*>(.*?)</main>",markup,re.I|re.S)
    if m:
        p=re.search(r"<p\b[^>]*>(.*?)</p>",m.group(1),re.I|re.S)
        if p:
            cleaned=plain(p.group(1))
            if 25<len(cleaned)<3000:
                return cleaned[:157].rsplit(" ",1)[0].rstrip(" ,;:") if len(cleaned)>160 else cleaned
    return ""

def url_for(file:Path)->str:
    # Keep the original indexed URLs. Files with query-style names are alias exports.
    relative=file.relative_to(ROOT).as_posix()
    if relative=="index.html":return "/"
    return "/"+relative.removesuffix("index.html")

def transform(markup:str,file:Path)->tuple[str,dict]:
    info={"css":False,"description":False,"search":0,"alias_noindex":False}
    if not re.search(r"<html\b",markup,re.I) or not HEAD_END.search(markup):
        return markup,info
    relative=file.relative_to(ROOT).as_posix()
    prefix="../"*(len(file.relative_to(ROOT).parts)-1)
    inject=[]
    if "gma-modern.css" not in markup:
        inject.append(f'<link rel="stylesheet" href="{prefix}assets/gma-modern.css">')
        info["css"]=True
    if not re.search(r'<meta\b[^>]*name=["\']description["\']',markup,re.I):
        desc=description_from(markup,title_from(markup,file.parent.name))
        if desc:
            inject.append('<meta name="description" content="'+html.escape(desc,quote=True)+'">')
            info["description"]=True
    alias=(relative.startswith("index.html@") or relative.startswith("author/admin/"))
    if alias and not re.search(r'<meta\b[^>]*name=["\']robots["\']',markup,re.I):
        inject.append('<meta name="robots" content="noindex,follow">')
        info["alias_noindex"]=True
    # Do not fabricate an authoritative canonical if the export already declares one.
    if not alias and not re.search(r'<link\b[^>]*rel=["\']canonical["\']',markup,re.I):
        inject.append('<link rel="canonical" href="'+CANONICAL+html.escape(url_for(file),quote=True)+'">')
    if inject:
        markup=HEAD_END.sub("\n"+"\n".join(inject)+"\n</head>",markup,count=1)
    if "gma-skip-link" not in markup and re.search(r'<main\b[^>]*\bid=["\']main["\']',markup,re.I):
        markup=BODY_START.sub(lambda m:m.group(0)+'\n<a class="gma-skip-link" href="#main">Saltar al contenido principal</a>',markup,count=1)
    markup,n=SEARCH_ACTION.subn(lambda m:m.group(1)+m.group(2)+prefix+"buscar/index.html"+m.group(2),markup)
    info["search"]=n
    return markup,info

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="dist",help="new directory inside repository; never deploys")
    args=parser.parse_args()
    output=ROOT/args.output
    if not args.output or Path(args.output).is_absolute() or len(Path(args.output).parts)!=1 or args.output in OMIT or args.output.startswith("."):
        parser.error("output must be a new top-level directory such as dist")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    stats={"copied_files":0,"transformed_html":0,"css_added":0,"descriptions_added":0,"search_forms_repaired":0,"alias_noindex":0}
    for file in ROOT.rglob("*"):
        if not file.is_file() or any(part in OMIT or part==args.output for part in file.relative_to(ROOT).parts):
            continue
        if file.name in {"README.md",".gitignore"}:
            continue
        relative=file.relative_to(ROOT)
        target=output/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        if file.suffix.lower()==".html":
            original=file.read_text(encoding="utf-8",errors="replace")
            result,counts=transform(original,file)
            target.write_text(result,encoding="utf-8")
            if "<html" in original.lower():stats["transformed_html"]+=1
            stats["css_added"]+=int(counts["css"])
            stats["descriptions_added"]+=int(counts["description"])
            stats["search_forms_repaired"]+=counts["search"]
            stats["alias_noindex"]+=int(counts["alias_noindex"])
        else:
            shutil.copy2(file,target)
        stats["copied_files"]+=1
    existing=json.loads(SOURCE_PATHS.read_text(encoding="utf-8"))
    enriched=[]
    for item in existing:
        url=item["url"]
        if url=="/buscar/":
            continue
        filepath=(ROOT/url.lstrip("/")/"index.html") if url.endswith("/") else ROOT/url.lstrip("/")
        if not filepath.is_file():continue
        text=filepath.read_text(encoding="utf-8",errors="replace")
        title=title_from(text,item["title"])
        desc=description_from(text,title)
        match=re.search(r'<main\b[^>]*>(.*?)</main>',text,re.I|re.S)
        body=plain(match.group(1))[:650] if match else ""
        # Use page title/body rather than URL-only slug: no synthetic content.
        enriched.append({"title":title,"url":url,"type":item["type"],"description":desc,"body":body})
    (output/"assets/gma-search-index.json").write_text(json.dumps(enriched,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    stats["indexed_pages"]=len(enriched)
    stats["index_bytes"]=(output/"assets/gma-search-index.json").stat().st_size
    report=ROOT/"reports/gma-build.json"
    report.parent.mkdir(exist_ok=True)
    report.write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(stats,ensure_ascii=False,indent=2))
    print("Build local disponible en:",output)

if __name__=="__main__":
    main()
