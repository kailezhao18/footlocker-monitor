# Foot Locker Monitor V6

This project now includes a Chrome extension in `/extension` that reads the visible Foot Locker product page you open in your own browser. It does not attempt to bypass CAPTCHA, authentication, rate limits, or other access controls.

## Recommended workflow

1. Open a Foot Locker product page in Chrome.
2. Click the Foot Locker Monitor V6 extension.
3. Click **Scan Current Product Page**.
4. The extension records product name, price, SKU, visible size states, and the check time.
5. On the next scan of the same SKU, it compares the new available-size list to the prior scan and shows:
   - RESTOCKED sizes
   - SOLD OUT sizes

Data is stored locally in Chrome using `chrome.storage.local`.

## Install the Chrome extension manually

1. Download or clone this repository.
2. In Chrome, open `chrome://extensions`.
3. Turn on **Developer mode**.
4. Click **Load unpacked**.
5. Select the repository's `extension` folder.
6. Pin **Foot Locker Monitor V6** to the Chrome toolbar.

## Notes

- The extension reads the DOM of Foot Locker pages that you open. Foot Locker may change page markup, so selectors may require maintenance.
- The current V6 scan is user-initiated. It is not an unattended background scraper.
- The older Render dashboard remains in the repository, but direct server-side product requests may be rejected with HTTP 403.
