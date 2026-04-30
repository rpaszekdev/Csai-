/* ═══════════════════════════════════════════════════════════════
   dl-layout.js — INTENTIONAL NO-OP.

   Earlier this script reordered each section.step's children at load
   time so the floated .stage-wrap appeared before the prose. That
   reparented elements with live Canvas2D/WebGL contexts, which broke
   animations on some lessons. The text-wrap-around effect is now
   handled in CSS via absolute positioning on .stage-wrap inside a
   relatively-positioned section.step (see /deep-learning/dl.skin.css).

   This file is kept so the existing <script src="…dl-layout.js">
   tags don't 404; it does nothing else.
   ═══════════════════════════════════════════════════════════════ */
