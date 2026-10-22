#!/usr/bin/env node
'use strict';
/* Local Chromium layout regression for the Cloudflare Pages review build.
   Run with NODE_PATH pointing to an installed playwright-core package and
   start a localhost server for preview-dist before executing. */
const fs=require('fs');
const path=require('path');
const {chromium}=require('playwright-core');

const BASE=process.env.PREVIEW_URL||'http://127.0.0.1:8765';
const CHROME=process.env.CHROME_BIN||[
  '/usr/bin/google-chrome','/usr/bin/google-chrome-stable',
  '/usr/bin/chromium','/usr/bin/chromium-browser',
].find(fs.existsSync);
const widths=[320,360,390,768,1024,1440];
const routes=['/propuesta/','/propuesta/servicios/','/propuesta/nosotros/',
  '/propuesta/novedades/','/propuesta/oportunidades/',
  '/propuesta/contacto/','/buscar/'];
async function run() {
 if(!CHROME)throw new Error('Chrome/Chromium no instalado');
 const browser=await chromium.launch({
   executablePath:CHROME,headless:true,args:['--no-sandbox','--disable-dev-shm-usage'],
 });
 const failures=[],summary=[];
 const folder=path.resolve('reports/responsive');
 fs.mkdirSync(folder,{recursive:true});
 try{
  for(const width of widths){
   const page=await browser.newPage({viewport:{width,height:900},deviceScaleFactor:1});
   for(const route of routes){
    const response=await page.goto(BASE+route,{waitUntil:'networkidle',timeout:20000});
    const result=await page.evaluate(()=>{
      const width=window.innerWidth;
      const html=document.documentElement;
      const body=document.body;
      const check=document.querySelector('.hero,.subhero,main');
      const style=check?getComputedStyle(check):null;
      const visible=[...document.querySelectorAll('body *')].filter(el=>{
        const css=getComputedStyle(el);
        if(css.display==='none'||css.visibility==='hidden'||css.position==='fixed')return false;
        const r=el.getBoundingClientRect();
        return r.width>0&&r.height>0&&(r.right>width+2||r.left< -2);
      }).slice(0,8).map(el=>({
        tag:el.tagName.toLowerCase(),cls:typeof el.className==='string'?el.className.slice(0,64):'',
        right:Math.round(el.getBoundingClientRect().right),
        left:Math.round(el.getBoundingClientRect().left),
      }));
      const imgFailures=[...document.images].filter(img=>!img.complete||img.naturalWidth===0)
        .map(img=>img.getAttribute('src'));
      const interactive=[...document.querySelectorAll('.button,.mobile-nav summary')].filter(el=>
        getComputedStyle(el).display!=='none'&&el.getBoundingClientRect().height>0);
      const tooSmall=interactive.filter(el=>el.getBoundingClientRect().height<42)
        .map(el=>el.textContent.trim().slice(0,50));
      const stylesLoaded=routeFromBody()!=="/buscar/"?
        [...document.styleSheets].some(s=>s.href&&s.href.includes("gma-preview.css")):
        !!document.querySelector("style");
      function routeFromBody(){return location.pathname}
      return {
        viewport:width,htmlWidth:html.scrollWidth,bodyWidth:body.scrollWidth,
        overflow:Math.max(html.scrollWidth,body.scrollWidth)-width,
        outliers:visible,brokenImages:imgFailures,smallTargets:tooSmall,
        stylesLoaded,mainPadding:style?.paddingTop||'',
      };
    });
    const status=response?.status()||0;
    summary.push({route,width,status,overflow:result.overflow,padding:result.mainPadding});
    if(status!==200) failures.push(route+' '+width+'px HTTP '+status);
    if(result.overflow>2)failures.push(route+' '+width+'px overflow '+result.overflow+'px '+JSON.stringify(result.outliers));
    if(!result.stylesLoaded)failures.push(route+' '+width+'px CSS not loaded');
    if(result.brokenImages.length)failures.push(route+' '+width+'px images: '+JSON.stringify(result.brokenImages));
    if(result.smallTargets.length)failures.push(route+' '+width+'px targets: '+JSON.stringify(result.smallTargets));
    if((width===390||width===1440)&&route==='/propuesta/'||
       (width===390&&route==='/propuesta/servicios/')){
       await page.screenshot({path:path.join(folder,(route.includes('servicios')?'servicios':'inicio')+'-'+width+'.png'),fullPage:true});
    }
   }
   await page.close();
  }
 }finally{await browser.close()}
 fs.writeFileSync(path.join(folder,'resultados.json'),JSON.stringify({pages:summary.length,widths,routes,failures,summary},null,2));
 console.log(JSON.stringify({tested:summary.length,widths,failures,preview:BASE},null,2));
 if(failures.length)process.exitCode=1;
}
run().catch(err=>{console.error(err);process.exitCode=1});
