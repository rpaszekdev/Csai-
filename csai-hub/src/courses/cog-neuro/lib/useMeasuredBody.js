import { useEffect, useMemo, useRef, useState } from "react";
import {
  prepare,
  layout,
  prepareWithSegments,
  layoutNextLineRange,
} from "@chenglou/pretext";

// Approximate plain text from markdown so pretext can measure it.
// We strip markup tokens but keep the visible characters that drive width.
function markdownToPlain(md = "") {
  return md
    .replace(/```[\s\S]*?```/g, "")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/[*_`~]/g, "")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/\|/g, "  ")
    .replace(/^\s*[-+*]\s+/gm, "· ")
    .replace(/\n{3,}/g, "\n\n");
}

/**
 * Measure the rendered height of a markdown body using pretext.
 *
 * Pass `getMaxWidth(y, containerWidth) → number` to flow text around floated
 * elements (the brain + brush in the lessons view): pretext walks one line at
 * a time, asking for the available width at each Y. This is a direct lift of
 * the README's "Flow text around a floated image" pattern.
 *
 * Without `getMaxWidth`, the hook uses the simpler fixed-width API and pure
 * arithmetic over cached widths.
 *
 * Returns [height, lineCount, ref]. Attach the ref to the element whose
 * width the body fills.
 */
export function useMeasuredBody(markdown, { font, lineHeight, getMaxWidth }) {
  const ref = useRef(null);
  const [height, setHeight] = useState(0);
  const [lineCount, setLineCount] = useState(0);

  const useFlow = typeof getMaxWidth === "function";

  const prepared = useMemo(() => {
    if (!markdown) return null;
    const plain = markdownToPlain(markdown);
    return useFlow ? prepareWithSegments(plain, font) : prepare(plain, font);
  }, [markdown, font, useFlow]);

  useEffect(() => {
    const node = ref.current;
    if (!node || !prepared) {
      setHeight(0);
      setLineCount(0);
      return;
    }

    const recompute = () => {
      const containerWidth = node.clientWidth;
      if (containerWidth <= 0) return;

      if (useFlow) {
        let cursor = { segmentIndex: 0, graphemeIndex: 0 };
        let y = 0;
        let lines = 0;
        // Hard ceiling — runaway loops would be a bug, but cap at 4000 lines.
        for (let i = 0; i < 4000; i++) {
          const w = Math.max(40, getMaxWidth(y, containerWidth));
          const range = layoutNextLineRange(prepared, cursor, w);
          if (range === null) break;
          cursor = range.end;
          y += lineHeight;
          lines++;
        }
        setHeight(y);
        setLineCount(lines);
      } else {
        const result = layout(prepared, containerWidth, lineHeight);
        setHeight(result.height);
        setLineCount(result.lineCount);
      }
    };

    recompute();
    const observer = new ResizeObserver(recompute);
    observer.observe(node);
    return () => observer.disconnect();
  }, [prepared, lineHeight, useFlow, getMaxWidth]);

  return [height, lineCount, ref];
}
