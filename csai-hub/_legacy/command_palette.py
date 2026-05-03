"""
Command palette for quick actions in Statistics Study Assistant.
VS Code-style popup with fuzzy search filtering.
"""

import tkinter as tk
from themes import DARK_THEME


class CommandPalette:
    """VS Code-style command palette."""

    def __init__(self, parent, colors, actions):
        """
        Args:
            parent: Root window
            colors: Theme colors dict
            actions: List of dicts with 'name', 'description', 'callback', 'icon'
        """
        self.parent = parent
        self.colors = colors if colors else DARK_THEME
        self.all_actions = actions
        self.filtered_actions = actions.copy()
        self.selected_index = 0

        self.create_palette()

    def create_palette(self):
        """Create the command palette overlay."""
        # Overlay background
        self.overlay = tk.Frame(self.parent, bg=self.colors["bg"])
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.overlay.bind("<Button-1>", lambda e: self.close())

        # Palette container (centered, top portion of screen)
        self.palette = tk.Frame(self.overlay, bg=self.colors["surface"],
                               highlightbackground=self.colors["border"],
                               highlightthickness=1)
        self.palette.place(relx=0.5, rely=0.15, anchor="n", width=550)

        # Search entry frame
        search_frame = tk.Frame(self.palette, bg=self.colors["surface"])
        search_frame.pack(fill=tk.X, padx=15, pady=15)

        tk.Label(search_frame, text=">",
            font=("SF Pro Display", 16, "bold"),
            bg=self.colors["surface"],
            fg=self.colors["primary"]).pack(side=tk.LEFT)

        self.search_entry = tk.Entry(search_frame,
            font=("SF Pro Display", 15),
            bg=self.colors["surface"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief=tk.FLAT,
            highlightthickness=0)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        self.search_entry.focus_set()
        self.search_entry.bind("<KeyRelease>", self.on_search)
        self.search_entry.bind("<Return>", lambda e: self.execute_selected())
        self.search_entry.bind("<Up>", lambda e: self.move_selection(-1))
        self.search_entry.bind("<Down>", lambda e: self.move_selection(1))
        self.search_entry.bind("<Escape>", lambda e: self.close())

        # Divider
        tk.Frame(self.palette, bg=self.colors["border"], height=1).pack(fill=tk.X)

        # Results list
        self.results_frame = tk.Frame(self.palette, bg=self.colors["surface"])
        self.results_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        self.render_results()

    def on_search(self, event):
        """Filter actions based on search."""
        query = self.search_entry.get().lower()

        if not query:
            self.filtered_actions = self.all_actions.copy()
        else:
            self.filtered_actions = [
                a for a in self.all_actions
                if query in a["name"].lower() or query in a.get("description", "").lower()
            ]

        self.selected_index = 0
        self.render_results()

    def render_results(self):
        """Render the filtered results."""
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not self.filtered_actions:
            tk.Label(self.results_frame, text="No matching commands",
                    font=("SF Pro Display", 12),
                    bg=self.colors["surface"],
                    fg=self.colors["text_muted"]).pack(pady=20)
            return

        for i, action in enumerate(self.filtered_actions[:10]):
            is_selected = (i == self.selected_index)

            row = tk.Frame(self.results_frame,
                bg=self.colors["surface_hover"] if is_selected else self.colors["surface"],
                cursor="hand2")
            row.pack(fill=tk.X, pady=1)

            inner = tk.Frame(row,
                bg=self.colors["surface_hover"] if is_selected else self.colors["surface"])
            inner.pack(fill=tk.X, padx=10, pady=8)

            # Icon
            tk.Label(inner, text=action.get("icon", "⚡"),
                font=("SF Pro Display", 14),
                bg=inner.cget("bg")).pack(side=tk.LEFT)

            # Name
            tk.Label(inner, text=action["name"],
                font=("SF Pro Display", 13),
                bg=inner.cget("bg"),
                fg=self.colors["text"]).pack(side=tk.LEFT, padx=(10, 0))

            # Description (if present)
            if action.get("description"):
                tk.Label(inner, text=action["description"],
                    font=("SF Pro Display", 11),
                    bg=inner.cget("bg"),
                    fg=self.colors["text_muted"]).pack(side=tk.RIGHT)

            # Bind click
            for widget in [row, inner] + list(inner.winfo_children()):
                widget.bind("<Button-1>", lambda e, idx=i: self.execute_action(idx))

    def move_selection(self, direction):
        """Move selection up or down."""
        self.selected_index = max(0, min(len(self.filtered_actions) - 1,
                                         self.selected_index + direction))
        self.render_results()

    def execute_selected(self):
        """Execute the currently selected action."""
        self.execute_action(self.selected_index)

    def execute_action(self, index):
        """Execute an action by index."""
        if 0 <= index < len(self.filtered_actions):
            action = self.filtered_actions[index]
            self.close()
            try:
                action["callback"]()
            except Exception:
                pass

    def close(self):
        """Close the command palette."""
        self.overlay.destroy()


def open_command_palette(parent, colors, app):
    """Open the command palette with available actions.

    Args:
        parent: Root window
        colors: Theme colors dict
        app: StatsStudyApp instance for callbacks
    """
    # Import STUDY_GUIDE here to avoid circular imports
    from ui import STUDY_GUIDE

    actions = [
        # Navigation
        {"name": "Go to Study Guide", "icon": "📖", "callback": lambda: app.notebook.select(0)},
        {"name": "Go to Materials", "icon": "📊", "callback": lambda: app.notebook.select(1)},
        {"name": "Go to Q&A", "icon": "💬", "callback": lambda: app.notebook.select(2)},
        {"name": "Go to Quiz", "icon": "📝", "callback": lambda: app.notebook.select(3)},
        {"name": "Go to Flashcards", "icon": "🃏", "callback": lambda: app.notebook.select(4)},

        # Pomodoro actions
        {"name": "Start/Pause Pomodoro", "icon": "🍅", "callback": app.toggle_timer, "description": "Start or pause timer"},
        {"name": "Reset Timer", "icon": "↺", "callback": app.reset_timer, "description": "Reset to 25:00"},
        {"name": "Skip to Break", "icon": "⏭", "callback": app.skip_timer, "description": "Skip current phase"},

        # Quick actions
        {"name": "Focus Search", "icon": "🔍", "callback": app.focus_global_search, "description": "⌘K"},
        {"name": "Open Flashcard Browser", "icon": "📚", "callback": app.open_deck_browser},
        {"name": "Review Due Flashcards", "icon": "🔄", "callback": app.study_flashcards},

        # Theme
        {"name": "Toggle Theme", "icon": "🌙", "callback": app.toggle_theme, "description": "Light/Dark mode"},
    ]

    # Add lecture shortcuts
    for lecture, data in STUDY_GUIDE.items():
        short_name = lecture.split(":")[0] if ":" in lecture else lecture[:20]
        actions.append({
            "name": f"Study: {short_name}",
            "icon": data["icon"],
            "description": f"{len(data['topics'])} topics",
            "callback": lambda l=lecture, d=data: app.study_topic(d["topics"][0]) if d["topics"] else None
        })

    return CommandPalette(parent, colors, actions)
