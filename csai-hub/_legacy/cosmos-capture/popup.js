const $ = (id) => document.getElementById(id);

async function load() {
  const s = await chrome.storage.sync.get({
    enabled: true,
    folder: "cosmos-capture",
    groupByPage: true,
  });
  $("enabled").checked = s.enabled;
  $("groupByPage").checked = s.groupByPage;
  $("folder").value = s.folder;

  const { totalSaved = 0 } = await chrome.storage.local.get("totalSaved");
  $("totalCount").textContent = totalSaved;

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab) {
    try {
      const res = await chrome.tabs.sendMessage(tab.id, { type: "GET_COUNT" });
      $("pageCount").textContent = (res && res.count) || 0;
    } catch {
      $("pageCount").textContent = "—";
    }
  }
}

function bindToggle(id, key) {
  $(id).addEventListener("change", () => {
    chrome.storage.sync.set({ [key]: $(id).checked });
  });
}

bindToggle("enabled", "enabled");
bindToggle("groupByPage", "groupByPage");

$("folder").addEventListener("change", () => {
  chrome.storage.sync.set({ folder: $("folder").value.trim() || "cosmos-capture" });
});

$("rescan").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;
  try {
    const res = await chrome.tabs.sendMessage(tab.id, { type: "RESCAN" });
    $("pageCount").textContent = (res && res.count) || 0;
  } catch {
    /* content script not loaded on this page */
  }
});

$("reset").addEventListener("click", async () => {
  await chrome.storage.local.set({ totalSaved: 0 });
  $("totalCount").textContent = "0";
});

load();
