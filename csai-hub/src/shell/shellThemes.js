// shellThemes.js — light/dark CSS-variable token sets for the IDE shell.
//
// Ported verbatim from the .dc.html prototype's `themes()` method. The shell
// applies the chosen set as inline custom properties on its root element, so
// every `var(--token)` reference in the component resolves correctly.

export const THEMES = Object.freeze({
  light: Object.freeze({
    "--bg": "#ffffff",
    "--ink": "#141414",
    "--mute": "#9c9c9c",
    "--line": "#e4e4e4",
    "--sel": "#f3f3f3",
    "--hover": "#f8f8f8",
    "--fill": "#141414",
    "--onFill": "#ffffff",
    "--ok": "#141414",
    "--accent": "#141414",
    "--good": "#1f9e5a",
    "--bad": "#d83a3a",
  }),
  dark: Object.freeze({
    "--bg": "#272927",
    "--ink": "#dfe0e6",
    "--mute": "#8f9088",
    "--line": "#3a3c38",
    "--sel": "#31332f",
    "--hover": "#2d2f2b",
    "--fill": "#dfe0e6",
    "--onFill": "#272927",
    "--ok": "#dfe0e6",
    "--accent": "#dfe0e6",
    "--good": "#3ecf8e",
    "--bad": "#f1707a",
  }),
});

export const SHELL_FONT = "'JetBrains Mono', ui-monospace, monospace";

/** Returns the token set for a theme name, defaulting to light. */
export function themeVars(theme) {
  return THEMES[theme] || THEMES.light;
}

/**
 * Root-element inline style: the theme tokens plus the base layout the
 * prototype set on its outermost div. Returned fresh each call (no mutation).
 */
export function rootStyle(theme) {
  const t = themeVars(theme);
  return {
    ...t,
    height: "100vh",
    display: "flex",
    fontFamily: SHELL_FONT,
    color: t["--ink"],
    background: t["--bg"],
    overflow: "hidden",
    imageRendering: "pixelated",
  };
}
