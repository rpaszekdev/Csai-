#!/usr/bin/env python3
"""
📚 Study Assistant - Desktop UI
A clean, modern Python GUI for RAG-powered studying
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import subprocess
import json
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from study_rag import (
    retrieve_context,
    retrieve_context_smart,
    get_vector_store,
    index_documents,
    CONFIG
)

import subject_config

from config import (
    CLAUDE_MODELS, DEFAULT_MODEL, DEFAULT_OUTPUT_WORDS,
    MIN_OUTPUT_WORDS, MAX_OUTPUT_WORDS,
    get_user_preferences, save_user_preferences
)

from themes import get_theme, DARK_THEME

from flashcard_db import (
    parse_claude_flashcards,
    get_all_decks,
    get_deck_stats,
    get_due_cards
)

from flashcard_review import open_deck_browser, open_review
from quiz_system import open_quiz, load_quiz_db
from study_session import open_study_session
from lecture_study import open_lecture_study
from concept_quiz import open_concept_quiz
from qa_window import open_qa_window, open_qa_result
from onboarding import show_onboarding_if_needed, Tooltip
from command_palette import open_command_palette
# R interpreter removed — subject-agnostic version
from content_storage import (
    save_quiz, get_quiz, quiz_exists, add_quiz_attempt,
    get_all_study_sessions, get_all_quizzes, study_session_exists,
    get_storage_stats, save_pomodoro_session, get_total_study_time,
    get_pomodoro_stats
)

# Progress file path
PROGRESS_FILE = Path(__file__).parent / "study_progress.json"

# Study Guide Data Structure - loaded from subject config
STUDY_GUIDE = subject_config.STUDY_GUIDE


class StudyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"📚 {subject_config.SUBJECT_NAME} Study Assistant")
        self.root.geometry("1200x900")

        # Load user preferences and theme
        self.prefs = get_user_preferences()
        self.current_theme = self.prefs.get("theme", "dark")
        self.colors = get_theme(self.current_theme)

        self.root.configure(bg=self.colors["bg"])

        # Load progress
        self.progress = self.load_progress()

        # Pomodoro timer state (persistent across all tabs)
        self.pomodoro_work_minutes = 25
        self.pomodoro_break_minutes = 5
        self.pomodoro_long_break_minutes = 15
        self.pomodoros_until_long_break = 4
        self.timer_running = False
        self.timer_paused = False
        self.is_break_time = False
        self.time_remaining = self.pomodoro_work_minutes * 60
        self.current_session_time = 0  # Time spent in current session
        self.total_study_time = get_total_study_time()  # Load persisted total
        self.pomodoros_completed = 0
        self.timer_id = None

        # Q&A Settings (model selection and output length)
        self.qa_model = tk.StringVar(value=DEFAULT_MODEL)
        self.qa_output_words = tk.IntVar(value=DEFAULT_OUTPUT_WORDS)

        # Style configuration
        self.setup_styles()

        # Create main container with more padding
        self.main_frame = tk.Frame(root, bg=self.colors["bg"])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Create Pomodoro timer bar (above tabs)
        self.create_pomodoro_bar()

        # Create global search bar
        self.create_global_search_bar()

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.main_frame, style="Custom.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self.create_study_guide_tab()
        self.create_overview_tab()
        self.create_qa_tab()
        self.create_quiz_tab()
        self.create_flashcard_tab()
        self.create_my_notes_tab()
        # R interpreter tab removed — subject-agnostic

        # Create floating mini-timer (subtle, bottom-right)
        self.create_floating_mini_timer()

        # Load initial stats
        self.root.after(100, self.load_stats)

        # Show onboarding if first run (after short delay to let UI render)
        self.root.after(500, lambda: show_onboarding_if_needed(self.root, self.colors))

    def load_progress(self):
        """Load study progress from file."""
        if PROGRESS_FILE.exists():
            try:
                return json.loads(PROGRESS_FILE.read_text())
            except:
                pass
        return {}

    def save_progress(self):
        """Save study progress to file."""
        PROGRESS_FILE.write_text(json.dumps(self.progress, indent=2))

    def setup_styles(self):
        """Configure ttk styles for modern look."""
        style = ttk.Style()

        # Main frame styles
        style.configure("Main.TFrame", background=self.colors["bg"])
        style.configure("Card.TFrame", background=self.colors["surface"])

        # Notebook (tabs) styling
        style.configure("Custom.TNotebook", background=self.colors["bg"])
        style.configure("Custom.TNotebook.Tab",
                       padding=[28, 14],
                       font=("Helvetica Neue", 13, "bold"))

        # Labels
        style.configure("Title.TLabel",
                       background=self.colors["surface"],
                       foreground=self.colors["text"],
                       font=("Helvetica Neue", 20, "bold"))
        style.configure("Info.TLabel",
                       background=self.colors["surface"],
                       foreground=self.colors["text_secondary"],
                       font=("Helvetica Neue", 12))

        # Progress bar
        style.configure("Custom.Horizontal.TProgressbar",
                       troughcolor=self.colors["input_bg"],
                       background=self.colors["primary"],
                       thickness=10)

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        # Switch theme
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.colors = get_theme(self.current_theme)

        # Save preference
        self.prefs["theme"] = self.current_theme
        save_user_preferences(self.prefs)

        # Update theme button icon
        theme_icon = "☀️" if self.current_theme == "dark" else "🌙"
        self.theme_btn.config(text=theme_icon)

        # Show message about restart (full theme refresh requires restart)
        messagebox.showinfo(
            "Theme Changed",
            f"Theme switched to {'Light' if self.current_theme == 'light' else 'Dark'} mode.\n\n"
            "Restart the app to apply the theme fully."
        )

    def create_global_search_bar(self):
        """Create the always-visible global search bar."""
        search_frame = tk.Frame(self.main_frame, bg=self.colors["surface"])
        search_frame.pack(fill=tk.X, pady=(0, 10))

        inner = tk.Frame(search_frame, bg=self.colors["surface"])
        inner.pack(fill=tk.X, padx=15, pady=8)

        # Search icon
        tk.Label(inner, text="🔍", font=("SF Pro Display", 14),
                bg=self.colors["surface"]).pack(side=tk.LEFT)

        # Search entry
        self.global_search_var = tk.StringVar()
        self.global_search_entry = tk.Entry(inner,
            textvariable=self.global_search_var,
            font=("SF Pro Display", 13),
            bg=self.colors["input_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief=tk.FLAT,
            width=50)
        self.global_search_entry.pack(side=tk.LEFT, padx=(10, 0), ipady=6)
        self.global_search_entry.insert(0, "Search topics, flashcards, quizzes...")
        self.global_search_entry.config(fg=self.colors["text_muted"])

        self.global_search_entry.bind("<FocusIn>", self.on_search_focus)
        self.global_search_entry.bind("<FocusOut>", self.on_search_blur)
        self.global_search_entry.bind("<Return>", lambda e: self.perform_global_search())
        self.global_search_entry.bind("<KeyRelease>", self.on_search_key)

        # Keyboard shortcut hint
        shortcut = "⌘K" if sys.platform == "darwin" else "Ctrl+K"
        tk.Label(inner, text=shortcut,
                font=("SF Pro Display", 10),
                bg=self.colors["input_bg"],
                fg=self.colors["text_muted"],
                padx=8).pack(side=tk.LEFT)

        # Results dropdown (hidden initially)
        self.search_results_frame = tk.Frame(self.main_frame, bg=self.colors["surface"],
                                             highlightbackground=self.colors["border"],
                                             highlightthickness=1)
        self.search_results_visible = False

        # Bind global shortcuts
        self.root.bind("<Command-k>", lambda e: self.focus_global_search())
        self.root.bind("<Control-k>", lambda e: self.focus_global_search())
        self.root.bind("<Command-p>", lambda e: self.show_command_palette())
        self.root.bind("<Control-p>", lambda e: self.show_command_palette())
        self.root.bind("<Escape>", lambda e: self.close_search_results())

    def focus_global_search(self):
        """Focus the global search entry."""
        self.global_search_entry.focus_set()
        self.global_search_entry.select_range(0, tk.END)

    def on_search_focus(self, event):
        """Handle search entry focus."""
        current = self.global_search_entry.get()
        if current == "Search topics, flashcards, quizzes...":
            self.global_search_entry.delete(0, tk.END)
            self.global_search_entry.config(fg=self.colors["text"])

    def on_search_blur(self, event):
        """Handle search entry blur."""
        if not self.global_search_entry.get():
            self.global_search_entry.insert(0, "Search topics, flashcards, quizzes...")
            self.global_search_entry.config(fg=self.colors["text_muted"])
        self.root.after(200, self.close_search_results)

    def on_search_key(self, event):
        """Handle key release in search - live search."""
        query = self.global_search_entry.get()
        if query and query != "Search topics, flashcards, quizzes..." and len(query) >= 2:
            self.perform_global_search()
        else:
            self.close_search_results()

    def perform_global_search(self):
        """Search all content sources."""
        query = self.global_search_entry.get().lower().strip()
        if not query or query == "search topics, flashcards, quizzes...":
            return

        results = {"topics": [], "flashcards": [], "quizzes": []}

        # Search topics from STUDY_GUIDE
        for lecture_name, lecture_data in STUDY_GUIDE.items():
            if query in lecture_name.lower():
                results["topics"].append({"type": "lecture", "name": lecture_name, "icon": lecture_data["icon"]})
            for topic in lecture_data["topics"]:
                if query in topic.lower():
                    results["topics"].append({"type": "topic", "name": topic, "lecture": lecture_name})

        # Search flashcards
        try:
            from flashcard_db import load_db
            flash_db = load_db()
            for card_id, card in flash_db.get("cards", {}).items():
                if query in card.get("front", "").lower() or query in card.get("back", "").lower():
                    results["flashcards"].append({
                        "id": card_id,
                        "front": card["front"][:50] + "..." if len(card["front"]) > 50 else card["front"],
                        "deck_id": card.get("deck_id")
                    })
        except Exception:
            pass

        # Search quiz history
        try:
            quiz_db = load_quiz_db()
            for quiz_id, quiz in quiz_db.get("quizzes", {}).items():
                if query in quiz.get("topic", "").lower():
                    results["quizzes"].append({
                        "id": quiz_id,
                        "topic": quiz["topic"],
                        "score": f"{quiz.get('score', 0)}/{quiz.get('total', 0)}",
                        "date": quiz.get("date", "")[:10]
                    })
        except Exception:
            pass

        self.show_search_results(results)

    def show_search_results(self, results):
        """Display search results in dropdown."""
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()

        total_results = sum(len(v) for v in results.values())
        if total_results == 0:
            self.close_search_results()
            return

        # Position below search bar
        self.search_results_frame.place(x=15, y=145, width=600)
        self.search_results_visible = True

        categories = [
            ("📚 Topics", results["topics"], self.go_to_topic),
            ("🃏 Flashcards", results["flashcards"], self.go_to_flashcard),
            ("📝 Quiz History", results["quizzes"], self.go_to_quiz),
        ]

        for cat_name, items, callback in categories:
            if not items:
                continue

            tk.Label(self.search_results_frame, text=cat_name,
                    font=("SF Pro Display", 10, "bold"),
                    bg=self.colors["surface"],
                    fg=self.colors["text_muted"]).pack(anchor="w", padx=15, pady=(10, 5))

            for item in items[:5]:
                row = tk.Frame(self.search_results_frame, bg=self.colors["surface"], cursor="hand2")
                row.pack(fill=tk.X, padx=10, pady=2)

                display_text = item.get("name") or item.get("front") or item.get("topic") or ""
                lbl = tk.Label(row, text=display_text,
                        font=("SF Pro Display", 12),
                        bg=self.colors["surface"],
                        fg=self.colors["text"])
                lbl.pack(side=tk.LEFT, padx=10, pady=6)

                row.bind("<Button-1>", lambda e, i=item, cb=callback: cb(i))
                lbl.bind("<Button-1>", lambda e, i=item, cb=callback: cb(i))

                # Hover effect
                row.bind("<Enter>", lambda e, r=row: r.config(bg=self.colors["surface_hover"]))
                row.bind("<Leave>", lambda e, r=row: r.config(bg=self.colors["surface"]))

    def close_search_results(self):
        """Hide the search results dropdown."""
        if self.search_results_visible:
            self.search_results_frame.place_forget()
            self.search_results_visible = False

    def go_to_topic(self, item):
        """Navigate to a topic."""
        self.close_search_results()
        self.notebook.select(0)  # Study Guide tab

    def go_to_flashcard(self, item):
        """Navigate to flashcards."""
        self.close_search_results()
        self.notebook.select(4)  # Flashcards tab

    def go_to_quiz(self, item):
        """Navigate to quiz tab."""
        self.close_search_results()
        self.notebook.select(3)  # Quiz tab

    def show_command_palette(self):
        """Show the command palette."""
        open_command_palette(self.root, self.colors, self)

    def create_pomodoro_bar(self):
        """Create the Pomodoro timer bar above tabs."""
        timer_bar = tk.Frame(self.main_frame, bg=self.colors["surface"])
        timer_bar.pack(fill=tk.X, pady=(0, 15))

        inner = tk.Frame(timer_bar, bg=self.colors["surface"])
        inner.pack(fill=tk.X, padx=20, pady=12)

        # Left side: App title/icon
        left_frame = tk.Frame(inner, bg=self.colors["surface"])
        left_frame.pack(side=tk.LEFT)

        tk.Label(left_frame, text="🍅",
                font=("Helvetica Neue", 24),
                bg=self.colors["surface"]).pack(side=tk.LEFT)

        tk.Label(left_frame, text="Pomodoro Timer",
                font=("Helvetica Neue", 16, "bold"),
                bg=self.colors["surface"],
                fg=self.colors["text"]).pack(side=tk.LEFT, padx=(10, 0))

        # Theme toggle button
        theme_icon = "☀️" if self.current_theme == "dark" else "🌙"
        self.theme_btn = tk.Button(left_frame, text=theme_icon,
                                   command=self.toggle_theme,
                                   bg=self.colors["surface"],
                                   fg=self.colors["text"],
                                   font=("SF Pro Display", 16),
                                   relief=tk.FLAT,
                                   padx=8, pady=2,
                                   cursor="hand2",
                                   activebackground=self.colors["surface_hover"])
        self.theme_btn.pack(side=tk.LEFT, padx=(20, 0))

        # Total Study Time - visible and persistent across sessions
        initial_total = self.format_total_time(self.total_study_time)
        self.total_time_label = tk.Label(left_frame, text=initial_total,
                                         font=("Menlo", 14, "bold"),
                                         bg=self.colors["surface"],
                                         fg=self.colors["primary"])
        self.total_time_label.pack(side=tk.LEFT, padx=(25, 0))

        # Right side: Timer controls
        right_frame = tk.Frame(inner, bg=self.colors["surface"])
        right_frame.pack(side=tk.RIGHT)

        # Pomodoro count
        self.pomodoro_count_label = tk.Label(right_frame, text="🍅 0/4",
                                             font=("Helvetica Neue", 12),
                                             bg=self.colors["surface"],
                                             fg=self.colors["text_secondary"])
        self.pomodoro_count_label.pack(side=tk.RIGHT, padx=(15, 0))

        # Skip button
        skip_btn = tk.Button(right_frame, text="⏭",
                             command=self.skip_timer,
                             bg=self.colors["input_bg"],
                             fg="#000000",
                             font=("Helvetica Neue", 14),
                             relief=tk.FLAT,
                             padx=8, pady=3,
                             cursor="hand2",
                             activebackground=self.colors["surface_hover"],
                             activeforeground="#000000")
        skip_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Reset button
        reset_btn = tk.Button(right_frame, text="↺",
                              command=self.reset_timer,
                              bg=self.colors["input_bg"],
                              fg="#000000",
                              font=("Helvetica Neue", 14),
                              relief=tk.FLAT,
                              padx=8, pady=3,
                              cursor="hand2",
                              activebackground=self.colors["surface_hover"],
                              activeforeground="#000000")
        reset_btn.pack(side=tk.RIGHT, padx=(8, 0))

        # Start/Pause button
        self.timer_btn = tk.Button(right_frame, text="▶ Start",
                                   command=self.toggle_timer,
                                   bg=self.colors["success"],
                                   fg="#000000",
                                   font=("Helvetica Neue", 11, "bold"),
                                   relief=tk.FLAT,
                                   padx=12, pady=5,
                                   cursor="hand2",
                                   activebackground="#059669",
                                   activeforeground="#000000")
        self.timer_btn.pack(side=tk.RIGHT, padx=(15, 0))

        # Status label (WORK/BREAK)
        self.timer_status = tk.Label(right_frame, text="WORK",
                                     font=("Helvetica Neue", 10, "bold"),
                                     bg=self.colors["primary"],
                                     fg="white",
                                     padx=8, pady=2)
        self.timer_status.pack(side=tk.RIGHT, padx=(10, 0))

        # Time display
        self.timer_display = tk.Label(right_frame, text="25:00",
                                      font=("Menlo", 28, "bold"),
                                      bg=self.colors["surface"],
                                      fg=self.colors["text"])
        self.timer_display.pack(side=tk.RIGHT)

    def create_floating_mini_timer(self):
        """Create a subtle floating mini-timer in top-right corner."""
        # Container positioned at top-right of the window
        self.mini_timer_frame = tk.Frame(self.root, bg="#2d2d3a")
        self.mini_timer_frame.place(relx=1.0, rely=0, anchor="ne", x=-25, y=20)

        # Inner padding
        inner = tk.Frame(self.mini_timer_frame, bg="#2d2d3a")
        inner.pack(padx=10, pady=6)

        # Status indicator (small dot)
        self.mini_status_dot = tk.Label(inner, text="●",
                                        font=("SF Pro Display", 8),
                                        bg="#2d2d3a",
                                        fg="#6b7280")  # Gray when paused
        self.mini_status_dot.pack(side=tk.LEFT, padx=(0, 5))

        # Time display
        self.mini_timer_label = tk.Label(inner, text="25:00",
                                         font=("Menlo", 13),
                                         bg="#2d2d3a",
                                         fg="#9ca3af")  # Subtle gray text
        self.mini_timer_label.pack(side=tk.LEFT)

        # Initially semi-transparent/hidden when not running
        self.mini_timer_frame.configure(bg="#2d2d3a")

    def update_mini_timer(self):
        """Update the floating mini-timer display."""
        if not hasattr(self, 'mini_timer_label'):
            return

        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        self.mini_timer_label.config(text=f"{minutes:02d}:{seconds:02d}")

        # Update status dot color based on state
        if self.timer_running:
            if self.is_break_time:
                # Green for break
                self.mini_status_dot.config(fg="#10b981")
                self.mini_timer_label.config(fg="#6ee7b7")
            else:
                # Blue/purple for work - pulsing effect
                self.mini_status_dot.config(fg="#8b5cf6")
                self.mini_timer_label.config(fg="#c4b5fd")
        else:
            # Gray when paused/stopped
            self.mini_status_dot.config(fg="#6b7280")
            self.mini_timer_label.config(fg="#9ca3af")

    def toggle_timer(self):
        """Start or pause the timer."""
        if not self.timer_running:
            self.timer_running = True
            self.timer_paused = False
            self.timer_btn.config(text="⏸ Pause", bg=self.colors["warning"], fg="#000000")
            self.tick_timer()
        else:
            self.timer_running = False
            self.timer_paused = True
            self.timer_btn.config(text="▶ Resume", bg=self.colors["success"], fg="#000000")
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
        self.update_mini_timer()

    def tick_timer(self):
        """Update timer every second."""
        if not self.timer_running:
            return

        if self.time_remaining > 0:
            self.time_remaining -= 1

            if not self.is_break_time:
                self.current_session_time += 1
                self.total_study_time += 1
                self.update_total_time_display()

            self.update_timer_display()
            self.timer_id = self.root.after(1000, self.tick_timer)
        else:
            self.on_timer_complete()

    def update_timer_display(self):
        """Update the timer display."""
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        self.timer_display.config(text=f"{minutes:02d}:{seconds:02d}")

        if self.time_remaining <= 60 and not self.is_break_time:
            self.timer_display.config(fg="#ef4444")
        elif self.is_break_time:
            self.timer_display.config(fg=self.colors["success"])
        else:
            self.timer_display.config(fg=self.colors["text"])

        # Update the floating mini-timer too
        self.update_mini_timer()

    def format_total_time(self, seconds: int) -> str:
        """Format total study time for display."""
        total_minutes = seconds // 60
        if total_minutes < 60:
            return f"Total: {total_minutes}m"
        else:
            hours = total_minutes // 60
            mins = total_minutes % 60
            return f"Total: {hours}h {mins}m"

    def update_total_time_display(self):
        """Update total study time display."""
        self.total_time_label.config(text=self.format_total_time(self.total_study_time))

    def on_timer_complete(self):
        """Handle timer completion."""
        self.timer_running = False

        if not self.is_break_time:
            # Save the completed work session to persistent storage
            if self.current_session_time > 0:
                save_pomodoro_session(
                    duration_seconds=self.current_session_time,
                    session_type="work"
                )
            self.current_session_time = 0

            self.pomodoros_completed += 1
            self.pomodoro_count_label.config(
                text=f"🍅 {self.pomodoros_completed}/{self.pomodoros_until_long_break}"
            )
            self.root.bell()

            self.is_break_time = True
            if self.pomodoros_completed % self.pomodoros_until_long_break == 0:
                self.time_remaining = self.pomodoro_long_break_minutes * 60
                self.timer_status.config(text="LONG BREAK", bg="#06b6d4")
            else:
                self.time_remaining = self.pomodoro_break_minutes * 60
                self.timer_status.config(text="BREAK", bg=self.colors["success"])
        else:
            self.is_break_time = False
            self.time_remaining = self.pomodoro_work_minutes * 60
            self.timer_status.config(text="WORK", bg=self.colors["primary"])
            self.root.bell()

        self.update_timer_display()
        self.timer_btn.config(text="▶ Start", bg=self.colors["success"], fg="#000000")

    def reset_timer(self):
        """Reset current timer to full duration."""
        self.timer_running = False
        if self.timer_id:
            self.root.after_cancel(self.timer_id)

        # Save partial work session if any time was spent
        if not self.is_break_time and self.current_session_time > 0:
            save_pomodoro_session(
                duration_seconds=self.current_session_time,
                session_type="work"
            )
            self.current_session_time = 0

        if self.is_break_time:
            if self.pomodoros_completed % self.pomodoros_until_long_break == 0:
                self.time_remaining = self.pomodoro_long_break_minutes * 60
            else:
                self.time_remaining = self.pomodoro_break_minutes * 60
        else:
            self.time_remaining = self.pomodoro_work_minutes * 60

        self.update_timer_display()
        self.timer_btn.config(text="▶ Start", bg=self.colors["success"], fg="#000000")
        self.timer_display.config(fg=self.colors["text"])

    def skip_timer(self):
        """Skip to next phase (work/break)."""
        self.timer_running = False
        if self.timer_id:
            self.root.after_cancel(self.timer_id)

        # Save partial work session if skipping from work to break
        if not self.is_break_time and self.current_session_time > 0:
            save_pomodoro_session(
                duration_seconds=self.current_session_time,
                session_type="work"
            )
            self.current_session_time = 0

        if self.is_break_time:
            self.is_break_time = False
            self.time_remaining = self.pomodoro_work_minutes * 60
            self.timer_status.config(text="WORK", bg=self.colors["primary"])
        else:
            self.is_break_time = True
            self.time_remaining = self.pomodoro_break_minutes * 60
            self.timer_status.config(text="BREAK", bg=self.colors["success"])

        self.update_timer_display()
        self.timer_btn.config(text="▶ Start", bg=self.colors["success"], fg="#000000")
        self.timer_display.config(fg=self.colors["text"])

    def create_study_guide_tab(self):
        """Create the Study Guide overview tab with beautiful design."""
        tab = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.notebook.add(tab, text="  📖 Study Guide  ")

        # ═══════════════════════════════════════════════════════════
        # HEADER - Clean, minimal with progress ring
        # ═══════════════════════════════════════════════════════════
        header = tk.Frame(tab, bg=self.colors["surface"])
        header.pack(fill=tk.X)

        header_inner = tk.Frame(header, bg=self.colors["surface"])
        header_inner.pack(fill=tk.X, padx=35, pady=28)

        # Left side: Title and stats
        left_section = tk.Frame(header_inner, bg=self.colors["surface"])
        left_section.pack(side=tk.LEFT, fill=tk.Y)

        # Small category label
        tk.Label(left_section, text="EXAM PREPARATION",
                font=("SF Pro Display", 10, "bold"),
                bg=self.colors["surface"],
                fg=self.colors["text_muted"]).pack(anchor="w")

        # Main title
        tk.Label(left_section, text="Statistics II Study Guide",
                font=("SF Pro Display", 26, "bold"),
                bg=self.colors["surface"],
                fg=self.colors["text"]).pack(anchor="w", pady=(6, 0))

        # Subtitle
        tk.Label(left_section, text="Master all 12 lectures with interactive study sessions",
                font=("SF Pro Display", 13),
                bg=self.colors["surface"],
                fg=self.colors["text_secondary"]).pack(anchor="w", pady=(4, 0))

        # Right side: Progress visualization
        right_section = tk.Frame(header_inner, bg=self.colors["surface"])
        right_section.pack(side=tk.RIGHT, fill=tk.Y)

        # Progress percentage (large)
        self.progress_percent_label = tk.Label(right_section, text="0%",
                                               font=("SF Pro Display", 36, "bold"),
                                               bg=self.colors["surface"],
                                               fg=self.colors["primary"])
        self.progress_percent_label.pack(anchor="e")

        self.progress_label = tk.Label(right_section, text="0 of 50 topics",
                                       font=("SF Pro Display", 12),
                                       bg=self.colors["surface"],
                                       fg=self.colors["text_secondary"])
        self.progress_label.pack(anchor="e")

        # ═══════════════════════════════════════════════════════════
        # STATS BAR - Quick overview cards
        # ═══════════════════════════════════════════════════════════
        stats_bar = tk.Frame(tab, bg=self.colors["bg"])
        stats_bar.pack(fill=tk.X, padx=20, pady=(20, 0))

        # Progress bar (full width, thin)
        progress_container = tk.Frame(stats_bar, bg=self.colors["input_bg"], height=8)
        progress_container.pack(fill=tk.X, pady=(0, 15))
        progress_container.pack_propagate(False)

        self.main_progress_fill = tk.Frame(progress_container, bg=self.colors["primary"], height=8)
        self.main_progress_fill.place(x=0, y=0, width=0, height=8)

        # Stat cards row
        cards_row = tk.Frame(stats_bar, bg=self.colors["bg"])
        cards_row.pack(fill=tk.X)

        # Card 1: Topics completed
        self.topics_count_label = self.create_stat_mini_card(
            cards_row, "📚", "Topics", "0/50", self.colors["primary"])

        # Card 2: Study sessions
        self.study_count_label = self.create_stat_mini_card(
            cards_row, "📖", "Studied", "0", self.colors["secondary"])

        # Card 3: Quizzes passed
        self.quiz_count_label = self.create_stat_mini_card(
            cards_row, "✅", "Quizzes", "0", self.colors["success"])

        # Card 4: Mastery level
        self.mastery_label = self.create_stat_mini_card(
            cards_row, "🎯", "Mastery", "Beginner", self.colors["warning"])

        # ═══════════════════════════════════════════════════════════
        # SCROLLABLE CONTENT - Lecture cards
        # ═══════════════════════════════════════════════════════════
        canvas_container = tk.Frame(tab, bg=self.colors["bg"])
        canvas_container.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

        # Create canvas with smooth scrolling
        self.study_canvas = tk.Canvas(canvas_container, bg=self.colors["bg"],
                                      highlightthickness=0, borderwidth=0)

        # Subtle scrollbar
        scrollbar = tk.Scrollbar(canvas_container, orient="vertical",
                                 command=self.study_canvas.yview,
                                 bg=self.colors["bg"],
                                 troughcolor=self.colors["bg"],
                                 activebackground=self.colors["text_muted"],
                                 width=10)

        self.scrollable_frame = tk.Frame(self.study_canvas, bg=self.colors["bg"])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.study_canvas.configure(scrollregion=self.study_canvas.bbox("all"))
        )

        self.canvas_window = self.study_canvas.create_window((0, 0), window=self.scrollable_frame,
                                                              anchor="nw")
        self.study_canvas.configure(yscrollcommand=scrollbar.set)

        # Resize scrollable frame width with canvas
        def on_canvas_resize(event):
            self.study_canvas.itemconfig(self.canvas_window, width=event.width)
        self.study_canvas.bind("<Configure>", on_canvas_resize)

        # ═══ SMOOTH SCROLLING FOR MACOS TOUCHPAD ═══
        def on_mousewheel(event):
            # macOS uses different delta values
            if event.delta:
                # macOS touchpad - smooth scrolling
                self.study_canvas.yview_scroll(int(-1 * event.delta), "units")
            else:
                # Linux/Windows
                if event.num == 4:
                    self.study_canvas.yview_scroll(-3, "units")
                elif event.num == 5:
                    self.study_canvas.yview_scroll(3, "units")

        # Bind to canvas and all children
        self.study_canvas.bind("<MouseWheel>", on_mousewheel)
        self.study_canvas.bind("<Button-4>", on_mousewheel)
        self.study_canvas.bind("<Button-5>", on_mousewheel)

        # Recursive function to bind scrolling to widget and ALL children
        def bind_mousewheel_recursive(widget):
            widget.bind("<MouseWheel>", on_mousewheel)
            widget.bind("<Button-4>", on_mousewheel)
            widget.bind("<Button-5>", on_mousewheel)
            for child in widget.winfo_children():
                bind_mousewheel_recursive(child)

        self.scrollable_frame.bind("<MouseWheel>", on_mousewheel)

        # Store bind function for child widgets
        self.bind_scroll = bind_mousewheel_recursive

        self.study_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Store variables
        self.topic_vars = {}
        self.lecture_progress_labels = {}
        self.lecture_vars = {}

        # Create beautiful lecture cards
        for lecture_name, lecture_data in STUDY_GUIDE.items():
            self.create_lecture_card(lecture_name, lecture_data)

        # Update progress display
        self.update_progress_display()

    def create_stat_mini_card(self, parent, icon, label, value, color):
        """Create a minimal stat card."""
        card = tk.Frame(parent, bg=self.colors["surface"])
        card.pack(side=tk.LEFT, padx=(0, 12), ipadx=20, ipady=12)

        inner = tk.Frame(card, bg=self.colors["surface"])
        inner.pack(padx=15, pady=8)

        # Icon and value row
        top_row = tk.Frame(inner, bg=self.colors["surface"])
        top_row.pack(anchor="w")

        tk.Label(top_row, text=icon,
                font=("SF Pro Display", 16),
                bg=self.colors["surface"]).pack(side=tk.LEFT)

        value_label = tk.Label(top_row, text=value,
                              font=("SF Pro Display", 18, "bold"),
                              bg=self.colors["surface"],
                              fg=color)
        value_label.pack(side=tk.LEFT, padx=(8, 0))

        # Label
        tk.Label(inner, text=label,
                font=("SF Pro Display", 10),
                bg=self.colors["surface"],
                fg=self.colors["text_muted"]).pack(anchor="w")

        return value_label

    def create_lecture_card(self, lecture_name, lecture_data):
        """Create a beautiful lecture card with topics."""
        # Outer card with subtle rounded appearance
        card = tk.Frame(self.scrollable_frame, bg=self.colors["surface"],
                       highlightbackground=self.colors["border"],
                       highlightthickness=1)
        card.pack(fill=tk.X, padx=15, pady=8)

        # Inner padding
        inner = tk.Frame(card, bg=self.colors["surface"])
        inner.pack(fill=tk.X, padx=28, pady=22)

        # ═══ HEADER ROW ═══
        header_row = tk.Frame(inner, bg=self.colors["surface"])
        header_row.pack(fill=tk.X)

        # Left: Icon with colored background circle effect
        icon_container = tk.Frame(header_row, bg=lecture_data["color"])
        icon_container.pack(side=tk.LEFT)

        icon_inner = tk.Frame(icon_container, bg=lecture_data["color"])
        icon_inner.pack(padx=12, pady=8)

        icon_label = tk.Label(icon_inner, text=lecture_data["icon"],
                             font=("SF Pro Display", 22),
                             bg=lecture_data["color"], fg="white")
        icon_label.pack()

        # Title section - CLICKABLE to open lecture study mode
        title_frame = tk.Frame(header_row, bg=self.colors["surface"], cursor="hand2")
        title_frame.pack(side=tk.LEFT, padx=(18, 0), fill=tk.Y)

        # Extract lecture number and name
        title_label = tk.Label(title_frame, text=lecture_name,
                              font=("SF Pro Display", 15, "bold"),
                              bg=self.colors["surface"], fg=self.colors["text"],
                              cursor="hand2")
        title_label.pack(anchor="w")

        # Topic count subtitle with hint
        topic_count = len(lecture_data['topics'])
        subtitle_label = tk.Label(title_frame, text=f"{topic_count} topics  |  Click to study lecture",
                font=("SF Pro Display", 11),
                bg=self.colors["surface"],
                fg=self.colors["text_muted"],
                cursor="hand2")
        subtitle_label.pack(anchor="w")

        # Bind click events to open lecture study mode
        def open_lecture(event=None, ln=lecture_name, ld=lecture_data):
            self.open_lecture_study_mode(ln, ld)

        title_frame.bind("<Button-1>", open_lecture)
        title_label.bind("<Button-1>", open_lecture)
        subtitle_label.bind("<Button-1>", open_lecture)
        icon_container.bind("<Button-1>", open_lecture)
        icon_inner.bind("<Button-1>", open_lecture)
        icon_label.bind("<Button-1>", open_lecture)

        # Hover effects for visual feedback
        def on_enter(event):
            title_label.config(fg=lecture_data["color"])

        def on_leave(event):
            title_label.config(fg=self.colors["text"])

        for widget in [title_frame, title_label, subtitle_label, icon_container, icon_inner, icon_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

        # Right: Progress indicator
        progress_frame = tk.Frame(header_row, bg=self.colors["surface"])
        progress_frame.pack(side=tk.RIGHT)

        lecture_progress = tk.Label(progress_frame, text="0%",
                                   font=("SF Pro Display", 20, "bold"),
                                   bg=self.colors["surface"],
                                   fg=self.colors["text_muted"])
        lecture_progress.pack(anchor="e")

        progress_detail = tk.Label(progress_frame,
                                  text=f"0/{topic_count}",
                                  font=("SF Pro Display", 10),
                                  bg=self.colors["surface"],
                                  fg=self.colors["text_muted"])
        progress_detail.pack(anchor="e")

        # Store references
        self.lecture_progress_labels[lecture_name] = (lecture_progress, progress_detail)

        # ═══ PROGRESS BAR ═══
        progress_bar_container = tk.Frame(inner, bg=self.colors["input_bg"], height=4)
        progress_bar_container.pack(fill=tk.X, pady=(18, 0))
        progress_bar_container.pack_propagate(False)

        progress_bar_fill = tk.Frame(progress_bar_container, bg=lecture_data["color"], height=4)
        progress_bar_fill.place(x=0, y=0, width=0, height=4)

        # Store reference for updates
        lecture_data["progress_bar"] = progress_bar_fill
        lecture_data["progress_container"] = progress_bar_container

        # ═══ TOPICS LIST ═══
        topics_frame = tk.Frame(inner, bg=self.colors["surface"])
        topics_frame.pack(fill=tk.X, pady=(18, 0))

        lecture_vars = []

        for idx, topic in enumerate(lecture_data["topics"]):
            topic_key = f"{lecture_name}::{topic}"

            var = tk.BooleanVar(value=self.progress.get(topic_key, False))
            self.topic_vars[topic_key] = var
            lecture_vars.append(var)

            # Topic row - cleaner design
            topic_row = tk.Frame(topics_frame, bg=self.colors["surface"])
            topic_row.pack(fill=tk.X, pady=5)

            # Left side: checkbox + topic
            left_side = tk.Frame(topic_row, bg=self.colors["surface"])
            left_side.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Custom checkbox appearance
            cb = tk.Checkbutton(left_side, variable=var,
                               bg=self.colors["surface"],
                               activebackground=self.colors["surface"],
                               selectcolor=self.colors["primary"],
                               command=lambda k=topic_key, lv=lecture_vars, lp=lecture_progress,
                                              pd=progress_detail, pb=progress_bar_fill,
                                              pc=progress_bar_container, lt=lecture_data["topics"],
                                              c=lecture_data["color"]:
                                       self.on_topic_toggle(k, lv, lp, pd, pb, pc, lt, c))
            cb.pack(side=tk.LEFT)

            # Topic text
            topic_label = tk.Label(left_side, text=topic,
                                  font=("SF Pro Display", 13),
                                  bg=self.colors["surface"],
                                  fg=self.colors["success"] if var.get() else self.colors["text_secondary"])
            topic_label.pack(side=tk.LEFT, padx=(8, 0))

            var.label = topic_label
            var.checkbox = cb  # Store checkbox reference to invoke its command

            # Right side: Action buttons (minimal, icon-style)
            btn_frame = tk.Frame(topic_row, bg=self.colors["surface"])
            btn_frame.pack(side=tk.RIGHT)

            # Study button - outlined style
            study_btn = tk.Button(btn_frame, text="Study",
                                 command=lambda t=topic: self.study_topic(t),
                                 bg=self.colors["surface"],
                                 fg=self.colors["primary"],
                                 activebackground=self.colors["primary"],
                                 activeforeground="white",
                                 font=("SF Pro Display", 11),
                                 relief=tk.FLAT,
                                 padx=12, pady=4,
                                 cursor="hand2",
                                 highlightbackground=self.colors["primary"],
                                 highlightthickness=1)
            study_btn.pack(side=tk.LEFT, padx=(0, 6))

            # Quiz button - filled style
            quiz_btn = tk.Button(btn_frame, text="Quiz",
                                command=lambda t=topic: self.quiz_topic(t),
                                bg=self.colors["warning"],
                                fg="#000000",
                                activebackground=self.colors["warning"],
                                activeforeground="#000000",
                                font=("SF Pro Display", 11, "bold"),
                                relief=tk.FLAT,
                                padx=12, pady=4,
                                cursor="hand2")
            quiz_btn.pack(side=tk.LEFT)

        # Store lecture vars
        self.lecture_vars[lecture_name] = lecture_vars

        # Calculate initial progress
        completed = sum(1 for v in lecture_vars if v.get())
        total = len(lecture_data['topics'])
        percent = int((completed / total) * 100) if total > 0 else 0

        lecture_progress.config(text=f"{percent}%",
                               fg=self.colors["success"] if percent == 100 else self.colors["text_muted"])
        progress_detail.config(text=f"{completed}/{total}")

        # Update progress bar
        if total > 0:
            bar_width = int((completed / total) * progress_bar_container.winfo_reqwidth()) or 0
            progress_bar_fill.place(x=0, y=0, relwidth=completed/total, height=4)

        # Bind scroll to card and ALL its children (recursive)
        if hasattr(self, 'bind_scroll'):
            self.bind_scroll(card)

    def on_topic_toggle(self, topic_key, lecture_vars, lecture_progress, progress_detail,
                        progress_bar, progress_container, lecture_topics, color):
        """Handle topic checkbox toggle with visual updates."""
        var = self.topic_vars[topic_key]
        self.progress[topic_key] = var.get()
        self.save_progress()

        # Update label color
        if hasattr(var, 'label'):
            var.label.config(fg=self.colors["success"] if var.get() else self.colors["text_secondary"])

        # Update lecture progress
        completed = sum(1 for v in lecture_vars if v.get())
        total = len(lecture_topics)
        percent = int((completed / total) * 100) if total > 0 else 0

        lecture_progress.config(text=f"{percent}%",
                               fg=self.colors["success"] if percent == 100 else self.colors["text_muted"])
        progress_detail.config(text=f"{completed}/{total}")

        # Update progress bar
        if total > 0:
            progress_bar.place(x=0, y=0, relwidth=completed/total, height=4)

        # Update overall progress
        self.update_progress_display()

    def update_progress_display(self):
        """Update the overall progress bar and label."""
        total_topics = sum(len(data["topics"]) for data in STUDY_GUIDE.values())
        completed_topics = sum(1 for v in self.topic_vars.values() if v.get())

        percentage = (completed_topics / total_topics * 100) if total_topics > 0 else 0

        # Update header progress
        self.progress_percent_label.config(text=f"{int(percentage)}%")
        self.progress_label.config(text=f"{completed_topics} of {total_topics} topics")

        # Update main progress bar
        if hasattr(self, 'main_progress_fill'):
            self.main_progress_fill.place(x=0, y=0, relwidth=percentage/100, height=8)

        # Update Topics stat card
        if hasattr(self, 'topics_count_label'):
            self.topics_count_label.config(text=f"{completed_topics}/{total_topics}")

        # Count study sessions and quizzes
        study_count = sum(1 for k, v in self.progress.items()
                        if k.startswith("study_completed::") and isinstance(v, dict) and v.get("completed"))
        quiz_count = sum(1 for k, v in self.progress.items()
                        if k.startswith("quiz_completed::") and isinstance(v, dict) and v.get("percentage", 0) >= 70)

        self.study_count_label.config(text=f"{study_count}")
        self.quiz_count_label.config(text=f"{quiz_count}")

        # Update Mastery level based on percentage
        if hasattr(self, 'mastery_label'):
            if percentage >= 90:
                mastery = "Master"
            elif percentage >= 70:
                mastery = "Advanced"
            elif percentage >= 50:
                mastery = "Intermediate"
            elif percentage >= 25:
                mastery = "Learning"
            else:
                mastery = "Beginner"
            self.mastery_label.config(text=mastery)

    def study_topic(self, topic):
        """Open dedicated study session window for a topic."""
        # Find the full topic key for this topic
        topic_key = None
        for lecture_name, lecture_data in STUDY_GUIDE.items():
            for t in lecture_data["topics"]:
                if t == topic:
                    topic_key = f"{lecture_name}::{t}"
                    break
            if topic_key:
                break

        # Open study session window with completion callback and timer reference
        open_study_session(
            self.root,
            topic,
            on_complete_callback=lambda t, sections, total: self.on_study_complete(topic_key, t, sections, total),
            timer_ref=self,  # Pass reference to main app for timer access
            colors=self.colors
        )

    def on_study_complete(self, topic_key, topic, sections_read, total_sections):
        """Handle study session completion - update progress."""
        # Save study session to progress
        study_key = f"study_completed::{topic}"
        self.progress[study_key] = {
            "completed": True,
            "sections_read": sections_read,
            "total_sections": total_sections,
            "percentage": round(sections_read / total_sections * 100, 1) if total_sections > 0 else 0
        }
        self.save_progress()

        # If read at least 2/3 of sections, mark topic as completed
        if total_sections > 0 and (sections_read / total_sections) >= 0.67:
            if topic_key and topic_key in self.topic_vars:
                self.topic_vars[topic_key].set(True)
                self.progress[topic_key] = True

                # Update label color to green
                var = self.topic_vars[topic_key]
                if hasattr(var, 'label'):
                    var.label.config(fg=self.colors["success"])

                self.save_progress()

        # Refresh the progress display
        self.update_progress_display()

        # Refresh lecture progress counters
        self.refresh_lecture_progress()

    def refresh_lecture_progress(self):
        """Refresh all lecture progress counters."""
        for lecture_name, lecture_data in STUDY_GUIDE.items():
            if lecture_name in self.lecture_vars and lecture_name in self.lecture_progress_labels:
                lecture_vars = self.lecture_vars[lecture_name]
                completed = sum(1 for v in lecture_vars if v.get())
                total = len(lecture_data["topics"])
                self.lecture_progress_labels[lecture_name].config(
                    text=f"{completed}/{total} completed"
                )

    def open_lecture_study_mode(self, lecture_name, lecture_data):
        """Open the lecture study window for an entire lecture."""
        open_lecture_study(self.root, lecture_name, lecture_data, self.colors)

    def quiz_topic(self, topic):
        """Generate a quiz for a topic."""
        # Switch to Quiz tab
        self.notebook.select(3)  # Quiz tab index
        # Set the full topic name in combobox (add it temporarily if not present)
        self.quiz_topic_combo.set(topic)
        # Generate quiz with full topic for better RAG results
        self.generate_quiz()

    def create_overview_tab(self):
        """Create the materials overview tab."""
        tab = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.notebook.add(tab, text="  📊 Materials  ")

        # Main content area - use PanedWindow for 70/30 split
        content_frame = tk.Frame(tab, bg=self.colors["bg"])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # ═══════════════════════════════════════════════════════════
        # TOP SECTION (70%) - Indexed Files Table
        # ═══════════════════════════════════════════════════════════
        list_frame = tk.Frame(content_frame, bg=self.colors["surface"])
        list_frame.place(relx=0, rely=0, relwidth=1, relheight=0.70)

        list_header = tk.Frame(list_frame, bg=self.colors["surface"])
        list_header.pack(fill=tk.X, padx=30, pady=(20, 12))

        tk.Label(list_header, text="📁 Indexed Files",
                font=("Helvetica Neue", 18, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(side=tk.LEFT)

        # File count badge
        self.file_count_label = tk.Label(list_header, text="",
                font=("Helvetica Neue", 12),
                bg=self.colors["primary"], fg="white",
                padx=12, pady=4)
        self.file_count_label.pack(side=tk.LEFT, padx=(15, 0))

        # Treeview for materials
        tree_frame = tk.Frame(list_frame, bg="#1a1a24", highlightbackground="#3f3f5a",
                             highlightthickness=1)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))

        # Style the treeview
        style = ttk.Style()
        style.configure("Materials.Treeview",
                       background="#1a1a24",
                       foreground="#e4e4e7",
                       fieldbackground="#1a1a24",
                       rowheight=32,
                       font=("SF Pro Display", 13))
        style.configure("Materials.Treeview.Heading",
                       background="#2a2a3a",
                       foreground="#a1a1aa",
                       font=("SF Pro Display", 12, "bold"))
        style.map("Materials.Treeview",
                 background=[("selected", "#8b5cf6")],
                 foreground=[("selected", "white")])

        columns = ("name", "type", "chunks")
        self.materials_tree = ttk.Treeview(tree_frame, columns=columns,
                                           show="headings",
                                           style="Materials.Treeview")

        self.materials_tree.heading("name", text="File Name")
        self.materials_tree.heading("type", text="Type")
        self.materials_tree.heading("chunks", text="Chunks")

        self.materials_tree.column("name", width=550, minwidth=300)
        self.materials_tree.column("type", width=150, minwidth=80)
        self.materials_tree.column("chunks", width=120, minwidth=60)

        # Scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.materials_tree.yview)
        self.materials_tree.configure(yscrollcommand=tree_scroll.set)

        self.materials_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=2)

        # ═══════════════════════════════════════════════════════════
        # BOTTOM SECTION (30%) - Stats Cards
        # ═══════════════════════════════════════════════════════════
        bottom_frame = tk.Frame(content_frame, bg=self.colors["bg"])
        bottom_frame.place(relx=0, rely=0.70, relwidth=1, relheight=0.30)

        # Header for stats section
        stats_header = tk.Frame(bottom_frame, bg=self.colors["surface"])
        stats_header.pack(fill=tk.X)

        stats_header_inner = tk.Frame(stats_header, bg=self.colors["surface"])
        stats_header_inner.pack(fill=tk.X, padx=30, pady=15)

        tk.Label(stats_header_inner, text="📚 Indexed Study Materials",
                font=("Helvetica Neue", 18, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(side=tk.LEFT)

        tk.Label(stats_header_inner, text="Your lecture PDFs and transcripts ready for search",
                font=("Helvetica Neue", 12),
                bg=self.colors["surface"], fg=self.colors["text_secondary"]).pack(side=tk.LEFT, padx=(20, 0))

        # Stats cards in a row
        stats_frame = tk.Frame(bottom_frame, bg=self.colors["bg"])
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Configure grid for equal columns
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)
        stats_frame.rowconfigure(0, weight=1)

        # Stat cards
        self.chunks_card = self.create_stat_card(stats_frame, "Total Chunks", "---", "📦", 0)
        self.sources_card = self.create_stat_card(stats_frame, "Source Files", "---", "📄", 1)
        self.topics_card = self.create_stat_card(stats_frame, "Lectures", "12", "🎓", 2)

        # Buttons in the stats header (right side)
        btn_container = tk.Frame(stats_header_inner, bg=self.colors["surface"])
        btn_container.pack(side=tk.RIGHT)

        reindex_btn = tk.Button(btn_container, text="🔄 Reindex",
                               command=self.reindex_materials,
                               bg=self.colors["primary"],
                               fg="#000000",
                               font=("Helvetica Neue", 11, "bold"),
                               padx=14, pady=6,
                               relief=tk.FLAT,
                               cursor="hand2",
                               activebackground="#7c3aed",
                               activeforeground="#000000")
        reindex_btn.pack(side=tk.RIGHT)

        refresh_btn = tk.Button(btn_container, text="↻ Refresh",
                               command=self.load_stats,
                               bg=self.colors["input_bg"],
                               fg="#000000",
                               font=("Helvetica Neue", 11, "bold"),
                               padx=14, pady=6,
                               relief=tk.FLAT,
                               cursor="hand2",
                               activebackground=self.colors["surface_hover"],
                               activeforeground="#000000")
        refresh_btn.pack(side=tk.RIGHT, padx=(0, 10))

    def create_stat_card(self, parent, title, value, icon, column):
        """Create a statistics card widget."""
        card = tk.Frame(parent, bg=self.colors["surface"])
        card.grid(row=0, column=column, sticky="nsew", padx=8)

        inner = tk.Frame(card, bg=self.colors["surface"])
        inner.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)

        tk.Label(inner, text=icon, font=("Helvetica Neue", 32),
                bg=self.colors["surface"], fg=self.colors["primary"]).pack(anchor="w")

        value_label = tk.Label(inner, text=value, font=("Helvetica Neue", 36, "bold"),
                              bg=self.colors["surface"], fg=self.colors["text"])
        value_label.pack(anchor="w", pady=(10, 5))
        card.value_label = value_label

        tk.Label(inner, text=title, font=("Helvetica Neue", 13),
                bg=self.colors["surface"], fg=self.colors["text_muted"]).pack(anchor="w")

        return card

    def create_qa_tab(self):
        """Create the Q&A tab with beautiful modern design."""
        tab = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.notebook.add(tab, text="  💬 Q&A  ")

        # ═══════════════════════════════════════════════════════════
        # HEADER - Clean, modern with gradient accent
        # ═══════════════════════════════════════════════════════════
        header = tk.Frame(tab, bg=self.colors["surface"])
        header.pack(fill=tk.X)

        header_inner = tk.Frame(header, bg=self.colors["surface"])
        header_inner.pack(fill=tk.X, padx=40, pady=30)

        # Title row with icon
        title_row = tk.Frame(header_inner, bg=self.colors["surface"])
        title_row.pack(fill=tk.X)

        # Decorative accent bar
        accent_bar = tk.Frame(title_row, bg="#8b5cf6", width=4)
        accent_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))

        title_content = tk.Frame(title_row, bg=self.colors["surface"])
        title_content.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(title_content, text="Ask About Your Materials",
                font=("SF Pro Display", 24, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(anchor="w")

        tk.Label(title_content, text="Search your study materials or get AI-powered explanations",
                font=("SF Pro Display", 13),
                bg=self.colors["surface"], fg=self.colors["text_muted"]).pack(anchor="w", pady=(6, 0))

        # ═══════════════════════════════════════════════════════════
        # SEARCH INPUT - Modern floating card style
        # ═══════════════════════════════════════════════════════════
        input_container = tk.Frame(tab, bg=self.colors["bg"])
        input_container.pack(fill=tk.X, padx=40, pady=20)

        # Input card with subtle shadow effect (darker border on bottom/right)
        input_card = tk.Frame(input_container, bg=self.colors["surface"],
                             highlightbackground=self.colors["border"],
                             highlightthickness=1)
        input_card.pack(fill=tk.X)

        input_inner = tk.Frame(input_card, bg=self.colors["surface"])
        input_inner.pack(fill=tk.X, padx=25, pady=25)

        # Search icon + label row
        label_row = tk.Frame(input_inner, bg=self.colors["surface"])
        label_row.pack(fill=tk.X, pady=(0, 12))

        tk.Label(label_row, text="💭",
                font=("SF Pro Display", 16),
                bg=self.colors["surface"]).pack(side=tk.LEFT)

        tk.Label(label_row, text="What would you like to know?",
                font=("SF Pro Display", 14, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(side=tk.LEFT, padx=(8, 0))

        # Modern search box with icon inside
        search_box = tk.Frame(input_inner, bg=self.colors["input_bg"],
                             highlightbackground=self.colors["border"],
                             highlightthickness=1)
        search_box.pack(fill=tk.X, pady=(0, 18))

        search_icon = tk.Label(search_box, text="🔍",
                              font=("SF Pro Display", 14),
                              bg=self.colors["input_bg"],
                              fg=self.colors["text_muted"])
        search_icon.pack(side=tk.LEFT, padx=(15, 0))

        self.question_entry = tk.Entry(search_box,
                                       font=("SF Pro Display", 15),
                                       bg=self.colors["input_bg"],
                                       fg=self.colors["text"],
                                       insertbackground=self.colors["text"],
                                       relief=tk.FLAT,
                                       highlightthickness=0)
        self.question_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=12, pady=14)
        self.question_entry.bind("<Return>", lambda e: self.search_question())

        # Buttons row - pill-shaped modern buttons
        btn_row = tk.Frame(input_inner, bg=self.colors["surface"])
        btn_row.pack(fill=tk.X)

        # Search button
        search_btn = tk.Button(btn_row, text="📚  Search Materials",
                              command=self.search_question,
                              bg=self.colors["input_bg"],
                              fg="#000000",
                              font=("SF Pro Display", 12, "bold"),
                              padx=20, pady=10,
                              relief=tk.FLAT,
                              cursor="hand2",
                              activebackground=self.colors["surface_hover"],
                              activeforeground="#000000")
        search_btn.pack(side=tk.LEFT)

        # AI button with gradient-like accent
        ask_claude_btn = tk.Button(btn_row, text="✨  Ask AI",
                                   command=self.ask_claude,
                                   bg="#8b5cf6",
                                   fg="#000000",
                                   font=("SF Pro Display", 12, "bold"),
                                   padx=24, pady=10,
                                   relief=tk.FLAT,
                                   cursor="hand2",
                                   activebackground="#7c3aed",
                                   activeforeground="#000000")
        ask_claude_btn.pack(side=tk.LEFT, padx=(12, 0))

        # Keyboard hint
        hint = tk.Label(btn_row, text="Press Enter to search",
                       font=("SF Pro Display", 10),
                       bg=self.colors["surface"],
                       fg=self.colors["text_muted"])
        hint.pack(side=tk.RIGHT)

        # ═══════════════════════════════════════════════════════════
        # AI SETTINGS ROW - Model selection and output length
        # ═══════════════════════════════════════════════════════════
        settings_divider = tk.Frame(input_inner, bg=self.colors["border"], height=1)
        settings_divider.pack(fill=tk.X, pady=(18, 15))

        settings_row = tk.Frame(input_inner, bg=self.colors["surface"])
        settings_row.pack(fill=tk.X)

        # --- Column 1: Model Selection ---
        model_col = tk.Frame(settings_row, bg=self.colors["surface"])
        model_col.pack(side=tk.LEFT)

        tk.Label(model_col, text="🤖  AI Model",
                font=("SF Pro Display", 11, "bold"),
                bg=self.colors["surface"], fg=self.colors["text_muted"]).pack(anchor="w")

        # Model dropdown
        model_frame = tk.Frame(model_col, bg=self.colors["surface"])
        model_frame.pack(anchor="w", pady=(6, 0))

        model_values = [CLAUDE_MODELS[m]["display_name"] for m in ["haiku", "sonnet", "opus"]]
        self.model_combo = ttk.Combobox(model_frame, values=model_values,
                                         state="readonly",
                                         font=("SF Pro Display", 11),
                                         width=18)
        self.model_combo.set(CLAUDE_MODELS[DEFAULT_MODEL]["display_name"])
        self.model_combo.pack(side=tk.LEFT)
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_change)

        # Model description label
        self.model_desc_label = tk.Label(model_col,
                                          text=CLAUDE_MODELS[DEFAULT_MODEL]["description"],
                                          font=("SF Pro Display", 10),
                                          bg=self.colors["surface"],
                                          fg=self.colors["text_muted"])
        self.model_desc_label.pack(anchor="w", pady=(4, 0))

        # --- Column 2: Output Length Slider ---
        length_col = tk.Frame(settings_row, bg=self.colors["surface"])
        length_col.pack(side=tk.LEFT, padx=(50, 0))

        tk.Label(length_col, text="📏  Response Length",
                font=("SF Pro Display", 11, "bold"),
                bg=self.colors["surface"], fg=self.colors["text_muted"]).pack(anchor="w")

        # Slider row with value display
        slider_row = tk.Frame(length_col, bg=self.colors["surface"])
        slider_row.pack(anchor="w", pady=(6, 0))

        self.word_slider = tk.Scale(slider_row,
                                    from_=MIN_OUTPUT_WORDS,
                                    to=MAX_OUTPUT_WORDS,
                                    orient=tk.HORIZONTAL,
                                    variable=self.qa_output_words,
                                    bg=self.colors["surface"],
                                    fg=self.colors["text"],
                                    troughcolor=self.colors["input_bg"],
                                    highlightthickness=0,
                                    sliderrelief=tk.FLAT,
                                    activebackground=self.colors["primary"],
                                    font=("SF Pro Display", 9),
                                    length=180,
                                    showvalue=False,
                                    command=self.on_word_count_change)
        self.word_slider.pack(side=tk.LEFT)

        self.word_count_label = tk.Label(slider_row,
                                          text=f"{DEFAULT_OUTPUT_WORDS} words",
                                          font=("SF Pro Display", 11, "bold"),
                                          bg=self.colors["surface"],
                                          fg=self.colors["text"])
        self.word_count_label.pack(side=tk.LEFT, padx=(12, 0))

        # Preset buttons for quick selection
        presets_row = tk.Frame(length_col, bg=self.colors["surface"])
        presets_row.pack(anchor="w", pady=(6, 0))

        for label, value in [("Brief", 100), ("Medium", 250), ("Detailed", 500), ("Long", 800)]:
            btn = tk.Button(presets_row, text=label,
                            command=lambda v=value: self.set_word_count(v),
                            bg=self.colors["input_bg"],
                            fg="#000000",
                            font=("SF Pro Display", 9),
                            padx=8, pady=2,
                            relief=tk.FLAT,
                            cursor="hand2",
                            activebackground=self.colors["surface_hover"],
                            activeforeground="#000000")
            btn.pack(side=tk.LEFT, padx=(0, 5))

        # ═══════════════════════════════════════════════════════════
        # RESULTS AREA - Beautiful card with proper typography
        # ═══════════════════════════════════════════════════════════
        results_container = tk.Frame(tab, bg=self.colors["bg"])
        results_container.pack(fill=tk.BOTH, expand=True, padx=40, pady=(0, 20))

        results_card = tk.Frame(results_container, bg=self.colors["surface"],
                               highlightbackground=self.colors["border"],
                               highlightthickness=1)
        results_card.pack(fill=tk.BOTH, expand=True)

        # Results header
        results_header = tk.Frame(results_card, bg=self.colors["surface"])
        results_header.pack(fill=tk.X, padx=25, pady=(20, 0))

        tk.Label(results_header, text="📋",
                font=("SF Pro Display", 14),
                bg=self.colors["surface"]).pack(side=tk.LEFT)

        tk.Label(results_header, text="Results",
                font=("SF Pro Display", 14, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(side=tk.LEFT, padx=(8, 0))

        # Divider line
        divider = tk.Frame(results_card, bg=self.colors["border"], height=1)
        divider.pack(fill=tk.X, padx=25, pady=(15, 0))

        # Results text area - high contrast for readability
        self.qa_results = scrolledtext.ScrolledText(
            results_card,
            font=("Georgia", 15),
            bg="#1a1a24",  # Slightly lighter than surface for contrast
            fg="#e4e4e7",  # Bright white text - high contrast
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=25,
            pady=20,
            spacing1=8,
            spacing2=4,
            spacing3=8,
            highlightthickness=0,
            borderwidth=0,
            insertbackground="#e4e4e7"
        )
        self.qa_results.pack(fill=tk.BOTH, expand=True, padx=0, pady=(10, 15))

        # Configure text tags for markdown rendering - all with good contrast
        self.qa_results.tag_configure("h1",
            font=("SF Pro Display", 22, "bold"),
            foreground="#c4b5fd",  # Brighter purple
            spacing1=25, spacing3=12)

        self.qa_results.tag_configure("h2",
            font=("SF Pro Display", 18, "bold"),
            foreground="#67e8f9",  # Brighter cyan
            spacing1=20, spacing3=10)

        self.qa_results.tag_configure("h3",
            font=("SF Pro Display", 16, "bold"),
            foreground="#6ee7b7",  # Brighter emerald
            spacing1=16, spacing3=8)

        self.qa_results.tag_configure("bold",
            font=("Georgia", 15, "bold"),
            foreground="#ffffff")

        self.qa_results.tag_configure("code",
            font=("JetBrains Mono", 13),
            background="#2d2d3a",
            foreground="#fcd34d",  # Brighter amber
            spacing1=4, spacing3=4)

        self.qa_results.tag_configure("bullet",
            font=("Georgia", 15),
            lmargin1=25, lmargin2=45,
            foreground="#d4d4d8")  # Light gray - readable

        self.qa_results.tag_configure("source",
            font=("SF Pro Display", 12),
            foreground="#a1a1aa",
            spacing1=20)

        self.qa_results.tag_configure("context",
            font=("Georgia", 14),
            foreground="#e2e8f0",  # Much brighter - almost white
            background="#252530",  # Subtle background
            lmargin1=20, lmargin2=20,
            rmargin=20,
            spacing1=10, spacing3=10)

        self.qa_results.tag_configure("divider",
            font=("SF Pro Display", 10),
            foreground="#4a5568")

        self.qa_results.tag_configure("source_header",
            font=("SF Pro Display", 14, "bold"),
            foreground="#a78bfa",  # Purple
            spacing1=15, spacing3=5)

        self.qa_results.tag_configure("relevance",
            font=("SF Pro Display", 11),
            foreground="#22c55e",  # Green
            spacing1=2, spacing3=8)

        self.qa_results.tag_configure("page_info",
            font=("SF Pro Display", 11),
            foreground="#fbbf24",  # Amber/yellow
            spacing1=2, spacing3=8)

    def create_quiz_tab(self):
        """Create the Quiz tab with beautiful modern design."""
        tab = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.notebook.add(tab, text="  📝 Quiz  ")

        # ═══════════════════════════════════════════════════════════
        # HEADER - Clean with accent
        # ═══════════════════════════════════════════════════════════
        header = tk.Frame(tab, bg=self.colors["surface"])
        header.pack(fill=tk.X)

        header_inner = tk.Frame(header, bg=self.colors["surface"])
        header_inner.pack(fill=tk.X, padx=40, pady=30)

        # Title row with icon
        title_row = tk.Frame(header_inner, bg=self.colors["surface"])
        title_row.pack(fill=tk.X)

        # Decorative accent bar
        accent_bar = tk.Frame(title_row, bg="#10b981", width=4)
        accent_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))

        title_content = tk.Frame(title_row, bg=self.colors["surface"])
        title_content.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(title_content, text="Practice Quiz Generator",
                font=("SF Pro Display", 24, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(anchor="w")

        tk.Label(title_content, text="Test your knowledge with AI-generated questions",
                font=("SF Pro Display", 13),
                bg=self.colors["surface"], fg=self.colors["text_muted"]).pack(anchor="w", pady=(6, 0))

        # ═══════════════════════════════════════════════════════════
        # OPTIONS PANEL - Modern card with grouped settings
        # ═══════════════════════════════════════════════════════════
        options_container = tk.Frame(tab, bg=self.colors["bg"])
        options_container.pack(fill=tk.X, padx=40, pady=20)

        options_card = tk.Frame(options_container, bg=self.colors["surface"],
                               highlightbackground=self.colors["border"],
                               highlightthickness=1)
        options_card.pack(fill=tk.X)

        options_inner = tk.Frame(options_card, bg=self.colors["surface"])
        options_inner.pack(fill=tk.X, padx=25, pady=25)

        # Settings row with 3 columns
        settings_row = tk.Frame(options_inner, bg=self.colors["surface"])
        settings_row.pack(fill=tk.X, pady=(0, 20))

        # Column 1: Quiz Type
        type_col = tk.Frame(settings_row, bg=self.colors["surface"])
        type_col.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(type_col, text="🎲  Quiz Type",
                font=("SF Pro Display", 12, "bold"),
                bg=self.colors["surface"], fg=self.colors["text_muted"]).pack(anchor="w")

        self.quiz_type = tk.StringVar(value="multiple_choice")

        type_btns = tk.Frame(type_col, bg=self.colors["surface"])
        type_btns.pack(anchor="w", pady=(8, 0))

        for text, value in [("Multiple Choice", "multiple_choice"), ("Open Ended", "open_ended")]:
            rb = tk.Radiobutton(type_btns, text=text, variable=self.quiz_type,
                               value=value, bg=self.colors["surface"],
                               fg=self.colors["text"],
                               selectcolor=self.colors["primary"],
                               activebackground=self.colors["surface"],
                               font=("SF Pro Display", 12))
            rb.pack(side=tk.LEFT, padx=(0, 20))

        # Column 2: Topic
        topic_col = tk.Frame(settings_row, bg=self.colors["surface"])
        topic_col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(30, 0))

        tk.Label(topic_col, text="📚  Topic",
                font=("SF Pro Display", 12, "bold"),
                bg=self.colors["surface"], fg=self.colors["text_muted"]).pack(anchor="w")

        self.quiz_topic_values = [
            "All Topics", "Exam Concepts", "Probability", "Sampling", "Hypothesis Testing",
            "Correlation", "Linear Regression", "Multiple Regression",
            "Assumptions", "Interactions", "Categorical", "Polynomials",
            "Mixed Models", "Growth Curves", "Outliers"
        ]
        self.quiz_topic_combo = ttk.Combobox(topic_col, values=self.quiz_topic_values,
                                             font=("SF Pro Display", 12), width=24)
        self.quiz_topic_combo.set("All Topics")
        self.quiz_topic_combo.pack(anchor="w", pady=(8, 0))

        # Allow custom topic entry - add to list when user types a new topic
        self.quiz_topic_combo.bind('<Return>', self._add_custom_quiz_topic)
        self.quiz_topic_combo.bind('<FocusOut>', self._add_custom_quiz_topic)

        # Column 3: Question Count
        count_col = tk.Frame(settings_row, bg=self.colors["surface"])
        count_col.pack(side=tk.LEFT, padx=(30, 0))

        tk.Label(count_col, text="🔢  Questions",
                font=("SF Pro Display", 12, "bold"),
                bg=self.colors["surface"], fg=self.colors["text_muted"]).pack(anchor="w")

        count_frame = tk.Frame(count_col, bg=self.colors["input_bg"],
                              highlightbackground=self.colors["border"],
                              highlightthickness=1)
        count_frame.pack(anchor="w", pady=(8, 0))

        self.quiz_count = tk.Spinbox(count_frame, from_=1, to=20, width=5,
                                     font=("SF Pro Display", 12),
                                     bg=self.colors["input_bg"],
                                     fg=self.colors["text"],
                                     buttonbackground=self.colors["input_bg"],
                                     relief=tk.FLAT,
                                     highlightthickness=0)
        self.quiz_count.delete(0, tk.END)
        self.quiz_count.insert(0, "5")
        self.quiz_count.pack(padx=10, pady=6)

        # Divider
        divider = tk.Frame(options_inner, bg=self.colors["border"], height=1)
        divider.pack(fill=tk.X, pady=(5, 20))

        # Action buttons row
        btn_row = tk.Frame(options_inner, bg=self.colors["surface"])
        btn_row.pack(fill=tk.X)

        # Primary action - Generate with Claude (purple)
        gen_frame = tk.Frame(btn_row, bg="#8b5cf6", padx=2, pady=2)
        gen_frame.pack(side=tk.LEFT)
        generate_claude_btn = tk.Button(gen_frame, text="✨  Generate Quiz",
                                        command=self.generate_quiz_with_claude,
                                        bg="#8b5cf6",
                                        fg="#000000",
                                        font=("SF Pro Display", 12, "bold"),
                                        padx=22, pady=8,
                                        relief=tk.FLAT,
                                        cursor="hand2",
                                        activebackground="#7c3aed",
                                        activeforeground="#000000",
                                        highlightthickness=0,
                                        bd=0)
        generate_claude_btn.pack()

        # Secondary action - Take Quiz (green)
        take_frame = tk.Frame(btn_row, bg="#10b981", padx=2, pady=2)
        take_frame.pack(side=tk.LEFT, padx=(12, 0))
        take_quiz_btn = tk.Button(take_frame, text="🎯  Take Quiz",
                                  command=self.start_interactive_quiz,
                                  bg="#10b981",
                                  fg="#000000",
                                  font=("SF Pro Display", 12, "bold"),
                                  padx=22, pady=8,
                                  relief=tk.FLAT,
                                  cursor="hand2",
                                  activebackground="#059669",
                                  activeforeground="#000000",
                                  highlightthickness=0,
                                  bd=0)
        take_quiz_btn.pack()

        # Tertiary actions (with visible borders)
        new_frame = tk.Frame(btn_row, bg=self.colors["border"], padx=2, pady=2)
        new_frame.pack(side=tk.LEFT, padx=(12, 0))
        regenerate_btn = tk.Button(new_frame, text="🔄  New",
                                   command=self.regenerate_quiz,
                                   bg=self.colors["input_bg"],
                                   fg="#000000",
                                   font=("SF Pro Display", 11),
                                   padx=14, pady=8,
                                   relief=tk.FLAT,
                                   cursor="hand2",
                                   activebackground=self.colors["surface_hover"],
                                   activeforeground="#000000",
                                   highlightthickness=0,
                                   bd=0)
        regenerate_btn.pack()

        prompt_frame = tk.Frame(btn_row, bg=self.colors["border"], padx=2, pady=2)
        prompt_frame.pack(side=tk.LEFT, padx=(8, 0))
        generate_btn = tk.Button(prompt_frame, text="📋  Show Prompt",
                                command=self.generate_quiz,
                                bg=self.colors["input_bg"],
                                fg="#000000",
                                font=("SF Pro Display", 11),
                                padx=14, pady=8,
                                relief=tk.FLAT,
                                cursor="hand2",
                                activebackground=self.colors["surface_hover"],
                                activeforeground="#000000",
                                highlightthickness=0,
                                bd=0)
        generate_btn.pack()

        # Comprehensive Test button (indigo)
        comp_frame = tk.Frame(btn_row, bg="#6366f1", padx=2, pady=2)
        comp_frame.pack(side=tk.LEFT, padx=(12, 0))
        comp_test_btn = tk.Button(comp_frame, text="📋  Comprehensive Test (30Q)",
                                  command=self.open_comprehensive_test,
                                  bg="#6366f1",
                                  fg="white",
                                  font=("SF Pro Display", 11, "bold"),
                                  padx=14, pady=8,
                                  relief=tk.FLAT,
                                  cursor="hand2",
                                  activebackground="#4f46e5",
                                  activeforeground="white",
                                  highlightthickness=0,
                                  bd=0)
        comp_test_btn.pack()

        # Concept Explanation Quiz button (teal)
        concept_frame = tk.Frame(btn_row, bg="#14b8a6", padx=2, pady=2)
        concept_frame.pack(side=tk.LEFT, padx=(12, 0))
        concept_quiz_btn = tk.Button(concept_frame, text="💡  Concept Quiz",
                                     command=lambda: open_concept_quiz(self.root),
                                     bg="#14b8a6",
                                     fg="white",
                                     font=("SF Pro Display", 11, "bold"),
                                     padx=14, pady=8,
                                     relief=tk.FLAT,
                                     cursor="hand2",
                                     activebackground="#0d9488",
                                     activeforeground="white",
                                     highlightthickness=0,
                                     bd=0)
        concept_quiz_btn.pack()

        # ═══════════════════════════════════════════════════════════
        # OUTPUT AREA - Generated quiz preview
        # ═══════════════════════════════════════════════════════════
        output_container = tk.Frame(tab, bg=self.colors["bg"])
        output_container.pack(fill=tk.BOTH, expand=True, padx=40, pady=(0, 20))

        output_card = tk.Frame(output_container, bg=self.colors["surface"],
                              highlightbackground=self.colors["border"],
                              highlightthickness=1)
        output_card.pack(fill=tk.BOTH, expand=True)

        # Output header
        output_header = tk.Frame(output_card, bg=self.colors["surface"])
        output_header.pack(fill=tk.X, padx=25, pady=(20, 0))

        tk.Label(output_header, text="📝",
                font=("SF Pro Display", 14),
                bg=self.colors["surface"]).pack(side=tk.LEFT)

        tk.Label(output_header, text="Generated Quiz Preview",
                font=("SF Pro Display", 14, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(side=tk.LEFT, padx=(8, 0))

        # Status indicator
        self.quiz_status = tk.Label(output_header, text="Ready to generate",
                                   font=("SF Pro Display", 11),
                                   bg=self.colors["surface"],
                                   fg=self.colors["text_muted"])
        self.quiz_status.pack(side=tk.RIGHT)

        # Divider
        divider2 = tk.Frame(output_card, bg=self.colors["border"], height=1)
        divider2.pack(fill=tk.X, padx=25, pady=(15, 0))

        # Quiz output text area
        self.quiz_output = scrolledtext.ScrolledText(
            output_card,
            font=("JetBrains Mono", 13),
            bg=self.colors["surface"],
            fg=self.colors["text_secondary"],
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=25,
            pady=20,
            spacing1=6,
            spacing2=3,
            spacing3=6,
            highlightthickness=0,
            borderwidth=0
        )
        self.quiz_output.pack(fill=tk.BOTH, expand=True, padx=0, pady=(10, 15))

    def create_flashcard_tab(self):
        """Create the Flashcard tab."""
        tab = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.notebook.add(tab, text="  🃏 Flashcards  ")

        # Header
        header = tk.Frame(tab, bg=self.colors["surface"])
        header.pack(fill=tk.X, pady=(0, 15))

        header_inner = tk.Frame(header, bg=self.colors["surface"])
        header_inner.pack(fill=tk.X, padx=30, pady=25)

        tk.Label(header_inner, text="🃏 Flashcard Studio",
                font=("Helvetica Neue", 22, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(anchor="w")

        tk.Label(header_inner, text="Create and study flashcards with spaced repetition",
                font=("Helvetica Neue", 13),
                bg=self.colors["surface"], fg=self.colors["text_secondary"]).pack(anchor="w", pady=(8, 0))

        # Options card
        options_frame = tk.Frame(tab, bg=self.colors["surface"])
        options_frame.pack(fill=tk.X, pady=(0, 15))

        inner_opts = tk.Frame(options_frame, bg=self.colors["surface"])
        inner_opts.pack(fill=tk.X, padx=30, pady=25)

        # Topic row
        topic_frame = tk.Frame(inner_opts, bg=self.colors["surface"])
        topic_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(topic_frame, text="Topic",
                font=("Helvetica Neue", 14, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(side=tk.LEFT)

        self.flash_topic_values = [
            "All Topics", "Exam Concepts", "Probability", "Sampling", "Hypothesis Testing",
            "Correlation", "Linear Regression", "Multiple Regression",
            "Assumptions", "Interactions", "Categorical", "Polynomials",
            "Mixed Models", "Growth Curves", "Outliers"
        ]
        self.flash_topic = ttk.Combobox(topic_frame, values=self.flash_topic_values,
                                        font=("Helvetica Neue", 13), width=28)
        self.flash_topic.set("All Topics")
        self.flash_topic.pack(side=tk.LEFT, padx=(30, 0))

        # Allow custom topic entry - add to list when user types a new topic
        self.flash_topic.bind('<Return>', self._add_custom_flash_topic)
        self.flash_topic.bind('<FocusOut>', self._add_custom_flash_topic)

        # Count row
        count_frame = tk.Frame(inner_opts, bg=self.colors["surface"])
        count_frame.pack(fill=tk.X, pady=(0, 25))

        tk.Label(count_frame, text="Number of Cards",
                font=("Helvetica Neue", 14, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(side=tk.LEFT)

        self.flash_count = tk.Spinbox(count_frame, from_=1, to=30, width=6,
                                      font=("Helvetica Neue", 13),
                                      bg=self.colors["input_bg"],
                                      fg=self.colors["text"],
                                      relief=tk.FLAT)
        self.flash_count.delete(0, tk.END)
        self.flash_count.insert(0, "10")
        self.flash_count.pack(side=tk.LEFT, padx=(30, 0))

        # First button row - Generate
        btn_row1 = tk.Frame(inner_opts, bg=self.colors["surface"])
        btn_row1.pack(fill=tk.X, pady=(0, 15))

        generate_btn = tk.Button(btn_row1, text="📋 Show Prompt",
                                command=self.generate_flashcards,
                                bg=self.colors["input_bg"],
                                fg="#000000",
                                font=("Helvetica Neue", 13, "bold"),
                                padx=22, pady=12,
                                relief=tk.FLAT,
                                cursor="hand2",
                                activebackground=self.colors["surface_hover"],
                                activeforeground="#000000")
        generate_btn.pack(side=tk.LEFT)

        generate_claude_btn = tk.Button(btn_row1, text="🤖 Generate with Claude",
                                        command=self.generate_flashcards_with_claude,
                                        bg=self.colors["success"],
                                        fg="#000000",
                                        font=("Helvetica Neue", 13, "bold"),
                                        padx=28, pady=12,
                                        relief=tk.FLAT,
                                        cursor="hand2",
                                        activebackground="#059669",
                                        activeforeground="#000000")
        generate_claude_btn.pack(side=tk.LEFT, padx=(15, 0))

        # Second button row - Deck management
        btn_row2 = tk.Frame(inner_opts, bg=self.colors["surface"])
        btn_row2.pack(fill=tk.X)

        save_deck_btn = tk.Button(btn_row2, text="💾 Save to Deck",
                                  command=self.save_flashcards_to_deck,
                                  bg=self.colors["secondary"],
                                  fg="#000000",
                                  font=("Helvetica Neue", 13, "bold"),
                                  padx=22, pady=12,
                                  relief=tk.FLAT,
                                  cursor="hand2",
                                  activebackground="#0891b2",
                                  activeforeground="#000000")
        save_deck_btn.pack(side=tk.LEFT)

        browse_decks_btn = tk.Button(btn_row2, text="📚 My Decks",
                                     command=self.open_deck_browser,
                                     bg=self.colors["input_bg"],
                                     fg="#000000",
                                     font=("Helvetica Neue", 13, "bold"),
                                     padx=22, pady=12,
                                     relief=tk.FLAT,
                                     cursor="hand2",
                                     activebackground=self.colors["surface_hover"],
                                     activeforeground="#000000")
        browse_decks_btn.pack(side=tk.LEFT, padx=(15, 0))

        study_btn = tk.Button(btn_row2, text="📖 Study Now",
                              command=self.study_flashcards,
                              bg=self.colors["primary"],
                              fg="#000000",
                              font=("Helvetica Neue", 13, "bold"),
                              padx=22, pady=12,
                              relief=tk.FLAT,
                              cursor="hand2",
                              activebackground="#7c3aed",
                              activeforeground="#000000")
        study_btn.pack(side=tk.LEFT, padx=(15, 0))

        # Output card
        output_frame = tk.Frame(tab, bg=self.colors["surface"])
        output_frame.pack(fill=tk.BOTH, expand=True)

        output_header = tk.Frame(output_frame, bg=self.colors["surface"])
        output_header.pack(fill=tk.X, padx=30, pady=(20, 10))

        tk.Label(output_header, text="Generated Flashcards",
                font=("Helvetica Neue", 16, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(side=tk.LEFT)

        self.deck_info_label = tk.Label(output_header, text="",
                                        font=("Helvetica Neue", 13),
                                        bg=self.colors["surface"],
                                        fg=self.colors["success"])
        self.deck_info_label.pack(side=tk.RIGHT)

        self.flash_output = scrolledtext.ScrolledText(
            output_frame,
            font=("Menlo", 14),
            bg=self.colors["input_bg"],
            fg=self.colors["text"],
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=20,
            pady=20,
            spacing1=4,
            spacing2=2,
            spacing3=4
        )
        self.flash_output.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 25))

    def create_my_notes_tab(self):
        """Create the My Notes tab showing all synthesized notes across topics."""
        tab = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.notebook.add(tab, text="  📝 My Notes  ")

        # Header
        header = tk.Frame(tab, bg=self.colors["surface"])
        header.pack(fill=tk.X)

        header_inner = tk.Frame(header, bg=self.colors["surface"])
        header_inner.pack(fill=tk.X, padx=30, pady=20)

        tk.Label(header_inner, text="📝 My Notes",
                font=("Helvetica Neue", 24, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(side=tk.LEFT)

        tk.Label(header_inner, text="Your synthesized thoughts and summaries from study sessions",
                font=("Helvetica Neue", 12),
                bg=self.colors["surface"], fg=self.colors["text_secondary"]).pack(side=tk.LEFT, padx=(20, 0))

        # Refresh button
        refresh_btn = tk.Label(
            header_inner,
            text="↻ Refresh",
            font=("SF Pro Display", 12),
            fg=self.colors["primary"],
            bg=self.colors["surface"],
            cursor="hand2"
        )
        refresh_btn.pack(side=tk.RIGHT)
        refresh_btn.bind("<Button-1>", lambda e: self.load_my_notes())

        # Content area with scrollable frame
        content_frame = tk.Frame(tab, bg=self.colors["bg"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # Create canvas for scrolling
        canvas = tk.Canvas(content_frame, bg=self.colors["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        self.notes_container = tk.Frame(canvas, bg=self.colors["bg"])

        self.notes_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.notes_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Enable mousewheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Load notes after a short delay
        self.root.after(200, self.load_my_notes)

    def load_my_notes(self):
        """Load and display all notes from study sessions."""
        from content_storage import get_all_study_sessions

        # Clear existing notes
        for widget in self.notes_container.winfo_children():
            widget.destroy()

        sessions = get_all_study_sessions()

        # Filter sessions that have my_thoughts data
        notes_found = False
        for session in sessions:
            my_thoughts = session.get("my_thoughts", {})
            raw_notes = my_thoughts.get("raw_notes", "")
            summary = my_thoughts.get("summary", "")

            if raw_notes or summary:
                notes_found = True
                self._create_note_card(session)

        if not notes_found:
            # Show empty state
            empty_frame = tk.Frame(self.notes_container, bg=self.colors["bg"])
            empty_frame.pack(fill=tk.X, pady=50)

            tk.Label(
                empty_frame,
                text="No notes yet!",
                font=("SF Pro Display", 18, "bold"),
                fg=self.colors["text_muted"],
                bg=self.colors["bg"]
            ).pack()

            tk.Label(
                empty_frame,
                text="Open a study session, go to 'My Thoughts' tab,\nand write your reflections to see them here.",
                font=("SF Pro Display", 12),
                fg=self.colors["text_muted"],
                bg=self.colors["bg"],
                justify=tk.CENTER
            ).pack(pady=(10, 0))

    def _create_note_card(self, session):
        """Create a card for displaying a topic's notes."""
        topic = session.get("topic", "Unknown Topic")
        my_thoughts = session.get("my_thoughts", {})
        raw_notes = my_thoughts.get("raw_notes", "")
        summary = my_thoughts.get("summary", "")
        key_concepts = my_thoughts.get("key_concepts", [])
        last_accessed = session.get("last_accessed", "")

        # Card container
        card = tk.Frame(
            self.notes_container,
            bg=self.colors["surface"],
            highlightbackground=self.colors["content_border"],
            highlightthickness=1
        )
        card.pack(fill=tk.X, pady=(0, 15))

        # Card header
        header = tk.Frame(card, bg=self.colors["surface"])
        header.pack(fill=tk.X, padx=20, pady=(15, 10))

        tk.Label(
            header,
            text=topic,
            font=("SF Pro Display", 16, "bold"),
            fg=self.colors["text"],
            bg=self.colors["surface"]
        ).pack(side=tk.LEFT)

        # Format date
        if last_accessed:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(last_accessed)
                date_str = dt.strftime("%b %d, %Y")
            except:
                date_str = ""
        else:
            date_str = ""

        if date_str:
            tk.Label(
                header,
                text=date_str,
                font=("SF Pro Display", 11),
                fg=self.colors["text_muted"],
                bg=self.colors["surface"]
            ).pack(side=tk.RIGHT)

        # Key concepts as chips
        if key_concepts:
            concepts_frame = tk.Frame(card, bg=self.colors["surface"])
            concepts_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

            for concept in key_concepts[:6]:  # Show max 6
                chip = tk.Label(
                    concepts_frame,
                    text=concept,
                    font=("SF Pro Display", 10),
                    fg="#ffffff",
                    bg=self.colors["primary"],
                    padx=8,
                    pady=3
                )
                chip.pack(side=tk.LEFT, padx=(0, 5))

            if len(key_concepts) > 6:
                tk.Label(
                    concepts_frame,
                    text=f"+{len(key_concepts) - 6} more",
                    font=("SF Pro Display", 10),
                    fg=self.colors["text_muted"],
                    bg=self.colors["surface"]
                ).pack(side=tk.LEFT)

        # Summary section
        if summary:
            summary_label = tk.Label(
                card,
                text="Your Summary:",
                font=("SF Pro Display", 11, "bold"),
                fg=self.colors["text_muted"],
                bg=self.colors["surface"],
                anchor=tk.W
            )
            summary_label.pack(fill=tk.X, padx=20, pady=(5, 5))

            summary_text = tk.Label(
                card,
                text=summary[:300] + ("..." if len(summary) > 300 else ""),
                font=("Georgia", 12),
                fg=self.colors["text_reading"],
                bg=self.colors["surface"],
                wraplength=700,
                justify=tk.LEFT,
                anchor=tk.W
            )
            summary_text.pack(fill=tk.X, padx=20, pady=(0, 15))

        # Raw notes preview (collapsed)
        if raw_notes and not summary:
            notes_preview = tk.Label(
                card,
                text=raw_notes[:200] + ("..." if len(raw_notes) > 200 else ""),
                font=("Georgia", 11),
                fg=self.colors["text_muted"],
                bg=self.colors["surface"],
                wraplength=700,
                justify=tk.LEFT,
                anchor=tk.W
            )
            notes_preview.pack(fill=tk.X, padx=20, pady=(0, 15))

        # Open study session button
        btn_frame = tk.Frame(card, bg=self.colors["surface"])
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 15))

        open_btn = tk.Label(
            btn_frame,
            text="📖 Open Study Session",
            font=("SF Pro Display", 11),
            fg=self.colors["primary"],
            bg=self.colors["surface"],
            cursor="hand2"
        )
        open_btn.pack(side=tk.LEFT)
        open_btn.bind("<Button-1>", lambda e, t=topic: self.open_study_session_for_topic(t))

    def open_study_session_for_topic(self, topic):
        """Open the study session window for a specific topic."""
        from study_session import StudySessionWindow
        StudySessionWindow(
            self.root,
            topic,
            on_complete_callback=self.on_study_complete,
            timer_ref=self,
            colors=self.colors
        )

    # R interpreter tab removed — subject-agnostic version

    # ========================================================================
    # ACTIONS
    # ========================================================================

    def load_stats(self):
        """Load and display statistics."""
        try:
            collection = get_vector_store()
            count = collection.count()

            self.chunks_card.value_label.config(text=str(count))

            if count > 0:
                sample = collection.peek(limit=min(count, 500))
                source_dict = {}

                for meta in sample["metadatas"]:
                    filename = meta.get("filename", "unknown")
                    file_type = meta.get("type", "unknown")
                    if filename not in source_dict:
                        source_dict[filename] = {"type": file_type, "chunks": 0}
                    source_dict[filename]["chunks"] += 1

                self.sources_card.value_label.config(text=str(len(source_dict)))

                # Update file count badge
                if hasattr(self, 'file_count_label'):
                    self.file_count_label.config(text=f"{len(source_dict)} files")

                # Update treeview
                for item in self.materials_tree.get_children():
                    self.materials_tree.delete(item)

                for name, info in sorted(source_dict.items()):
                    self.materials_tree.insert("", tk.END, values=(
                        name, info["type"], info["chunks"]
                    ))
            else:
                self.sources_card.value_label.config(text="0")
                if hasattr(self, 'file_count_label'):
                    self.file_count_label.config(text="0 files")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load stats: {e}")

    def reindex_materials(self):
        """Reindex all materials."""
        if messagebox.askyesno("Confirm", "Reindex all study materials?"):
            def do_reindex():
                try:
                    index_documents()
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Materials reindexed!"))
                    self.root.after(0, self.load_stats)
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

            threading.Thread(target=do_reindex, daemon=True).start()

    def search_question(self):
        """Search materials for a question - opens in new window."""
        question = self.question_entry.get().strip()
        if not question:
            messagebox.showwarning("Warning", "Please enter a question")
            return

        try:
            # Get model and word count settings from the UI
            model_key = self.qa_model.get()
            word_count = self.qa_output_words.get()

            # Retrieve contexts
            n_chunks = CLAUDE_MODELS[model_key]["context_chunks"]
            contexts = retrieve_context(question, n_results=n_chunks)

            # Update inline results to show status
            self.qa_results.delete(1.0, tk.END)
            self.qa_results.insert(tk.END, f"✅ Found {len(contexts)} sources\n", "h2")
            self.qa_results.insert(tk.END, f"\nOpened results in new window...\n", "source")

            # Open the new Q&A window with sources
            open_qa_window(self.root, question, contexts, model_key, word_count, colors=self.colors)

        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {e}")

    def render_qa_markdown(self, text, question="", sources=None):
        """Render markdown text with proper formatting in the Q&A results widget."""
        import re

        self.qa_results.delete(1.0, tk.END)

        # Add header if question provided
        if question:
            self.qa_results.insert(tk.END, f"Question: {question}\n", "h2")
            self.qa_results.insert(tk.END, "\n")

        lines = text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]

            # Headers
            if line.startswith('# '):
                self.qa_results.insert(tk.END, line[2:] + '\n', "h1")
            elif line.startswith('## '):
                self.qa_results.insert(tk.END, line[3:] + '\n', "h2")
            elif line.startswith('### '):
                self.qa_results.insert(tk.END, line[4:] + '\n', "h3")
            # Bullet points
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                bullet_text = line.strip()[2:]
                bullet_text = self.clean_inline_markdown(bullet_text)
                self.qa_results.insert(tk.END, "  • " + bullet_text + '\n', "bullet")
            # Numbered lists
            elif re.match(r'^\d+\.\s', line.strip()):
                match = re.match(r'^(\d+)\.\s(.*)$', line.strip())
                if match:
                    num, text_content = match.groups()
                    text_content = self.clean_inline_markdown(text_content)
                    self.qa_results.insert(tk.END, f"  {num}. {text_content}\n", "bullet")
            # Code blocks
            elif line.strip().startswith('```'):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                code_text = '\n'.join(code_lines)
                self.qa_results.insert(tk.END, "\n" + code_text + "\n\n", "code")
            # Regular text
            else:
                processed = self.clean_inline_markdown(line)
                self.qa_results.insert(tk.END, processed + '\n')

            i += 1

        # Add sources at the end
        if sources:
            self.qa_results.insert(tk.END, "\n")
            self.qa_results.insert(tk.END, f"📚 Sources: {sources}\n", "source")

    def clean_inline_markdown(self, text):
        """Clean inline markdown formatting."""
        import re
        # Remove ** for bold
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        # Remove * for italic
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        # Clean up inline code markers
        text = re.sub(r'`([^`]+)`', r'[\1]', text)
        # Clean remaining markers
        text = text.replace('**', '').replace('`', '')
        return text

    def on_model_change(self, event=None):
        """Handle model selection change."""
        selected_display = self.model_combo.get()

        # Find the model key from display name
        for key, config in CLAUDE_MODELS.items():
            if config["display_name"] == selected_display:
                self.qa_model.set(key)
                self.model_desc_label.config(text=config["description"])
                break

    def on_word_count_change(self, value):
        """Handle word count slider change."""
        word_count = int(float(value))
        self.word_count_label.config(text=f"{word_count} words")

    def set_word_count(self, value):
        """Set word count from preset button."""
        self.qa_output_words.set(value)
        self.word_count_label.config(text=f"{value} words")

    def ask_claude(self):
        """Open Q&A window and automatically ask AI."""
        question = self.question_entry.get().strip()
        if not question:
            messagebox.showwarning("Warning", "Please enter a question")
            return

        # Get selected model settings
        model_key = self.qa_model.get()
        model_config = CLAUDE_MODELS[model_key]
        n_chunks = model_config["context_chunks"]

        # Get output length preference
        word_count = self.qa_output_words.get()

        # Get context from RAG
        try:
            contexts = retrieve_context(question, n_results=n_chunks)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve context: {e}")
            return

        # Show status in main window
        self.qa_results.delete(1.0, tk.END)
        self.qa_results.insert(tk.END, f"✨ Asking AI ({model_config['display_name']})...\n", "h2")
        self.qa_results.insert(tk.END, f"\nOpened in new window...\n", "source")

        # Open the Q&A window and auto-trigger AI
        qa_win = open_qa_window(self.root, question, contexts, model_key, word_count, colors=self.colors)
        # Automatically ask AI after a short delay (let window render first)
        qa_win.window.after(100, qa_win.ask_ai)

    def generate_quiz(self):
        """Generate quiz prompt."""
        quiz_type = self.quiz_type.get()
        topic = self.quiz_topic_combo.get()
        count = int(self.quiz_count.get())

        if topic == "All Topics":
            topic = None

        search_query = topic if topic else "key concepts statistics regression"

        try:
            # Use smart retrieval for special topics like "Exam Concepts"
            contexts = retrieve_context_smart(search_query, n_results=6)

            context_text = "\n\n".join([
                f"[From {ctx['metadata'].get('filename', 'unknown')}]\n{ctx['content'][:800]}"
                for ctx in contexts
            ])

            type_name = "Multiple Choice" if quiz_type == "multiple_choice" else "Open Ended"
            topic_text = f" about {topic}" if topic else ""

            prompt = f"""Generate {count} {type_name} questions{topic_text} based on this study material:

{context_text}

---

"""
            if quiz_type == "multiple_choice":
                prompt += """For each question:
1. Write a clear question
2. Provide 4 options (A, B, C, D)
3. Mark the correct answer
4. Brief explanation

CRITICAL: Make ALL answer options indistinguishable by length/style:
- Correct and incorrect answers must be approximately the same length
- Use same detail level and technical language for all options
- Don't make correct answer more "complete-sounding"
- Create plausible distractors based on common misconceptions

Format:
**Q1:** [Question]
A) ... B) ... C) ... D) ...
**Answer:** [Letter] - [Explanation]
"""
            else:
                prompt += """For each question:
1. Ask a question requiring explanation
2. Provide model answer
3. List key points to include

Format:
**Q1:** [Question]
**Model Answer:** [Answer]
**Key Points:** [Bullet points]
"""

            self.quiz_output.delete(1.0, tk.END)
            self.quiz_output.insert(tk.END, prompt)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate quiz: {e}")

    def generate_quiz_with_claude(self):
        """Generate quiz using Claude Code CLI or load from storage."""
        quiz_type = self.quiz_type.get()
        topic = self.quiz_topic_combo.get()
        count = int(self.quiz_count.get())

        if topic == "All Topics":
            topic = None

        # Create a storage key for this quiz (includes count so different counts = different quizzes)
        base_topic = topic if topic else "Statistics"
        storage_topic = f"{base_topic}::{count}q"

        # Check if we have a saved quiz for this topic+count
        saved_quiz = get_quiz(storage_topic)
        if saved_quiz and saved_quiz.get("quiz_content"):
            # Load from storage
            self.quiz_output.delete(1.0, tk.END)
            self.quiz_output.insert(tk.END, f"📂 Loaded saved quiz for '{storage_topic}'\n")
            self.quiz_output.insert(tk.END, "=" * 60 + "\n\n")
            self.quiz_output.insert(tk.END, saved_quiz["quiz_content"])

            # Show attempt history if any
            attempts = saved_quiz.get("attempts", [])
            if attempts:
                self.quiz_output.insert(tk.END, "\n\n" + "=" * 60 + "\n")
                self.quiz_output.insert(tk.END, f"📊 Previous attempts: {len(attempts)}\n")
                for i, attempt in enumerate(attempts[-3:], 1):  # Show last 3
                    self.quiz_output.insert(tk.END,
                        f"   • {attempt['score']}/{attempt['total']} ({attempt['percentage']}%)\n")
            return

        search_query = topic if topic else "key concepts statistics regression"

        try:
            # Use smart retrieval for special topics like "Exam Concepts"
            contexts = retrieve_context_smart(search_query, n_results=6)

            context_text = "\n\n".join([
                f"[From {ctx['metadata'].get('filename', 'unknown')}]\n{ctx['content'][:800]}"
                for ctx in contexts
            ])

            type_name = "Multiple Choice" if quiz_type == "multiple_choice" else "Open Ended"
            topic_text = f" about {topic}" if topic else ""

            prompt = f"""Based on these Statistics study materials:

{context_text}

---

Generate {count} {type_name} questions{topic_text}.

"""
            if quiz_type == "multiple_choice":
                prompt += """For each question provide:
1. A clear question testing understanding
2. 4 options (A, B, C, D)
3. The correct answer
4. A brief explanation

CRITICAL RULES:

1. RANDOMIZE CORRECT ANSWER POSITION:
- Distribute correct answers evenly across A, B, C, D
- Do NOT favor any letter - roughly equal distribution
- For example in 8 questions: ~2 A's, ~2 B's, ~2 C's, ~2 D's

2. Answer Options Must Be Indistinguishable:
- ALL options must be approximately the same length
- Use identical level of detail across all options
- DO NOT make correct answer longer or more detailed
- Each wrong option should be a plausible misconception

Format as:
**Q1:** [Question]
A) ... B) ... C) ... D) ...
**Answer:** [Letter] - [Explanation]
"""
            else:
                prompt += """For each question provide:
1. A question requiring explanation
2. A model answer
3. Key points to include

Format as:
**Q1:** [Question]
**Model Answer:** [Answer]
**Key Points:** [Bullets]
"""

            # Show loading
            self.quiz_output.delete(1.0, tk.END)
            self.quiz_output.insert(tk.END, f"🤖 Generating {count} {type_name} questions{topic_text}...\n\n")
            self.quiz_output.insert(tk.END, "⏳ Please wait...\n")
            self.quiz_output.update()

            def run_claude():
                try:
                    result = subprocess.run(
                        ["claude", "-p", prompt, "--model", "opus"],
                        capture_output=True,
                        text=True,
                        timeout=180
                    )

                    response = result.stdout if result.stdout else result.stderr

                    # Save to persistent storage
                    save_quiz(storage_topic, response)

                    def update_ui():
                        self.quiz_output.delete(1.0, tk.END)
                        self.quiz_output.insert(tk.END, f"🎯 {type_name} Quiz{topic_text}\n")
                        self.quiz_output.insert(tk.END, "=" * 60 + "\n\n")
                        self.quiz_output.insert(tk.END, response)

                    self.root.after(0, update_ui)

                except subprocess.TimeoutExpired:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Claude took too long"))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed: {e}"))

            threading.Thread(target=run_claude, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate quiz: {e}")

    def regenerate_quiz(self):
        """Force regeneration of quiz (delete cached and generate new)."""
        from content_storage import delete_quiz

        topic = self.quiz_topic_combo.get()
        count = int(self.quiz_count.get())
        base_topic = topic if topic != "All Topics" else "Statistics"
        storage_topic = f"{base_topic}::{count}q"

        # Delete existing cached quiz for this topic+count
        delete_quiz(storage_topic)

        # Now generate fresh
        self.generate_quiz_with_claude()

    def start_interactive_quiz(self):
        """Start an interactive quiz from the generated content."""
        content = self.quiz_output.get(1.0, tk.END).strip()

        if not content or "Generating" in content or "Please wait" in content:
            messagebox.showwarning("Warning", "Generate a quiz first using 'Generate with Claude'!")
            return

        topic = self.quiz_topic_combo.get()
        if topic == "All Topics":
            topic = "Statistics"

        # Open the interactive quiz window with callback and timer reference
        quiz_window = open_quiz(self.root, content, topic, timer_ref=self, colors=self.colors)
        if quiz_window:
            # Store reference to update progress when quiz closes
            quiz_window.on_complete_callback = lambda score, total: self.on_quiz_complete(topic, score, total)

    def open_comprehensive_test(self):
        """Open the comprehensive test topic selection dialog."""
        from comprehensive_test import open_comprehensive_test
        open_comprehensive_test(self.root, STUDY_GUIDE, self.colors, timer_ref=self)

    def on_quiz_complete(self, topic, score, total):
        """Handle quiz completion - update progress."""
        # Save quiz attempt to persistent storage
        add_quiz_attempt(topic, score, total)

        # Save quiz result to progress
        quiz_key = f"quiz_completed::{topic}"
        self.progress[quiz_key] = {
            "completed": True,
            "last_score": score,
            "last_total": total,
            "percentage": round(score / total * 100, 1) if total > 0 else 0
        }
        self.save_progress()

        # If score is good (>=70%), mark related topic as studied
        if total > 0 and (score / total) >= 0.7:
            # Find matching topic in study guide
            for lecture_name, lecture_data in STUDY_GUIDE.items():
                for t in lecture_data["topics"]:
                    # Check if topic matches
                    if topic.lower() in t.lower() or t.lower() in topic.lower():
                        topic_key = f"{lecture_name}::{t}"
                        if topic_key in self.topic_vars:
                            var = self.topic_vars[topic_key]
                            # Only mark if not already completed
                            if not var.get():
                                # invoke() toggles the checkbox AND calls its command
                                # This triggers the full update (label color, lecture progress, etc.)
                                if hasattr(var, 'checkbox'):
                                    var.checkbox.invoke()

    def _add_custom_flash_topic(self, event=None):
        """Add a custom topic to the flashcard combobox if not already present."""
        current = self.flash_topic.get().strip()
        if current and current not in self.flash_topic_values:
            self.flash_topic_values.append(current)
            self.flash_topic['values'] = self.flash_topic_values

    def _add_custom_quiz_topic(self, event=None):
        """Add a custom topic to the quiz combobox if not already present."""
        current = self.quiz_topic_combo.get().strip()
        if current and current not in self.quiz_topic_values:
            self.quiz_topic_values.append(current)
            self.quiz_topic_combo['values'] = self.quiz_topic_values

    def generate_flashcards(self):
        """Generate flashcard prompt."""
        topic = self.flash_topic.get()
        count = int(self.flash_count.get())

        if topic == "All Topics":
            topic = None

        search_query = topic if topic else "definitions concepts formulas statistics"

        try:
            # Use smart retrieval for special topics like "Exam Concepts"
            contexts = retrieve_context_smart(search_query, n_results=6)

            context_text = "\n\n".join([
                f"[From {ctx['metadata'].get('filename', 'unknown')}]\n{ctx['content'][:800]}"
                for ctx in contexts
            ])

            topic_text = f" about {topic}" if topic else ""

            prompt = f"""Generate {count} flashcards{topic_text} based on this study material:

{context_text}

---

For each flashcard:
📝 **Front:** [Term/Concept/Question]
💡 **Back:** [Definition/Explanation/Answer]
📌 **Example:** [Practical example if applicable]

Focus on key terms, formulas, and concepts that are likely to appear on the exam.
"""

            self.flash_output.delete(1.0, tk.END)
            self.flash_output.insert(tk.END, prompt)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate flashcards: {e}")

    def generate_flashcards_with_claude(self):
        """Generate flashcards using Claude Code CLI."""
        topic = self.flash_topic.get()
        count = int(self.flash_count.get())

        if topic == "All Topics":
            topic = None

        search_query = topic if topic else "definitions concepts formulas statistics"

        try:
            # Use smart retrieval for special topics like "Exam Concepts"
            contexts = retrieve_context_smart(search_query, n_results=6)

            context_text = "\n\n".join([
                f"[From {ctx['metadata'].get('filename', 'unknown')}]\n{ctx['content'][:800]}"
                for ctx in contexts
            ])

            topic_text = f" about {topic}" if topic else ""

            prompt = f"""Based on these Statistics study materials:

{context_text}

---

Generate {count} flashcards{topic_text} for exam preparation.

For each flashcard provide:
- Front: A term, concept, or question
- Back: Clear definition or answer
- Example: A practical example if applicable

Format as:
**Card 1**
📝 Front: [Term/Question]
💡 Back: [Definition/Answer]
📌 Example: [Example]

Focus on key terms, formulas, and concepts likely to appear on the exam."""

            # Show loading
            self.flash_output.delete(1.0, tk.END)
            self.flash_output.insert(tk.END, f"🤖 Generating {count} flashcards{topic_text}...\n\n")
            self.flash_output.insert(tk.END, "⏳ Please wait...\n")
            self.flash_output.update()

            def run_claude():
                try:
                    result = subprocess.run(
                        ["claude", "-p", prompt, "--model", "opus"],
                        capture_output=True,
                        text=True,
                        timeout=180
                    )

                    response = result.stdout if result.stdout else result.stderr

                    def update_ui():
                        self.flash_output.delete(1.0, tk.END)
                        self.flash_output.insert(tk.END, f"🃏 Flashcards{topic_text}\n")
                        self.flash_output.insert(tk.END, "=" * 60 + "\n\n")
                        self.flash_output.insert(tk.END, response)

                    self.root.after(0, update_ui)

                except subprocess.TimeoutExpired:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Claude took too long"))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed: {e}"))

            threading.Thread(target=run_claude, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate flashcards: {e}")

    def save_flashcards_to_deck(self):
        """Save generated flashcards to a deck."""
        content = self.flash_output.get(1.0, tk.END).strip()

        if not content or "Generating" in content or "Please wait" in content:
            messagebox.showwarning("Warning", "Generate flashcards first before saving!")
            return

        # Get topic for deck name
        topic = self.flash_topic.get()
        if topic == "All Topics":
            topic = "Statistics"

        deck_name = f"{topic} Flashcards"

        try:
            deck_id = parse_claude_flashcards(content, deck_name, topic)
            stats = get_deck_stats(deck_id)

            self.deck_info_label.config(text=f"✅ Saved {stats['total']} cards to '{deck_name}'")
            messagebox.showinfo("Success", f"Saved {stats['total']} flashcards to deck '{deck_name}'!\n\nClick 'My Decks' or 'Study Now' to review them.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save flashcards: {e}")

    def open_deck_browser(self):
        """Open the deck browser window."""
        open_deck_browser(self.root, colors=self.colors)

    def study_flashcards(self):
        """Open the flashcard review window."""
        due_cards = get_due_cards()
        if not due_cards:
            messagebox.showinfo("No Cards Due", "No flashcards due for review!\n\nGenerate some flashcards and save them to a deck first.")
            return

        open_review(self.root, colors=self.colors)


def main():
    root = tk.Tk()
    app = StudyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
