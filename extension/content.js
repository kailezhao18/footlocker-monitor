function cleanText(v){return (v||'').replace(/\s+/g,' ').trim();}
function isSizeText(t){return /^\d{1,2}(?:\.5)?$/.test(t);}
function getSku(){const m=location.pathname.match(/\/product\/~\/([^/.]+)\.html/i);return m?m[1]:'';}
function getMeta(prop){const el=document.querySelector(`meta[property="${prop}"]`)||document.querySelector(`meta[name="${prop}"]`);return el?el.content:'';}
function getName(){return cleanText(document.querySelector('h1')?.textContent)||getMeta('og:title')||document.title.split('|')[0].trim();}
function getPrice(){
  const candidates=[...document.querySelectorAll('[data-testid*="price" i], [class*="price" i], [itemprop="price"]')];
  for(const el of candidates){const t=cleanText(el.textContent||el.getAttribute('content'));const m=t.match(/\$\s*([0-9]+(?:\.[0-9]{2})?)/);if(m)return m[1];}
  const body=cleanText(document.body.innerText);const m=body.match(/\$\s*([0-9]+(?:\.[0-9]{2})?)/);return m?m[1]:'';
}
function collectSizeButtons(){
  const all=[...document.querySelectorAll('button, [role="button"], input[type="radio"]')];
  return all.filter(el=>{
    const t=cleanText(el.value||el.getAttribute('aria-label')||el.textContent);
    const exact=t.match(/(?:^|\b)(\d{1,2}(?:\.5)?)(?:\b|$)/);
    return exact && isSizeText(exact[1]);
  });
}
function classify(el){
  const raw=cleanText(el.value||el.getAttribute('aria-label')||el.textContent);
  const m=raw.match(/(?:^|\b)(\d{1,2}(?:\.5)?)(?:\b|$)/); if(!m)return null;
  const size=m[1];
  const cls=(el.className||'').toString().toLowerCase();
  const aria=(el.getAttribute('aria-disabled')||'').toLowerCase();
  const disabled=el.disabled||aria==='true'||cls.includes('disabled')||cls.includes('sold')||cls.includes('unavailable')||cls.includes('out-of-stock')||cls.includes('outofstock');
  return {size,available:!disabled};
}
function scan(){
  const found=collectSizeButtons().map(classify).filter(Boolean);
  const bySize=new Map(); for(const x of found){if(!bySize.has(x.size)||x.available)bySize.set(x.size,x.available)}
  const sizes=[...bySize.keys()].sort((a,b)=>parseFloat(a)-parseFloat(b));
  return {
    sku:getSku(), name:getName(), price:getPrice(), image:getMeta('og:image'), url:location.href,
    availableSizes:sizes.filter(s=>bySize.get(s)),
    unavailableSizes:sizes.filter(s=>!bySize.get(s)),
    checkedAt:new Date().toISOString()
  };
}
chrome.runtime.onMessage.addListener((msg, sender, sendResponse)=>{
  if(msg?.type==='SCAN_FOOTLOCKER'){try{sendResponse({ok:true,data:scan()})}catch(e){sendResponse({ok:false,error:e.message})}return true;}
});
