#!/usr/bin/env python3
"""
Interactive Quiz System with scoring and review
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import re
import random
from pathlib import Path
from datetime import datetime
from typing import Optional
import uuid

from themes import DARK_THEME

# Database file
QUIZ_DB_FILE = Path(__file__).parent / "quiz_history.json"


def load_quiz_db() -> dict:
    """Load quiz history database."""
    if QUIZ_DB_FILE.exists():
        try:
            return json.loads(QUIZ_DB_FILE.read_text())
        except:
            pass
    return {"quizzes": {}, "stats": {"total_quizzes": 0, "total_correct": 0, "total_questions": 0}}


def save_quiz_db(db: dict):
    """Save quiz history."""
    QUIZ_DB_FILE.write_text(json.dumps(db, indent=2, default=str))


def parse_quiz_from_claude(text: str) -> list:
    """
    Parse Claude's quiz output into structured questions.
    Returns list of question dicts.
    """
    questions = []

    # Split by question markers - match **Q1:** or **Question 1:** etc.
    question_pattern = r'\*\*Q(?:uestion)?\s*(\d+)[:\.]?\*\*'
    parts = re.split(question_pattern, text, flags=re.IGNORECASE)

    # Process pairs (number, content)
    for i in range(1, len(parts), 2):
        if i + 1 >= len(parts):
            break

        q_num = parts[i]
        q_content = parts[i + 1]

        # Find where the answer section starts to limit option parsing
        answer_section_match = re.search(r'\*\*(?:Correct\s*)?Answer', q_content, re.IGNORECASE)
        if answer_section_match:
            options_section = q_content[:answer_section_match.start()]
            answer_section = q_content[answer_section_match.start():]
        else:
            options_section = q_content
            answer_section = ""

        # Extract question text (before options A/B/C/D)
        q_text_match = re.match(r'\s*(.+?)(?=\n\s*A[)\.])', options_section, re.DOTALL)
        if not q_text_match:
            continue
        question_text = q_text_match.group(1).strip()

        # Extract options - each option ends at the next option letter or end of options section
        options = {}

        # Match A) through D) more precisely
        for letter in ['A', 'B', 'C', 'D']:
            # Pattern: letter followed by ) or . then the option text
            pattern = rf'{letter}[)\.][ \t]*(.+?)(?=\n\s*[B-D][)\.]\s|\n\s*\*\*|$)'
            if letter == 'D':
                pattern = rf'D[)\.][ \t]*(.+?)(?=\n\s*\*\*|$)'
            elif letter == 'C':
                pattern = rf'C[)\.][ \t]*(.+?)(?=\n\s*D[)\.]\s|\n\s*\*\*|$)'
            elif letter == 'B':
                pattern = rf'B[)\.][ \t]*(.+?)(?=\n\s*C[)\.]\s|\n\s*\*\*|$)'
            elif letter == 'A':
                pattern = rf'A[)\.][ \t]*(.+?)(?=\n\s*B[)\.]\s|\n\s*\*\*|$)'

            match = re.search(pattern, options_section, re.DOTALL | re.IGNORECASE)
            if match:
                opt_text = match.group(1).strip()
                # Clean up - remove trailing newlines and extra whitespace
                opt_text = re.sub(r'\n+', ' ', opt_text).strip()
                if opt_text:
                    options[letter] = opt_text

        if len(options) < 2:
            continue

        # Extract correct answer from answer section
        answer_match = re.search(r'\*\*(?:Correct\s*)?Answer[:\s]*\*\*\s*([A-D])', answer_section, re.IGNORECASE)
        if not answer_match:
            answer_match = re.search(r'Answer[:\s]*([A-D])', answer_section, re.IGNORECASE)
        if not answer_match:
            # Try finding just a standalone letter after "Answer"
            answer_match = re.search(r'([A-D])\s*[-–—]', answer_section)

        correct_answer = answer_match.group(1).upper() if answer_match else None

        # Extract explanation
        explanation_match = re.search(r'\*\*Explanation[:\s]*\*\*\s*(.+?)(?=\n\n\*\*Q|\n---|\Z)', answer_section, re.DOTALL | re.IGNORECASE)
        if not explanation_match:
            # Try alternative: text after the answer letter and dash
            explanation_match = re.search(r'[A-D]\s*[-–—]\s*(.+?)(?=\n\n|\n---|\Z)', answer_section, re.DOTALL)
        explanation = explanation_match.group(1).strip() if explanation_match else ""
        # Clean up explanation
        explanation = re.sub(r'\n+', ' ', explanation).strip()

        if correct_answer and options:
            questions.append({
                "id": str(uuid.uuid4())[:8],
                "number": int(q_num),
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "explanation": explanation,
                "user_answer": None
            })

    return questions


def save_quiz_result(topic: str, questions: list, score: int, total: int):
    """Save quiz result to history."""
    db = load_quiz_db()

    quiz_id = str(uuid.uuid4())[:8]
    db["quizzes"][quiz_id] = {
        "id": quiz_id,
        "topic": topic,
        "date": datetime.now().isoformat(),
        "score": score,
        "total": total,
        "percentage": round(score / total * 100, 1) if total > 0 else 0,
        "questions": questions
    }

    db["stats"]["total_quizzes"] += 1
    db["stats"]["total_correct"] += score
    db["stats"]["total_questions"] += total

    save_quiz_db(db)
    return quiz_id


class QuizWindow:
    """Interactive quiz window with ABCD answers and modern design."""

    def __init__(self, parent, questions: list, topic: str = "Statistics", timer_ref=None, colors=None):
        self.timer_ref = timer_ref  # Reference to main app for timer state
        self.window = tk.Toplevel(parent)
        self.window.title("📝 Quiz Time!")
        self.window.geometry("950x750")

        # Use passed colors or default to dark theme
        self.colors = colors if colors else DARK_THEME

        self.window.configure(bg=self.colors["bg"])

        self.questions = questions
        self.topic = topic
        self.on_complete_callback = None
        self.current_index = 0
        self.score = 0
        self.answered = False
        self.selected_option = None
        self.selected_index = 0  # For arrow key navigation
        self.option_buttons = {}
        self.option_order = []  # Track available options
        self.letter_mapping = {}  # display_letter -> original_letter
        self.reverse_mapping = {}  # original_letter -> display_letter
        self.current_correct_display = None  # Correct answer in display letter

        self.setup_ui()
        self.create_floating_mini_timer()
        self.show_question()

        # Keyboard bindings - letters
        self.window.bind("a", lambda e: self.select_option("A"))
        self.window.bind("b", lambda e: self.select_option("B"))
        self.window.bind("c", lambda e: self.select_option("C"))
        self.window.bind("d", lambda e: self.select_option("D"))
        self.window.bind("A", lambda e: self.select_option("A"))
        self.window.bind("B", lambda e: self.select_option("B"))
        self.window.bind("C", lambda e: self.select_option("C"))
        self.window.bind("D", lambda e: self.select_option("D"))
        self.window.bind("<Return>", lambda e: self.handle_enter())
        self.window.bind("<space>", lambda e: self.handle_enter())

        # Arrow key navigation
        self.window.bind("<Up>", lambda e: self.navigate_options(-1))
        self.window.bind("<Down>", lambda e: self.navigate_options(1))
        self.window.bind("<Left>", lambda e: self.navigate_options(-1))
        self.window.bind("<Right>", lambda e: self.navigate_options(1))

    def create_floating_mini_timer(self):
        """Create a subtle floating mini-timer in top-right corner."""
        self.mini_timer_frame = tk.Frame(self.window, bg="#2d2d3a")
        self.mini_timer_frame.place(relx=1.0, rely=0, anchor="ne", x=-25, y=20)

        inner = tk.Frame(self.mini_timer_frame, bg="#2d2d3a")
        inner.pack(padx=10, pady=6)

        self.mini_status_dot = tk.Label(inner, text="●",
                                        font=("SF Pro Display", 8),
                                        bg="#2d2d3a",
                                        fg="#6b7280")
        self.mini_status_dot.pack(side=tk.LEFT, padx=(0, 5))

        self.mini_timer_label = tk.Label(inner, text="--:--",
                                         font=("Menlo", 13),
                                         bg="#2d2d3a",
                                         fg="#9ca3af")
        self.mini_timer_label.pack(side=tk.LEFT)

        self.update_mini_timer()

    def update_mini_timer(self):
        """Update the floating mini-timer display from main app."""
        if not hasattr(self, 'mini_timer_label'):
            return

        try:
            if not self.window.winfo_exists():
                return
        except:
            return

        if self.timer_ref:
            try:
                time_remaining = self.timer_ref.time_remaining
                timer_running = self.timer_ref.timer_running
                is_break = self.timer_ref.is_break_time

                minutes = time_remaining // 60
                seconds = time_remaining % 60
                self.mini_timer_label.config(text=f"{minutes:02d}:{seconds:02d}")

                if timer_running:
                    if is_break:
                        self.mini_status_dot.config(fg="#10b981")
                        self.mini_timer_label.config(fg="#6ee7b7")
                    else:
                        self.mini_status_dot.config(fg="#8b5cf6")
                        self.mini_timer_label.config(fg="#c4b5fd")
                else:
                    self.mini_status_dot.config(fg="#6b7280")
                    self.mini_timer_label.config(fg="#9ca3af")
            except:
                pass

        self.window.after(500, self.update_mini_timer)

    def setup_ui(self):
        """Set up the quiz UI with modern design."""
        # ═══════════════════════════════════════════════════════════
        # HEADER - Clean, minimal
        # ═══════════════════════════════════════════════════════════
        header = tk.Frame(self.window, bg=self.colors["surface"])
        header.pack(fill=tk.X)

        header_inner = tk.Frame(header, bg=self.colors["surface"])
        header_inner.pack(fill=tk.X, padx=40, pady=20)

        # Left: Title with accent bar
        title_row = tk.Frame(header_inner, bg=self.colors["surface"])
        title_row.pack(side=tk.LEFT)

        accent_bar = tk.Frame(title_row, bg=self.colors["accent"], width=4)
        accent_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        self.title_label = tk.Label(title_row, text=f"{self.topic} Quiz",
                                    font=("SF Pro Display", 20, "bold"),
                                    bg=self.colors["surface"], fg=self.colors["text"])
        self.title_label.pack(side=tk.LEFT)

        # Right: Score display
        score_frame = tk.Frame(header_inner, bg=self.colors["surface"])
        score_frame.pack(side=tk.RIGHT)

        tk.Label(score_frame, text="Score",
                font=("SF Pro Display", 11),
                bg=self.colors["surface"], fg=self.colors["text_muted"]).pack(anchor="e")

        self.score_label = tk.Label(score_frame, text="0/0",
                                    font=("SF Pro Display", 24, "bold"),
                                    bg=self.colors["surface"], fg=self.colors["success"])
        self.score_label.pack(anchor="e")

        # ═══════════════════════════════════════════════════════════
        # PROGRESS BAR - Full width, subtle
        # ═══════════════════════════════════════════════════════════
        progress_container = tk.Frame(self.window, bg=self.colors["bg"])
        progress_container.pack(fill=tk.X, padx=40, pady=(15, 0))

        progress_row = tk.Frame(progress_container, bg=self.colors["bg"])
        progress_row.pack(fill=tk.X)

        self.progress_label = tk.Label(progress_row,
                                       text=f"Question 1 of {len(self.questions)}",
                                       font=("SF Pro Display", 12),
                                       bg=self.colors["bg"], fg=self.colors["text_muted"])
        self.progress_label.pack(side=tk.LEFT)

        # Custom progress bar
        self.progress_bar_container = tk.Frame(progress_row, bg=self.colors["border"], height=6)
        self.progress_bar_container.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(20, 0))
        self.progress_bar_container.pack_propagate(False)

        self.progress_bar_fill = tk.Frame(self.progress_bar_container, bg=self.colors["accent"], height=6)
        self.progress_bar_fill.place(x=0, y=0, relwidth=0, height=6)

        # ═══════════════════════════════════════════════════════════
        # QUESTION CARD - Main content area
        # ═══════════════════════════════════════════════════════════
        self.question_frame = tk.Frame(self.window, bg=self.colors["card"],
                                       highlightbackground=self.colors["border"],
                                       highlightthickness=1)
        self.question_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

        # Question content
        question_inner = tk.Frame(self.question_frame, bg=self.colors["card"])
        question_inner.pack(fill=tk.X, padx=30, pady=25)

        # Question number badge
        q_badge = tk.Frame(question_inner, bg=self.colors["accent"])
        q_badge.pack(anchor="w")

        self.question_number = tk.Label(q_badge, text="  Q1  ",
                                        font=("SF Pro Display", 11, "bold"),
                                        bg=self.colors["accent"], fg="white")
        self.question_number.pack(padx=2, pady=2)

        # Question text
        self.question_text = tk.Label(question_inner, text="",
                                      font=("Georgia", 17),
                                      bg=self.colors["card"], fg=self.colors["text"],
                                      wraplength=820, justify=tk.LEFT)
        self.question_text.pack(anchor="w", pady=(18, 25))

        # ═══════════════════════════════════════════════════════════
        # OPTIONS - Modern card-style buttons
        # ═══════════════════════════════════════════════════════════
        self.options_frame = tk.Frame(self.question_frame, bg=self.colors["card"])
        self.options_frame.pack(fill=tk.X, padx=30, pady=(0, 15))

        for letter in ["A", "B", "C", "D"]:
            # Option container with border
            btn_frame = tk.Frame(self.options_frame, bg=self.colors["option_bg"],
                                highlightbackground=self.colors["option_border"],
                                highlightthickness=1)
            btn_frame.pack(fill=tk.X, pady=5)

            # Inner content with letter badge
            btn_inner = tk.Frame(btn_frame, bg=self.colors["option_bg"])
            btn_inner.pack(fill=tk.X, padx=3, pady=3)

            # Letter badge
            letter_badge = tk.Label(btn_inner, text=f" {letter} ",
                                   font=("SF Pro Display", 12, "bold"),
                                   bg=self.colors["border"], fg=self.colors["text"],
                                   padx=8, pady=4)
            letter_badge.pack(side=tk.LEFT, padx=(10, 0), pady=10)

            # Option text
            btn = tk.Label(btn_inner, text="",
                          font=("SF Pro Display", 14),
                          bg=self.colors["option_bg"],
                          fg=self.colors["text"],
                          anchor="w",
                          padx=12, pady=12,
                          cursor="hand2")
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Bind events to both frame and label
            for widget in [btn_frame, btn_inner, btn, letter_badge]:
                widget.bind("<Button-1>", lambda e, l=letter: self.select_option(l))
                widget.bind("<Enter>", lambda e, f=btn_frame, b=btn, bi=btn_inner, lb=letter_badge: self.on_option_enter(f, b, bi, lb))
                widget.bind("<Leave>", lambda e, f=btn_frame, b=btn, bi=btn_inner, lb=letter_badge, l=letter: self.on_option_leave(f, b, bi, lb, l))

            btn.frame = btn_frame
            btn.inner = btn_inner
            btn.letter_badge = letter_badge
            self.option_buttons[letter] = btn

        # ═══════════════════════════════════════════════════════════
        # FEEDBACK AREA
        # ═══════════════════════════════════════════════════════════
        self.feedback_frame = tk.Frame(self.question_frame, bg=self.colors["card"])
        self.feedback_frame.pack(fill=tk.X, padx=30, pady=(5, 15))

        self.feedback_label = tk.Label(self.feedback_frame, text="",
                                       font=("SF Pro Display", 13),
                                       bg=self.colors["card"], fg=self.colors["text"],
                                       wraplength=820, justify=tk.LEFT)

        # ═══════════════════════════════════════════════════════════
        # BOTTOM ACTIONS
        # ═══════════════════════════════════════════════════════════
        btn_frame = tk.Frame(self.window, bg=self.colors["bg"])
        btn_frame.pack(fill=tk.X, padx=40, pady=(0, 20))

        self.submit_btn = tk.Button(btn_frame, text="Submit Answer",
                                    command=self.submit_answer,
                                    bg=self.colors["accent"], fg="white",
                                    font=("SF Pro Display", 13, "bold"),
                                    padx=28, pady=12,
                                    relief=tk.FLAT, cursor="hand2",
                                    state=tk.DISABLED,
                                    activebackground=self.colors.get("accent_glow", "#ff6b8a"))
        self.submit_btn.pack(side=tk.LEFT)

        self.next_btn = tk.Button(btn_frame, text="Next Question  →",
                                  command=self.next_question,
                                  bg=self.colors["success"], fg="white",
                                  font=("SF Pro Display", 13, "bold"),
                                  padx=28, pady=12,
                                  relief=tk.FLAT, cursor="hand2",
                                  activebackground="#059669")

        # Keyboard hints
        hint = tk.Label(btn_frame, text="⌨️  A/B/C/D or ↑↓ to select  •  Enter to submit",
                       font=("SF Pro Display", 11),
                       bg=self.colors["bg"], fg=self.colors["text_muted"])
        hint.pack(side=tk.RIGHT)

    def on_option_enter(self, frame, btn, inner, badge):
        """Handle mouse enter on option."""
        if self.answered:
            return
        frame.config(bg=self.colors["option_hover"], highlightbackground=self.colors["accent"])
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

    def navigate_options(self, direction: int):
        """Navigate through options using arrow keys."""
        if self.answered or not self.option_order:
            return

        # Find current position
        if self.selected_option and self.selected_option in self.option_order:
            current_idx = self.option_order.index(self.selected_option)
        else:
            current_idx = -1 if direction > 0 else len(self.option_order)

        # Calculate new position
        new_idx = current_idx + direction
        if new_idx < 0:
            new_idx = len(self.option_order) - 1
        elif new_idx >= len(self.option_order):
            new_idx = 0

        # Select the new option
        self.select_option(self.option_order[new_idx])

    def show_question(self):
        """Display the current question."""
        if self.current_index >= len(self.questions):
            self.show_results()
            return

        q = self.questions[self.current_index]
        self.answered = False
        self.selected_option = None
        self.option_order = []  # Reset available options

        # Update progress
        self.progress_label.config(text=f"Question {self.current_index + 1} of {len(self.questions)}")
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

    def select_option(self, letter: str):
        """Select an option (letter is the display letter A/B/C/D)."""
        if self.answered:
            return

        # Check if this display letter is currently shown
        if letter not in self.option_order:
            return

        self.selected_option = letter

        # Update button styles
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

        # Update score display
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

        if q["explanation"]:
            feedback += f"\n\n📖 {q['explanation']}"

        self.feedback_label.config(text=feedback)
        self.feedback_label.pack(pady=(15, 0))

        # Show next button
        self.submit_btn.pack_forget()

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
        """Show quiz results with enhanced review features."""
        # Save quiz result
        save_quiz_result(self.topic, self.questions, self.score, len(self.questions))

        # Call the completion callback if set
        if self.on_complete_callback:
            try:
                self.on_complete_callback(self.score, len(self.questions))
            except Exception:
                pass

        # Clear question frame
        for widget in self.question_frame.winfo_children():
            widget.destroy()

        self.progress_bar_fill.place(x=0, y=0, relwidth=1, height=6)
        self.progress_label.config(text="Quiz Complete!")

        percentage = (self.score / len(self.questions)) * 100 if self.questions else 0

        # Determine message and color
        if percentage >= 80:
            emoji, message = "🎉", "Excellent work!"
            color = self.colors.get("success", "#10b981")
        elif percentage >= 60:
            emoji, message = "👍", "Good job!"
            color = self.colors.get("warning", "#f59e0b")
        else:
            emoji, message = "📚", "Keep practicing!"
            color = self.colors.get("accent", "#8b5cf6")

        # Get wrong questions
        self.wrong_questions = [q for q in self.questions if q.get("user_answer") != q.get("correct_answer")]

        # Main container
        main_container = tk.Frame(self.question_frame, bg=self.colors.get("card", "#1a1a24"))
        main_container.pack(expand=True, fill=tk.BOTH, padx=20, pady=15)

        # Score summary (compact)
        score_section = tk.Frame(main_container, bg=self.colors.get("card", "#1a1a24"))
        score_section.pack(fill=tk.X, pady=(10, 20))

        score_row = tk.Frame(score_section, bg=self.colors.get("card", "#1a1a24"))
        score_row.pack()

        tk.Label(score_row, text=emoji, font=("SF Pro Display", 36),
                bg=self.colors.get("card", "#1a1a24")).pack(side=tk.LEFT, padx=(0, 15))

        score_text = tk.Frame(score_row, bg=self.colors.get("card", "#1a1a24"))
        score_text.pack(side=tk.LEFT)

        tk.Label(score_text, text=f"{percentage:.0f}%",
                font=("SF Pro Display", 32, "bold"),
                bg=self.colors.get("card", "#1a1a24"), fg=color).pack(anchor="w")

        tk.Label(score_text, text=f"{message} • {self.score}/{len(self.questions)} correct",
                font=("SF Pro Display", 12),
                bg=self.colors.get("card", "#1a1a24"),
                fg=self.colors.get("text_secondary", "#a1a1aa")).pack(anchor="w")

        # Tab buttons
        tab_frame = tk.Frame(main_container, bg=self.colors.get("card", "#1a1a24"))
        tab_frame.pack(fill=tk.X, pady=(0, 10))

        self.active_tab = "summary"
        self.tab_buttons = {}

        for tab_id, tab_label in [("summary", "📊 Summary"), ("wrong", f"❌ Wrong ({len(self.wrong_questions)})"), ("trends", "📈 Trends")]:
            btn = tk.Button(tab_frame, text=tab_label,
                           command=lambda t=tab_id: self.switch_result_tab(t),
                           font=("SF Pro Display", 11),
                           relief=tk.FLAT, cursor="hand2", padx=15, pady=6)
            btn.pack(side=tk.LEFT, padx=(0, 5))
            self.tab_buttons[tab_id] = btn

        # Tab content area
        self.result_content = tk.Frame(main_container, bg=self.colors.get("card", "#1a1a24"))
        self.result_content.pack(fill=tk.BOTH, expand=True)

        self.switch_result_tab("summary")

        # Action buttons
        btn_frame = tk.Frame(main_container, bg=self.colors.get("card", "#1a1a24"))
        btn_frame.pack(fill=tk.X, pady=(15, 5))

        if self.wrong_questions:
            flashcard_btn = tk.Button(btn_frame, text="🃏 Create Flashcards from Mistakes",
                                     command=self.create_flashcards_from_wrong,
                                     bg=self.colors.get("success", "#10b981"), fg="white",
                                     font=("SF Pro Display", 11, "bold"),
                                     padx=15, pady=8, relief=tk.FLAT, cursor="hand2")
            flashcard_btn.pack(side=tk.LEFT, padx=(0, 10))

            summary_btn = tk.Button(btn_frame, text="📝 Generate Summary from Mistakes",
                                   command=self.generate_summary_from_wrong,
                                   bg=self.colors.get("warning", "#f59e0b"), fg="white",
                                   font=("SF Pro Display", 11, "bold"),
                                   padx=15, pady=8, relief=tk.FLAT, cursor="hand2")
            summary_btn.pack(side=tk.LEFT, padx=(0, 10))

        close_btn = tk.Button(btn_frame, text="Close Quiz",
                             command=self.window.destroy,
                             bg=self.colors.get("accent", "#8b5cf6"), fg="white",
                             font=("SF Pro Display", 11, "bold"),
                             padx=20, pady=8, relief=tk.FLAT, cursor="hand2")
        close_btn.pack(side=tk.RIGHT)

        self.next_btn.pack_forget()
        self.submit_btn.pack_forget()

    def switch_result_tab(self, tab_id):
        """Switch between result tabs."""
        self.active_tab = tab_id
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.config(bg=self.colors.get("accent", "#8b5cf6"), fg="white")
            else:
                btn.config(bg=self.colors.get("surface", "#16161d"), fg=self.colors.get("text_secondary", "#a1a1aa"))

        for widget in self.result_content.winfo_children():
            widget.destroy()

        if tab_id == "summary":
            self.show_summary_tab()
        elif tab_id == "wrong":
            self.show_wrong_answers_tab()
        elif tab_id == "trends":
            self.show_trends_tab()

    def show_summary_tab(self):
        """Show summary of all questions."""
        canvas = tk.Canvas(self.result_content, bg=self.colors.get("card", "#1a1a24"), highlightthickness=0)
        scrollbar = tk.Scrollbar(self.result_content, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.colors.get("card", "#1a1a24"))

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for i, q in enumerate(self.questions):
            is_correct = q.get("user_answer") == q.get("correct_answer")
            icon = "✓" if is_correct else "✗"
            bg_color = self.colors.get("success_bg", "#064e3b") if is_correct else self.colors.get("danger_bg", "#7f1d1d")
            fg_color = self.colors.get("success", "#10b981") if is_correct else self.colors.get("danger", "#ef4444")

            row = tk.Frame(scrollable, bg=bg_color)
            row.pack(fill=tk.X, pady=2, padx=5)
            row_inner = tk.Frame(row, bg=bg_color)
            row_inner.pack(fill=tk.X, padx=12, pady=8)

            tk.Label(row_inner, text=icon, font=("SF Pro Display", 12, "bold"), bg=bg_color, fg=fg_color).pack(side=tk.LEFT)
            question_preview = q.get('question', '')[:60] + "..." if len(q.get('question', '')) > 60 else q.get('question', '')
            tk.Label(row_inner, text=f"Q{i+1}: {question_preview}", font=("SF Pro Display", 11),
                    bg=bg_color, fg=self.colors.get("text", "#e4e4e7"), anchor="w").pack(side=tk.LEFT, padx=(10, 0))

    def show_wrong_answers_tab(self):
        """Show detailed view of wrong answers with explanations."""
        if not self.wrong_questions:
            tk.Label(self.result_content, text="🎉 Perfect score! No wrong answers!",
                    font=("SF Pro Display", 16), bg=self.colors.get("card", "#1a1a24"),
                    fg=self.colors.get("success", "#10b981")).pack(expand=True)
            return

        canvas = tk.Canvas(self.result_content, bg=self.colors.get("card", "#1a1a24"), highlightthickness=0)
        scrollbar = tk.Scrollbar(self.result_content, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.colors.get("card", "#1a1a24"))

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for q in self.wrong_questions:
            card = tk.Frame(scrollable, bg=self.colors.get("danger_bg", "#7f1d1d"))
            card.pack(fill=tk.X, pady=8, padx=10)
            inner = tk.Frame(card, bg=self.colors.get("danger_bg", "#7f1d1d"))
            inner.pack(fill=tk.X, padx=15, pady=12)

            q_num = self.questions.index(q) + 1
            tk.Label(inner, text=f"Question {q_num}", font=("SF Pro Display", 10, "bold"),
                    bg=self.colors.get("danger_bg", "#7f1d1d"), fg=self.colors.get("danger", "#ef4444")).pack(anchor="w")

            tk.Label(inner, text=q.get('question', ''), font=("SF Pro Display", 12),
                    bg=self.colors.get("danger_bg", "#7f1d1d"), fg=self.colors.get("text", "#e4e4e7"),
                    wraplength=700, justify=tk.LEFT).pack(anchor="w", pady=(5, 10))

            user_ans, correct_ans = q.get('user_answer', '?'), q.get('correct_answer', '?')
            options = q.get('options', {})

            tk.Label(inner, text=f"Your answer: {user_ans}) {options.get(user_ans, 'N/A')}",
                    font=("SF Pro Display", 11), bg=self.colors.get("danger_bg", "#7f1d1d"),
                    fg=self.colors.get("danger", "#ef4444")).pack(anchor="w")

            tk.Label(inner, text=f"Correct: {correct_ans}) {options.get(correct_ans, 'N/A')}",
                    font=("SF Pro Display", 11, "bold"), bg=self.colors.get("danger_bg", "#7f1d1d"),
                    fg=self.colors.get("success", "#10b981")).pack(anchor="w", pady=(3, 0))

            explanation = q.get('explanation', '')
            if explanation:
                tk.Frame(inner, bg=self.colors.get("border", "#3f3f5a"), height=1).pack(fill=tk.X, pady=10)
                tk.Label(inner, text="📖 Explanation:", font=("SF Pro Display", 10, "bold"),
                        bg=self.colors.get("danger_bg", "#7f1d1d"), fg=self.colors.get("text_secondary", "#a1a1aa")).pack(anchor="w")
                tk.Label(inner, text=explanation, font=("SF Pro Display", 11),
                        bg=self.colors.get("danger_bg", "#7f1d1d"), fg=self.colors.get("text", "#e4e4e7"),
                        wraplength=700, justify=tk.LEFT).pack(anchor="w", pady=(5, 0))

    def show_trends_tab(self):
        """Show performance trends over time."""
        db = load_quiz_db()
        all_quizzes = list(db.get("quizzes", {}).values())
        topic_quizzes = [q for q in all_quizzes if q.get("topic") == self.topic]
        topic_quizzes.sort(key=lambda x: x.get("date", ""))

        if len(topic_quizzes) < 2:
            empty = tk.Frame(self.result_content, bg=self.colors.get("card", "#1a1a24"))
            empty.pack(expand=True)
            tk.Label(empty, text="📊", font=("SF Pro Display", 36), bg=self.colors.get("card", "#1a1a24")).pack()
            tk.Label(empty, text="Not enough data yet", font=("SF Pro Display", 14, "bold"),
                    bg=self.colors.get("card", "#1a1a24"), fg=self.colors.get("text", "#e4e4e7")).pack(pady=(10, 5))
            tk.Label(empty, text=f"Take more quizzes on '{self.topic}' to see trends", font=("SF Pro Display", 11),
                    bg=self.colors.get("card", "#1a1a24"), fg=self.colors.get("text_muted", "#52525b")).pack()
            return

        header = tk.Frame(self.result_content, bg=self.colors.get("card", "#1a1a24"))
        header.pack(fill=tk.X, pady=(10, 15), padx=15)

        tk.Label(header, text=f"📈 Your Progress on '{self.topic}'", font=("SF Pro Display", 14, "bold"),
                bg=self.colors.get("card", "#1a1a24"), fg=self.colors.get("text", "#e4e4e7")).pack(anchor="w")

        percentages = [q.get("percentage", 0) for q in topic_quizzes[-10:]]
        avg = sum(percentages) / len(percentages) if percentages else 0
        trend = "📈" if len(percentages) > 1 and percentages[-1] > percentages[0] else "📉"

        tk.Label(header, text=f"Average: {avg:.0f}% • {len(topic_quizzes)} quizzes • {trend}",
                font=("SF Pro Display", 11), bg=self.colors.get("card", "#1a1a24"),
                fg=self.colors.get("text_secondary", "#a1a1aa")).pack(anchor="w")

        chart = tk.Frame(self.result_content, bg=self.colors.get("card", "#1a1a24"))
        chart.pack(fill=tk.BOTH, expand=True, padx=15)

        for q in topic_quizzes[-10:]:
            row = tk.Frame(chart, bg=self.colors.get("card", "#1a1a24"))
            row.pack(fill=tk.X, pady=3)

            pct = q.get("percentage", 0)
            tk.Label(row, text=q.get("date", "")[:10], width=12, font=("SF Pro Display", 10),
                    bg=self.colors.get("card", "#1a1a24"), fg=self.colors.get("text_muted", "#52525b"), anchor="w").pack(side=tk.LEFT)

            bar_container = tk.Frame(row, bg=self.colors.get("surface", "#16161d"), height=18, width=300)
            bar_container.pack(side=tk.LEFT, padx=10)
            bar_container.pack_propagate(False)

            bar_color = self.colors.get("success", "#10b981") if pct >= 70 else self.colors.get("warning", "#f59e0b") if pct >= 50 else self.colors.get("danger", "#ef4444")
            tk.Frame(bar_container, bg=bar_color, width=int(pct * 3), height=18).place(x=0, y=0)

            tk.Label(row, text=f"{pct:.0f}%", font=("SF Pro Display", 10, "bold"),
                    bg=self.colors.get("card", "#1a1a24"), fg=self.colors.get("text", "#e4e4e7"), width=5).pack(side=tk.LEFT)

    def create_flashcards_from_wrong(self):
        """Generate flashcards from incorrectly answered questions."""
        if not self.wrong_questions:
            messagebox.showinfo("No Mistakes", "No wrong answers to create flashcards from!")
            return
        try:
            from flashcard_db import create_deck, add_card, load_db
            deck_name = f"{self.topic} - Quiz Mistakes"
            db = load_db()
            existing_deck = None
            for deck_id, deck in db.get("decks", {}).items():
                if deck.get("name") == deck_name:
                    existing_deck = deck_id
                    break
            deck_id = existing_deck if existing_deck else create_deck(deck_name, self.topic)

            for q in self.wrong_questions:
                front = q.get('question', '')
                correct_ans = q.get('correct_answer', '')
                options = q.get('options', {})
                back = f"Correct Answer: {correct_ans}) {options.get(correct_ans, '')}"
                if q.get('explanation'):
                    back += f"\n\nExplanation: {q.get('explanation')}"
                add_card(deck_id, front, back)

            messagebox.showinfo("Flashcards Created", f"Created {len(self.wrong_questions)} flashcard(s) in deck:\n'{deck_name}'")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create flashcards: {e}")

    def generate_summary_from_wrong(self):
        """Generate a study summary from incorrectly answered questions using Claude."""
        if not self.wrong_questions:
            messagebox.showinfo("No Mistakes", "No wrong answers to generate summary from!")
            return

        import subprocess
        import threading

        # Build the prompt with wrong question details
        wrong_details = []
        for i, q in enumerate(self.wrong_questions, 1):
            user_ans = q.get('user_answer', '?')
            correct_ans = q.get('correct_answer', '?')
            options = q.get('options', {})
            detail = f"""
