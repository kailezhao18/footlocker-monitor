from flask import Flask, render_template, request, jsonify
import requests, json, re
from bs4 import BeautifulSoup

app = Flask(__name__)
HEADERS = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36','Accept-Language':'en-US,en;q=0.9'}

def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values(): yield from walk(v)
    elif isinstance(obj, list):
        for v in obj: yield from walk(v)

def parse(url, sku=''):
    r=requests.get(url,headers=HEADERS,timeout=20); r.raise_for_status()
    soup=BeautifulSoup(r.text,'html.parser')
    out={'sku':sku,'url':url,'sizes':[]}
    for tag in soup.find_all('script',type='application/ld+json'):
        try: data=json.loads(tag.string or tag.get_text())
        except: continue
        for n in walk(data):
            if n.get('@type')=='Product':
                out['name']=n.get('name',out.get('name'))
                out['sku']=str(n.get('sku') or n.get('mpn') or out['sku'])
                im=n.get('image'); out['image']=(im[0] if isinstance(im,list) and im else im) or out.get('image')
                offers=n.get('offers')
                if isinstance(offers,dict): out['price']=offers.get('price') or offers.get('lowPrice')
    for tag in soup.find_all('script'):
        txt=(tag.string or tag.get_text() or '').strip()
        if not (txt.startswith('{') and txt.endswith('}')): continue
        try: data=json.loads(txt)
        except: continue
        for n in walk(data):
            for key in ('size','sizeLabel','displaySize'):
                v=n.get(key)
                if isinstance(v,(str,int,float)):
                    s=str(v).strip()
                    if re.fullmatch(r'\d{1,2}(?:\.5)?',s) and s not in out['sizes']: out['sizes'].append(s)
    if not out.get('image') and out['sku']:
        out['image']=f"https://assets.footlocker.com/is/image/FLDM/{out['sku']}_01?$tile500jpg$=true&fmt=png-alpha"
    if not out.get('name'):
        out['name']=(soup.title.get_text(' ',strip=True).split('|')[0] if soup.title else 'Foot Locker Product')
    return out

@app.route('/')
def home(): return render_template('index.html')

@app.post('/api/product')
def product():
    d=request.get_json() or {}; sku=str(d.get('sku','')).strip()
    if not sku: return jsonify(ok=False,error='SKU is required'),400
    url=f'https://www.footlocker.com/product/~/{sku}.html'
    try: return jsonify(ok=True,product=parse(url,sku))
    except Exception as e: return jsonify(ok=False,error=str(e)),502

if __name__=='__main__': app.run(host='0.0.0.0',port=5000)
