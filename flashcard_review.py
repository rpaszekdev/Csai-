#!/usr/bin/env python3
"""
Modern Flashcard Review Window
Clean, aesthetic design with smooth animations
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import sys
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from flashcard_db import (
    get_all_decks, get_deck, get_cards_for_deck, get_due_cards,
    review_card, get_deck_stats, delete_deck, delete_card
)
from themes import DARK_THEME, LIGHT_THEME

# Modern color palette with good contrast
ANKI_COLORS = {
    # Vibrant, visible rating colors
    "again": "#ef4444",      # Bright red
    "hard": "#f59e0b",       # Bright amber
    "good": "#22c55e",       # Bright green
    "easy": "#3b82f6",       # Bright blue
    "show_answer": "#7c3aed", # Vibrant purple
    # Card backgrounds - cleaner, more modern
    "card_bg_light": "#ffffff",
    "card_bg_dark": "#1e1e2e",
    "review_bg_light": "#f5f7fa",
    "review_bg_dark": "#12131a",
    # Additional modern colors
    "shadow_dark": "#0a0a0f",
    "shadow_light": "#c4c9d4",
    "accent_glow": "#a78bfa",
    "progress_track": "#2d2d3d",
    "progress_fill": "#7c4dff",
}


class FlashcardReviewWindow:
    """Modern, aesthetic flashcard review window."""

    def __init__(self, parent, deck_id=None, colors=None):
        self.window = tk.Toplevel(parent)
        self.window.title("Flashcard Review")
        self.window.geometry("950x700")
        self.window.minsize(700, 500)

        # Determine if dark mode based on colors
        self.colors = colors if colors else DARK_THEME
        self.is_dark = self.colors.get("bg", "#000") in ["#12131a", "#1e1e1e", "#2f2f31"]

        # Modern color scheme
        self.bg_color = ANKI_COLORS["review_bg_dark"] if self.is_dark else ANKI_COLORS["review_bg_light"]
        self.card_bg = ANKI_COLORS["card_bg_dark"] if self.is_dark else ANKI_COLORS["card_bg_light"]
        self.text_color = "#e8e8e8" if self.is_dark else "#1a1a2e"
        self.text_dim = "#8b8b9e" if self.is_dark else "#6b7280"
        self.shadow_color = ANKI_COLORS["shadow_dark"] if self.is_dark else ANKI_COLORS["shadow_light"]

        self.window.configure(bg=self.bg_color)

        self.deck_id = deck_id
        self.cards = []
        self.current_index = 0
        self.showing_back = False
        self.review_buttons = []
        self.animation_id = None  # For fade animations

        self.setup_ui()
        self.load_cards()

        # Bind resize to update wraplength
        self.window.bind("<Configure>", self._on_resize)

    def _on_resize(self, event=None):
        """Handle window resize to adjust text wrapping."""
        if hasattr(self, 'card_text') and self.card_text.winfo_exists():
            new_width = max(300, self.window.winfo_width() - 150)
            self.card_text.config(wraplength=new_width)
            if hasattr(self, 'answer_text') and self.answer_text.winfo_exists():
                self.answer_text.config(wraplength=new_width)
            if hasattr(self, 'example_text') and self.example_text.winfo_exists():
                self.example_text.config(wraplength=new_width - 50)

    def _on_card_canvas_resize(self, event):
        """Center content in canvas and update scroll region."""
        # Center the content window horizontally
        canvas_width = event.width
        self.card_canvas.itemconfig(self.card_content_window, width=canvas_width)

    def _on_card_content_resize(self, event):
        """Update scroll region when content changes."""
        self.card_canvas.configure(scrollregion=self.card_canvas.bbox("all"))
        # Show/hide scrollbar based on content height
        content_height = self.card_content.winfo_reqheight()
        canvas_height = self.card_canvas.winfo_height()
        if content_height > canvas_height:
            self.card_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self.card_scrollbar.pack_forget()
            # Reset scroll position
            self.card_canvas.yview_moveto(0)

    def _on_card_mousewheel(self, event):
        """Handle mousewheel scrolling on card content."""
        self.card_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def setup_ui(self):
        """Set up modern, aesthetic review UI."""
        # Top header area with progress
        self.header = tk.Frame(self.window, bg=self.bg_color)
        self.header.pack(fill=tk.X, padx=30, pady=(20, 10))

        # Deck name with modern styling
        self.deck_label = tk.Label(
            self.header,
            text="",
            font=("SF Pro Display", 14, "bold") if sys.platform == "darwin" else ("Segoe UI", 14, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.deck_label.pack(side=tk.LEFT)

        # Card counts on right - pill-style badges
        self.counts_frame = tk.Frame(self.header, bg=self.bg_color)
        self.counts_frame.pack(side=tk.RIGHT)

        # New count badge (blue pill)
        self.new_badge = tk.Frame(self.counts_frame, bg="#3b82f6", padx=8, pady=2)
        self.new_badge.pack(side=tk.LEFT, padx=3)
        self.new_count = tk.Label(
            self.new_badge,
            text="0",
            font=("SF Pro Display", 11, "bold") if sys.platform == "darwin" else ("Segoe UI", 11, "bold"),
            bg="#3b82f6",
            fg="white"
        )
        self.new_count.pack()

        # Learning count badge (amber pill)
        self.learning_badge = tk.Frame(self.counts_frame, bg="#f59e0b", padx=8, pady=2)
        self.learning_badge.pack(side=tk.LEFT, padx=3)
        self.learning_count = tk.Label(
            self.learning_badge,
            text="0",
            font=("SF Pro Display", 11, "bold") if sys.platform == "darwin" else ("Segoe UI", 11, "bold"),
            bg="#f59e0b",
            fg="white"
        )
        self.learning_count.pack()

        # Review count badge (green pill)
        self.review_badge = tk.Frame(self.counts_frame, bg="#10b981", padx=8, pady=2)
        self.review_badge.pack(side=tk.LEFT, padx=3)
        self.review_count = tk.Label(
            self.review_badge,
            text="0",
            font=("SF Pro Display", 11, "bold") if sys.platform == "darwin" else ("Segoe UI", 11, "bold"),
            bg="#10b981",
            fg="white"
        )
        self.review_count.pack()

        # Progress bar
        self.progress_container = tk.Frame(self.window, bg=self.bg_color)
        self.progress_container.pack(fill=tk.X, padx=30, pady=(5, 15))

        self.progress_track = tk.Frame(
            self.progress_container,
            bg=ANKI_COLORS["progress_track"] if self.is_dark else "#e2e8f0",
            height=4
        )
        self.progress_track.pack(fill=tk.X)
        self.progress_track.pack_propagate(False)

        self.progress_fill = tk.Frame(
            self.progress_track,
            bg=ANKI_COLORS["progress_fill"],
            height=4
        )
        self.progress_fill.place(x=0, y=0, relheight=1, relwidth=0)

        # Main card area with shadow effect
        self.card_container = tk.Frame(self.window, bg=self.bg_color)
        self.card_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        # Shadow layer (creates depth effect)
        self.shadow_frame = tk.Frame(
            self.card_container,
            bg=self.shadow_color
        )
        self.shadow_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        # Card frame - elevated with subtle border
        card_border_color = "#2d2d3d" if self.is_dark else "#e2e8f0"
        self.card_frame = tk.Frame(
            self.shadow_frame,
            bg=self.card_bg,
            highlightbackground=card_border_color,
            highlightthickness=1
        )
        self.card_frame.place(x=-4, y=-4, relwidth=1, relheight=1)

        # Scrollable card content area
        self.card_canvas = tk.Canvas(
            self.card_frame,
            bg=self.card_bg,
            highlightthickness=0
        )
        self.card_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar (hidden by default, shows when needed)
        self.card_scrollbar = ttk.Scrollbar(
            self.card_frame,
            orient="vertical",
            command=self.card_canvas.yview
        )

        self.card_canvas.configure(yscrollcommand=self.card_scrollbar.set)

        # Card content frame inside canvas
        self.card_content = tk.Frame(self.card_canvas, bg=self.card_bg)
        self.card_content_window = self.card_canvas.create_window(
            (0, 0),
            window=self.card_content,
            anchor="n"
        )

        # Bind canvas resize to center content
        self.card_canvas.bind("<Configure>", self._on_card_canvas_resize)
        self.card_content.bind("<Configure>", self._on_card_content_resize)

        # Enable mousewheel scrolling on card
        self.card_canvas.bind("<MouseWheel>", self._on_card_mousewheel)
        self.card_content.bind("<MouseWheel>", self._on_card_mousewheel)

        # Card type indicator (subtle label at top)
        self.card_type_label = tk.Label(
            self.card_content,
            text="QUESTION",
            font=("SF Pro Display", 10) if sys.platform == "darwin" else ("Segoe UI", 10),
            bg=self.card_bg,
            fg=self.text_dim
        )
        self.card_type_label.pack(pady=(20, 5))

        # Question text - modern typography
        self.card_text = tk.Label(
            self.card_content,
            text="",
            font=("Georgia", 22) if sys.platform == "darwin" else ("Cambria", 22),
            bg=self.card_bg,
            fg=self.text_color,
            wraplength=700,
            justify=tk.CENTER
        )
        self.card_text.pack(padx=50, pady=(20, 30))

        # Decorative divider with gradient effect (dots)
        self.divider_frame = tk.Frame(self.card_content, bg=self.card_bg)
        self.divider_dots = tk.Label(
            self.divider_frame,
            text="•  •  •",
            font=("Arial", 14),
            bg=self.card_bg,
            fg=ANKI_COLORS["accent_glow"]
        )
        self.divider_dots.pack()

        # Answer text (shown below divider)
        self.answer_text = tk.Label(
            self.card_content,
            text="",
            font=("Georgia", 18) if sys.platform == "darwin" else ("Cambria", 18),
            bg=self.card_bg,
            fg=self.text_color,
            wraplength=700,
            justify=tk.CENTER
        )

        # Example text (smaller, styled)
        self.example_text = tk.Label(
            self.card_content,
            text="",
            font=("SF Pro Display", 12, "italic") if sys.platform == "darwin" else ("Segoe UI", 12, "italic"),
            bg=self.card_bg,
            fg=self.text_dim,
            wraplength=650,
            justify=tk.CENTER
        )

        # Bottom button area with extra padding
        self.button_area = tk.Frame(self.window, bg=self.bg_color)
        self.button_area.pack(fill=tk.X, padx=30, pady=(15, 30))

        # Show Answer button - modern pill style
        self.show_btn = tk.Button(
            self.button_area,
            text="Show Answer",
            command=self.show_answer,
            bg=ANKI_COLORS["show_answer"],
            fg="white",
            font=("SF Pro Display", 14, "bold") if sys.platform == "darwin" else ("Segoe UI", 14, "bold"),
            padx=60,
            pady=14,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=ANKI_COLORS["accent_glow"],
            activeforeground="white",
            borderwidth=0
        )
        self.show_btn.pack(expand=True)

        # Add hover effect to show button
        self._add_button_hover(self.show_btn, ANKI_COLORS["show_answer"], ANKI_COLORS["accent_glow"])

        # Rating buttons frame (hidden initially)
        self.rating_frame = tk.Frame(self.button_area, bg=self.bg_color)

        # Create rating buttons with modern styling
        self._create_rating_buttons()

        # Keyboard bindings
        self.window.bind("<space>", lambda e: self._handle_space())
        self.window.bind("<Return>", lambda e: self._handle_space())
        self.window.bind("1", lambda e: self.rate_card(0) if self.showing_back else None)
        self.window.bind("2", lambda e: self.rate_card(1) if self.showing_back else None)
        self.window.bind("3", lambda e: self.rate_card(2) if self.showing_back else None)
        self.window.bind("4", lambda e: self.rate_card(3) if self.showing_back else None)

    def _add_button_hover(self, button, normal_color, hover_color):
        """Add smooth hover effect to button."""
        def on_enter(e):
            button.config(bg=hover_color)
        def on_leave(e):
            button.config(bg=normal_color)
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def _handle_space(self):
        """Handle space bar - show answer or rate Good."""
        if not self.showing_back:
            self.show_answer()
        else:
            self.rate_card(2)  # Good is default on space when answer shown

    def _create_rating_buttons(self):
        """Create modern, aesthetic rating buttons."""
        # Clear existing buttons
        for widget in self.rating_frame.winfo_children():
            widget.destroy()
        self.review_buttons = []

        button_configs = [
            ("Again", "1", ANKI_COLORS["again"], 0),
            ("Hard", "2", ANKI_COLORS["hard"], 1),
            ("Good", "3", ANKI_COLORS["good"], 2),
            ("Easy", "4", ANKI_COLORS["easy"], 3),
        ]

        font_family = "SF Pro Display" if sys.platform == "darwin" else "Segoe UI"

        for label, key, color, quality in button_configs:
            btn_frame = tk.Frame(self.rating_frame, bg=self.bg_color)
            btn_frame.pack(side=tk.LEFT, padx=12, expand=True)

            # Time interval label above button - more prominent
            time_label = tk.Label(
                btn_frame,
                text="",
                font=(font_family, 11),
                bg=self.bg_color,
                fg=self.text_dim
            )
            time_label.pack(pady=(0, 5))

            # Modern pill-style button
            btn = tk.Button(
                btn_frame,
                text=label,
                command=lambda q=quality: self.rate_card(q),
                bg=color,
                fg="white",
                font=(font_family, 13, "bold"),
                width=12,
                height=2,
                relief=tk.FLAT,
                cursor="hand2",
                activebackground=self._lighten_color(color),
                activeforeground="white",
                borderwidth=0
            )
            btn.pack()

            # Add hover effect
            self._add_button_hover(btn, color, self._lighten_color(color))

            # Keyboard shortcut hint - subtle styling
            hint_label = tk.Label(
                btn_frame,
                text=f"Press {key}",
                font=(font_family, 9),
                bg=self.bg_color,
                fg=self.text_dim
            )
            hint_label.pack(pady=(5, 0))

            self.review_buttons.append((btn, time_label))

    def _lighten_color(self, hex_color):
        """Lighten a hex color for hover effect."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:], 16)
        r = min(255, int(r * 1.2))
        g = min(255, int(g * 1.2))
        b = min(255, int(b * 1.2))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_interval_text(self, quality: int, card: dict) -> str:
        """Calculate and return the interval text for each button (like Anki)."""
        ease = card.get("ease_factor", 2.5)
        interval = card.get("interval", 0)
        reps = card.get("repetitions", 0)

        if quality == 0:  # Again
            return "<1m"
        elif quality == 1:  # Hard
            if reps == 0:
                return "1m"
            new_interval = max(1, int(interval * 0.8))
            return self._format_interval(new_interval)
        elif quality == 2:  # Good
            if reps == 0:
                return "10m"
            elif reps == 1:
                return "1d"
            new_interval = max(1, int(interval * ease))
            return self._format_interval(new_interval)
        else:  # Easy
            if reps == 0:
                return "4d"
            new_interval = int(interval * ease * 1.3)
            return self._format_interval(new_interval)

    def _format_interval(self, days: int) -> str:
        """Format interval in days to human readable string."""
        if days < 1:
            return "<1d"
        elif days == 1:
            return "1d"
        elif days < 30:
            return f"{days}d"
        elif days < 365:
            months = days // 30
            return f"{months}mo"
        else:
            years = days // 365
            return f"{years}y"

    def load_cards(self):
        """Load cards for review."""
        if self.deck_id:
            self.cards = get_due_cards(self.deck_id)
            deck = get_deck(self.deck_id)
            if deck:
                self.deck_label.config(text=deck['name'])
        else:
            self.cards = get_due_cards()
            self.deck_label.config(text="All Decks")

        self._update_counts()

        if not self.cards:
            self.show_completion()
        else:
            self.show_card()

    def _update_counts(self):
        """Update the card counts display (New + Learning + Review)."""
        remaining = len(self.cards) - self.current_index
        # Categorize remaining cards
        new_cards = 0
        learning_cards = 0
        review_cards = 0

        for i, card in enumerate(self.cards[self.current_index:]):
            reps = card.get("repetitions", 0)
            interval = card.get("interval", 0)

            if reps == 0:
                new_cards += 1
            elif interval < 1:
                learning_cards += 1
            else:
                review_cards += 1

        self.new_count.config(text=str(new_cards))
        self.learning_count.config(text=str(learning_cards))
        self.review_count.config(text=str(review_cards))

    def _update_progress(self):
        """Update the progress bar."""
        if len(self.cards) > 0:
            progress = self.current_index / len(self.cards)
            self.progress_fill.place(x=0, y=0, relheight=1, relwidth=progress)

    def show_card(self):
        """Display the current card (front side) with modern styling."""
        if self.current_index >= len(self.cards):
            self.show_completion()
            return

        card = self.cards[self.current_index]
        self.showing_back = False

        # Update counts and progress
        self._update_counts()
        self._update_progress()

        # Reset scroll position to top
        self.card_canvas.yview_moveto(0)

        # Update card type label
        self.card_type_label.config(text="QUESTION")

        # Show question only (hide answer elements)
        self.card_text.config(text=card["front"])
        self.divider_frame.pack_forget()
        self.answer_text.pack_forget()
        self.example_text.pack_forget()

        # Show "Show Answer" button, hide rating buttons
        self.rating_frame.pack_forget()
        self.show_btn.config(text="Show Answer", bg=ANKI_COLORS["show_answer"])
        self._add_button_hover(self.show_btn, ANKI_COLORS["show_answer"], ANKI_COLORS["accent_glow"])
        self.show_btn.pack(expand=True)

    def show_answer(self):
        """Reveal the answer with smooth animation."""
        if self.showing_back or self.current_index >= len(self.cards):
            return

        card = self.cards[self.current_index]
        self.showing_back = True

        # Update card type label
        self.card_type_label.config(text="ANSWER")

        # Show decorative divider and answer
        self.divider_frame.pack(pady=15)
        self.answer_text.config(text=card["back"])
        self.answer_text.pack(expand=True, fill=tk.BOTH, padx=50, pady=(0, 25))

        # Show example if available
        if card.get("example"):
            self.example_text.config(text=f"Example: {card['example']}")
            self.example_text.pack(padx=50, pady=(0, 25))

        # Update interval labels on buttons
        for i, (btn, time_label) in enumerate(self.review_buttons):
            interval_text = self._get_interval_text(i, card)
            time_label.config(text=interval_text)

        # Hide "Show Answer", show rating buttons with fade effect
        self.show_btn.pack_forget()
        self.rating_frame.pack(expand=True)

        # Animate answer appearance (simple fade simulation)
        self._fade_in_answer()

    def _fade_in_answer(self):
        """Simulate fade-in effect for answer text."""
        # Cancel any existing animation
        if self.animation_id:
            self.window.after_cancel(self.animation_id)

        # Simple color transition for fade effect
        colors = [
            self.text_dim,  # Start dimmed
            self._blend_colors(self.text_dim, self.text_color, 0.33),
            self._blend_colors(self.text_dim, self.text_color, 0.66),
            self.text_color  # End at full color
        ]

        def animate(step=0):
            if step < len(colors) and self.answer_text.winfo_exists():
                self.answer_text.config(fg=colors[step])
                self.animation_id = self.window.after(40, lambda: animate(step + 1))

        animate()

    def _blend_colors(self, color1, color2, ratio):
        """Blend two hex colors together."""
        c1 = color1.lstrip('#')
        c2 = color2.lstrip('#')
        r1, g1, b1 = int(c1[:2], 16), int(c1[2:4], 16), int(c1[4:], 16)
        r2, g2, b2 = int(c2[:2], 16), int(c2[2:4], 16), int(c2[4:], 16)
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        return f"#{r:02x}{g:02x}{b:02x}"

    def rate_card(self, quality: int):
        """Rate the card and move to next."""
        if not self.showing_back or self.current_index >= len(self.cards):
            return

        card = self.cards[self.current_index]
        review_card(card["id"], quality)

        self.current_index += 1
        self.show_card()

    def show_completion(self):
        """Show completion screen with celebration."""
        # Update progress to 100%
        self.progress_fill.place(x=0, y=0, relheight=1, relwidth=1)

        # Update card type label
        self.card_type_label.config(text="COMPLETE")

        # Clear card content and show celebration
        self.card_text.config(
            text="Well done!\n\nYou've completed all cards in this session.",
            font=("Georgia", 24) if sys.platform == "darwin" else ("Cambria", 24)
        )
        self.divider_frame.pack_forget()
        self.answer_text.pack_forget()
        self.example_text.pack_forget()

        # Update counts to zeros
        self.new_count.config(text="0")
        self.learning_count.config(text="0")
        self.review_count.config(text="0")

        # Change button to close with softer styling
        self.rating_frame.pack_forget()
        close_color = "#6366f1"  # Indigo
        self.show_btn.config(
            text="Done",
            command=self.window.destroy,
            bg=close_color
        )
        self._add_button_hover(self.show_btn, close_color, "#818cf8")
        self.show_btn.pack(expand=True)

        # Add celebration animation (sparkle effect on divider dots)
        self._celebrate()

    def _celebrate(self):
        """Show a subtle celebration animation."""
        # Color pulse animation on the card type label
        celebration_colors = ["#a78bfa", "#f472b6", "#34d399", "#fbbf24", "#60a5fa"]

        def pulse(step=0):
            if step < 15 and hasattr(self, 'card_type_label') and self.card_type_label.winfo_exists():
                color = celebration_colors[step % len(celebration_colors)]
                self.card_type_label.config(fg=color)
                self.window.after(150, lambda: pulse(step + 1))
            elif hasattr(self, 'card_type_label') and self.card_type_label.winfo_exists():
                self.card_type_label.config(fg=self.text_dim)

        pulse()


