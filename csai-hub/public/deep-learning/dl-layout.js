/* ═══════════════════════════════════════════════════════════════
   dl-layout.js — re-orders each section.step's children at load
   time so that the floated .stage-wrap appears BEFORE the prose,
   not after it. This is what lets text wrap around the framed
   animation card from the very first paragraph (cog-neuro pattern).

   Floats anchor at their position in the document. With the original
   markup (text first, stage-wrap second), the float can only start
   below the prose, leaving an L-shaped void on the left. Moving
   stage-wrap to be the first child of .text fixes that — the float
   anchors at the top of the section and prose flows around it.

   Three.js scenes still find their canvas-host by id, so reordering
   doesn't disrupt scene mounting.
   ═══════════════════════════════════════════════════════════════ */
(() => {
  const apply = () => {
    document.querySelectorAll("section.step").forEach((section) => {
      const text = section.querySelector(":scope > .text");
      const stage = section.querySelector(":scope > .stage-wrap");
      if (!text || !stage) return;
      if (stage.dataset.dlReordered === "1") return;
      text.insertBefore(stage, text.firstChild);
      stage.dataset.dlReordered = "1";
    });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", apply);
  } else {
    apply();
  }
})();
