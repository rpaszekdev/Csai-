"""
Onboarding overlay and tooltip system for Study Assistant.
"""

import tkinter as tk
from config import get_user_preferences, save_user_preferences
from themes import DARK_THEME
import subject_config


class OnboardingOverlay:
    """First-run tutorial overlay with step-by-step guide."""

    def __init__(self, parent, colors=None):
        self.parent = parent
        self.colors = colors if colors else DARK_THEME
        self.current_step = 0
        self.steps = [
            {
                "title": f"Welcome to {subject_config.SUBJECT_NAME} Study Assistant!",
                "text": f"Your AI-powered study companion for {subject_config.COURSE_NAME}.\nLet's take a quick tour of the main features.",
                "icon": "📚"
            },
            {
                "title": "Study Guide",
                "text": f"Browse all {len(subject_config.STUDY_GUIDE)} lectures and their topics.\nClick 'Study' to open an AI-generated study session\nwith summaries and key concepts.",
                "icon": "📖"
            },
            {
                "title": "Q&A with AI",
                "text": "Ask any question about your course materials.\nThe AI searches your lecture PDFs and provides\ncontextual answers with source references.",
                "icon": "💬"
            },
            {
                "title": "Practice Quizzes",
                "text": "Generate practice quizzes on any topic.\nTrack your progress over time and create\nflashcards from questions you got wrong.",
                "icon": "📝"
            },
            {
                "title": "Flashcards",
                "text": "Create flashcards with spaced repetition.\nPerfect for memorizing key concepts and formulas.",
                "icon": "🃏"
            },
            {
                "title": "Pomodoro Timer",
                "text": "Built-in timer to keep you focused.\nTracks your total study time across sessions.",
                "icon": "🍅"
            },
            {
                "title": "You're Ready!",
                "text": "Start by exploring a topic in the Study Guide,\nor ask a question in the Q&A tab.\n\nPress ⌘K anytime to search everything.",
                "icon": "🎉"
            }
        ]

        self.create_overlay()

    def create_overlay(self):
        """Create the overlay window."""
        # Semi-transparent overlay
        self.overlay = tk.Frame(self.parent, bg=self.colors["bg"])
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Center card
        self.card = tk.Frame(self.overlay, bg=self.colors["surface"],
                            highlightbackground=self.colors["border"],
                            highlightthickness=1)
        self.card.place(relx=0.5, rely=0.5, anchor="center", width=480, height=340)

        inner = tk.Frame(self.card, bg=self.colors["surface"])
        inner.pack(expand=True, fill=tk.BOTH, padx=35, pady=30)

        # Icon
        self.icon_label = tk.Label(inner, text="📚",
            font=("SF Pro Display", 42),
            bg=self.colors["surface"])
        self.icon_label.pack(pady=(0, 10))

        # Title
        self.title_label = tk.Label(inner, text="",
            font=("SF Pro Display", 18, "bold"),
            bg=self.colors["surface"],
            fg=self.colors["text"])
        self.title_label.pack()

        # Text
        self.text_label = tk.Label(inner, text="",
            font=("SF Pro Display", 13),
            bg=self.colors["surface"],
            fg=self.colors["text_secondary"],
            justify=tk.CENTER)
        self.text_label.pack(pady=(15, 0))

        # Progress dots
        self.dots_frame = tk.Frame(inner, bg=self.colors["surface"])
        self.dots_frame.pack(pady=(25, 0))

        self.dots = []
        for i in range(len(self.steps)):
            dot = tk.Label(self.dots_frame, text="●",
                font=("SF Pro Display", 8),
                bg=self.colors["surface"],
                fg=self.colors["primary"] if i == 0 else self.colors["text_muted"])
            dot.pack(side=tk.LEFT, padx=3)
            self.dots.append(dot)

        # Buttons
        btn_frame = tk.Frame(inner, bg=self.colors["surface"])
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

        self.skip_btn = tk.Button(btn_frame, text="Skip Tour",
            command=self.close,
            bg=self.colors["surface"],
            fg=self.colors["text_muted"],
            font=("SF Pro Display", 11),
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=self.colors["surface_hover"])
        self.skip_btn.pack(side=tk.LEFT)

        self.next_btn = tk.Button(btn_frame, text="Next →",
            command=self.next_step,
            bg=self.colors["primary"],
            fg="white",
            font=("SF Pro Display", 12, "bold"),
            padx=20, pady=8,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=self.colors.get("primary_hover", "#8b5cf6"))
        self.next_btn.pack(side=tk.RIGHT)

        # Show first step
        self.show_step(0)

        # Bind keyboard
        self.parent.bind("<Return>", lambda e: self.next_step())
        self.parent.bind("<Escape>", lambda e: self.close())

    def show_step(self, step_idx):
        """Display a specific step."""
        self.current_step = step_idx
        step = self.steps[step_idx]

        self.icon_label.config(text=step["icon"])
        self.title_label.config(text=step["title"])
        self.text_label.config(text=step["text"])

        # Update dots
        for i, dot in enumerate(self.dots):
            dot.config(fg=self.colors["primary"] if i == step_idx else self.colors["text_muted"])

        # Update button text for last step
        if step_idx == len(self.steps) - 1:
            self.next_btn.config(text="Get Started!")
            self.skip_btn.pack_forget()
        else:
            self.next_btn.config(text="Next →")
            self.skip_btn.pack(side=tk.LEFT)

    def next_step(self):
        """Go to next step or close."""
        if self.current_step < len(self.steps) - 1:
            self.show_step(self.current_step + 1)
        else:
            self.close()

    def close(self):
        """Close overlay and mark onboarding complete."""
        # Unbind keyboard
        try:
            self.parent.unbind("<Return>")
            self.parent.unbind("<Escape>")
        except:
            pass

        self.overlay.destroy()
        prefs = get_user_preferences()
        prefs["onboarding_complete"] = True
        save_user_preferences(prefs)


