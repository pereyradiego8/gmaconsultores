#!/usr/bin/env python3
"""Full-file inventory and non-executing checks of the mirrored WordPress archive.
Creates an evidence report; it does not claim runtime/performance/security penetration testing.
"""
from __future__ import annotations
from collections import Counter
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse
import json
import re

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT.rglob("*.html")
TAG_IMAGE=re.compile(r"<img\b[^>]*>",re.I)
TAG_FORM=re.compile(r"<form\b[^>]*>",re.I)
SRC=re.compile(r"\bsrc\s*=\s*['\"]([^'\"]+)['\"]",re.I)
TITLE=re.compile(r"<title[^>]*>(.*?)</title>",re.I|re.S)
H1=re.compile(r"<h1\b",re.I)
summary=Counter()
titles=Counter()
sample_missing_images=[]
pages_missing_title=[]
all_paths=list(ROOT.rglob("*"))
summary["files_total"]=sum(p.is_file() for p in all_paths)
summary["file_bytes"]=sum(p.stat().st_size for p in all_paths if p.is_file())
for file in HTML:
 path=file.relative_to(ROOT).as_posix()
 try: html=file.read_text(encoding="utf-8",errors="replace")
 except OSError: summary["html_unreadable"]+=1; continue
 summary["html_pages"]+=1
 match=TITLE.search(html)
 if match:
  title=unescape(re.sub(r"<[^>]*>","",match.group(1))).strip()
  if title: titles[title]+=1
  else:summary["html_missing_title"]+=1
 else:
  summary["html_missing_title"]+=1
  if len(pages_missing_title)<15:pages_missing_title.append(path)
 if not re.search(r"<html\b[^>]*\blang=",html,re.I): summary["html_missing_lang"]+=1
 if not re.search(r"<meta\b[^>]*name=['\"]viewport",html,re.I):summary["html_missing_viewport"]+=1
 if not re.search(r"<meta\b[^>]*name=['\"]description",html,re.I):summary["html_missing_description"]+=1
 if not re.search(r"<link\b[^>]*rel=['\"]canonical",html,re.I):summary["html_missing_canonical"]+=1
 if not H1.search(html):summary["html_missing_h1"]+=1
 if "googletagmanager.com" in html:summary["html_with_gtm_reference"]+=1
 if "admin-ajax.php" in html:summary["html_with_wp_ajax_reference"]+=1
 for form in TAG_FORM.findall(html):
  summary["form_tags"]+=1
  if "elementor-form" in form:summary["elementor_forms"]+=1
 for img in TAG_IMAGE.findall(html):
  summary["image_tags"]+=1
  if not re.search(r"\balt\s*=",img,re.I):summary["image_tags_without_alt"]+=1
  m=SRC.search(img)
  if not m:continue
  src=unescape(m.group(1)).strip()
  if not src or src.startswith(("http:","https:","data:","//")):continue
  p=urlsplit(src).path
  if not p:continue
  target=(ROOT/p.lstrip("/")) if p.startswith("/") else file.parent/unquote(p)
  if not target.is_file():
   summary["local_image_references_missing"]+=1
   if len(sample_missing_images)<25:
    sample_missing_images.append({"page":path,"src":src[:160]})
report={
 "scope":"Static repository files only; not a live-browser or WordPress backend test",
 "metrics":dict(summary),
 "repeated_html_titles":titles.most_common(15),
 "sample_missing_title":pages_missing_title,
 "sample_missing_local_images":sample_missing_images,
 "notes":[
  "Duplicate titles may be caused by mirrored alias/query pages",
  "WordPress AJAX and Elementor form tags are not proof of a functional backend on static hosting",
  "Unreachable dynamic or external resources are not fully assessed",
  "Lighthouse, LCP, INP and CLS require real browser measurements"
 ]
}
parser=argparse.ArgumentParser()
parser.add_argument("--output",default="reports/gma-static-audit.json")
args=parser.parse_args()
out=ROOT/args.output
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report["metrics"],ensure_ascii=False,indent=2))
print("Reporte guardado en:",out.relative_to(ROOT))
