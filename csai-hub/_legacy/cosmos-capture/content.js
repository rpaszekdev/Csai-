// Cosmos Capture — content script
// Watches the DOM for <img> elements, deduplicates by URL, and asks the
// background service worker to download each one.

const seen = new Set();
const MIN_DIMENSION = 200; // skip tiny avatars / icons

function pickBestUrl(img) {
  // srcset can give a higher-res variant than src
  const srcset = img.getAttribute("srcset");
  if (srcset) {
    const candidates = srcset
      .split(",")
      .map((s) => s.trim())
      .map((s) => {
        const [url, descriptor] = s.split(/\s+/);
        const w = descriptor && descriptor.endsWith("w")
          ? parseInt(descriptor, 10)
          : 0;
        return { url, w };
      })
      .sort((a, b) => b.w - a.w);
    if (candidates.length && candidates[0].url) return candidates[0].url;
  }
  return img.currentSrc || img.src;
}

function shouldCapture(img) {
  const url = pickBestUrl(img);
  if (!url || !/^https?:/.test(url)) return null;
  if (seen.has(url)) return null;
  // Tiny images are almost always UI chrome
  const w = img.naturalWidth || img.width || 0;
  const h = img.naturalHeight || img.height || 0;
  if (w && h && (w < MIN_DIMENSION || h < MIN_DIMENSION)) return null;
  return url;
}

function capture(img) {
  const url = shouldCapture(img);
  if (!url) return;
  seen.add(url);
  chrome.runtime.sendMessage({
    type: "CAPTURE_IMAGE",
    url,
    pageUrl: location.href,
    pageTitle: document.title,
  });
}

function captureAll(root = document) {
  root.querySelectorAll("img").forEach((img) => {
    if (img.complete && img.naturalWidth) {
      capture(img);
    } else {
      img.addEventListener("load", () => capture(img), { once: true });
    }
  });
}

// Initial sweep
captureAll();

// Watch for lazy-loaded images as user scrolls
const observer = new MutationObserver((mutations) => {
  for (const m of mutations) {
    for (const node of m.addedNodes) {
      if (node.nodeType !== 1) continue;
      if (node.tagName === "IMG") {
        if (node.complete && node.naturalWidth) capture(node);
        else node.addEventListener("load", () => capture(node), { once: true });
      } else if (node.querySelectorAll) {
        captureAll(node);
      }
    }
    // Also handle src/srcset swaps on existing imgs
    if (m.type === "attributes" && m.target.tagName === "IMG") {
      capture(m.target);
    }
  }
});

observer.observe(document.documentElement, {
  childList: true,
  subtree: true,
  attributes: true,
  attributeFilter: ["src", "srcset"],
});

// Allow popup to ask "how many on this page so far?"
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === "GET_COUNT") {
    sendResponse({ count: seen.size });
  }
  if (msg.type === "RESCAN") {
    captureAll();
    sendResponse({ count: seen.size });
  }
  return true;
});