class Tooltip:
    """Hover tooltip for widgets."""

    def __init__(self, widget, text, colors=None):
        self.widget = widget
        self.text = text
        self.colors = colors if colors else DARK_THEME
        self.tooltip = None

        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        """Show the tooltip."""
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip, text=self.text,
            font=("SF Pro Display", 11),
            bg=self.colors["surface"],
            fg=self.colors["text"],
            padx=10, pady=6,
            highlightbackground=self.colors["border"],
            highlightthickness=1)
        label.pack()

    def hide(self, event=None):
        """Hide the tooltip."""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


def show_onboarding_if_needed(parent, colors=None):
    """Show onboarding if user hasn't completed it.

    Args:
        parent: Root window
        colors: Theme colors dict

    Returns:
        OnboardingOverlay instance if shown, None otherwise
    """
    prefs = get_user_preferences()
    if not prefs.get("onboarding_complete", False):
        return OnboardingOverlay(parent, colors)
    return None


def create_empty_state(parent, icon, title, subtitle, colors=None):
    """Create an empty state widget.

    Args:
        parent: Parent widget
        icon: Emoji icon to display
        title: Main message
        subtitle: Secondary message
        colors: Theme colors dict

    Returns:
        Frame containing the empty state
    """
    colors = colors if colors else DARK_THEME

    frame = tk.Frame(parent, bg=colors["bg"])

    tk.Label(frame, text=icon,
            font=("SF Pro Display", 48),
            bg=colors["bg"]).pack()

    tk.Label(frame, text=title,
            font=("SF Pro Display", 16, "bold"),
            bg=colors["bg"],
            fg=colors["text"]).pack(pady=(15, 5))

    tk.Label(frame, text=subtitle,
            font=("SF Pro Display", 12),
            bg=colors["bg"],
            fg=colors["text_muted"],
            justify=tk.CENTER).pack()

    return frame
