#!/usr/bin/env python3
"""Inspect local HTML links and file references without touching network services.

This reports missing resources; legacy WordPress routes can legitimately require
a backend and are not automatically rewritten or deleted.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit
from html import unescape
import argparse
import json
import re

ROOT=Path(__file__).resolve().parents[1]
ATTR=re.compile(r'(?<![\w-])(href|src|action)=([\'"])(.*?)\2',re.I|re.S)
SKIP={"mailto","tel","javascript","data","blob","sms","whatsapp","intent","ftp"}
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--root",default=".")
 parser.add_argument("--output",default="reports/gma-links.json")
 parser.add_argument("--focus",default="",help="Comprobar solo páginas bajo una subcarpeta, por ejemplo propuesta/")
 parser.add_argument("--strict",action="store_true",help="Fail when any local resource is missing (not recommended on imported WordPress archives)")
 args=parser.parse_args()
 root=(ROOT/args.root).resolve()
 counts=Counter()
 bad=[]
 missing_by_file=Counter()
 checked=0
 for page in root.rglob("*.html"):
  if any(part in {".git","reports","dist","node_modules"} for part in page.relative_to(root).parts):continue
  if args.focus and not page.relative_to(root).as_posix().startswith(args.focus):continue
  html=page.read_text(encoding="utf-8",errors="replace")
  if not re.search(r"<html\b",html,re.I):continue
  checked+=1
  for kind,_,raw in ATTR.findall(html):
   link=unescape(raw).strip()
   if not link or link.startswith("#"):continue
   parsed=urlsplit(link)
   if parsed.scheme.lower() in SKIP or parsed.scheme or parsed.netloc:continue
   if link.startswith("//"):continue
   target=unquote(parsed.path)
   if not target:continue
   if target.startswith("/"):file=root/target.lstrip("/")
   else:file=page.parent/target
   if file.is_dir() or (not file.exists() and (target.endswith("/") or not Path(target).suffix)):
    file=file/"index.html"
   counts[kind.lower()+"_checked"]+=1
   if not file.is_file():
    counts[kind.lower()+"_missing"]+=1
    missing_by_file[page.relative_to(root).as_posix()]+=1
    if len(bad)<70:bad.append({"page":page.relative_to(root).as_posix(),"attribute":kind.lower(),"reference":link[:220]})
 stats={"pages_scanned":checked,**counts}
 report={"scope":"Local references in HTML; no network or back-end availability tests","counts":stats,"missing_samples":bad,
         "pages_with_most_missing_references":missing_by_file.most_common(25)}
 outfile=(ROOT/args.output)
 outfile.parent.mkdir(parents=True,exist_ok=True)
 outfile.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 print(json.dumps(stats,ensure_ascii=False))
 print("Ejemplos reportados:",len(bad))
 print("Primeras referencias faltantes:",json.dumps(bad[:18],ensure_ascii=False))
 print("Páginas con más referencias faltantes:",json.dumps(missing_by_file.most_common(12),ensure_ascii=False))
 print("Reporte:",outfile.relative_to(ROOT))
 if args.strict and sum(n for k,n in counts.items() if k.endswith("_missing")):raise SystemExit(1)
if __name__=="__main__":main()
