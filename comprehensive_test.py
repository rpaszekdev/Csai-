#!/usr/bin/env python3
"""
Comprehensive Test System - 30 questions across multiple topics with Teacher's Mind prediction.

Features:
- Multi-topic selection dialog
- Mark as Unknown (?) capability
- Teacher's Mind question generation
- Results overview with correct/incorrect/unknown breakdown
- Study mode combining flashcards, explanations, and re-quizzing
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import json
import uuid
import re
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Callable

from themes import DARK_THEME
from quiz_system import parse_quiz_from_claude
from study_rag import (
    retrieve_context,
    retrieve_context_smart,
    retrieve_context_with_emphasis,
    generate_teacher_mind_prompt,
    generate_quiz_prompt
)

import subject_config
from content_storage import (
    save_comprehensive_test,
    get_question_hashes,
    compute_question_hash,
    is_duplicate_question,
    STORAGE_DIR,
    save_question_note,
    get_question_note,
    add_to_targeted_requiz,
    get_targeted_requiz_questions,
    clear_targeted_requiz,
    get_targeted_requiz_count
)
from flashcard_db import create_deck, add_card, load_db


# ============================================================================
# TOPIC SELECTION DIALOG
# ============================================================================

class TopicSelectionDialog:
    """Multi-select dialog for choosing topics for comprehensive test."""

    def __init__(self, parent, study_guide: dict, colors: dict = None,
                 on_start: Callable = None):
        self.window = tk.Toplevel(parent)
        self.window.title("Select Topics for Comprehensive Test")
        self.window.geometry("700x800")
        self.window.transient(parent)

        self.colors = colors if colors else DARK_THEME
        self.window.configure(bg=self.colors["bg"])

        self.study_guide = study_guide
        self.on_start = on_start
        self.selected_topics = {}  # {topic_name: BooleanVar}
        self.lecture_vars = {}  # {lecture_name: BooleanVar for select all}
        self.lecture_frames = {}  # {lecture_name: topics_frame}
        self.expanded = {}  # {lecture_name: bool}

        self.use_teacher_mind = tk.BooleanVar(value=True)

        self.setup_ui()

    def setup_ui(self):
        """Set up the topic selection UI."""
        # Header
        header = tk.Frame(self.window, bg=self.colors["surface"])
        header.pack(fill=tk.X)

        header_inner = tk.Frame(header, bg=self.colors["surface"])
        header_inner.pack(fill=tk.X, padx=30, pady=20)

        tk.Label(header_inner, text="📋 Comprehensive Test",
                font=("SF Pro Display", 22, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(anchor="w")

        tk.Label(header_inner, text="Select topics to include in your 30-question test",
                font=("SF Pro Display", 12),
                bg=self.colors["surface"], fg=self.colors["text_muted"]).pack(anchor="w", pady=(5, 0))

        # Teacher's Mind toggle
        toggle_frame = tk.Frame(self.window, bg=self.colors["bg"])
        toggle_frame.pack(fill=tk.X, padx=30, pady=(20, 10))

        teacher_check = tk.Checkbutton(
            toggle_frame,
            text="🧠 Use Teacher's Mind (predict exam questions)",
            variable=self.use_teacher_mind,
            font=("SF Pro Display", 12),
            bg=self.colors["bg"],
            fg=self.colors["text"],
            selectcolor=self.colors["surface"],
            activebackground=self.colors["bg"],
            activeforeground=self.colors["text"]
        )
        teacher_check.pack(anchor="w")

        tk.Label(toggle_frame,
                text="Analyzes lecture emphasis and common misconceptions to predict what your teacher will ask",
                font=("SF Pro Display", 10),
                bg=self.colors["bg"], fg=self.colors["text_muted"]).pack(anchor="w", padx=(24, 0))

        # Scrollable lectures area
        canvas_frame = tk.Frame(self.window, bg=self.colors["bg"])
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        canvas = tk.Canvas(canvas_frame, bg=self.colors["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)

        self.scrollable = tk.Frame(canvas, bg=self.colors["bg"])
        self.scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=self.scrollable, anchor="nw", width=620)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mousewheel
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Create lecture sections
        for lecture_name, lecture_data in self.study_guide.items():
            self.create_lecture_section(lecture_name, lecture_data)

        # Counter and buttons
        bottom_frame = tk.Frame(self.window, bg=self.colors["surface"])
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        bottom_inner = tk.Frame(bottom_frame, bg=self.colors["surface"])
        bottom_inner.pack(fill=tk.X, padx=30, pady=20)

        # Counter
        self.counter_label = tk.Label(bottom_inner,
                                      text="0 topics selected (≈0 questions)",
                                      font=("SF Pro Display", 12),
                                      bg=self.colors["surface"], fg=self.colors["text_muted"])
        self.counter_label.pack(side=tk.LEFT)

        # Buttons
        btn_frame = tk.Frame(bottom_inner, bg=self.colors["surface"])
        btn_frame.pack(side=tk.RIGHT)

        cancel_btn = tk.Button(btn_frame, text="Cancel",
                              command=self.window.destroy,
                              bg=self.colors["surface"], fg=self.colors["text"],
                              font=("SF Pro Display", 12),
                              padx=20, pady=8, relief=tk.FLAT, cursor="hand2")
        cancel_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.start_btn = tk.Button(btn_frame, text="Start Test (30 Questions)",
                                   command=self.start_test,
                                   bg="#6366f1", fg="white",
                                   font=("SF Pro Display", 12, "bold"),
                                   padx=20, pady=8, relief=tk.FLAT, cursor="hand2",
                                   state=tk.DISABLED)
        self.start_btn.pack(side=tk.LEFT)

        self.update_counter()

    def create_lecture_section(self, lecture_name: str, lecture_data: dict):
        """Create an expandable lecture section with topic checkboxes."""
        icon = lecture_data.get("icon", "📚")
        color = lecture_data.get("color", self.colors["primary"])
        topics = lecture_data.get("topics", [])

        # Lecture header (clickable to expand/collapse)
        lecture_frame = tk.Frame(self.scrollable, bg=self.colors["surface"])
        lecture_frame.pack(fill=tk.X, pady=5)

        header = tk.Frame(lecture_frame, bg=self.colors["surface"])
        header.pack(fill=tk.X, padx=10, pady=8)

        # Expand/collapse arrow
        self.expanded[lecture_name] = True
        arrow_label = tk.Label(header, text="▼",
                              font=("SF Pro Display", 10),
                              bg=self.colors["surface"], fg=self.colors["text_muted"])
        arrow_label.pack(side=tk.LEFT, padx=(0, 8))

        # Select all checkbox for lecture
        lecture_var = tk.BooleanVar(value=False)
        self.lecture_vars[lecture_name] = lecture_var

        lecture_check = tk.Checkbutton(
            header,
            text=f"{icon} {lecture_name}",
            variable=lecture_var,
            command=lambda ln=lecture_name: self.toggle_lecture(ln),
            font=("SF Pro Display", 12, "bold"),
            bg=self.colors["surface"],
            fg=self.colors["text"],
            selectcolor=self.colors["bg"],
            activebackground=self.colors["surface"],
            activeforeground=self.colors["text"]
        )
        lecture_check.pack(side=tk.LEFT)

        # Topic count badge
        badge = tk.Label(header, text=f"{len(topics)} topics",
                        font=("SF Pro Display", 10),
                        bg=color, fg="white", padx=8, pady=2)
        badge.pack(side=tk.RIGHT)

        # Click header to expand/collapse
        for widget in [header, arrow_label]:
            widget.bind("<Button-1>", lambda e, ln=lecture_name, al=arrow_label: self.toggle_expand(ln, al))

        # Topics frame (collapsible)
        topics_frame = tk.Frame(lecture_frame, bg=self.colors["bg"])
        topics_frame.pack(fill=tk.X, padx=(40, 10), pady=(0, 5))
        self.lecture_frames[lecture_name] = topics_frame

        # Individual topic checkboxes
        for topic in topics:
            topic_var = tk.BooleanVar(value=False)
            self.selected_topics[topic] = topic_var

            topic_check = tk.Checkbutton(
                topics_frame,
                text=topic,
                variable=topic_var,
                command=self.update_counter,
                font=("SF Pro Display", 11),
                bg=self.colors["bg"],
                fg=self.colors["text_secondary"],
                selectcolor=self.colors["surface"],
                activebackground=self.colors["bg"],
                activeforeground=self.colors["text"]
            )
            topic_check.pack(anchor="w", pady=2)

    def toggle_expand(self, lecture_name: str, arrow_label: tk.Label):
        """Toggle lecture section expansion."""
        self.expanded[lecture_name] = not self.expanded[lecture_name]

        if self.expanded[lecture_name]:
            arrow_label.config(text="▼")
            self.lecture_frames[lecture_name].pack(fill=tk.X, padx=(40, 10), pady=(0, 5))
        else:
            arrow_label.config(text="▶")
            self.lecture_frames[lecture_name].pack_forget()

    def toggle_lecture(self, lecture_name: str):
        """Select/deselect all topics in a lecture."""
        lecture_var = self.lecture_vars[lecture_name]
        select_all = lecture_var.get()

        topics = self.study_guide[lecture_name].get("topics", [])
        for topic in topics:
            if topic in self.selected_topics:
                self.selected_topics[topic].set(select_all)

        self.update_counter()

    def update_counter(self):
        """Update the selected topics counter."""
        selected = [t for t, var in self.selected_topics.items() if var.get()]
        count = len(selected)

        # Calculate approximate questions (30 distributed across topics)
        if count > 0:
            questions = min(30, count * 5)  # ~5 per topic, max 30
            self.counter_label.config(text=f"{count} topics selected (≈{questions} questions)")
            self.start_btn.config(state=tk.NORMAL)
        else:
            self.counter_label.config(text="0 topics selected (≈0 questions)")
            self.start_btn.config(state=tk.DISABLED)

    def start_test(self):
        """Start the comprehensive test with selected topics."""
        selected = [t for t, var in self.selected_topics.items() if var.get()]

        if not selected:
            messagebox.showwarning("No Topics", "Please select at least one topic.")
            return

        self.window.destroy()

        if self.on_start:
            self.on_start(selected, self.use_teacher_mind.get())


# ============================================================================
# COMPREHENSIVE TEST WINDOW
# ============================================================================

class ComprehensiveTestWindow:
    """30-question comprehensive test with unknown marking capability."""

    def __init__(self, parent, selected_topics: List[str], use_teacher_mind: bool = False,
                 colors: dict = None, timer_ref=None):
        self.window = tk.Toplevel(parent)
        self.window.title("📋 Comprehensive Test")
        self.window.geometry("1000x800")

        self.colors = colors if colors else DARK_THEME
        self.window.configure(bg=self.colors["bg"])

        self.selected_topics = selected_topics
        self.use_teacher_mind = use_teacher_mind
        self.timer_ref = timer_ref

        self.questions = []
        self.current_index = 0
        self.score = 0
        self.answered = False
        self.selected_option = None
        self.option_buttons = {}
        self.option_order = []
        self.letter_mapping = {}  # display_letter -> original_letter
        self.reverse_mapping = {}  # original_letter -> display_letter
        self.current_correct_display = None  # Correct answer in display letter

        # Track three categories
        self.results = {
            "correct": [],
            "incorrect": [],
            "unknown": []
        }

        self.test_id = str(uuid.uuid4())[:8]

        # Show loading, generate questions
        self.setup_loading_ui()
        self.generate_questions()

    def setup_loading_ui(self):
        """Show loading screen while generating questions."""
        self.loading_frame = tk.Frame(self.window, bg=self.colors["bg"])
        self.loading_frame.pack(expand=True, fill=tk.BOTH)

        center = tk.Frame(self.loading_frame, bg=self.colors["bg"])
        center.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(center, text="🧠",
                font=("SF Pro Display", 48),
                bg=self.colors["bg"]).pack()

        mode_text = "Teacher's Mind" if self.use_teacher_mind else "Standard"
        tk.Label(center, text=f"Generating {mode_text} Questions...",
                font=("SF Pro Display", 18, "bold"),
                bg=self.colors["bg"], fg=self.colors["text"]).pack(pady=(20, 10))

        tk.Label(center, text=f"Analyzing {len(self.selected_topics)} topics",
                font=("SF Pro Display", 12),
                bg=self.colors["bg"], fg=self.colors["text_muted"]).pack()

        self.progress_var = tk.StringVar(value="Preparing...")
        tk.Label(center, textvariable=self.progress_var,
                font=("SF Pro Display", 11),
                bg=self.colors["bg"], fg=self.colors["text_secondary"]).pack(pady=(20, 0))

    def generate_questions(self):
        """Generate 30 questions across selected topics."""
        def _generate():
            try:
                all_questions = []
                existing_hashes = get_question_hashes()

                # Calculate distribution
                total_questions = 30
                num_topics = len(self.selected_topics)
                base_per_topic = total_questions // num_topics
                remainder = total_questions % num_topics

                for i, topic in enumerate(self.selected_topics):
                    count = base_per_topic + (1 if i < remainder else 0)
                    if count == 0:
                        continue

                    self.progress_var.set(f"Generating questions for: {topic[:40]}...")

                    # Retrieve context - use smart retrieval for special topics like "Exam Concepts"
                    if self.use_teacher_mind:
                        contexts = retrieve_context_with_emphasis(topic, n_results=8)
                    else:
                        contexts = retrieve_context_smart(topic, n_results=8)

                    context_text = "\n\n---\n\n".join([
                        f"**From {ctx['metadata'].get('filename', 'unknown')}:**\n{ctx['content']}"
                        for ctx in contexts
                    ])

                    # Generate prompt
                    if self.use_teacher_mind:
                        prompt = generate_teacher_mind_prompt(
                            topic, count, context_text, existing_hashes
                        )
                    else:
                        prompt = generate_quiz_prompt("multiple_choice", topic, count)

                    # Call Claude
                    result = subprocess.run(
                        ["claude", "-p", prompt],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )

                    if result.returncode == 0:
                        questions = parse_quiz_from_claude(result.stdout)
                        for q in questions:
                            q["topic"] = topic
                            # Check for duplicates
                            q_hash = compute_question_hash(q.get("question", ""))
                            if q_hash not in existing_hashes:
                                all_questions.append(q)
                                existing_hashes.add(q_hash)

                # Limit to 30 questions
                self.questions = all_questions[:30]

                # Update UI on main thread
                self.window.after(0, self.show_quiz_ui)

            except Exception as e:
                self.window.after(0, lambda: self.show_error(str(e)))

        thread = threading.Thread(target=_generate, daemon=True)
        thread.start()

    def show_error(self, error_msg: str):
        """Show error if question generation fails."""
        self.loading_frame.destroy()
        error_frame = tk.Frame(self.window, bg=self.colors["bg"])
        error_frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(error_frame, text="❌ Error Generating Questions",
                font=("SF Pro Display", 18, "bold"),
                bg=self.colors["bg"], fg=self.colors["danger"]).pack(pady=(100, 20))

        tk.Label(error_frame, text=error_msg,
                font=("SF Pro Display", 12),
                bg=self.colors["bg"], fg=self.colors["text_muted"],
                wraplength=600).pack(pady=10)

        tk.Button(error_frame, text="Close",
                 command=self.window.destroy,
                 bg=self.colors["accent"], fg="white",
                 font=("SF Pro Display", 12), padx=20, pady=8,
                 relief=tk.FLAT).pack(pady=20)

    def show_quiz_ui(self):
        """Show the quiz interface after questions are generated."""
        self.loading_frame.destroy()

        if not self.questions:
            self.show_error("No questions were generated. Please try again.")
            return

        self.setup_ui()
        self.setup_bindings()
        self.show_question()

    def setup_ui(self):
        """Set up the quiz UI."""
        # Header
        header = tk.Frame(self.window, bg=self.colors["surface"])
        header.pack(fill=tk.X)

        header_inner = tk.Frame(header, bg=self.colors["surface"])
        header_inner.pack(fill=tk.X, padx=40, pady=20)

        # Left: Title
        title_row = tk.Frame(header_inner, bg=self.colors["surface"])
        title_row.pack(side=tk.LEFT)

        accent_bar = tk.Frame(title_row, bg="#6366f1", width=4)
        accent_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        mode_text = "Teacher's Mind" if self.use_teacher_mind else "Comprehensive"
        self.title_label = tk.Label(title_row, text=f"📋 {mode_text} Test",
                                    font=("SF Pro Display", 20, "bold"),
                                    bg=self.colors["surface"], fg=self.colors["text"])
        self.title_label.pack(side=tk.LEFT)

        # Right: Score
        score_frame = tk.Frame(header_inner, bg=self.colors["surface"])
        score_frame.pack(side=tk.RIGHT)

        tk.Label(score_frame, text="Score",
                font=("SF Pro Display", 11),
                bg=self.colors["surface"], fg=self.colors["text_muted"]).pack(anchor="e")

        self.score_label = tk.Label(score_frame, text="0/0",
                                    font=("SF Pro Display", 24, "bold"),
                                    bg=self.colors["surface"], fg=self.colors["success"])
        self.score_label.pack(anchor="e")

        # Progress bar
        progress_container = tk.Frame(self.window, bg=self.colors["bg"])
        progress_container.pack(fill=tk.X, padx=40, pady=(15, 0))

        progress_row = tk.Frame(progress_container, bg=self.colors["bg"])
        progress_row.pack(fill=tk.X)

        self.progress_label = tk.Label(progress_row,
                                       text=f"Question 1 of {len(self.questions)}",
                                       font=("SF Pro Display", 12),
                                       bg=self.colors["bg"], fg=self.colors["text_muted"])
        self.progress_label.pack(side=tk.LEFT)

        self.topic_label = tk.Label(progress_row, text="",
                                   font=("SF Pro Display", 11),
                                   bg=self.colors["bg"], fg=self.colors["text_secondary"])
        self.topic_label.pack(side=tk.RIGHT)

        self.progress_bar_container = tk.Frame(progress_container, bg=self.colors["border"], height=6)
        self.progress_bar_container.pack(fill=tk.X, pady=(10, 0))
        self.progress_bar_container.pack_propagate(False)

        self.progress_bar_fill = tk.Frame(self.progress_bar_container, bg="#6366f1", height=6)
        self.progress_bar_fill.place(x=0, y=0, relwidth=0, height=6)

        # Question card
        self.question_frame = tk.Frame(self.window, bg=self.colors["card"],
                                       highlightbackground=self.colors["border"],
                                       highlightthickness=1)
        self.question_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

        question_inner = tk.Frame(self.question_frame, bg=self.colors["card"])
        question_inner.pack(fill=tk.X, padx=30, pady=25)

        # Question number badge
        q_badge = tk.Frame(question_inner, bg="#6366f1")
        q_badge.pack(anchor="w")

        self.question_number = tk.Label(q_badge, text="  Q1  ",
                                        font=("SF Pro Display", 11, "bold"),
                                        bg="#6366f1", fg="white")
        self.question_number.pack(padx=2, pady=2)

        # Question text
        self.question_text = tk.Label(question_inner, text="",
                                      font=("Georgia", 17),
                                      bg=self.colors["card"], fg=self.colors["text"],
                                      wraplength=860, justify=tk.LEFT)
        self.question_text.pack(anchor="w", pady=(18, 25))

        # Options frame
        self.options_frame = tk.Frame(self.question_frame, bg=self.colors["card"])
        self.options_frame.pack(fill=tk.X, padx=30, pady=(0, 15))

        for letter in ["A", "B", "C", "D"]:
            btn_frame = tk.Frame(self.options_frame, bg=self.colors["option_bg"],
                                highlightbackground=self.colors["option_border"],
                                highlightthickness=1)
            btn_frame.pack(fill=tk.X, pady=5)

            btn_inner = tk.Frame(btn_frame, bg=self.colors["option_bg"])
            btn_inner.pack(fill=tk.X, padx=3, pady=3)

            letter_badge = tk.Label(btn_inner, text=f" {letter} ",
                                   font=("SF Pro Display", 12, "bold"),
                                   bg=self.colors["border"], fg=self.colors["text"],
                                   padx=8, pady=4)
            letter_badge.pack(side=tk.LEFT, padx=(10, 0), pady=10)

            btn = tk.Label(btn_inner, text="",
                          font=("SF Pro Display", 14),
                          bg=self.colors["option_bg"],
                          fg=self.colors["text"],
                          anchor="w", padx=12, pady=12, cursor="hand2")
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

            for widget in [btn_frame, btn_inner, btn, letter_badge]:
                widget.bind("<Button-1>", lambda e, l=letter: self.select_option(l))
                widget.bind("<Enter>", lambda e, f=btn_frame, b=btn, bi=btn_inner, lb=letter_badge: self.on_option_enter(f, b, bi, lb))
                widget.bind("<Leave>", lambda e, f=btn_frame, b=btn, bi=btn_inner, lb=letter_badge, l=letter: self.on_option_leave(f, b, bi, lb, l))

            btn.frame = btn_frame
            btn.inner = btn_inner
            btn.letter_badge = letter_badge
            self.option_buttons[letter] = btn

        # Feedback area
        self.feedback_frame = tk.Frame(self.question_frame, bg=self.colors["card"])
        self.feedback_frame.pack(fill=tk.X, padx=30, pady=(5, 15))

        self.feedback_label = tk.Label(self.feedback_frame, text="",
                                       font=("SF Pro Display", 13),
                                       bg=self.colors["card"], fg=self.colors["text"],
                                       wraplength=860, justify=tk.LEFT)

        # Bottom buttons
        btn_frame = tk.Frame(self.window, bg=self.colors["bg"])
        btn_frame.pack(fill=tk.X, padx=40, pady=(0, 20))

        self.submit_btn = tk.Button(btn_frame, text="Submit Answer",
                                    command=self.submit_answer,
                                    bg="#6366f1", fg="white",
                                    font=("SF Pro Display", 13, "bold"),
                                    padx=28, pady=12, relief=tk.FLAT, cursor="hand2",
                                    state=tk.DISABLED)
        self.submit_btn.pack(side=tk.LEFT)

        self.unknown_btn = tk.Button(btn_frame, text="❓ Mark as Unknown",
                                     command=self.mark_as_unknown,
                                     bg=self.colors.get("option_unknown", "#6366f1"),
                                     fg="white",
                                     font=("SF Pro Display", 13, "bold"),
                                     padx=28, pady=12, relief=tk.FLAT, cursor="hand2")
        self.unknown_btn.pack(side=tk.LEFT, padx=(15, 0))

        self.next_btn = tk.Button(btn_frame, text="Next Question  →",
                                  command=self.next_question,
                                  bg=self.colors["success"], fg="white",
                                  font=("SF Pro Display", 13, "bold"),
                                  padx=28, pady=12, relief=tk.FLAT, cursor="hand2")

        # Keyboard hints
        hint = tk.Label(btn_frame, text="⌨️  A/B/C/D to select  •  U for unknown  •  Enter to submit",
                       font=("SF Pro Display", 11),
                       bg=self.colors["bg"], fg=self.colors["text_muted"])
        hint.pack(side=tk.RIGHT)

    def setup_bindings(self):
        """Set up keyboard bindings."""
        self.window.bind("a", lambda e: self.select_option("A"))
        self.window.bind("b", lambda e: self.select_option("B"))
        self.window.bind("c", lambda e: self.select_option("C"))
        self.window.bind("d", lambda e: self.select_option("D"))
        self.window.bind("A", lambda e: self.select_option("A"))
        self.window.bind("B", lambda e: self.select_option("B"))
        self.window.bind("C", lambda e: self.select_option("C"))
        self.window.bind("D", lambda e: self.select_option("D"))
        self.window.bind("u", lambda e: self.mark_as_unknown())
        self.window.bind("U", lambda e: self.mark_as_unknown())
        self.window.bind("<Return>", lambda e: self.handle_enter())
        self.window.bind("<space>", lambda e: self.handle_enter())

    def on_option_enter(self, frame, btn, inner, badge):
        """Handle mouse enter on option."""
        if self.answered:
            return
        frame.config(bg=self.colors["option_hover"], highlightbackground=self.colors["primary"])
        btn.config(bg=self.colors["option_hover"])
        inner.config(bg=self.colors["option_hover"])

    def on_option_leave(self, frame, btn, inner, badge, letter):
        """Handle mouse leave on option."""
        if self.answered:
            return
        if self.selected_option == letter:
            frame.config(bg=self.colors["option_selected_bg"], highlightbackground=self.colors["option_selected"])
            btn.config(bg=self.colors["option_selected_bg"])
            inner.config(bg=self.colors["option_selected_bg"])
        else:
            frame.config(bg=self.colors["option_bg"], highlightbackground=self.colors["option_border"])
            btn.config(bg=self.colors["option_bg"])
            inner.config(bg=self.colors["option_bg"])

    def show_question(self):
        """Display the current question."""
        if self.current_index >= len(self.questions):
            self.show_results()
            return

        q = self.questions[self.current_index]
        self.answered = False
        self.selected_option = None
        self.option_order = []

        # Update progress
        self.progress_label.config(text=f"Question {self.current_index + 1} of {len(self.questions)}")
        self.topic_label.config(text=f"Topic: {q.get('topic', 'General')[:30]}")
        progress = self.current_index / len(self.questions)
        self.progress_bar_fill.place(x=0, y=0, relwidth=progress, height=6)

        # Update question
        self.question_number.config(text=f"  Q{self.current_index + 1}  ")
        self.question_text.config(text=q["question"])

        # Randomize options: shuffle the original options and map to new display letters
        original_options = [(letter, text) for letter, text in q["options"].items()]
        random.shuffle(original_options)

        # Create mapping from display letter (A,B,C,D) to original letter
        display_letters = ["A", "B", "C", "D"][:len(original_options)]
        self.letter_mapping = {}  # display_letter -> original_letter
        self.reverse_mapping = {}  # original_letter -> display_letter

        for i, (orig_letter, _) in enumerate(original_options):
            display_letter = display_letters[i]
            self.letter_mapping[display_letter] = orig_letter
            self.reverse_mapping[orig_letter] = display_letter

        # Store shuffled correct answer for this question display
        self.current_correct_display = self.reverse_mapping.get(q["correct_answer"], q["correct_answer"])

        # Update options with shuffled order
        for i, display_letter in enumerate(display_letters):
            btn = self.option_buttons[display_letter]
            orig_letter, text = original_options[i]
            btn.config(text=text,
                      bg=self.colors["option_bg"],
                      fg=self.colors["text"])
            btn.frame.config(bg=self.colors["option_bg"],
                           highlightbackground=self.colors["option_border"])
            btn.inner.config(bg=self.colors["option_bg"])
            btn.letter_badge.config(bg=self.colors["border"], fg=self.colors["text"])
            btn.frame.pack(fill=tk.X, pady=5)
            self.option_order.append(display_letter)

        # Hide unused option buttons
        for letter in ["A", "B", "C", "D"]:
            if letter not in display_letters:
                self.option_buttons[letter].frame.pack_forget()

        # Reset UI state
        self.feedback_label.pack_forget()
        self.next_btn.pack_forget()
        self.submit_btn.config(state=tk.DISABLED)
        self.submit_btn.pack(side=tk.LEFT)
        self.unknown_btn.pack(side=tk.LEFT, padx=(15, 0))

    def select_option(self, letter: str):
        """Select an option (letter is the display letter A/B/C/D)."""
        if self.answered:
            return

        # Check if this display letter is currently shown
        if letter not in self.option_order:
            return

        self.selected_option = letter

        for l, btn in self.option_buttons.items():
            if l not in self.option_order:
                continue
            if l == letter:
                btn.config(bg=self.colors["option_selected_bg"], fg="white")
                btn.frame.config(bg=self.colors["option_selected_bg"],
                               highlightbackground=self.colors["option_selected"])
                btn.inner.config(bg=self.colors["option_selected_bg"])
                btn.letter_badge.config(bg=self.colors["option_selected"], fg="white")
            else:
                btn.config(bg=self.colors["option_bg"], fg=self.colors["text"])
                btn.frame.config(bg=self.colors["option_bg"],
                               highlightbackground=self.colors["option_border"])
                btn.inner.config(bg=self.colors["option_bg"])
                btn.letter_badge.config(bg=self.colors["border"], fg=self.colors["text"])

        self.submit_btn.config(state=tk.NORMAL)

    def submit_answer(self):
        """Submit the selected answer."""
        if self.answered or not self.selected_option:
            return

        self.answered = True
        q = self.questions[self.current_index]

        # Convert display letter back to original letter for storage
        original_answer = self.letter_mapping.get(self.selected_option, self.selected_option)
        q["user_answer"] = original_answer

        # Compare using display letters (selected vs shuffled correct)
        is_correct = self.selected_option == self.current_correct_display

        if is_correct:
            self.score += 1
            self.results["correct"].append(self.current_index)
        else:
            self.results["incorrect"].append(self.current_index)

        self.score_label.config(text=f"{self.score}/{self.current_index + 1}")

        # Show correct/wrong styling using display letters
        for letter, btn in self.option_buttons.items():
            if letter not in self.option_order:
                continue
            if letter == self.current_correct_display:
                btn.config(bg=self.colors["option_correct_bg"], fg="white")
                btn.frame.config(bg=self.colors["option_correct_bg"],
                               highlightbackground=self.colors["option_correct"])
                btn.inner.config(bg=self.colors["option_correct_bg"])
                btn.letter_badge.config(bg=self.colors["option_correct"], fg="white")
            elif letter == self.selected_option and not is_correct:
                btn.config(bg=self.colors["option_wrong_bg"], fg="white")
                btn.frame.config(bg=self.colors["option_wrong_bg"],
                               highlightbackground=self.colors["option_wrong"])
                btn.inner.config(bg=self.colors["option_wrong_bg"])
                btn.letter_badge.config(bg=self.colors["option_wrong"], fg="white")
            else:
                btn.config(bg=self.colors["option_bg"], fg=self.colors["text_muted"])
                btn.frame.config(bg=self.colors["option_bg"],
                               highlightbackground=self.colors["option_border"])
                btn.inner.config(bg=self.colors["option_bg"])
                btn.letter_badge.config(bg=self.colors["border"], fg=self.colors["text_muted"])

        # Show feedback - use display letter for the correct answer message
        if is_correct:
            feedback = "✅ Correct!"
            self.feedback_label.config(fg=self.colors["success"])
        else:
            feedback = f"❌ Incorrect. The correct answer is {self.current_correct_display}."
            self.feedback_label.config(fg=self.colors["danger"])

        if q.get("explanation"):
            feedback += f"\n\n📖 {q['explanation']}"

        self.feedback_label.config(text=feedback)
        self.feedback_label.pack(pady=(15, 0))

        # Show next button
        self.submit_btn.pack_forget()
        self.unknown_btn.pack_forget()

        if self.current_index + 1 >= len(self.questions):
            self.next_btn.config(text="See Results  →")

        self.next_btn.pack(side=tk.LEFT)

    def mark_as_unknown(self):
        """Mark current question as unknown."""
        if self.answered:
            return

        self.answered = True
        q = self.questions[self.current_index]
        q["user_answer"] = "UNKNOWN"

        self.results["unknown"].append(self.current_index)

        # Show unknown styling (indigo) - use display letters
        for letter, btn in self.option_buttons.items():
            if letter not in self.option_order:
                continue
            if letter == self.current_correct_display:
                # Show correct answer
                btn.config(bg=self.colors["option_correct_bg"], fg="white")
                btn.frame.config(bg=self.colors["option_correct_bg"],
                               highlightbackground=self.colors["option_correct"])
                btn.inner.config(bg=self.colors["option_correct_bg"])
                btn.letter_badge.config(bg=self.colors["option_correct"], fg="white")
            else:
                btn.config(bg=self.colors["option_bg"], fg=self.colors["text_muted"])

        # Show feedback - use display letter for the correct answer message
        feedback = f"❓ Marked as Unknown. The correct answer is {self.current_correct_display}."
        if q.get("explanation"):
            feedback += f"\n\n📖 {q['explanation']}"

        self.feedback_label.config(text=feedback, fg=self.colors.get("option_unknown", "#6366f1"))
        self.feedback_label.pack(pady=(15, 0))

        # Show next button
        self.submit_btn.pack_forget()
        self.unknown_btn.pack_forget()

        if self.current_index + 1 >= len(self.questions):
            self.next_btn.config(text="See Results  →")

        self.next_btn.pack(side=tk.LEFT)

    def next_question(self):
        """Move to the next question."""
        self.current_index += 1
        self.show_question()

    def handle_enter(self):
        """Handle enter/space key press."""
        if not self.answered and self.selected_option:
            self.submit_answer()
        elif self.answered:
            self.next_question()

    def show_results(self):
        """Show comprehensive test results."""
        # Save test results
        save_comprehensive_test(
            self.test_id,
            self.questions,
            self.results,
            self.selected_topics,
            self.use_teacher_mind
        )

        # Open results window (use master as parent so it persists after test window closes)
        ComprehensiveTestResultsWindow(
            self.window.master,
            self.questions,
            self.results,
            self.selected_topics,
            self.use_teacher_mind,
            self.colors
        )

        self.window.destroy()


# ============================================================================
# RESULTS WINDOW
# ============================================================================

class ComprehensiveTestResultsWindow:
    """Results overview with correct/incorrect/unknown breakdown."""

    def __init__(self, parent, questions: List[Dict], results: Dict,
                 topics: List[str], use_teacher_mind: bool, colors: dict = None):
        self.window = tk.Toplevel(parent)
        self.window.title("📊 Test Results")
        self.window.geometry("950x750")

        self.colors = colors if colors else DARK_THEME
        self.window.configure(bg=self.colors["bg"])

        self.questions = questions
        self.results = results
        self.topics = topics
        self.use_teacher_mind = use_teacher_mind

        self.setup_ui()

    def setup_ui(self):
        """Set up the results UI."""
        total = len(self.questions)
        correct = len(self.results.get("correct", []))
        incorrect = len(self.results.get("incorrect", []))
        unknown = len(self.results.get("unknown", []))
        percentage = round(correct / total * 100, 1) if total > 0 else 0

        # Header
        header = tk.Frame(self.window, bg=self.colors["surface"])
        header.pack(fill=tk.X)

        header_inner = tk.Frame(header, bg=self.colors["surface"])
        header_inner.pack(fill=tk.X, padx=40, pady=25)

        # Emoji and message
        if percentage >= 80:
            emoji, message = "🎉", "Excellent work!"
        elif percentage >= 60:
            emoji, message = "👍", "Good job!"
        else:
            emoji, message = "📚", "Keep practicing!"

        title_row = tk.Frame(header_inner, bg=self.colors["surface"])
        title_row.pack(fill=tk.X)

        tk.Label(title_row, text=emoji,
                font=("SF Pro Display", 36),
                bg=self.colors["surface"]).pack(side=tk.LEFT, padx=(0, 15))

        title_text = tk.Frame(title_row, bg=self.colors["surface"])
        title_text.pack(side=tk.LEFT)

        tk.Label(title_text, text=f"{percentage:.0f}%",
                font=("SF Pro Display", 32, "bold"),
                bg=self.colors["surface"],
                fg=self.colors["success"] if percentage >= 60 else self.colors["warning"]).pack(anchor="w")

        tk.Label(title_text, text=message,
                font=("SF Pro Display", 14),
                bg=self.colors["surface"], fg=self.colors["text_muted"]).pack(anchor="w")

        # Score cards
        cards_row = tk.Frame(header_inner, bg=self.colors["surface"])
        cards_row.pack(fill=tk.X, pady=(20, 0))

        # Correct card
        self.create_stat_card(cards_row, "✓", "Correct", correct,
                             self.colors["success"], self.colors.get("success_bg", "#064e3b"))

        # Incorrect card
        self.create_stat_card(cards_row, "✗", "Incorrect", incorrect,
                             self.colors["danger"], self.colors.get("danger_bg", "#7f1d1d"))

        # Unknown card
        self.create_stat_card(cards_row, "❓", "Unknown", unknown,
                             self.colors.get("option_unknown", "#6366f1"),
                             self.colors.get("unknown_bg", "#312e81"))

        # Tabs
        tab_frame = tk.Frame(self.window, bg=self.colors["bg"])
        tab_frame.pack(fill=tk.X, padx=40, pady=(20, 10))

        self.active_tab = "all"
        self.tab_buttons = {}

        for tab_id, tab_label in [
            ("all", f"📋 All ({total})"),
            ("incorrect", f"❌ Incorrect ({incorrect})"),
            ("unknown", f"❓ Unknown ({unknown})")
        ]:
            btn = tk.Button(tab_frame, text=tab_label,
                           command=lambda t=tab_id: self.switch_tab(t),
                           font=("SF Pro Display", 11),
                           relief=tk.FLAT, cursor="hand2", padx=15, pady=6)
            btn.pack(side=tk.LEFT, padx=(0, 5))
            self.tab_buttons[tab_id] = btn

        # Content area
        self.content_frame = tk.Frame(self.window, bg=self.colors["bg"])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=(0, 10))

        self.switch_tab("all")

        # Bottom buttons
        btn_frame = tk.Frame(self.window, bg=self.colors["surface"])
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        btn_inner = tk.Frame(btn_frame, bg=self.colors["surface"])
        btn_inner.pack(fill=tk.X, padx=40, pady=15)

        weak_count = incorrect + unknown

        # Row 1: Primary actions
        row1 = tk.Frame(btn_inner, bg=self.colors["surface"])
        row1.pack(fill=tk.X, pady=(0, 10))

        if weak_count > 0:
            # Study weak areas
            study_btn = tk.Button(row1, text=f"📖 Study ({weak_count})",
                                 command=self.open_study_mode,
                                 bg=self.colors.get("option_unknown", "#6366f1"), fg="white",
                                 font=("SF Pro Display", 11, "bold"),
                                 padx=15, pady=8, relief=tk.FLAT, cursor="hand2")
            study_btn.pack(side=tk.LEFT, padx=(0, 8))

            # Quiz from wrong
            wrong_quiz_btn = tk.Button(row1, text="🔄 Quiz Wrong",
                                       command=self.create_quiz_from_wrong,
                                       bg=self.colors.get("warning", "#f59e0b"), fg="white",
                                       font=("SF Pro Display", 11, "bold"),
                                       padx=15, pady=8, relief=tk.FLAT, cursor="hand2")
            wrong_quiz_btn.pack(side=tk.LEFT, padx=(0, 8))

            # Targeted re-quiz
            requiz_count = get_targeted_requiz_count()
            requiz_btn = tk.Button(row1, text=f"🎯 Re-quiz List ({requiz_count})",
                                  command=self.start_targeted_requiz,
                                  bg=self.colors.get("danger", "#ef4444"), fg="white",
                                  font=("SF Pro Display", 11, "bold"),
                                  padx=15, pady=8, relief=tk.FLAT, cursor="hand2")
            requiz_btn.pack(side=tk.LEFT)

        close_btn = tk.Button(row1, text="Close",
                             command=self.window.destroy,
                             bg=self.colors["surface"], fg=self.colors["text"],
                             font=("SF Pro Display", 11),
                             padx=15, pady=8, relief=tk.FLAT, cursor="hand2")
        close_btn.pack(side=tk.RIGHT)

        # Row 2: Secondary actions
        if weak_count > 0:
            row2 = tk.Frame(btn_inner, bg=self.colors["surface"])
            row2.pack(fill=tk.X)

            # Bulk create flashcards
            flashcard_btn = tk.Button(row2, text=f"🃏 All Flashcards ({weak_count})",
                                     command=self.create_flashcards_from_mistakes,
                                     bg=self.colors.get("success", "#10b981"), fg="white",
                                     font=("SF Pro Display", 10),
                                     padx=12, pady=6, relief=tk.FLAT, cursor="hand2")
            flashcard_btn.pack(side=tk.LEFT, padx=(0, 8))

            # Summarize
            summarize_btn = tk.Button(row2, text="📊 Summarize",
                                     command=self.summarize_weak_areas,
                                     bg=self.colors.get("secondary", "#8b5cf6"), fg="white",
                                     font=("SF Pro Display", 10),
                                     padx=12, pady=6, relief=tk.FLAT, cursor="hand2")
            summarize_btn.pack(side=tk.LEFT, padx=(0, 8))

            # Export
            export_btn = tk.Button(row2, text="📄 Export",
                                  command=self.export_to_document,
                                  bg=self.colors.get("primary", "#3b82f6"), fg="white",
                                  font=("SF Pro Display", 10),
                                  padx=12, pady=6, relief=tk.FLAT, cursor="hand2")
            export_btn.pack(side=tk.LEFT)

    def create_stat_card(self, parent, icon: str, label: str, value: int,
                        fg_color: str, bg_color: str):
        """Create a stat card."""
        card = tk.Frame(parent, bg=bg_color, padx=20, pady=15)
        card.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(card, text=icon,
                font=("SF Pro Display", 20),
                bg=bg_color, fg=fg_color).pack(side=tk.LEFT, padx=(0, 10))

        text_frame = tk.Frame(card, bg=bg_color)
        text_frame.pack(side=tk.LEFT)

        tk.Label(text_frame, text=str(value),
                font=("SF Pro Display", 20, "bold"),
                bg=bg_color, fg=fg_color).pack(anchor="w")

        tk.Label(text_frame, text=label,
                font=("SF Pro Display", 11),
                bg=bg_color, fg=self.colors["text_muted"]).pack(anchor="w")

    def switch_tab(self, tab_id: str):
        """Switch between result tabs."""
        self.active_tab = tab_id

        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.config(bg=self.colors.get("option_unknown", "#6366f1"), fg="white")
            else:
                btn.config(bg=self.colors["surface"], fg=self.colors["text_muted"])

        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if tab_id == "all":
            self.show_all_questions()
        elif tab_id == "incorrect":
            self.show_filtered_questions(self.results.get("incorrect", []), "incorrect")
        elif tab_id == "unknown":
            self.show_filtered_questions(self.results.get("unknown", []), "unknown")

    def show_all_questions(self):
        """Show all questions summary."""
        canvas = tk.Canvas(self.content_frame, bg=self.colors["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.colors["bg"])

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw", width=850)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for i, q in enumerate(self.questions):
            user_ans = q.get("user_answer", "")

            if i in self.results.get("correct", []):
                icon, bg_color, fg_color = "✓", self.colors.get("success_bg", "#064e3b"), self.colors["success"]
            elif i in self.results.get("incorrect", []):
                icon, bg_color, fg_color = "✗", self.colors.get("danger_bg", "#7f1d1d"), self.colors["danger"]
            else:
                icon, bg_color, fg_color = "❓", self.colors.get("unknown_bg", "#312e81"), self.colors.get("option_unknown", "#6366f1")

            row = tk.Frame(scrollable, bg=bg_color)
            row.pack(fill=tk.X, pady=2, padx=5)
            row_inner = tk.Frame(row, bg=bg_color)
            row_inner.pack(fill=tk.X, padx=12, pady=8)

            tk.Label(row_inner, text=icon,
                    font=("SF Pro Display", 12, "bold"),
                    bg=bg_color, fg=fg_color).pack(side=tk.LEFT)

            preview = q.get('question', '')[:60] + "..." if len(q.get('question', '')) > 60 else q.get('question', '')
            tk.Label(row_inner, text=f"Q{i+1}: {preview}",
                    font=("SF Pro Display", 11),
                    bg=bg_color, fg=self.colors["text"], anchor="w").pack(side=tk.LEFT, padx=(10, 0))

    def show_filtered_questions(self, indices: List[int], question_type: str):
        """Show filtered questions (incorrect or unknown)."""
        if not indices:
            tk.Label(self.content_frame, text="🎉 None in this category!",
                    font=("SF Pro Display", 16),
                    bg=self.colors["bg"], fg=self.colors["success"]).pack(expand=True)
            return

        canvas = tk.Canvas(self.content_frame, bg=self.colors["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.colors["bg"])

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw", width=850)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        if question_type == "incorrect":
            bg_color = self.colors.get("danger_bg", "#7f1d1d")
            fg_color = self.colors["danger"]
        else:
            bg_color = self.colors.get("unknown_bg", "#312e81")
            fg_color = self.colors.get("option_unknown", "#6366f1")

        for idx in indices:
            q = self.questions[idx]

            card = tk.Frame(scrollable, bg=bg_color)
            card.pack(fill=tk.X, pady=8, padx=5)
            inner = tk.Frame(card, bg=bg_color)
            inner.pack(fill=tk.X, padx=15, pady=12)

            tk.Label(inner, text=f"Question {idx + 1} • {q.get('topic', 'General')[:25]}",
                    font=("SF Pro Display", 10, "bold"),
                    bg=bg_color, fg=fg_color).pack(anchor="w")

            tk.Label(inner, text=q.get('question', ''),
                    font=("SF Pro Display", 12),
                    bg=bg_color, fg=self.colors["text"],
                    wraplength=800, justify=tk.LEFT).pack(anchor="w", pady=(5, 10))

            user_ans = q.get('user_answer', '?')
            correct_ans = q.get('correct_answer', '?')
            options = q.get('options', {})

            if user_ans == "UNKNOWN":
                tk.Label(inner, text="Your answer: (Marked as Unknown)",
                        font=("SF Pro Display", 11),
                        bg=bg_color, fg=fg_color).pack(anchor="w")
            else:
                tk.Label(inner, text=f"Your answer: {user_ans}) {options.get(user_ans, 'N/A')}",
                        font=("SF Pro Display", 11),
                        bg=bg_color, fg=fg_color).pack(anchor="w")

            tk.Label(inner, text=f"Correct: {correct_ans}) {options.get(correct_ans, 'N/A')}",
                    font=("SF Pro Display", 11, "bold"),
                    bg=bg_color, fg=self.colors["success"]).pack(anchor="w", pady=(3, 0))

            if q.get('explanation'):
                tk.Frame(inner, bg=self.colors["border"], height=1).pack(fill=tk.X, pady=10)
                tk.Label(inner, text=q['explanation'],
                        font=("SF Pro Display", 11),
                        bg=bg_color, fg=self.colors["text_secondary"],
                        wraplength=800, justify=tk.LEFT).pack(anchor="w")

            # Show existing note if any
            q_hash = compute_question_hash(q.get("question", ""))
            existing_note = get_question_note(q_hash)
            if existing_note:
                tk.Frame(inner, bg=self.colors["border"], height=1).pack(fill=tk.X, pady=10)
                note_frame = tk.Frame(inner, bg=bg_color)
                note_frame.pack(fill=tk.X)
                tk.Label(note_frame, text="📋 Your note:",
                        font=("SF Pro Display", 10, "bold"),
                        bg=bg_color, fg=self.colors.get("warning", "#f59e0b")).pack(anchor="w")
                tk.Label(note_frame, text=existing_note,
                        font=("SF Pro Display", 11, "italic"),
                        bg=bg_color, fg=self.colors["text_muted"],
                        wraplength=800, justify=tk.LEFT).pack(anchor="w", pady=(3, 0))

            # Action buttons row
            actions_frame = tk.Frame(inner, bg=bg_color)
            actions_frame.pack(fill=tk.X, pady=(12, 0))

            # Create flashcard button
            flashcard_btn = tk.Button(
                actions_frame,
                text="🃏 Flashcard",
                command=lambda q=q: self.create_single_flashcard(q),
                bg=self.colors.get("success", "#10b981"), fg="white",
                font=("SF Pro Display", 10),
                padx=10, pady=5, relief=tk.FLAT, cursor="hand2"
            )
            flashcard_btn.pack(side=tk.LEFT, padx=(0, 8))

            # Add notes button
            notes_btn = tk.Button(
                actions_frame,
                text="📝 Note",
                command=lambda q=q, idx=idx: self.add_question_note(q, idx),
                bg=self.colors.get("secondary", "#8b5cf6"), fg="white",
                font=("SF Pro Display", 10),
                padx=10, pady=5, relief=tk.FLAT, cursor="hand2"
            )
            notes_btn.pack(side=tk.LEFT, padx=(0, 8))

            # Add to re-quiz button
            requiz_btn = tk.Button(
                actions_frame,
                text="🎯 Re-quiz",
                command=lambda q=q: self.add_to_requiz_list(q),
                bg=self.colors.get("primary", "#3b82f6"), fg="white",
                font=("SF Pro Display", 10),
                padx=10, pady=5, relief=tk.FLAT, cursor="hand2"
            )
            requiz_btn.pack(side=tk.LEFT)

    def create_single_flashcard(self, question: Dict):
        """Create a flashcard from a single question."""
        try:
            deck_name = f"Test Questions - {datetime.now().strftime('%Y-%m-%d')}"
            db = load_db()

            deck_id = None
            for did, deck in db.get("decks", {}).items():
                if deck.get("name") == deck_name:
                    deck_id = did
                    break

            if not deck_id:
                deck_id = create_deck(deck_name, "Individual Test Questions")

            front = question.get("question", "")
            correct = question.get("correct_answer", "")
            options = question.get("options", {})
            explanation = question.get("explanation", "")
            topic = question.get("topic", "General")

            back = f"**Answer:** {correct}) {options.get(correct, '')}\n\n"
            if explanation:
                back += f"**Explanation:** {explanation}\n\n"
            back += f"**Topic:** {topic}"

            add_card(deck_id, front, back)

            messagebox.showinfo(
                "Flashcard Created",
                f"Created flashcard in deck:\n'{deck_name}'"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create flashcard: {e}")

    def add_question_note(self, question: Dict, question_idx: int):
        """Open dialog to add/edit personal note for a question."""
        q_hash = compute_question_hash(question.get("question", ""))
        existing_note = get_question_note(q_hash) or ""

        note_dialog = tk.Toplevel(self.window)
        note_dialog.title("📝 Add Note")
        note_dialog.geometry("550x450")
        note_dialog.transient(self.window)
        note_dialog.configure(bg=self.colors["bg"])

        # Header
        header = tk.Frame(note_dialog, bg=self.colors["surface"])
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text=f"Note for Question {question_idx + 1}",
            font=("SF Pro Display", 14, "bold"),
            bg=self.colors["surface"], fg=self.colors["text"]
        ).pack(padx=20, pady=15)

        # Question preview
        preview = tk.Label(
            note_dialog,
            text=question.get("question", "")[:200] + ("..." if len(question.get("question", "")) > 200 else ""),
            font=("SF Pro Display", 11),
            bg=self.colors["bg"], fg=self.colors["text_muted"],
            wraplength=500, justify=tk.LEFT
        )
        preview.pack(padx=20, pady=(15, 10))

        # Hint
        hint = tk.Label(
            note_dialog,
            text="Why did you get this wrong? What should you remember?",
            font=("SF Pro Display", 10, "italic"),
            bg=self.colors["bg"], fg=self.colors.get("warning", "#f59e0b")
        )
        hint.pack(padx=20, pady=(0, 10))

        # Note text area
        note_text = tk.Text(
            note_dialog,
            font=("SF Pro Display", 12),
            bg=self.colors.get("card", "#1e1e2e"),
            fg=self.colors["text"],
            wrap=tk.WORD,
            height=8,
            padx=10, pady=10
        )
        note_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        note_text.insert("1.0", existing_note)
        note_text.focus_set()

        # Buttons
        btn_frame = tk.Frame(note_dialog, bg=self.colors["bg"])
        btn_frame.pack(fill=tk.X, padx=20, pady=15)

        def save_note():
            note = note_text.get("1.0", tk.END).strip()
            save_question_note(q_hash, note, {
                "question": question.get("question", ""),
                "topic": question.get("topic", ""),
                "correct_answer": question.get("correct_answer", "")
            })
            messagebox.showinfo("Saved", "Note saved!")
            note_dialog.destroy()
            # Refresh the current view
            self.switch_tab(self.active_tab)

        save_btn = tk.Button(
            btn_frame, text="Save Note",
            command=save_note,
            bg=self.colors.get("success", "#10b981"), fg="white",
            font=("SF Pro Display", 12, "bold"),
            padx=20, pady=8, relief=tk.FLAT, cursor="hand2"
        )
        save_btn.pack(side=tk.RIGHT)

        cancel_btn = tk.Button(
            btn_frame, text="Cancel",
            command=note_dialog.destroy,
            bg=self.colors["surface"], fg=self.colors["text"],
            font=("SF Pro Display", 12),
            padx=20, pady=8, relief=tk.FLAT, cursor="hand2"
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(0, 10))

    def add_to_requiz_list(self, question: Dict):
        """Add a question to the targeted re-quiz list."""
        if add_to_targeted_requiz(question):
            count = get_targeted_requiz_count()
            messagebox.showinfo("Added", f"Question added to re-quiz list!\n({count} questions in list)")
        else:
            messagebox.showinfo("Already Added", "This question is already in your re-quiz list.")

    def create_flashcards_from_mistakes(self):
        """Create flashcards from incorrect and unknown questions."""
        weak_indices = self.results.get("incorrect", []) + self.results.get("unknown", [])
        weak_questions = [self.questions[i] for i in weak_indices]

        if not weak_questions:
            messagebox.showinfo("No Mistakes", "No wrong answers to create flashcards from!")
            return

        try:
            # Create or find existing deck
            deck_name = f"Test Mistakes - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            db = load_db()

            # Check if deck exists
            deck_id = None
            for did, deck in db.get("decks", {}).items():
                if deck.get("name") == deck_name:
                    deck_id = did
                    break

            if not deck_id:
                deck_id = create_deck(deck_name, "Comprehensive Test Mistakes")

            # Add cards
            for q in weak_questions:
                front = q.get("question", "")
                correct = q.get("correct_answer", "")
                options = q.get("options", {})
                explanation = q.get("explanation", "")
                topic = q.get("topic", "General")

                back = f"**Answer:** {correct}) {options.get(correct, '')}\n\n"
                if explanation:
                    back += f"**Explanation:** {explanation}\n\n"
                back += f"**Topic:** {topic}"

                add_card(deck_id, front, back)

            messagebox.showinfo(
                "Flashcards Created",
                f"Created {len(weak_questions)} flashcard(s) in deck:\n'{deck_name}'\n\n"
                "Go to Flashcards tab to review them!"
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create flashcards: {e}")

    def summarize_weak_areas(self):
        """Generate AI summary of weak areas."""
        weak_indices = self.results.get("incorrect", []) + self.results.get("unknown", [])
        weak_questions = [self.questions[i] for i in weak_indices]

        if not weak_questions:
            messagebox.showinfo("No Mistakes", "No weak areas to summarize!")
            return

        # Group by topic
        by_topic = {}
        for q in weak_questions:
            topic = q.get("topic", "General")
            by_topic.setdefault(topic, []).append(q)

        # Build summary request
        questions_text = ""
        for topic, qs in by_topic.items():
            questions_text += f"\n## {topic} ({len(qs)} mistakes)\n"
            for q in qs:
                questions_text += f"- Q: {q.get('question', '')[:100]}...\n"
                questions_text += f"  Correct: {q.get('correct_answer', '')}\n"

        # Show loading window
        summary_window = tk.Toplevel(self.window)
        summary_window.title("📊 Weak Areas Summary")
        summary_window.geometry("700x600")
        summary_window.configure(bg=self.colors["bg"])

        # Header
        header = tk.Frame(summary_window, bg=self.colors["surface"])
        header.pack(fill=tk.X)
        tk.Label(header, text="📊 Analyzing Your Weak Areas...",
                font=("SF Pro Display", 18, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(padx=20, pady=15)

        # Content area
        from tkinter import scrolledtext
        content = scrolledtext.ScrolledText(
            summary_window,
            font=("Georgia", 12),
            bg=self.colors.get("card", "#1e1e2e"),
            fg=self.colors["text"],
            wrap=tk.WORD,
            padx=15, pady=15
        )
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        content.insert(tk.END, "Generating summary... Please wait.\n")

        def generate_summary():
            try:
                prompt = f"""Analyze these exam mistakes and provide a focused study summary.

