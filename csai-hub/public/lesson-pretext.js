/* ═══════════════════════════════════════════════════════════════
   lesson-pretext.js — embed mono labels INTO canvas drawings.
   Loaded as <script type="module"> by each lesson, *after* the
   importmap. Exposes window.Pretext for the inline lesson scripts
   to consume without rewriting their import structure.

   Two label flavors:
     1. makeTextSprite()   — a Three.js Sprite with mono text baked in.
     2. drawText2D()       — a Canvas2D helper for flat heatmaps/charts.

   Voice rules:
     • Labels live AT the anchor, not floating in chips.
     • IBM Plex Mono, ALL CAPS for short labels (terms, vars).
     • Ink for primary terms, faint for secondary annotation.
   ═══════════════════════════════════════════════════════════════ */

import * as THREE from 'three';

const FONT = '"IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace';

const TONES = {
  ink:   '#2A2826',
  faint: '#A8A29A',
  paper: '#F8F6EE',
  coral: '#C45A2A',
};

/* ── 1) Three.js text sprite ─────────────────────────────── */
function makeTextSprite(text, opts = {}) {
  const {
    color = TONES.ink,
    weight = 500,
    size = 56,             // px in the texture canvas
    letterSpacing = 0.06,  // em
    upper = true,
    bg = null,
    pad = 12,
  } = opts;

  const label = upper ? String(text).toUpperCase() : String(text);
  const tracked = label.split('').join('\u200A'); // hair-space tracking

  // Measure
  const meas = document.createElement('canvas').getContext('2d');
  meas.font = `${weight} ${size}px ${FONT}`;
  const tw = Math.ceil(meas.measureText(label).width * (1 + letterSpacing));
  const th = Math.ceil(size * 1.25);

  const canvas = document.createElement('canvas');
  canvas.width = tw + pad * 2;
  canvas.height = th + pad * 2;
  const ctx = canvas.getContext('2d');

  if (bg) {
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  ctx.font = `${weight} ${size}px ${FONT}`;
  ctx.fillStyle = color;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.letterSpacing = `${letterSpacing}em`;
  ctx.fillText(label, canvas.width / 2, canvas.height / 2);

  const tex = new THREE.CanvasTexture(canvas);
  tex.minFilter = THREE.LinearFilter;
  tex.magFilter = THREE.LinearFilter;
  tex.needsUpdate = true;

  const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false });
  const sprite = new THREE.Sprite(mat);

  // Scale to world units — label is ~0.04 world units per text-canvas pixel by default
  const worldScale = opts.scale ?? 0.0042;
  sprite.scale.set(canvas.width * worldScale, canvas.height * worldScale, 1);
  sprite.userData.canvas = canvas;
  return sprite;
}

/* ── 2) Three.js axis label group (place sprite at world point) ── */
function placeLabel(scene, text, position, opts = {}) {
  const sprite = makeTextSprite(text, opts);
  sprite.position.set(...position);
  scene.add(sprite);
  return sprite;
}

/* ── 3) Canvas2D — draw a label at (x, y) on a 2D context ── */
function drawText2D(ctx, text, x, y, opts = {}) {
  const {
    color = TONES.ink,
    weight = 500,
    size = 11,
    letterSpacing = 0.12,    // em
    align = 'left',
    baseline = 'middle',
    upper = true,
    bg = null,
    padX = 4,
    padY = 2,
  } = opts;

  const label = upper ? String(text).toUpperCase() : String(text);

  ctx.save();
  ctx.font = `${weight} ${size}px ${FONT}`;
  ctx.textAlign = align;
  ctx.textBaseline = baseline;
  ctx.letterSpacing = `${letterSpacing}em`;

  if (bg) {
    const tw = ctx.measureText(label).width * (1 + letterSpacing);
    let bx = x;
    if (align === 'center') bx -= tw / 2;
    else if (align === 'right') bx -= tw;
    let by = y;
    if (baseline === 'middle') by -= size / 2;
    else if (baseline === 'bottom') by -= size;
    ctx.fillStyle = bg;
    ctx.fillRect(bx - padX, by - padY, tw + padX * 2, size + padY * 2);
  }

  ctx.fillStyle = color;
  ctx.fillText(label, x, y);
  ctx.restore();
}

/* ── 4) Canvas2D — short helper for an axis tick row ────── */
function drawAxisRow(ctx, items, y, opts = {}) {
  // items: [{ x, text }, ...]
  items.forEach(({ x, text }) => drawText2D(ctx, text, x, y, opts));
}

/* ── 5) Canvas2D — section eyebrow (e.g. "STEP 02 / 09") ── */
function drawEyebrow(ctx, text, x, y, opts = {}) {
  drawText2D(ctx, text, x, y, {
    color: TONES.faint,
    size: 9,
    letterSpacing: 0.16,
    weight: 500,
    upper: true,
    ...opts,
  });
}

/* ── expose for non-module inline scripts ───────────────── */
window.Pretext = {
  TONES,
  FONT,
  makeTextSprite,
  placeLabel,
  drawText2D,
  drawAxisRow,
  drawEyebrow,
};

export {
  TONES,
  FONT,
  makeTextSprite,
  placeLabel,
  drawText2D,
  drawAxisRow,
  drawEyebrow,
};
