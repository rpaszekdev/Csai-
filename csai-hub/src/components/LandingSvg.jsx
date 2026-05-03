import { useEffect, useRef } from "react";

export default function LandingSvg() {
  const containerRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    fetch("/landing.svg")
      .then((r) => r.text())
      .then((text) => {
        if (cancelled || !containerRef.current) return;

        const parser = new DOMParser();
        const doc = parser.parseFromString(text, "image/svg+xml");
        const parsedSvg = doc.querySelector("svg");
        if (!parsedSvg) return;
        parsedSvg.querySelectorAll("script").forEach((s) => s.remove());
        containerRef.current.replaceChildren(parsedSvg);
        const svg = parsedSvg;
        if (!svg) return;

        const viewBox = svg.getAttribute("viewBox") || "0 0 1344 768";
        const [, , vbW] = viewBox.split(/\s+/).map(Number);
        const splitX = 950;

        const rightPaths = [];
        const paths = Array.from(svg.querySelectorAll("path"));

        paths.forEach((p) => {
          let bbox;
          try {
            bbox = p.getBBox();
          } catch {
            return;
          }
          if (bbox.width >= vbW - 10) return;
          const centerX = bbox.x + bbox.width / 2;
          if (centerX <= splitX) return;

          const originalFill = p.getAttribute("fill") || "#152229";
          p.setAttribute("data-original-fill", originalFill);
          p.setAttribute("fill", originalFill);
          p.setAttribute("stroke", originalFill);
          p.setAttribute("stroke-width", "1");
          p.setAttribute("pathLength", "1");
          p.classList.add("draw-path");

          rightPaths.push(p);
        });

        const total = rightPaths.length;
        const drawDuration = 1.6;
        const fillDuration = 0.4;
        const stagger = 1.6 / Math.max(total, 1);

        rightPaths.forEach((p, i) => {
          const delay = i * stagger;
          p.style.setProperty("--draw-delay", `${delay}s`);
          p.style.setProperty("--draw-duration", `${drawDuration}s`);
          p.style.setProperty("--fill-delay", `${delay + drawDuration * 0.6}s`);
          p.style.setProperty("--fill-duration", `${fillDuration}s`);
        });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return <div ref={containerRef} className="landing-svg-inline" />;
}