The student got these questions wrong:
{questions_text}

Provide a helpful study guide with:

## Key Weak Areas
[List the 2-3 main topics/concepts the student struggles with]

## Common Mistakes Pattern
[What patterns do you see in the mistakes? What misconceptions might they have?]

## Quick Review
[For each weak topic, provide 2-3 bullet points of the key facts they need to remember]

## Study Recommendations
[Specific, actionable study tips - what should they focus on?]

Keep it concise and actionable. Use bullet points.
"""
                result = subprocess.run(
                    ["claude", "-p", prompt],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                summary = result.stdout if result.stdout else "Error generating summary."

                def update_ui():
                    content.delete(1.0, tk.END)
                    # Format markdown for better display
                    self._insert_formatted_text(content, summary)
                    # Update header
                    for widget in header.winfo_children():
                        widget.configure(text="📊 Your Weak Areas Summary")

                summary_window.after(0, update_ui)

            except Exception as e:
                def show_error():
                    content.delete(1.0, tk.END)
                    content.insert(tk.END, f"Error: {str(e)}")
                summary_window.after(0, show_error)

        threading.Thread(target=generate_summary, daemon=True).start()

    def _insert_formatted_text(self, text_widget, markdown_text: str):
        """Insert markdown text with proper formatting into a Text widget."""
        # Configure tags for formatting
        text_widget.tag_configure("h1", font=("SF Pro Display", 18, "bold"),
                                  foreground=self.colors.get("primary", "#3b82f6"),
                                  spacing1=20, spacing3=10)
        text_widget.tag_configure("h2", font=("SF Pro Display", 16, "bold"),
                                  foreground=self.colors.get("success", "#10b981"),
                                  spacing1=15, spacing3=8)
        text_widget.tag_configure("h3", font=("SF Pro Display", 14, "bold"),
                                  foreground=self.colors.get("warning", "#f59e0b"),
                                  spacing1=12, spacing3=6)
        text_widget.tag_configure("bold", font=("SF Pro Display", 12, "bold"))
        text_widget.tag_configure("bullet", lmargin1=20, lmargin2=35)
        text_widget.tag_configure("normal", font=("Georgia", 12),
                                  foreground=self.colors["text"])

        lines = markdown_text.split('\n')
        for line in lines:
            stripped = line.strip()

            # Handle headers
            if stripped.startswith('## '):
                text_widget.insert(tk.END, stripped[3:] + '\n', "h2")
            elif stripped.startswith('### '):
                text_widget.insert(tk.END, stripped[4:] + '\n', "h3")
            elif stripped.startswith('# '):
                text_widget.insert(tk.END, stripped[2:] + '\n', "h1")
            # Handle bullet points
            elif stripped.startswith('- '):
                # Remove ** markers for bold
                content = stripped[2:].replace('**', '')
                text_widget.insert(tk.END, '  • ' + content + '\n', "bullet")
            elif stripped.startswith('* '):
                content = stripped[2:].replace('**', '')
                text_widget.insert(tk.END, '  • ' + content + '\n', "bullet")
            # Handle numbered lists
            elif stripped and stripped[0].isdigit() and '. ' in stripped[:4]:
                idx = stripped.index('. ')
                content = stripped[idx+2:].replace('**', '')
                text_widget.insert(tk.END, stripped[:idx+2] + content + '\n', "bullet")
            # Handle horizontal rules
            elif stripped == '---' or stripped == '***':
                text_widget.insert(tk.END, '─' * 50 + '\n', "normal")
            # Regular text (remove ** markers)
            else:
                content = stripped.replace('**', '')
                if content:
                    text_widget.insert(tk.END, content + '\n', "normal")
                else:
                    text_widget.insert(tk.END, '\n')

    def export_to_document(self):
        """Export wrong answers to a markdown file."""
        weak_indices = self.results.get("incorrect", []) + self.results.get("unknown", [])
        weak_questions = [self.questions[i] for i in weak_indices]

        if not weak_questions:
            messagebox.showinfo("No Mistakes", "No wrong answers to export!")
            return

        # Build markdown content
        total = len(self.questions)
        correct = len(self.results.get("correct", []))
        incorrect = len(self.results.get("incorrect", []))
        unknown = len(self.results.get("unknown", []))
        percentage = round(correct / total * 100, 1) if total > 0 else 0

        content = f"""# Comprehensive Test Review - Weak Areas

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Score:** {correct}/{total} ({percentage}%)
**Incorrect:** {incorrect} | **Unknown:** {unknown}

