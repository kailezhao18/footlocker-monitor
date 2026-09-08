# Foot Locker Monitor V4

Simple personal product-monitor dashboard.

## Current workflow

1. Enter a Foot Locker Product # / SKU.
2. Backend requests the corresponding public product page.
3. Dashboard attempts to extract product name, price, image and available sizes.
4. Click Refresh to compare the latest price/sizes with the previous result.

The monitor does not bypass CAPTCHA, authentication, rate limits, or other access controls. Foot Locker can change its page structure, so extraction may require maintenance.

## Render

This repository includes `render.yaml`.

Build command: `pip install -r requirements.txt`

Start command: `gunicorn app:app`
