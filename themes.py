"""
Centralized theme system for Statistics Study Assistant.
Provides light and dark color palettes with typography configuration.
"""

# Dark Theme - Default
DARK_THEME = {
    # Backgrounds
    "bg": "#12131a",
    "surface": "#1e2029",
    "surface_hover": "#282a36",
    "input_bg": "#2d303d",
    "content_bg": "#1a1a24",
    "content_border": "#2a2a3a",

    # Borders
    "border": "#3d4052",

    # Accents
    "primary": "#7c3aed",
    "primary_hover": "#8b5cf6",
    "primary_glow": "#a78bfa",
    "secondary": "#06b6d4",
    "success": "#22c55e",
    "warning": "#eab308",
    "danger": "#ef4444",

    # Text
    "text": "#f8fafc",
    "text_secondary": "#a1a1aa",
    "text_muted": "#71717a",
    "text_reading": "#d4d4d8",

    # Special
    "highlight": "#312e81",
    "progress_bg": "#27272a",

    # Quiz-specific
    "option_bg": "#1e1e2e",
    "option_hover": "#2a2a3e",
    "option_border": "#3f3f5a",
    "option_selected": "#6d5aac",
    "option_selected_bg": "#3d3566",

    # Button colors (softer, less bright)
    "btn_primary": "#6d5aac",
    "btn_primary_hover": "#7a68b8",
    "btn_success": "#1a9f4a",
    "btn_success_hover": "#22b856",
    "btn_muted": "#3a3d4d",
    "btn_muted_hover": "#4a4d5d",
    "btn_muted_text": "#b8b8c8",
    "option_correct": "#10b981",
    "option_correct_bg": "#064e3b",
    "option_wrong": "#ef4444",
    "option_wrong_bg": "#7f1d1d",
    "success_bg": "#064e3b",
    "danger_bg": "#7f1d1d",

    # Unknown state (for comprehensive test)
    "option_unknown": "#6366f1",
    "option_unknown_bg": "#312e81",
    "unknown_bg": "#312e81",

    # Flashcard-specific
    "card": "#16213e",
    "card_front": "#0f3460",
    "accent": "#e94560",

    # Text tags (for markdown rendering)
    "tag_h1": "#a78bfa",
    "tag_h2": "#22d3ee",
    "tag_h3": "#34d399",
    "tag_code_bg": "#1e1e2e",
    "tag_code_fg": "#fbbf24",
    "tag_bold": "#f8fafc",
    "tag_italic": "#d4d4d8",
    "tag_bullet": "#8b5cf6",
    "tag_link": "#60a5fa",

    # Graph panel (collapsible visualization section)
    "graph_panel_bg": "#1a1a2e",
    "graph_panel_header": "#252540",
    "graph_panel_border": "#3d4052",
    "graph_panel_text": "#e2e8f0",
    "graph_panel_badge": "#7c3aed",
}

# Light Theme
LIGHT_THEME = {
    # Backgrounds
    "bg": "#f8fafc",
    "surface": "#ffffff",
    "surface_hover": "#f1f5f9",
    "input_bg": "#e2e8f0",
    "content_bg": "#ffffff",
    "content_border": "#e2e8f0",

    # Borders
    "border": "#cbd5e1",

    # Accents (same hues, adjusted for light bg)
    "primary": "#7c3aed",
    "primary_hover": "#6d28d9",
    "primary_glow": "#8b5cf6",
    "secondary": "#0891b2",
    "success": "#16a34a",
    "warning": "#ca8a04",
    "danger": "#dc2626",

    # Text
    "text": "#0f172a",
    "text_secondary": "#475569",
    "text_muted": "#94a3b8",
    "text_reading": "#1e293b",

    # Special
    "highlight": "#e0e7ff",
    "progress_bg": "#e2e8f0",

    # Quiz-specific
    "option_bg": "#f1f5f9",
    "option_hover": "#e2e8f0",
    "option_border": "#cbd5e1",
    "option_selected": "#7c3aed",
    "option_selected_bg": "#ede9fe",
    "option_correct": "#16a34a",
    "option_correct_bg": "#dcfce7",
    "option_wrong": "#dc2626",
    "option_wrong_bg": "#fee2e2",
    "success_bg": "#dcfce7",
    "danger_bg": "#fee2e2",

    # Unknown state (for comprehensive test)
    "option_unknown": "#6366f1",
    "option_unknown_bg": "#e0e7ff",
    "unknown_bg": "#e0e7ff",

    # Flashcard-specific
    "card": "#f1f5f9",
    "card_front": "#e0e7ff",
    "accent": "#e94560",

    # Text tags (for markdown rendering)
    "tag_h1": "#6d28d9",
    "tag_h2": "#0891b2",
    "tag_h3": "#059669",
    "tag_code_bg": "#f1f5f9",
    "tag_code_fg": "#b45309",
    "tag_bold": "#0f172a",
    "tag_italic": "#334155",
    "tag_bullet": "#7c3aed",
    "tag_link": "#2563eb",

    # Graph panel (collapsible visualization section)
    "graph_panel_bg": "#f8fafc",
    "graph_panel_header": "#f1f5f9",
    "graph_panel_border": "#e2e8f0",
    "graph_panel_text": "#1e293b",
    "graph_panel_badge": "#7c3aed",
}


# Typography Configuration
TYPOGRAPHY = {
    "fonts": {
        "display": ("SF Pro Display", "Helvetica Neue", "Arial"),
        "body": ("Georgia", "Times New Roman", "serif"),
        "mono": ("JetBrains Mono", "Menlo", "Consolas", "monospace"),
    },
    "sizes": {
        "xs": 10,
        "sm": 12,
        "base": 14,
        "lg": 16,
        "xl": 20,
        "2xl": 24,
        "3xl": 32,
    },
    "line_heights": {
        "tight": {"spacing1": 2, "spacing2": 1, "spacing3": 2},
        "normal": {"spacing1": 6, "spacing2": 3, "spacing3": 6},
        "relaxed": {"spacing1": 10, "spacing2": 5, "spacing3": 10},
        "reading": {"spacing1": 12, "spacing2": 6, "spacing3": 12},
    }
}


def get_theme(theme_name: str) -> dict:
    """Get theme by name.

    Args:
        theme_name: Either "dark" or "light"

    Returns:
        Theme dictionary with all color values
    """
    return DARK_THEME if theme_name == "dark" else LIGHT_THEME


def get_font(category: str, size: str = "base", weight: str = "normal") -> tuple:
    """Get a font tuple for use in Tkinter widgets.

    Args:
        category: Font category - "display", "body", or "mono"
        size: Size key - "xs", "sm", "base", "lg", "xl", "2xl", "3xl"
        weight: Font weight - "normal" or "bold"

    Returns:
        Tuple suitable for Tkinter font parameter
    """
    font_family = TYPOGRAPHY["fonts"][category][0]
    font_size = TYPOGRAPHY["sizes"].get(size, 14)

    if weight == "bold":
        return (font_family, font_size, "bold")
    return (font_family, font_size)


def get_line_height(style: str = "normal") -> dict:
    """Get line height configuration for Text widgets.

    Args:
        style: Line height style - "tight", "normal", "relaxed", "reading"

    Returns:
        Dictionary with spacing1, spacing2, spacing3 values
    """
    return TYPOGRAPHY["line_heights"].get(style, TYPOGRAPHY["line_heights"]["normal"])