---

"""
        # Group by topic
        by_topic = {}
        for idx in weak_indices:
            q = self.questions[idx]
            topic = q.get("topic", "General")
            by_topic.setdefault(topic, []).append((idx, q))

        for topic, questions in by_topic.items():
            content += f"## {topic}\n\n"

            for idx, q in questions:
                status = "❌ Incorrect" if idx in self.results.get("incorrect", []) else "❓ Unknown"
                content += f"### Question {idx + 1} ({status})\n\n"
                content += f"**Question:** {q.get('question', '')}\n\n"

                options = q.get("options", {})
                for letter in ["A", "B", "C", "D"]:
                    if letter in options:
                        marker = "→" if letter == q.get("correct_answer") else " "
                        content += f"{marker} **{letter})** {options[letter]}\n"

                content += f"\n**Your Answer:** {q.get('user_answer', 'N/A')}\n"
                content += f"**Correct Answer:** {q.get('correct_answer', '')}\n\n"

                if q.get("explanation"):
                    content += f"**Explanation:** {q['explanation']}\n\n"

                content += "---\n\n"

        # Save to file
        STORAGE_DIR.mkdir(exist_ok=True)
        filename = f"test_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = STORAGE_DIR / filename

        try:
            filepath.write_text(content)
            messagebox.showinfo(
                "Exported Successfully",
                f"Saved to:\n{filepath}\n\nYou can open this file in any text editor or markdown viewer."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

    def open_study_mode(self):
        """Open study mode for weak questions."""
        weak_indices = self.results.get("incorrect", []) + self.results.get("unknown", [])
        weak_questions = [self.questions[i] for i in weak_indices]

        if weak_questions:
            StudyModeWindow(self.window, weak_questions, self.colors)

    def create_quiz_from_wrong(self):
        """Create a new quiz using only the wrong questions."""
        weak_indices = self.results.get("incorrect", []) + self.results.get("unknown", [])
        weak_questions = [self.questions[i] for i in weak_indices]

        if not weak_questions:
            messagebox.showinfo("No Questions", "No wrong questions to quiz on!")
            return

        # Shuffle the questions
        random.shuffle(weak_questions)

        # Launch a mini quiz window with just these questions
        MiniQuizWindow(
            self.window.master,
            weak_questions,
            title="Quiz: Wrong Questions",
            colors=self.colors
        )

    def start_targeted_requiz(self):
        """Start a quiz with all questions in the targeted re-quiz list."""
        questions = get_targeted_requiz_questions()

        if not questions:
            messagebox.showinfo(
                "Empty List",
                "Your targeted re-quiz list is empty.\n\n"
                "Add questions by clicking '🎯 Re-quiz' on wrong questions."
            )
            return

        # Ask if user wants to clear after completing
        clear_after = messagebox.askyesno(
            "Clear After Quiz?",
            f"You have {len(questions)} questions in your re-quiz list.\n\n"
            "Do you want to clear the list after completing the quiz?"
        )

        # Shuffle the questions
        random.shuffle(questions)

        # Launch the quiz
        MiniQuizWindow(
            self.window.master,
            questions,
            title="Targeted Re-quiz",
            colors=self.colors,
            clear_requiz_after=clear_after
        )


# ============================================================================
# MINI QUIZ WINDOW (for re-quizzing wrong questions)
# ============================================================================

class MiniQuizWindow:
    """Lightweight quiz window for re-quizzing wrong questions."""

    def __init__(self, parent, questions: List[Dict], title: str = "Quiz",
                 colors: dict = None, clear_requiz_after: bool = False):
        self.window = tk.Toplevel(parent)
        self.window.title(f"📝 {title}")
        self.window.geometry("900x700")

        self.colors = colors if colors else DARK_THEME
        self.window.configure(bg=self.colors["bg"])

        self.questions = questions
        self.title = title
        self.current_index = 0
        self.score = 0
        self.answered = False
        self.selected_option = None
        self.clear_requiz_after = clear_requiz_after
        self.option_buttons = {}
        self.option_frames = {}

        self.setup_ui()
        self.show_question()

    def setup_ui(self):
        """Set up the quiz UI."""
        # Header
        header = tk.Frame(self.window, bg=self.colors["surface"])
        header.pack(fill=tk.X)

        header_inner = tk.Frame(header, bg=self.colors["surface"])
        header_inner.pack(fill=tk.X, padx=30, pady=15)

        tk.Label(header_inner, text=f"📝 {self.title}",
                font=("SF Pro Display", 16, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(side=tk.LEFT)

        self.score_label = tk.Label(header_inner, text="0/0",
                                   font=("SF Pro Display", 14, "bold"),
                                   bg=self.colors["surface"], fg=self.colors["success"])
        self.score_label.pack(side=tk.RIGHT)

        # Progress
        progress_frame = tk.Frame(self.window, bg=self.colors["bg"])
        progress_frame.pack(fill=tk.X, padx=30, pady=(15, 5))

        self.progress_label = tk.Label(progress_frame, text="Question 1",
                                       font=("SF Pro Display", 12),
                                       bg=self.colors["bg"], fg=self.colors["text_muted"])
        self.progress_label.pack(side=tk.LEFT)

        # Progress bar
        self.progress_bar = tk.Frame(self.window, bg=self.colors["border"], height=4)
        self.progress_bar.pack(fill=tk.X, padx=30, pady=(0, 20))
        self.progress_fill = tk.Frame(self.progress_bar, bg=self.colors["primary"], height=4)
        self.progress_fill.place(relwidth=0, relheight=1)

        # Question frame
        self.question_frame = tk.Frame(self.window, bg=self.colors["bg"])
        self.question_frame.pack(fill=tk.BOTH, expand=True, padx=30)

        # Bottom buttons frame
        self.btn_frame = tk.Frame(self.window, bg=self.colors["surface"])
        self.btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

    def show_question(self):
        """Display the current question."""
        if self.current_index >= len(self.questions):
            self.show_results()
            return

        # Clear previous content
        for widget in self.question_frame.winfo_children():
            widget.destroy()
        for widget in self.btn_frame.winfo_children():
            widget.destroy()

        self.answered = False
        self.selected_option = None

        q = self.questions[self.current_index]
        total = len(self.questions)

        # Update progress
        self.progress_label.config(text=f"Question {self.current_index + 1} of {total}")
        self.score_label.config(text=f"{self.score}/{self.current_index}")
        progress = (self.current_index / total)
        self.progress_fill.place(relwidth=progress, relheight=1)

        # Topic label
        topic = q.get("topic", "General")
        tk.Label(self.question_frame, text=topic[:40],
                font=("SF Pro Display", 11),
                bg=self.colors["bg"], fg=self.colors["text_muted"]).pack(anchor="w", pady=(0, 10))

        # Question text
        tk.Label(self.question_frame, text=q.get("question", ""),
                font=("Georgia", 14),
                bg=self.colors["bg"], fg=self.colors["text"],
                wraplength=800, justify=tk.LEFT).pack(anchor="w", pady=(0, 20))

        # Options (using Frame-based buttons for proper colors on macOS)
        self.option_buttons = {}
        self.option_frames = {}
        options = q.get("options", {})

        for letter in ["A", "B", "C", "D"]:
            if letter in options:
                # Frame acts as the button container
                frame = tk.Frame(
                    self.question_frame,
                    bg=self.colors.get("card", "#1e1e2e"),
                    cursor="hand2"
                )
                frame.pack(fill=tk.X, pady=4)

                # Label inside frame
                label = tk.Label(
                    frame,
                    text=f"  {letter})  {options[letter]}",
                    font=("SF Pro Display", 12),
                    bg=self.colors.get("card", "#1e1e2e"),
                    fg=self.colors["text"],
                    anchor="w",
                    padx=15, pady=12
                )
                label.pack(fill=tk.X)

                # Bind click events to both frame and label
                frame.bind("<Button-1>", lambda e, l=letter: self.select_option(l))
                label.bind("<Button-1>", lambda e, l=letter: self.select_option(l))

                # Hover effects
                def on_enter(e, f=frame, lb=label):
                    if f not in [self.option_frames.get(self.selected_option)]:
                        f.config(bg=self.colors.get("card_hover", "#2a2a3e"))
                        lb.config(bg=self.colors.get("card_hover", "#2a2a3e"))

                def on_leave(e, f=frame, lb=label, let=letter):
                    if let != self.selected_option:
                        f.config(bg=self.colors.get("card", "#1e1e2e"))
                        lb.config(bg=self.colors.get("card", "#1e1e2e"))

                frame.bind("<Enter>", on_enter)
                frame.bind("<Leave>", on_leave)
                label.bind("<Enter>", on_enter)
                label.bind("<Leave>", on_leave)

                self.option_frames[letter] = frame
                self.option_buttons[letter] = label

        # Feedback area
        self.feedback_label = tk.Label(self.question_frame, text="",
                                       font=("SF Pro Display", 12),
                                       bg=self.colors["bg"], fg=self.colors["text"])
        self.feedback_label.pack(anchor="w", pady=(15, 0))

        # Bottom buttons
        btn_inner = tk.Frame(self.btn_frame, bg=self.colors["surface"])
        btn_inner.pack(fill=tk.X, padx=30, pady=15)

        self.submit_btn = tk.Button(btn_inner, text="Submit Answer",
                                   command=self.submit_answer,
                                   bg=self.colors["primary"], fg="white",
                                   font=("SF Pro Display", 12, "bold"),
                                   padx=20, pady=10, relief=tk.FLAT, cursor="hand2",
                                   state=tk.DISABLED)
        self.submit_btn.pack(side=tk.LEFT)

        quit_btn = tk.Button(btn_inner, text="Quit",
                            command=self.window.destroy,
                            bg=self.colors["surface"], fg=self.colors["text"],
                            font=("SF Pro Display", 11),
                            padx=15, pady=10, relief=tk.FLAT, cursor="hand2")
        quit_btn.pack(side=tk.RIGHT)

    def select_option(self, letter: str):
        """Select an answer option."""
        if self.answered:
            return

        self.selected_option = letter

        # Reset all buttons (both frame and label)
        for l in self.option_buttons.keys():
            default_bg = self.colors.get("card", "#1e1e2e")
            self.option_frames[l].config(bg=default_bg)
            self.option_buttons[l].config(bg=default_bg)

        # Highlight selected
        self.option_frames[letter].config(bg=self.colors["primary"])
        self.option_buttons[letter].config(bg=self.colors["primary"])
        self.submit_btn.config(state=tk.NORMAL)

    def submit_answer(self):
        """Submit the selected answer."""
        if not self.selected_option or self.answered:
            return

        self.answered = True
        q = self.questions[self.current_index]
        correct = q.get("correct_answer", "")

        if self.selected_option == correct:
            self.score += 1
            self.feedback_label.config(
                text="✓ Correct!",
                fg=self.colors["success"]
            )
            success_bg = self.colors.get("success", "#10b981")
            self.option_frames[self.selected_option].config(bg=success_bg)
            self.option_buttons[self.selected_option].config(bg=success_bg)
        else:
            self.feedback_label.config(
                text=f"✗ Incorrect. The answer is {correct}.",
                fg=self.colors["danger"]
            )
            danger_bg = self.colors.get("danger", "#ef4444")
            self.option_frames[self.selected_option].config(bg=danger_bg)
            self.option_buttons[self.selected_option].config(bg=danger_bg)
            if correct in self.option_buttons:
                success_bg = self.colors.get("success", "#10b981")
                self.option_frames[correct].config(bg=success_bg)
                self.option_buttons[correct].config(bg=success_bg)

        # Show explanation
        if q.get("explanation"):
            exp_label = tk.Label(self.question_frame, text=f"\n{q['explanation']}",
                                font=("SF Pro Display", 11),
                                bg=self.colors["bg"], fg=self.colors["text_secondary"],
                                wraplength=800, justify=tk.LEFT)
            exp_label.pack(anchor="w")

        # Update submit button to next
        self.submit_btn.config(text="Next →", command=self.next_question)

    def next_question(self):
        """Go to the next question."""
        self.current_index += 1
        self.show_question()

    def show_results(self):
        """Show quiz results."""
        # Clear everything
        for widget in self.question_frame.winfo_children():
            widget.destroy()
        for widget in self.btn_frame.winfo_children():
            widget.destroy()

        total = len(self.questions)
        percentage = round(self.score / total * 100, 1) if total > 0 else 0

        # Update header
        self.progress_label.config(text="Quiz Complete!")
        self.score_label.config(text=f"{self.score}/{total}")
        self.progress_fill.place(relwidth=1, relheight=1)

        # Results display
        if percentage >= 80:
            emoji, message = "🎉", "Excellent!"
        elif percentage >= 60:
            emoji, message = "👍", "Good job!"
        else:
            emoji, message = "📚", "Keep practicing!"

        tk.Label(self.question_frame, text=emoji,
                font=("SF Pro Display", 48),
                bg=self.colors["bg"]).pack(pady=(40, 10))

        tk.Label(self.question_frame, text=f"{percentage:.0f}%",
                font=("SF Pro Display", 36, "bold"),
                bg=self.colors["bg"],
                fg=self.colors["success"] if percentage >= 60 else self.colors["warning"]).pack()

        tk.Label(self.question_frame, text=message,
                font=("SF Pro Display", 18),
                bg=self.colors["bg"], fg=self.colors["text_muted"]).pack(pady=(5, 20))

        tk.Label(self.question_frame, text=f"{self.score} correct out of {total} questions",
                font=("SF Pro Display", 14),
                bg=self.colors["bg"], fg=self.colors["text"]).pack()

        # Clear re-quiz list if requested
        if self.clear_requiz_after:
            clear_targeted_requiz()
            tk.Label(self.question_frame, text="✓ Re-quiz list cleared",
                    font=("SF Pro Display", 12),
                    bg=self.colors["bg"], fg=self.colors["text_muted"]).pack(pady=(20, 0))

        # Close button
        btn_inner = tk.Frame(self.btn_frame, bg=self.colors["surface"])
        btn_inner.pack(fill=tk.X, padx=30, pady=15)

        close_btn = tk.Button(btn_inner, text="Close",
                             command=self.window.destroy,
                             bg=self.colors["primary"], fg="white",
                             font=("SF Pro Display", 12, "bold"),
                             padx=30, pady=10, relief=tk.FLAT, cursor="hand2")
        close_btn.pack()


# ============================================================================
# STUDY MODE WINDOW
# ============================================================================

class StudyModeWindow:
    """Combined review mode for incorrect and unknown questions."""

    def __init__(self, parent, weak_questions: List[Dict], colors: dict = None):
        self.window = tk.Toplevel(parent)
        self.window.title("📖 Study Mode")
        self.window.geometry("950x750")

        self.colors = colors if colors else DARK_THEME
        self.window.configure(bg=self.colors["bg"])

        self.weak_questions = weak_questions
        self.current_index = 0
        self.showing_answer = False
        self.mode = "flashcard"  # flashcard, explain, requiz

        self.setup_ui()
        self.show_card()

    def setup_ui(self):
        """Set up the study mode UI."""
        # Header
        header = tk.Frame(self.window, bg=self.colors["surface"])
        header.pack(fill=tk.X)

        header_inner = tk.Frame(header, bg=self.colors["surface"])
        header_inner.pack(fill=tk.X, padx=40, pady=20)

        tk.Label(header_inner, text="📖 Study Mode",
                font=("SF Pro Display", 20, "bold"),
                bg=self.colors["surface"], fg=self.colors["text"]).pack(side=tk.LEFT)

        # Mode buttons
        mode_frame = tk.Frame(header_inner, bg=self.colors["surface"])
        mode_frame.pack(side=tk.RIGHT)

        self.mode_buttons = {}
        for mode_id, mode_label in [("flashcard", "🃏 Flashcard"), ("explain", "💡 Explain"), ("requiz", "🔄 Re-Quiz")]:
            btn = tk.Button(mode_frame, text=mode_label,
                           command=lambda m=mode_id: self.switch_mode(m),
                           font=("SF Pro Display", 11),
                           relief=tk.FLAT, cursor="hand2", padx=12, pady=6)
            btn.pack(side=tk.LEFT, padx=(5, 0))
            self.mode_buttons[mode_id] = btn

        # Progress
        progress_frame = tk.Frame(self.window, bg=self.colors["bg"])
        progress_frame.pack(fill=tk.X, padx=40, pady=(15, 0))

        self.progress_label = tk.Label(progress_frame,
                                       text=f"Card 1 of {len(self.weak_questions)}",
                                       font=("SF Pro Display", 12),
                                       bg=self.colors["bg"], fg=self.colors["text_muted"])
        self.progress_label.pack(side=tk.LEFT)

        # Content area
        self.content_frame = tk.Frame(self.window, bg=self.colors["card"],
                                     highlightbackground=self.colors["border"],
                                     highlightthickness=1)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

        # Bottom buttons
        btn_frame = tk.Frame(self.window, bg=self.colors["bg"])
        btn_frame.pack(fill=tk.X, padx=40, pady=(0, 20))

        self.action_btn = tk.Button(btn_frame, text="Show Answer",
                                    command=self.toggle_answer,
                                    bg=self.colors.get("option_unknown", "#6366f1"), fg="white",
                                    font=("SF Pro Display", 13, "bold"),
                                    padx=28, pady=12, relief=tk.FLAT, cursor="hand2")
        self.action_btn.pack(side=tk.LEFT)

        # Navigation
        nav_frame = tk.Frame(btn_frame, bg=self.colors["bg"])
        nav_frame.pack(side=tk.RIGHT)

        self.prev_btn = tk.Button(nav_frame, text="← Previous",
                                 command=self.prev_card,
                                 bg=self.colors["surface"], fg=self.colors["text"],
                                 font=("SF Pro Display", 12),
                                 padx=15, pady=10, relief=tk.FLAT, cursor="hand2")
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.next_btn = tk.Button(nav_frame, text="Next →",
                                 command=self.next_card,
                                 bg=self.colors["success"], fg="white",
                                 font=("SF Pro Display", 12, "bold"),
                                 padx=15, pady=10, relief=tk.FLAT, cursor="hand2")
        self.next_btn.pack(side=tk.LEFT)

        # Keyboard bindings
        self.window.bind("<space>", lambda e: self.toggle_answer())
        self.window.bind("<Return>", lambda e: self.next_card())
        self.window.bind("<Left>", lambda e: self.prev_card())
        self.window.bind("<Right>", lambda e: self.next_card())

        self.switch_mode("flashcard")

    def switch_mode(self, mode: str):
        """Switch between study modes."""
        self.mode = mode

        for mid, btn in self.mode_buttons.items():
            if mid == mode:
                btn.config(bg=self.colors.get("option_unknown", "#6366f1"), fg="white")
            else:
                btn.config(bg=self.colors["surface"], fg=self.colors["text_muted"])

        if mode == "flashcard":
            self.action_btn.config(text="Show Answer", command=self.toggle_answer)
            self.showing_answer = False
            self.show_card()
        elif mode == "explain":
            self.action_btn.config(text="Get Explanation", command=self.get_explanation)
            self.show_explain_mode()
        elif mode == "requiz":
            self.action_btn.config(text="Generate New Questions", command=self.generate_requiz)
            self.show_requiz_mode()

    def show_card(self):
        """Show current flashcard."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if self.current_index >= len(self.weak_questions):
            self.current_index = 0

        q = self.weak_questions[self.current_index]
        self.progress_label.config(text=f"Card {self.current_index + 1} of {len(self.weak_questions)}")

        inner = tk.Frame(self.content_frame, bg=self.colors["card"])
        inner.pack(expand=True, fill=tk.BOTH, padx=30, pady=30)

        # Topic badge
        topic_badge = tk.Label(inner, text=f"📚 {q.get('topic', 'General')[:30]}",
                              font=("SF Pro Display", 11),
                              bg=self.colors["surface"], fg=self.colors["text_muted"],
                              padx=10, pady=4)
        topic_badge.pack(anchor="w")

        # Question
        tk.Label(inner, text=q.get("question", ""),
                font=("Georgia", 16),
                bg=self.colors["card"], fg=self.colors["text"],
                wraplength=800, justify=tk.LEFT).pack(anchor="w", pady=(20, 30))

        if self.showing_answer:
            # Divider
            tk.Frame(inner, bg=self.colors["border"], height=2).pack(fill=tk.X, pady=15)

            # Correct answer
            correct = q.get("correct_answer", "")
            options = q.get("options", {})
            tk.Label(inner, text=f"✅ Correct Answer: {correct}) {options.get(correct, '')}",
                    font=("SF Pro Display", 14, "bold"),
                    bg=self.colors["card"], fg=self.colors["success"],
                    wraplength=800, justify=tk.LEFT).pack(anchor="w", pady=(10, 15))

            # Explanation
            if q.get("explanation"):
                tk.Label(inner, text="📖 Explanation:",
                        font=("SF Pro Display", 12, "bold"),
                        bg=self.colors["card"], fg=self.colors["text_muted"]).pack(anchor="w")
                tk.Label(inner, text=q["explanation"],
                        font=("SF Pro Display", 12),
                        bg=self.colors["card"], fg=self.colors["text_secondary"],
                        wraplength=800, justify=tk.LEFT).pack(anchor="w", pady=(5, 0))

            self.action_btn.config(text="Hide Answer")
        else:
            self.action_btn.config(text="Show Answer")

    def toggle_answer(self):
        """Toggle answer visibility in flashcard mode."""
        if self.mode != "flashcard":
            return
        self.showing_answer = not self.showing_answer
        self.show_card()

    def show_explain_mode(self):
        """Show explanation mode UI."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        q = self.weak_questions[self.current_index]
        self.progress_label.config(text=f"Question {self.current_index + 1} of {len(self.weak_questions)}")

        inner = tk.Frame(self.content_frame, bg=self.colors["card"])
        inner.pack(expand=True, fill=tk.BOTH, padx=30, pady=30)

        tk.Label(inner, text="💡 Deep Explanation Mode",
                font=("SF Pro Display", 14, "bold"),
                bg=self.colors["card"], fg=self.colors.get("option_unknown", "#6366f1")).pack(anchor="w")

        tk.Label(inner, text=q.get("question", ""),
                font=("Georgia", 15),
                bg=self.colors["card"], fg=self.colors["text"],
                wraplength=800, justify=tk.LEFT).pack(anchor="w", pady=(20, 20))

        tk.Label(inner, text="Click 'Get Explanation' to receive a detailed breakdown from Claude.",
                font=("SF Pro Display", 12),
                bg=self.colors["card"], fg=self.colors["text_muted"]).pack(anchor="w")

        # Explanation will be added here
        self.explain_content = tk.Frame(inner, bg=self.colors["card"])
        self.explain_content.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

    def get_explanation(self):
        """Get deep explanation from Claude."""
        q = self.weak_questions[self.current_index]

        self.action_btn.config(state=tk.DISABLED, text="Generating...")

        def _generate():
            try:
                prompt = f"""Explain this {subject_config.SUBJECT_NAME} concept in detail:

