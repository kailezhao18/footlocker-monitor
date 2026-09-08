from flask import Flask, render_template, request, jsonify
import requests, json, re
from bs4 import BeautifulSoup
from datetime import datetime, timezone

app = Flask(__name__)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}

SIZE_RE = re.compile(r'^\d{1,2}(?:\.5)?$')


def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


def norm_size(v):
    if isinstance(v, (str, int, float)):
        s = str(v).strip()
        if SIZE_RE.fullmatch(s):
            return s
    return None


def uniq_sorted(values):
    def key(s):
        try:
            return float(s)
        except Exception:
            return 999
    return sorted(set(values), key=key)


def extract_variant_state(node):
    size = None
    for key in ('size', 'sizeLabel', 'displaySize', 'value', 'label'):
        size = norm_size(node.get(key))
        if size:
            break
    if not size:
        return None

    availability_values = []
    for key in ('available', 'isAvailable', 'inStock', 'isInStock', 'stockStatus', 'availability', 'inventoryStatus', 'sellable', 'isSellable', 'disabled'):
        if key in node:
            availability_values.append((key, node.get(key)))

    state = None
    for key, val in availability_values:
        if isinstance(val, bool):
            if key == 'disabled':
                state = not val
            else:
                state = val
        elif isinstance(val, str):
            text = val.lower()
            if any(x in text for x in ('outofstock', 'out of stock', 'unavailable', 'soldout', 'sold out', 'not available')):
                state = False
            elif any(x in text for x in ('instock', 'in stock', 'available', 'sellable')):
                state = True
    return size, state


def parse(url, sku=''):
    r = requests.get(url, headers=HEADERS, timeout=20)
    if r.status_code == 403:
        raise RuntimeError('Foot Locker blocked this server request (HTTP 403). The monitor UI is ready, but a permitted data source is still required for live inventory checks.')
    r.raise_for_status()

    soup = BeautifulSoup(r.text, 'html.parser')
    out = {
        'sku': sku,
        'url': url,
        'available_sizes': [],
        'out_of_stock_sizes': [],
        'unknown_sizes': [],
        'last_checked': datetime.now(timezone.utc).isoformat()
    }

    for tag in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(tag.string or tag.get_text())
        except Exception:
            continue
        for n in walk(data):
            if n.get('@type') == 'Product':
                out['name'] = n.get('name', out.get('name'))
                out['sku'] = str(n.get('sku') or n.get('mpn') or out['sku'])
                im = n.get('image')
                out['image'] = (im[0] if isinstance(im, list) and im else im) or out.get('image')
                offers = n.get('offers')
                if isinstance(offers, dict):
                    out['price'] = offers.get('price') or offers.get('lowPrice')

    # Embedded JSON variant inventory states.
    for tag in soup.find_all('script'):
        txt = (tag.string or tag.get_text() or '').strip()
        if not (txt.startswith('{') and txt.endswith('}')):
            continue
        try:
            data = json.loads(txt)
        except Exception:
            continue
        for n in walk(data):
            if not isinstance(n, dict):
                continue
            parsed = extract_variant_state(n)
            if not parsed:
                continue
            size, state = parsed
            if state is True:
                out['available_sizes'].append(size)
            elif state is False:
                out['out_of_stock_sizes'].append(size)
            else:
                out['unknown_sizes'].append(size)

    # DOM fallback: size buttons/options marked disabled or aria-disabled are sold out.
    for el in soup.find_all(['button', 'option', 'input', 'label']):
        text = el.get_text(' ', strip=True) or el.get('value') or el.get('aria-label') or ''
        m = re.search(r'(?<!\d)(\d{1,2}(?:\.5)?)(?!\d)', str(text))
        if not m:
            continue
        size = m.group(1)
        attrs = ' '.join([str(el.get('class', '')), str(el.get('aria-disabled', '')), str(el.get('disabled', ''))]).lower()
        if el.has_attr('disabled') or el.get('aria-disabled') == 'true' or any(x in attrs for x in ('disabled', 'soldout', 'sold-out', 'unavailable', 'out-of-stock')):
            out['out_of_stock_sizes'].append(size)

    out['available_sizes'] = uniq_sorted(out['available_sizes'])
    out['out_of_stock_sizes'] = uniq_sorted(out['out_of_stock_sizes'])
    out['unknown_sizes'] = uniq_sorted([
        s for s in out['unknown_sizes']
        if s not in out['available_sizes'] and s not in out['out_of_stock_sizes']
    ])

    if not out.get('image') and out['sku']:
        out['image'] = f"https://assets.footlocker.com/is/image/FLDM/{out['sku']}_01?$tile500jpg$=true&fmt=png-alpha"
    if not out.get('name'):
        out['name'] = soup.title.get_text(' ', strip=True).split('|')[0] if soup.title else 'Foot Locker Product'
    return out


@app.route('/')
def home():
    return render_template('index.html')


@app.post('/api/product')
def product():
    d = request.get_json() or {}
    sku = str(d.get('sku', '')).strip()
    if not sku:
        return jsonify(ok=False, error='SKU is required'), 400
    url = f'https://www.footlocker.com/product/~/{sku}.html'
    try:
        return jsonify(ok=True, product=parse(url, sku))
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 502


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
