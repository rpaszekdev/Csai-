// Cosmos Capture — background service worker
// Receives capture requests from the content script and writes each image
// into a per-page subfolder under the user's default Downloads folder.

const DEFAULTS = {
  enabled: true,
  folder: "cosmos-capture",
  groupByPage: true,
};

async function getSettings() {
  const stored = await chrome.storage.sync.get(DEFAULTS);
  return { ...DEFAULTS, ...stored };
}

function sanitize(s) {
  return (s || "untitled")
    .replace(/[\\/:*?"<>|]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 80) || "untitled";
}

function filenameFromUrl(url) {
  try {
    const u = new URL(url);
    const last = u.pathname.split("/").filter(Boolean).pop() || "image";
    // Strip query, ensure something extension-ish remains
    const clean = last.split("?")[0];
    return /\.[a-z0-9]{2,5}$/i.test(clean) ? clean : `${clean}.jpg`;
  } catch {
    return "image.jpg";
  }
}

async function bumpCount() {
  const { totalSaved = 0 } = await chrome.storage.local.get("totalSaved");
  await chrome.storage.local.set({ totalSaved: totalSaved + 1 });
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type !== "CAPTURE_IMAGE") return;

  (async () => {
    const settings = await getSettings();
    if (!settings.enabled) {
      sendResponse({ ok: false, reason: "disabled" });
      return;
    }

    const folder = sanitize(settings.folder);
    const subfolder = settings.groupByPage ? sanitize(msg.pageTitle) : "";
    const path = [folder, subfolder, filenameFromUrl(msg.url)]
      .filter(Boolean)
      .join("/");

    try {
      await chrome.downloads.download({
        url: msg.url,
        filename: path,
        conflictAction: "uniquify",
        saveAs: false,
      });
      await bumpCount();
      sendResponse({ ok: true });
    } catch (err) {
      console.warn("Cosmos Capture: download failed", msg.url, err);
      sendResponse({ ok: false, reason: String(err) });
    }
  })();

  return true; // keep the channel open for the async response
});

chrome.runtime.onInstalled.addListener(async () => {
  const current = await chrome.storage.sync.get(DEFAULTS);
  await chrome.storage.sync.set({ ...DEFAULTS, ...current });
});