Question: {q.get('question', '')}
Correct Answer: {q.get('correct_answer', '')}) {q.get('options', {}).get(q.get('correct_answer', ''), '')}
Topic: {q.get('topic', subject_config.SUBJECT_NAME)}

Provide a clear, educational explanation that covers:
1. **Why the correct answer is right** - detailed explanation
2. **Key concept to remember** - the core principle being tested
3. **Common pitfalls** - what mistakes students often make
4. **Memory tip** - a helpful way to remember this

Keep it concise but thorough. Use simple language."""

                result = subprocess.run(
                    ["claude", "-p", prompt],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    self.window.after(0, lambda: self.show_explanation(result.stdout))
                else:
                    self.window.after(0, lambda: self.show_explanation("Error generating explanation."))

            except Exception as e:
                self.window.after(0, lambda: self.show_explanation(f"Error: {e}"))

        thread = threading.Thread(target=_generate, daemon=True)
        thread.start()

    def show_explanation(self, text: str):
        """Display the generated explanation."""
        self.action_btn.config(state=tk.NORMAL, text="Get Explanation")

        for widget in self.explain_content.winfo_children():
            widget.destroy()

        # Create scrollable text area
        text_widget = tk.Text(self.explain_content,
                             font=("SF Pro Display", 12),
                             bg=self.colors["surface"],
                             fg=self.colors["text"],
                             wrap=tk.WORD,
                             padx=15, pady=15,
                             relief=tk.FLAT)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert("1.0", text)
        text_widget.config(state=tk.DISABLED)

    def show_requiz_mode(self):
        """Show re-quiz mode UI."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        inner = tk.Frame(self.content_frame, bg=self.colors["card"])
        inner.pack(expand=True, fill=tk.BOTH, padx=30, pady=30)

        tk.Label(inner, text="🔄 Re-Quiz Mode",
                font=("SF Pro Display", 14, "bold"),
                bg=self.colors["card"], fg=self.colors.get("option_unknown", "#6366f1")).pack(anchor="w")

        tk.Label(inner, text="Generate new questions on the concepts you missed.",
                font=("SF Pro Display", 12),
                bg=self.colors["card"], fg=self.colors["text_muted"]).pack(anchor="w", pady=(10, 20))

        # Show topics that will be tested
        topics = list(set(q.get("topic", "General") for q in self.weak_questions))
        tk.Label(inner, text=f"Topics to review: {', '.join(topics[:5])}{'...' if len(topics) > 5 else ''}",
                font=("SF Pro Display", 11),
                bg=self.colors["card"], fg=self.colors["text_secondary"]).pack(anchor="w")

        self.requiz_content = tk.Frame(inner, bg=self.colors["card"])
        self.requiz_content.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

    def generate_requiz(self):
        """Generate new questions for weak concepts."""
        self.action_btn.config(state=tk.DISABLED, text="Generating...")

        # Extract concepts from weak questions
        topics = list(set(q.get("topic", "General") for q in self.weak_questions))[:3]

        def _generate():
            try:
                all_new_questions = []

                for topic in topics:
                    contexts = retrieve_context_smart(topic, n_results=5)
                    context_text = "\n\n".join([ctx["content"] for ctx in contexts])

                    prompt = f"""Generate 3 NEW multiple choice questions about: {topic}

Context:
{context_text[:3000]}

These should be DIFFERENT from typical questions - test deeper understanding.

Format:
**Q1:** [Question]
A) ... B) ... C) ... D) ...
**Answer:** [Letter]
**Explanation:** [Brief explanation]"""

                    result = subprocess.run(
                        ["claude", "-p", prompt],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    if result.returncode == 0:
                        questions = parse_quiz_from_claude(result.stdout)
                        for q in questions:
                            q["topic"] = topic
                        all_new_questions.extend(questions)

                self.window.after(0, lambda: self.show_requiz_questions(all_new_questions))

            except Exception as e:
                self.window.after(0, lambda: self.show_requiz_questions([]))

        thread = threading.Thread(target=_generate, daemon=True)
        thread.start()

    def show_requiz_questions(self, questions: List[Dict]):
        """Display the generated re-quiz questions."""
        self.action_btn.config(state=tk.NORMAL, text="Generate New Questions")

        for widget in self.requiz_content.winfo_children():
            widget.destroy()

        if not questions:
            tk.Label(self.requiz_content, text="No questions generated. Try again.",
                    font=("SF Pro Display", 12),
                    bg=self.colors["card"], fg=self.colors["text_muted"]).pack()
            return

        tk.Label(self.requiz_content, text=f"Generated {len(questions)} new questions!",
                font=("SF Pro Display", 12, "bold"),
                bg=self.colors["card"], fg=self.colors["success"]).pack(anchor="w", pady=(0, 15))

        # Show questions in scrollable area
        canvas = tk.Canvas(self.requiz_content, bg=self.colors["card"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.requiz_content, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.colors["card"])

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw", width=800)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for i, q in enumerate(questions):
            card = tk.Frame(scrollable, bg=self.colors["surface"])
            card.pack(fill=tk.X, pady=8)
            inner = tk.Frame(card, bg=self.colors["surface"])
            inner.pack(fill=tk.X, padx=15, pady=12)

            tk.Label(inner, text=f"Q{i+1}: {q.get('question', '')[:100]}...",
                    font=("SF Pro Display", 11),
                    bg=self.colors["surface"], fg=self.colors["text"],
                    wraplength=750, justify=tk.LEFT).pack(anchor="w")

            tk.Label(inner, text=f"Answer: {q.get('correct_answer', '')}",
                    font=("SF Pro Display", 10),
                    bg=self.colors["surface"], fg=self.colors["success"]).pack(anchor="w", pady=(5, 0))

    def prev_card(self):
        """Go to previous card."""
        if self.current_index > 0:
            self.current_index -= 1
            self.showing_answer = False
            if self.mode == "flashcard":
                self.show_card()
            elif self.mode == "explain":
                self.show_explain_mode()

    def next_card(self):
        """Go to next card."""
        if self.current_index < len(self.weak_questions) - 1:
            self.current_index += 1
            self.showing_answer = False
            if self.mode == "flashcard":
                self.show_card()
            elif self.mode == "explain":
                self.show_explain_mode()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def open_comprehensive_test(parent, study_guide: dict, colors: dict = None,
                           timer_ref=None):
    """Open the comprehensive test topic selection dialog."""
    def on_start(topics, use_teacher_mind):
        ComprehensiveTestWindow(parent, topics, use_teacher_mind, colors, timer_ref)

    TopicSelectionDialog(parent, study_guide, colors, on_start)
