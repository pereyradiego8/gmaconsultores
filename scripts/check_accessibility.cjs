#!/usr/bin/env node
'use strict';
const fs=require('fs');
const path=require('path');
const {chromium}=require('playwright-core');
const axeScript=require.resolve('axe-core/axe.min.js');
const BASE=process.env.PREVIEW_URL||'http://127.0.0.1:8765';
const CHROME=process.env.CHROME_BIN||['/usr/bin/google-chrome','/usr/bin/google-chrome-stable','/usr/bin/chromium','/usr/bin/chromium-browser'].find(fs.existsSync);
const routes=['/propuesta/','/propuesta/servicios/','/propuesta/nosotros/','/propuesta/novedades/','/propuesta/oportunidades/','/propuesta/contacto/','/buscar/'];
const widths=[390,1440];
async function main(){
 if(!CHROME)throw Error('Chromium not found');
 const browser=await chromium.launch({executablePath:CHROME,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 const results=[];
 try{
  for(const width of widths){
   const page=await browser.newPage({viewport:{width,height:900}});
   for(const route of routes){
    await page.goto(BASE+route,{waitUntil:'networkidle',timeout:20000});
    await page.addScriptTag({path:axeScript});
    const result=await page.evaluate(()=>window.axe.run(document,{
      runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}
    }));
    const violations=result.violations.map(v=>({rule:v.id,impact:v.impact,description:v.help,targets:v.nodes.map(n=>n.target.join(' ')).slice(0,8)}));
    results.push({route,width,violations,passed:result.passes.length,incomplete:result.incomplete.length});
   }
   await page.close();
  }
 }finally{await browser.close();}
 fs.mkdirSync('reports/accessibility',{recursive:true});
 fs.writeFileSync('reports/accessibility/axe.json',JSON.stringify(results,null,2));
 const failures=results.flatMap(x=>x.violations.map(v=>({route:x.route,width:x.width,...v})));
 console.log(JSON.stringify({tested:results.length,failures},null,2));
 if(failures.length)process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1});
