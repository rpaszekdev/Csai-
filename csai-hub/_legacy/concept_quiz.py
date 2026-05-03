#!/usr/bin/env python3
"""
Concept Explanation Quiz - Test your understanding of key concepts
Uses Claude Haiku to evaluate free-form explanations against definitions.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import re
import random
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
import threading

from themes import DARK_THEME
from flashcard_db import create_deck, add_card, get_all_decks
import subject_config

# File paths
CONCEPTS_FILE = subject_config.CONCEPTS_FILE
HISTORY_FILE = Path(__file__).parent / "saved_content" / "concept_quiz_history.json"


@dataclass
class Concept:
    """A concept with its definition."""
    number: int
    title: str
    definition: str


def parse_concepts_from_md(filepath: Path) -> List[Concept]:
    """Parse the markdown file to extract all concepts."""
    if not filepath.exists():
        return []

    content = filepath.read_text(encoding='utf-8')
    concepts = []

    # Split by ## headers (concept sections)
    # Pattern: ## N. Title
    pattern = r'## (\d+)\.\s+(.+?)(?=\n)'
    sections = re.split(r'(?=## \d+\.)', content)

    for section in sections:
        if not section.strip():
            continue

        # Extract number and title from header
        header_match = re.match(r'## (\d+)\.\s+(.+?)(?:\n|$)', section)
        if not header_match:
            continue

        number = int(header_match.group(1))
        title = header_match.group(2).strip()

        # Get definition (everything after the header until next ## or end)
        definition = section[header_match.end():].strip()

        # Clean up definition - remove trailing horizontal rules
        definition = re.sub(r'\n---+\s*$', '', definition)

        if title and definition:
            concepts.append(Concept(
                number=number,
                title=title,
                definition=definition
            ))

    return concepts


def load_history() -> dict:
    """Load quiz history."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except:
            pass
    return {"sessions": [], "concept_stats": {}}


def save_history(history: dict):
    """Save quiz history."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, indent=2, default=str))


def get_or_create_concept_deck() -> str:
    """Get or create the Concept Quiz flashcard deck."""
    decks = get_all_decks()
    for deck in decks:
        if deck["name"] == "Concept Quiz - Need Review":
            return deck["id"]

    # Create new deck
    return create_deck("Concept Quiz - Need Review", f"{subject_config.SUBJECT_NAME} concepts that need more practice")


def evaluate_with_haiku(concept: Concept, user_answer: str) -> str:
    """Use Claude Haiku to evaluate the user's explanation."""
    prompt = f"""Evaluate this student's explanation of a {subject_config.SUBJECT_NAME} concept. Be encouraging but accurate.

CONCEPT: {concept.title}

CORRECT DEFINITION:
{concept.definition}

STUDENT'S EXPLANATION:
{user_answer}

Respond in EXACTLY this format (keep it concise, 2-3 sentences max per section):
RATING: [Excellent/Good/Partial/Needs Work]
COVERED: [Key points they got right, or "None" if nothing correct]
MISSING: [Important concepts they should add, or "None" if complete]
TIP: [One brief suggestion for improvement, or "Great job!" if excellent]"""

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", "haiku"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip() if result.stdout else "Error: No response from Claude"
    except subprocess.TimeoutExpired:
        return "Error: Evaluation timed out"
    except FileNotFoundError:
        return "Error: Claude CLI not found. Please install with: npm install -g @anthropic-ai/claude-code"
    except Exception as e:
        return f"Error: {str(e)}"


def parse_evaluation(evaluation: str) -> dict:
    """Parse the evaluation response into structured data."""
    result = {
        "rating": "Unknown",
        "covered": "",
        "missing": "",
        "tip": ""
    }

    # Extract each field
    rating_match = re.search(r'RATING:\s*(.+?)(?=\n|COVERED:|$)', evaluation, re.IGNORECASE)
    if rating_match:
        result["rating"] = rating_match.group(1).strip()

    covered_match = re.search(r'COVERED:\s*(.+?)(?=\nMISSING:|$)', evaluation, re.IGNORECASE | re.DOTALL)
    if covered_match:
        result["covered"] = covered_match.group(1).strip()

    missing_match = re.search(r'MISSING:\s*(.+?)(?=\nTIP:|$)', evaluation, re.IGNORECASE | re.DOTALL)
    if missing_match:
        result["missing"] = missing_match.group(1).strip()

    tip_match = re.search(r'TIP:\s*(.+?)$', evaluation, re.IGNORECASE | re.DOTALL)
    if tip_match:
        result["tip"] = tip_match.group(1).strip()

    return result