class DeckBrowserWindow:
    """Modern deck browser window."""

    def __init__(self, parent, colors=None):
        self.window = tk.Toplevel(parent)
        self.window.title("My Decks")
        self.window.geometry("800x600")
        self.window.minsize(600, 450)

        # Use passed colors or default to dark theme
        self.colors = colors if colors else DARK_THEME
        self.is_dark = self.colors.get("bg", "#000") in ["#12131a", "#1e1e1e", "#2f2f31"]

        # Modern color scheme
        self.bg_color = ANKI_COLORS["review_bg_dark"] if self.is_dark else ANKI_COLORS["review_bg_light"]
        self.card_bg = ANKI_COLORS["card_bg_dark"] if self.is_dark else ANKI_COLORS["card_bg_light"]
        self.text_color = "#e8e8e8" if self.is_dark else "#1a1a2e"
        self.text_dim = "#8b8b9e" if self.is_dark else "#6b7280"
        self.font_family = "SF Pro Display" if sys.platform == "darwin" else "Segoe UI"

        self.window.configure(bg=self.bg_color)

        self.parent = parent
        self.setup_ui()
        self.load_decks()

    def setup_ui(self):
        """Set up modern deck browser UI."""
        # Header with title
        header = tk.Frame(self.window, bg=self.bg_color)
        header.pack(fill=tk.X, padx=25, pady=20)

        tk.Label(
            header,
            text="My Decks",
            font=(self.font_family, 20, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        ).pack(side=tk.LEFT)

        # Study All button - modern pill style
        study_all_btn = tk.Button(
            header,
            text="Study All",
            command=self.study_all,
            bg=ANKI_COLORS["show_answer"],
            fg="white",
            font=(self.font_family, 12, "bold"),
            padx=25,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2",
            borderwidth=0
        )
        study_all_btn.pack(side=tk.RIGHT)
        self._add_button_hover(study_all_btn, ANKI_COLORS["show_answer"], ANKI_COLORS["accent_glow"])

        # Column headers with pill-style badges
        header_frame = tk.Frame(self.window, bg=self.bg_color)
        header_frame.pack(fill=tk.X, padx=25, pady=(5, 10))

        tk.Label(
            header_frame,
            text="DECK NAME",
            font=(self.font_family, 10),
            bg=self.bg_color,
            fg=self.text_dim
        ).pack(side=tk.LEFT, padx=(15, 0))

        # Right side headers for counts - pill style labels
        counts_header = tk.Frame(header_frame, bg=self.bg_color)
        counts_header.pack(side=tk.RIGHT, padx=15)

        tk.Label(counts_header, text="New", font=(self.font_family, 10),
                 bg=self.bg_color, fg="#3b82f6", width=6).pack(side=tk.LEFT)
        tk.Label(counts_header, text="Learn", font=(self.font_family, 10),
                 bg=self.bg_color, fg="#f59e0b", width=6).pack(side=tk.LEFT)
        tk.Label(counts_header, text="Due", font=(self.font_family, 10),
                 bg=self.bg_color, fg="#10b981", width=6).pack(side=tk.LEFT)

        # Deck list container with scrolling
        self.deck_container = tk.Frame(self.window, bg=self.bg_color)
        self.deck_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=10)

        # Canvas for scrolling
        self.canvas = tk.Canvas(self.deck_container, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.deck_container, orient="vertical", command=self.canvas.yview)

        self.deck_list = tk.Frame(self.canvas, bg=self.bg_color)

        self.deck_list.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.deck_list, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Bind canvas resize
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Enable mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_resize(self, event):
        """Update deck list width when canvas resizes."""
        self.canvas.itemconfig(self.canvas.find_all()[0], width=event.width)

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _add_button_hover(self, button, normal_color, hover_color):
        """Add smooth hover effect to button."""
        def on_enter(e):
            button.config(bg=hover_color)
        def on_leave(e):
            button.config(bg=normal_color)
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def load_decks(self):
        """Load and display all decks with modern styling."""
        # Clear existing
        for widget in self.deck_list.winfo_children():
            widget.destroy()

        decks = get_all_decks()

        if not decks:
            # Empty state with modern styling
            empty_frame = tk.Frame(self.deck_list, bg=self.bg_color)
            empty_frame.pack(pady=80, expand=True)

            tk.Label(
                empty_frame,
                text="No decks yet",
                font=(self.font_family, 18, "bold"),
                bg=self.bg_color,
                fg=self.text_color
            ).pack()

            tk.Label(
                empty_frame,
                text="Generate flashcards and save them to a deck to get started.",
                font=(self.font_family, 12),
                bg=self.bg_color,
                fg=self.text_dim
            ).pack(pady=(10, 0))
            return

        for deck in decks:
            self._create_deck_row(deck)

    def _create_deck_row(self, deck):
        """Create a modern deck row with card-like styling."""
        stats = get_deck_stats(deck["id"])

        # Row container with subtle shadow effect
        row_container = tk.Frame(self.deck_list, bg=self.bg_color)
        row_container.pack(fill=tk.X, pady=4)

        # Main row with card background
        row = tk.Frame(row_container, bg=self.card_bg, cursor="hand2")
        row.pack(fill=tk.X, padx=2, pady=2)

        # Inner padding
        inner = tk.Frame(row, bg=self.card_bg)
        inner.pack(fill=tk.X, padx=18, pady=14)

        # Left side - deck name
        name_frame = tk.Frame(inner, bg=self.card_bg)
        name_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        deck_name = tk.Label(
            name_frame,
            text=deck["name"],
            font=(self.font_family, 14),
            bg=self.card_bg,
            fg=self.text_color,
            cursor="hand2"
        )
        deck_name.pack(anchor="w")

        # Right side - counts with modern styling
        counts_frame = tk.Frame(inner, bg=self.card_bg)
        counts_frame.pack(side=tk.RIGHT)

        # New count (blue)
        new_cards = sum(1 for c in get_cards_for_deck(deck["id"]) if c.get("repetitions", 0) == 0)
        tk.Label(
            counts_frame,
            text=str(new_cards),
            font=(self.font_family, 13, "bold"),
            bg=self.card_bg,
            fg="#3b82f6",
            width=6
        ).pack(side=tk.LEFT)

        # Learning count (amber)
        tk.Label(
            counts_frame,
            text=str(stats['learning']),
            font=(self.font_family, 13, "bold"),
            bg=self.card_bg,
            fg="#f59e0b",
            width=6
        ).pack(side=tk.LEFT)

        # Due count (green)
        tk.Label(
            counts_frame,
            text=str(stats['due']),
            font=(self.font_family, 13, "bold"),
            bg=self.card_bg,
            fg="#10b981",
            width=6
        ).pack(side=tk.LEFT)

        # Delete button (modern styling)
        delete_btn = tk.Button(
            counts_frame,
            text="×",
            command=lambda d=deck["id"]: self.confirm_delete(d),
            bg=self.card_bg,
            fg=self.text_dim,
            font=(self.font_family, 14),
            width=2,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=ANKI_COLORS["again"],
            activeforeground="white",
            borderwidth=0
        )
        delete_btn.pack(side=tk.LEFT, padx=(15, 0))

        # Bind click to study
        for widget in [row, inner, name_frame, deck_name]:
            widget.bind("<Button-1>", lambda e, d=deck["id"]: self.study_deck(d))

        # Modern hover effect
        hover_bg = "#2a2a3a" if self.is_dark else "#f1f5f9"
        def on_enter(e):
            row.config(bg=hover_bg)
            inner.config(bg=hover_bg)
            name_frame.config(bg=hover_bg)
            deck_name.config(bg=hover_bg)
            for child in counts_frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=hover_bg)

        def on_leave(e):
            row.config(bg=self.card_bg)
            inner.config(bg=self.card_bg)
            name_frame.config(bg=self.card_bg)
            deck_name.config(bg=self.card_bg)
            for child in counts_frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=self.card_bg)

        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)

    def study_deck(self, deck_id):
        """Open review window for a deck."""
        FlashcardReviewWindow(self.window, deck_id, self.colors)

    def study_all(self):
        """Open review window for all due cards."""
        FlashcardReviewWindow(self.window, colors=self.colors)

    def confirm_delete(self, deck_id):
        """Confirm and delete a deck."""
        deck = get_deck(deck_id)
        if messagebox.askyesno("Delete Deck", f"Delete '{deck['name']}' and all its cards?"):
            delete_deck(deck_id)
            self.load_decks()


def open_deck_browser(parent, colors=None):
    """Open the deck browser window."""
    DeckBrowserWindow(parent, colors)


def open_review(parent, deck_id=None, colors=None):
    """Open the review window."""
    FlashcardReviewWindow(parent, deck_id, colors)