Question {i}: {q.get('question', '')}
Your answer: {user_ans}) {options.get(user_ans, 'N/A')}
Correct answer: {correct_ans}) {options.get(correct_ans, 'N/A')}
Explanation: {q.get('explanation', 'No explanation provided')}
"""
            wrong_details.append(detail)

        prompt = f"""Based on these quiz mistakes about '{self.topic}', create a concise study summary to help me understand and remember these concepts better.

WRONG ANSWERS:
{''.join(wrong_details)}

Please provide:
1. **Key Concepts to Review**: Brief explanation of each concept I got wrong
2. **Common Misconceptions**: Why I might have chosen the wrong answers
3. **Memory Tips**: Quick mnemonics or tips to remember the correct information
4. **Quick Reference**: A bullet-point summary of the key facts

Keep it concise and focused on what I need to learn."""

        # Create a loading window
        loading_window = tk.Toplevel(self.window)
        loading_window.title("Generating Summary...")
        loading_window.geometry("400x150")
        loading_window.configure(bg=self.colors.get("bg", "#0f0f14"))
        loading_window.transient(self.window)

        tk.Label(loading_window, text="🔄 Generating study summary...",
                font=("SF Pro Display", 14),
                bg=self.colors.get("bg", "#0f0f14"),
                fg=self.colors.get("text", "#e4e4e7")).pack(expand=True, pady=20)

        tk.Label(loading_window, text="This may take a moment",
                font=("SF Pro Display", 11),
                bg=self.colors.get("bg", "#0f0f14"),
                fg=self.colors.get("text_muted", "#52525b")).pack()

        def generate():
            try:
                result = subprocess.run(
                    ["claude", "-p", prompt],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                summary = result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr}"
            except subprocess.TimeoutExpired:
                summary = "Error: Request timed out. Please try again."
            except FileNotFoundError:
                summary = "Error: Claude CLI not found. Please install it with 'npm install -g @anthropic-ai/claude-code'"
            except Exception as e:
                summary = f"Error: {str(e)}"

            # Update UI in main thread
            self.window.after(0, lambda: show_summary(summary))

        def show_summary(summary):
            loading_window.destroy()

            # Create summary window
            summary_window = tk.Toplevel(self.window)
            summary_window.title(f"📝 Study Summary - {self.topic}")
            summary_window.geometry("800x600")
            summary_window.configure(bg=self.colors.get("bg", "#0f0f14"))

            # Header
            header = tk.Frame(summary_window, bg=self.colors.get("surface", "#16161d"))
            header.pack(fill=tk.X)

            header_inner = tk.Frame(header, bg=self.colors.get("surface", "#16161d"))
            header_inner.pack(fill=tk.X, padx=30, pady=15)

            tk.Label(header_inner, text=f"📝 Study Summary: {self.topic}",
                    font=("SF Pro Display", 18, "bold"),
                    bg=self.colors.get("surface", "#16161d"),
                    fg=self.colors.get("text", "#e4e4e7")).pack(side=tk.LEFT)

            tk.Label(header_inner, text=f"Based on {len(self.wrong_questions)} missed question(s)",
                    font=("SF Pro Display", 11),
                    bg=self.colors.get("surface", "#16161d"),
                    fg=self.colors.get("text_muted", "#52525b")).pack(side=tk.RIGHT)

            # Content area with scrolling
            content_frame = tk.Frame(summary_window, bg=self.colors.get("bg", "#0f0f14"))
            content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

            canvas = tk.Canvas(content_frame, bg=self.colors.get("card", "#1a1a24"), highlightthickness=0)
            scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
            scrollable = tk.Frame(canvas, bg=self.colors.get("card", "#1a1a24"))

            scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scrollable, anchor="nw", width=740)
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Display summary text
            summary_text = tk.Text(scrollable, wrap=tk.WORD,
                                  font=("SF Pro Display", 12),
                                  bg=self.colors.get("card", "#1a1a24"),
                                  fg=self.colors.get("text", "#e4e4e7"),
                                  relief=tk.FLAT, padx=20, pady=15,
                                  cursor="arrow")
            summary_text.pack(fill=tk.BOTH, expand=True)
            summary_text.insert("1.0", summary)
            summary_text.config(state=tk.DISABLED)

            # Enable mouse wheel scrolling
            def on_mousewheel(event):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            canvas.bind_all("<MouseWheel>", on_mousewheel)

            # Bottom buttons
            btn_frame = tk.Frame(summary_window, bg=self.colors.get("bg", "#0f0f14"))
            btn_frame.pack(fill=tk.X, padx=20, pady=(0, 15))

            def copy_to_clipboard():
                summary_window.clipboard_clear()
                summary_window.clipboard_append(summary)
                messagebox.showinfo("Copied", "Summary copied to clipboard!")

            copy_btn = tk.Button(btn_frame, text="📋 Copy to Clipboard",
                                command=copy_to_clipboard,
                                bg=self.colors.get("accent", "#8b5cf6"), fg="white",
                                font=("SF Pro Display", 11, "bold"),
                                padx=15, pady=8, relief=tk.FLAT, cursor="hand2")
            copy_btn.pack(side=tk.LEFT)

            close_btn = tk.Button(btn_frame, text="Close",
                                 command=summary_window.destroy,
                                 bg=self.colors.get("surface", "#16161d"),
                                 fg=self.colors.get("text", "#e4e4e7"),
                                 font=("SF Pro Display", 11),
                                 padx=15, pady=8, relief=tk.FLAT, cursor="hand2")
            close_btn.pack(side=tk.RIGHT)

        # Run generation in background thread
        thread = threading.Thread(target=generate, daemon=True)
        thread.start()


def open_quiz(parent, quiz_text: str, topic: str = "Statistics", timer_ref=None, colors=None):
    """Parse quiz text and open quiz window."""
    questions = parse_quiz_from_claude(quiz_text)

    if not questions:
        messagebox.showerror("Error", "Could not parse quiz questions.\nMake sure Claude generated a valid quiz first.")
        return None

    return QuizWindow(parent, questions, topic, timer_ref, colors)