class ConceptQuizWindow:
    """Window for the concept explanation quiz."""

    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Concept Explanation Quiz")
        self.window.geometry("800x700")
        self.window.configure(bg=DARK_THEME["bg"])

        # Load concepts and shuffle
        self.concepts = parse_concepts_from_md(CONCEPTS_FILE)
        if not self.concepts:
            messagebox.showerror("Error", "No concepts found. Make sure stats_concepts.md exists.")
            self.window.destroy()
            return

        random.shuffle(self.concepts)

        # Quiz state
        self.current_index = 0
        self.results = []  # List of (concept, rating) tuples
        self.session_start = datetime.now()

        self._build_ui()
        self._show_concept()

    def _build_ui(self):
        """Build the quiz UI."""
        theme = DARK_THEME

        # Header frame
        header = tk.Frame(self.window, bg=theme["surface"])
        header.pack(fill=tk.X, padx=20, pady=(20, 10))

        # Title
        title_label = tk.Label(
            header,
            text="Concept Explanation Quiz",
            font=("SF Pro Display", 20, "bold"),
            fg=theme["text"],
            bg=theme["surface"]
        )
        title_label.pack(side=tk.LEFT)

        # Progress
        self.progress_label = tk.Label(
            header,
            text="1 / " + str(len(self.concepts)),
            font=("SF Pro Display", 14),
            fg=theme["text_secondary"],
            bg=theme["surface"]
        )
        self.progress_label.pack(side=tk.RIGHT)

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.window,
            variable=self.progress_var,
            maximum=len(self.concepts),
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, padx=20, pady=(0, 20))

        # Concept card
        concept_frame = tk.Frame(self.window, bg=theme["surface"], padx=20, pady=15)
        concept_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        self.concept_label = tk.Label(
            concept_frame,
            text="",
            font=("SF Pro Display", 18, "bold"),
            fg=theme["primary"],
            bg=theme["surface"],
            wraplength=700
        )
        self.concept_label.pack()

        # Instruction
        instruction = tk.Label(
            self.window,
            text="Explain this concept in 2-3 sentences:",
            font=("SF Pro Display", 12),
            fg=theme["text_secondary"],
            bg=theme["bg"]
        )
        instruction.pack(anchor=tk.W, padx=20, pady=(10, 5))

        # Answer text area
        self.answer_text = scrolledtext.ScrolledText(
            self.window,
            font=("Georgia", 13),
            bg=theme["input_bg"],
            fg=theme["text"],
            insertbackground=theme["text"],
            wrap=tk.WORD,
            height=6,
            padx=10,
            pady=10
        )
        self.answer_text.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Button frame
        btn_frame = tk.Frame(self.window, bg=theme["bg"])
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 15))

        self.skip_btn = tk.Button(
            btn_frame,
            text="Skip",
            font=("SF Pro Display", 12),
            bg=theme["btn_muted"],
            fg=theme["btn_muted_text"],
            activebackground=theme["btn_muted_hover"],
            activeforeground=theme["text"],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=self._skip_concept
        )
        self.skip_btn.pack(side=tk.LEFT)

        self.submit_btn = tk.Button(
            btn_frame,
            text="Submit Answer",
            font=("SF Pro Display", 12, "bold"),
            bg=theme["btn_primary"],
            fg=theme["text"],
            activebackground=theme["btn_primary_hover"],
            activeforeground=theme["text"],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=self._submit_answer
        )
        self.submit_btn.pack(side=tk.RIGHT)

        # Feedback frame (hidden initially)
        self.feedback_frame = tk.Frame(self.window, bg=theme["surface"], padx=20, pady=15)

        self.rating_label = tk.Label(
            self.feedback_frame,
            text="",
            font=("SF Pro Display", 16, "bold"),
            fg=theme["success"],
            bg=theme["surface"]
        )
        self.rating_label.pack(anchor=tk.W)

        self.feedback_text = tk.Label(
            self.feedback_frame,
            text="",
            font=("Georgia", 12),
            fg=theme["text_reading"],
            bg=theme["surface"],
            wraplength=700,
            justify=tk.LEFT
        )
        self.feedback_text.pack(anchor=tk.W, pady=(10, 0))

        # Bottom buttons (hidden initially)
        self.bottom_btn_frame = tk.Frame(self.window, bg=theme["bg"])

        self.show_def_btn = tk.Button(
            self.bottom_btn_frame,
            text="Show Full Definition",
            font=("SF Pro Display", 11),
            bg=theme["btn_muted"],
            fg=theme["btn_muted_text"],
            activebackground=theme["btn_muted_hover"],
            activeforeground=theme["text"],
            relief=tk.FLAT,
            padx=15,
            pady=6,
            command=self._show_definition
        )
        self.show_def_btn.pack(side=tk.LEFT)

        self.next_btn = tk.Button(
            self.bottom_btn_frame,
            text="Next Concept",
            font=("SF Pro Display", 12, "bold"),
            bg=theme["btn_success"],
            fg=theme["text"],
            activebackground=theme["btn_success_hover"],
            activeforeground=theme["text"],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=self._next_concept
        )
        self.next_btn.pack(side=tk.RIGHT)

        # Definition popup (hidden)
        self.def_frame = None

    def _show_concept(self):
        """Display the current concept."""
        if self.current_index >= len(self.concepts):
            self._show_summary()
            return

        concept = self.concepts[self.current_index]
        self.concept_label.config(text=f'"{concept.title}"')
        self.progress_label.config(text=f"{self.current_index + 1} / {len(self.concepts)}")
        self.progress_var.set(self.current_index)

        # Reset UI state
        self.answer_text.delete("1.0", tk.END)
        self.answer_text.config(state=tk.NORMAL)
        self.submit_btn.config(state=tk.NORMAL)
        self.skip_btn.config(state=tk.NORMAL)
        self.feedback_frame.pack_forget()
        self.bottom_btn_frame.pack_forget()

        if self.def_frame:
            self.def_frame.destroy()
            self.def_frame = None

    def _submit_answer(self):
        """Submit the answer for evaluation."""
        answer = self.answer_text.get("1.0", tk.END).strip()
        if not answer:
            messagebox.showwarning("Empty Answer", "Please write an explanation before submitting.")
            return

        # Disable inputs while evaluating
        self.submit_btn.config(state=tk.DISABLED, text="Evaluating...")
        self.skip_btn.config(state=tk.DISABLED)
        self.answer_text.config(state=tk.DISABLED)

        # Run evaluation in thread
        def evaluate():
            concept = self.concepts[self.current_index]
            evaluation = evaluate_with_haiku(concept, answer)
            self.window.after(0, lambda: self._show_feedback(evaluation))

        thread = threading.Thread(target=evaluate, daemon=True)
        thread.start()

    def _show_feedback(self, evaluation: str):
        """Display the evaluation feedback."""
        theme = DARK_THEME
        concept = self.concepts[self.current_index]

        # Parse evaluation
        parsed = parse_evaluation(evaluation)
        rating = parsed["rating"]

        # Store result
        self.results.append((concept, rating, evaluation))

        # Create flashcard if needed
        if rating in ["Partial", "Needs Work"]:
            self._create_flashcard(concept)

        # Determine rating color
        rating_colors = {
            "Excellent": theme["success"],
            "Good": theme["secondary"],
            "Partial": theme["warning"],
            "Needs Work": theme["danger"]
        }
        color = rating_colors.get(rating, theme["text"])

        # Update rating label
        rating_emoji = {"Excellent": "Excellent!", "Good": "Good!", "Partial": "Partial", "Needs Work": "Needs Work"}
        self.rating_label.config(
            text=rating_emoji.get(rating, rating),
            fg=color
        )

        # Build feedback text
        feedback_parts = []
        if parsed["covered"] and parsed["covered"].lower() != "none":
            feedback_parts.append(f"Covered: {parsed['covered']}")
        if parsed["missing"] and parsed["missing"].lower() != "none":
            feedback_parts.append(f"Missing: {parsed['missing']}")
        if parsed["tip"]:
            feedback_parts.append(f"Tip: {parsed['tip']}")

        self.feedback_text.config(text="\n\n".join(feedback_parts) if feedback_parts else evaluation)

        # Show feedback UI
        self.feedback_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        self.bottom_btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        # Reset submit button text
        self.submit_btn.config(text="Submit Answer")

    def _create_flashcard(self, concept: Concept):
        """Create a flashcard for a concept that needs review."""
        deck_id = get_or_create_concept_deck()
        # Truncate definition for card back
        back_text = concept.definition[:800]
        if len(concept.definition) > 800:
            back_text += "..."

        add_card(
            deck_id=deck_id,
            front=f"Explain: {concept.title}",
            back=back_text
        )

    def _show_definition(self):
        """Show the full definition in a popup."""
        if self.def_frame:
            self.def_frame.destroy()
            self.def_frame = None
            self.show_def_btn.config(text="Show Full Definition")
            return

        theme = DARK_THEME
        concept = self.concepts[self.current_index]

        self.def_frame = tk.Frame(self.window, bg=theme["content_bg"], padx=15, pady=15)
        self.def_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Header
        header = tk.Label(
            self.def_frame,
            text="Full Definition:",
            font=("SF Pro Display", 12, "bold"),
            fg=theme["text_secondary"],
            bg=theme["content_bg"]
        )
        header.pack(anchor=tk.W)

        # Definition text
        def_text = scrolledtext.ScrolledText(
            self.def_frame,
            font=("Georgia", 12),
            bg=theme["content_bg"],
            fg=theme["text_reading"],
            wrap=tk.WORD,
            height=10,
            relief=tk.FLAT
        )
        def_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        def_text.insert("1.0", concept.definition)
        def_text.config(state=tk.DISABLED)

        self.show_def_btn.config(text="Hide Definition")

    def _skip_concept(self):
        """Skip the current concept."""
        concept = self.concepts[self.current_index]
        self.results.append((concept, "Skipped", ""))
        self._next_concept()

    def _next_concept(self):
        """Move to the next concept."""
        self.current_index += 1
        self._show_concept()

    def _show_summary(self):
        """Show the quiz summary."""
        theme = DARK_THEME

        # Clear window
        for widget in self.window.winfo_children():
            widget.destroy()

        # Calculate stats
        ratings = [r[1] for r in self.results]
        excellent = ratings.count("Excellent")
        good = ratings.count("Good")
        partial = ratings.count("Partial")
        needs_work = ratings.count("Needs Work")
        skipped = ratings.count("Skipped")

        # Save to history
        history = load_history()
        session = {
            "date": datetime.now().isoformat(),
            "total": len(self.concepts),
            "excellent": excellent,
            "good": good,
            "partial": partial,
            "needs_work": needs_work,
            "skipped": skipped
        }
        history["sessions"].append(session)
        save_history(history)

        # Summary frame
        summary = tk.Frame(self.window, bg=theme["bg"], padx=40, pady=40)
        summary.pack(fill=tk.BOTH, expand=True)

        # Title
        title = tk.Label(
            summary,
            text="Quiz Complete!",
            font=("SF Pro Display", 28, "bold"),
            fg=theme["text"],
            bg=theme["bg"]
        )
        title.pack(pady=(0, 30))

        # Stats
        stats_frame = tk.Frame(summary, bg=theme["surface"], padx=30, pady=20)
        stats_frame.pack(fill=tk.X, pady=(0, 20))

        stats = [
            ("Excellent", excellent, theme["success"]),
            ("Good", good, theme["secondary"]),
            ("Partial", partial, theme["warning"]),
            ("Needs Work", needs_work, theme["danger"]),
            ("Skipped", skipped, theme["text_muted"])
        ]

        for label, count, color in stats:
            row = tk.Frame(stats_frame, bg=theme["surface"])
            row.pack(fill=tk.X, pady=5)

            tk.Label(
                row,
                text=label,
                font=("SF Pro Display", 14),
                fg=color,
                bg=theme["surface"]
            ).pack(side=tk.LEFT)

            tk.Label(
                row,
                text=str(count),
                font=("SF Pro Display", 14, "bold"),
                fg=color,
                bg=theme["surface"]
            ).pack(side=tk.RIGHT)

        # Flashcard note
        needs_review = partial + needs_work
        if needs_review > 0:
            note = tk.Label(
                summary,
                text=f"{needs_review} concept(s) added to flashcards for review",
                font=("SF Pro Display", 12),
                fg=theme["text_secondary"],
                bg=theme["bg"]
            )
            note.pack(pady=(0, 20))

        # Close button
        close_btn = tk.Button(
            summary,
            text="Close",
            font=("SF Pro Display", 14, "bold"),
            bg=theme["btn_primary"],
            fg=theme["text"],
            activebackground=theme["btn_primary_hover"],
            activeforeground=theme["text"],
            relief=tk.FLAT,
            padx=30,
            pady=10,
            command=self.window.destroy
        )
        close_btn.pack()


def open_concept_quiz(parent):
    """Open the concept quiz window."""
    ConceptQuizWindow(parent)
