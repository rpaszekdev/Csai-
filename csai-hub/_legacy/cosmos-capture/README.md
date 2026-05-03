# Cosmos Capture

A Chrome (Manifest V3) extension that automatically captures and saves images
from Cosmos.so as you browse. Built as a learning project — small surface,
exercises the core extension APIs (`downloads`, `storage`, content scripts,
service worker messaging, `MutationObserver`).

## Install (unpacked)

1. Open `chrome://extensions`.
2. Toggle **Developer mode** on (top right).
3. Click **Load unpacked** and select this folder.
4. Visit `https://www.cosmos.so/...`. Images are saved to
   `~/Downloads/cosmos-capture/<page title>/`.

## How it works

```
content.js                       background.js
─────────                        ─────────────
MutationObserver on <body>  ──▶  chrome.runtime.onMessage
  │                                │
  └─ for each new <img>:           └─ chrome.downloads.download({
       pick best srcset url             url, filename, conflictAction:
       dedupe by URL                    "uniquify"
       sendMessage(CAPTURE_IMAGE)     })
```

- `content.js` runs in the page, watches the DOM, picks the highest-res variant
  from `srcset`, and skips images smaller than 200px (avatars, icons).
- `background.js` is the service worker. It receives messages, sanitises the
  filename, and calls `chrome.downloads.download`.
- `popup.html` / `popup.js` give a toggle, folder name, per-page count, and
  total counter persisted in `chrome.storage`.

## Settings

| Setting        | Where stored        | Default          |
|----------------|---------------------|------------------|
| Auto-save      | `chrome.storage.sync` | on             |
| Group by page  | `chrome.storage.sync` | on             |
| Folder         | `chrome.storage.sync` | `cosmos-capture` |
| Total saved    | `chrome.storage.local`| 0              |

## Caveats

- Cosmos serves images from a CDN; some links 403 if hotlink-protected. The
  download API still requests the URL with the page's referrer, which usually
  succeeds.
- Service workers sleep — counters live in `chrome.storage`, not module state.
- Chrome's `downloads.filename` cannot start with `/`; the manifest path is
  always relative to the user's Downloads folder.
- This captures *every* image above 200px on the page, including thumbnails
  in the grid. Tighten `MIN_DIMENSION` in `content.js` if you only want hero
  shots.
