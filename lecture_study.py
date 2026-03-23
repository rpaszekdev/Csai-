#!/usr/bin/env python3
"""
Lecture Study Mode - Engaging lecture summaries with study guide emphasis
"""

import tkinter as tk
from tkinter import scrolledtext, font as tkfont
import threading
import subprocess
import re
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from study_rag import retrieve_context
import subject_config
from content_storage import (
    save_lecture_summary, get_lecture_summary, lecture_summary_exists, delete_lecture_summary
)
from themes import DARK_THEME

# Import graph manager for visualizations
try:
    from graph_manager import get_graphs_for_study_topic, ImageInfo, GraphManager
    HAS_GRAPH_MANAGER = True
except ImportError:
    HAS_GRAPH_MANAGER = False
    logging.info("Graph manager not available")

# Import PIL for image display
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logging.info("PIL not available for image display")


class LectureStudyWindow:
    """A beautiful, engaging window for studying entire lectures."""

    def __init__(self, parent, lecture_name: str, lecture_data: dict, colors: dict = None):
        """
        Initialize the lecture study window.

        Args:
            parent: Parent tkinter window
            lecture_name: e.g., "Lecture 1: Introduction and Probability"
            lecture_data: Dict with 'icon', 'color', 'topics'
            colors: Theme colors dict
        """
        self.parent = parent
        self.lecture_name = lecture_name
        self.lecture_data = lecture_data
        self.colors = colors or DARK_THEME
        self.topics = lecture_data.get("topics", [])
        self.lecture_color = lecture_data.get("color", "#4ecca3")
        self.lecture_icon = lecture_data.get("icon", "")

        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Study: {lecture_name}")
        self.window.geometry("1100x850")
        self.window.configure(bg=self.colors["bg"])

        # Make it feel more app-like
        self.window.transient(parent)

        # Content storage
        self.summary_content = ""

        # Build UI
        self.create_ui()

        # Load content
        self.load_lecture_content()

    def create_ui(self):
        """Create the lecture study UI."""
        # Main container
        main_frame = tk.Frame(self.window, bg=self.colors["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ═══════════════════════════════════════════════════════════
        # HEADER - Lecture title with icon and color accent
        # ═══════════════════════════════════════════════════════════
        header = tk.Frame(main_frame, bg=self.lecture_color, height=120)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        header_inner = tk.Frame(header, bg=self.lecture_color)
        header_inner.pack(fill=tk.BOTH, expand=True, padx=40, pady=25)

        # Back button
        back_btn = tk.Button(header_inner, text="< Back",
                            command=self.window.destroy,
                            bg=self.lecture_color,
                            fg="white",
                            activebackground=self.lecture_color,
                            activeforeground="white",
                            font=("SF Pro Display", 12),
                            relief=tk.FLAT,
                            cursor="hand2")
        back_btn.pack(anchor="nw")

        # Title row
        title_row = tk.Frame(header_inner, bg=self.lecture_color)
        title_row.pack(fill=tk.X, pady=(10, 0))

        # Icon
        tk.Label(title_row, text=self.lecture_icon,
                font=("SF Pro Display", 36),
                bg=self.lecture_color,
                fg="white").pack(side=tk.LEFT)

        # Title and subtitle
        title_text = tk.Frame(title_row, bg=self.lecture_color)
        title_text.pack(side=tk.LEFT, padx=(15, 0))

        tk.Label(title_text, text=self.lecture_name,
                font=("SF Pro Display", 24, "bold"),
                bg=self.lecture_color,
                fg="white").pack(anchor="w")

        tk.Label(title_text, text=f"{len(self.topics)} topics to explore",
                font=("SF Pro Display", 13),
                bg=self.lecture_color,
                fg="rgba(255,255,255,0.8)").pack(anchor="w")

        # Right side: Refresh button
        btn_frame = tk.Frame(header_inner, bg=self.lecture_color)
        btn_frame.pack(side=tk.RIGHT, anchor="ne")

        refresh_btn = tk.Button(btn_frame, text="Regenerate",
                               command=self.regenerate_content,
                               bg="white",
                               fg=self.lecture_color,
                               activebackground="#f0f0f0",
                               activeforeground=self.lecture_color,
                               font=("SF Pro Display", 11, "bold"),
                               relief=tk.FLAT,
                               padx=15, pady=6,
                               cursor="hand2")
        refresh_btn.pack()

        # ═══════════════════════════════════════════════════════════
        # CONTENT AREA - Scrollable summary
        # ═══════════════════════════════════════════════════════════
        content_container = tk.Frame(main_frame, bg=self.colors["bg"])
        content_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # Two-column layout
        columns = tk.Frame(content_container, bg=self.colors["bg"])
        columns.pack(fill=tk.BOTH, expand=True)

        # Left column: Main summary (70%)
        left_col = tk.Frame(columns, bg=self.colors["bg"])
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Section label
        tk.Label(left_col, text="LECTURE SUMMARY",
                font=("SF Pro Display", 10, "bold"),
                bg=self.colors["bg"],
                fg=self.colors["text_muted"]).pack(anchor="w", pady=(0, 10))

        # Content text widget with custom styling
        text_frame = tk.Frame(left_col, bg=self.colors["surface"],
                             highlightbackground=self.colors["border"],
                             highlightthickness=1)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.content_text = tk.Text(text_frame,
                                   wrap=tk.WORD,
                                   bg=self.colors["surface"],
                                   fg=self.colors["text"],
                                   font=("SF Pro Display", 14),
                                   relief=tk.FLAT,
                                   padx=25,
                                   pady=20,
                                   spacing1=4,
                                   spacing2=6,
                                   spacing3=8)

        scrollbar = tk.Scrollbar(text_frame, command=self.content_text.yview,
                                bg=self.colors["surface"],
                                troughcolor=self.colors["surface"])
        self.content_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure text tags for markdown-like styling
        self.setup_text_tags()

        # Right column: Topics sidebar (30%)
        right_col = tk.Frame(columns, bg=self.colors["bg"], width=280)
        right_col.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        right_col.pack_propagate(False)

        # Study Guide Topics
        tk.Label(right_col, text="STUDY GUIDE TOPICS",
                font=("SF Pro Display", 10, "bold"),
                bg=self.colors["bg"],
                fg=self.colors["text_muted"]).pack(anchor="w", pady=(0, 10))

        topics_frame = tk.Frame(right_col, bg=self.colors["surface"],
                               highlightbackground=self.colors["border"],
                               highlightthickness=1)
        topics_frame.pack(fill=tk.BOTH, expand=True)

        topics_inner = tk.Frame(topics_frame, bg=self.colors["surface"])
        topics_inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        tk.Label(topics_inner, text="Key topics from the study guide:",
                font=("SF Pro Display", 11),
                bg=self.colors["surface"],
                fg=self.colors["text_secondary"],
                wraplength=230).pack(anchor="w", pady=(0, 15))

        # List each topic
        for i, topic in enumerate(self.topics, 1):
            topic_row = tk.Frame(topics_inner, bg=self.colors["surface"])
            topic_row.pack(fill=tk.X, pady=4)

            # Number badge
            badge = tk.Label(topic_row, text=str(i),
                           font=("SF Pro Display", 10, "bold"),
                           bg=self.lecture_color,
                           fg="white",
                           width=2)
            badge.pack(side=tk.LEFT)

            # Topic text
            tk.Label(topic_row, text=topic,
                    font=("SF Pro Display", 11),
                    bg=self.colors["surface"],
                    fg=self.colors["text"],
                    wraplength=200,
                    justify=tk.LEFT).pack(side=tk.LEFT, padx=(10, 0))

        # Quick actions at bottom
        actions_frame = tk.Frame(right_col, bg=self.colors["bg"])
        actions_frame.pack(fill=tk.X, pady=(15, 0))

        quiz_btn = tk.Button(actions_frame, text="Quiz This Lecture",
                            command=self.quiz_lecture,
                            bg=self.colors["warning"],
                            fg="#000000",
                            activebackground=self.colors["warning"],
                            activeforeground="#000000",
                            font=("SF Pro Display", 11, "bold"),
                            relief=tk.FLAT,
                            padx=15, pady=8,
                            cursor="hand2")
        quiz_btn.pack(fill=tk.X)

    def setup_text_tags(self):
        """Configure text tags for rich formatting."""
        # Headers
        self.content_text.tag_configure("h1",
                                        font=("SF Pro Display", 22, "bold"),
                                        foreground=self.colors["text"],
                                        spacing1=20,
                                        spacing3=10)

        self.content_text.tag_configure("h2",
                                        font=("SF Pro Display", 18, "bold"),
                                        foreground=self.lecture_color,
                                        spacing1=18,
                                        spacing3=8)

        self.content_text.tag_configure("h3",
                                        font=("SF Pro Display", 15, "bold"),
                                        foreground=self.colors["text"],
                                        spacing1=14,
                                        spacing3=6)

        # Body text
        self.content_text.tag_configure("body",
                                        font=("SF Pro Display", 14),
                                        foreground=self.colors["text"],
                                        spacing1=4,
                                        spacing2=4)

        # Emphasis
        self.content_text.tag_configure("bold",
                                        font=("SF Pro Display", 14, "bold"),
                                        foreground=self.colors["text"])

        self.content_text.tag_configure("italic",
                                        font=("SF Pro Display", 14, "italic"),
                                        foreground=self.colors["text_secondary"])

        # Key concept highlight
        self.content_text.tag_configure("concept",
                                        font=("SF Pro Display", 14, "bold"),
                                        foreground=self.lecture_color,
                                        background=self.colors["input_bg"])

        # Code
        self.content_text.tag_configure("code",
                                        font=("SF Mono", 12),
                                        foreground=self.colors["secondary"],
                                        background=self.colors["input_bg"])

        # Bullet points
        self.content_text.tag_configure("bullet",
                                        font=("SF Pro Display", 14),
                                        foreground=self.colors["text"],
                                        lmargin1=20,
                                        lmargin2=35)

        # Study guide connection highlight
        self.content_text.tag_configure("study_guide",
                                        font=("SF Pro Display", 13),
                                        foreground=self.colors["success"],
                                        background=self.colors["input_bg"],
                                        spacing1=8,
                                        spacing3=8)

    def render_markdown(self, text: str):
        """Render markdown-like text with proper formatting."""
        self.content_text.delete(1.0, tk.END)

        lines = text.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # H1: # Header
            if line.startswith('# '):
                self.content_text.insert(tk.END, line[2:] + '\n', 'h1')
            # H2: ## Header
            elif line.startswith('## '):
                self.content_text.insert(tk.END, line[3:] + '\n', 'h2')
            # H3: ### Header
            elif line.startswith('### '):
                self.content_text.insert(tk.END, line[4:] + '\n', 'h3')
            # Bullet points
            elif line.startswith('- ') or line.startswith('* '):
                self.content_text.insert(tk.END, '  ' + line + '\n', 'bullet')
            # Numbered lists
            elif re.match(r'^\d+\. ', line):
                self.content_text.insert(tk.END, '  ' + line + '\n', 'bullet')
            # Code blocks
            elif line.startswith('```'):
                i += 1
                code_lines = []
                while i < len(lines) and not lines[i].startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                self.content_text.insert(tk.END, '\n'.join(code_lines) + '\n\n', 'code')
            # Study guide marker
            elif line.startswith('[STUDY GUIDE]') or line.startswith('STUDY GUIDE:'):
                self.content_text.insert(tk.END, line + '\n', 'study_guide')
            # Empty line
            elif line.strip() == '':
                self.content_text.insert(tk.END, '\n')
            # Regular text with inline formatting
            else:
                self.render_inline_formatting(line)

            i += 1

        self.content_text.config(state=tk.DISABLED)

    def render_inline_formatting(self, line: str):
        """Handle inline formatting like **bold** and *italic*."""
        # Simple implementation - just insert as body text for now
        # Bold: **text**
        parts = re.split(r'(\*\*[^*]+\*\*)', line)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                self.content_text.insert(tk.END, part[2:-2], 'bold')
            else:
                # Check for italic: *text*
                italic_parts = re.split(r'(\*[^*]+\*)', part)
                for ip in italic_parts:
                    if ip.startswith('*') and ip.endswith('*') and len(ip) > 2:
                        self.content_text.insert(tk.END, ip[1:-1], 'italic')
                    else:
                        self.content_text.insert(tk.END, ip, 'body')

        self.content_text.insert(tk.END, '\n', 'body')

    def load_lecture_content(self):
        """Load or generate lecture summary content."""
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)

        # Check for saved summary
        saved = get_lecture_summary(self.lecture_name)

        if saved and saved.get("summary"):
            self.summary_content = saved["summary"]
            self.render_markdown(self.summary_content)
            return

        # Show loading state
        self.content_text.insert(tk.END, "Preparing your lecture summary...\n\n", "h2")
        self.content_text.insert(tk.END, "Claude is creating an engaging summary that highlights key study guide concepts.\n", "italic")
        self.content_text.config(state=tk.DISABLED)

        # Generate in background
        threading.Thread(target=self._generate_summary, daemon=True).start()

    def _generate_summary(self):
        """Generate lecture summary using Claude."""
        try:
            # Retrieve context for ALL topics in this lecture
            all_contexts = []
            for topic in self.topics:
                contexts = retrieve_context(topic, n_results=3)
                all_contexts.extend(contexts)

            # Also search for the lecture name itself
            lecture_contexts = retrieve_context(self.lecture_name, n_results=4)
            all_contexts.extend(lecture_contexts)

            # Deduplicate and limit
            seen_content = set()
            unique_contexts = []
            for ctx in all_contexts:
                content_hash = hash(ctx['content'][:200])
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_contexts.append(ctx)

            unique_contexts = unique_contexts[:12]  # Limit to 12 chunks

            context_text = "\n\n---\n\n".join([
                f"[Source: {ctx['metadata'].get('filename', 'unknown')}]\n{ctx['content'][:1200]}"
                for ctx in unique_contexts
            ])

            # Format topics for the prompt
            topics_list = "\n".join([f"  {i+1}. {t}" for i, t in enumerate(self.topics)])

            prompt = f"""You are creating an engaging, easy-to-understand summary of a {subject_config.SUBJECT_NAME} lecture.

LECTURE: {self.lecture_name}

STUDY GUIDE TOPICS (these are the key concepts students need to master):
{topics_list}

LECTURE MATERIALS:
{context_text}

---

Create a CAPTIVATING lecture summary that makes learning enjoyable. Think of yourself as a brilliant tutor who makes complex concepts click.

STRUCTURE YOUR RESPONSE LIKE THIS:

## The Big Picture
Start with a compelling hook - why does this lecture matter? What real-world problem does it solve? Make me WANT to learn this.

## Key Concepts Breakdown
For EACH study guide topic, create a mini-section:
- Use analogies and real-world examples
- Explain the "why" not just the "what"
- Include any formulas but explain what they MEAN
- Mark each with: **[Study Guide: Topic Name]**

## How It All Connects
Show how the topics in this lecture relate to each other. Draw connections. Help me see the bigger picture.

## Quick Reference
- Key formulas (with plain English explanations)
- Important terms to remember
- Common exam traps to avoid

## Why This Matters
End with practical applications - where would I actually use this?

STYLE GUIDELINES:
- Write like you're explaining to a smart friend, not reading from a textbook
- Use "you" and "we" to make it conversational
- Include relevant analogies (comparing stats concepts to everyday things)
- If there are technical details or formulas, explain them in plain English
- Keep paragraphs short and punchy
- Use bullet points liberally
- Highlight the study guide topics prominently - these are EXAM PRIORITIES

Make this summary something a student would actually ENJOY reading, not just tolerate."""

            result = subprocess.run(
                ["claude", "-p", prompt, "--model", "sonnet"],
                capture_output=True,
                text=True,
                timeout=180
            )

            response = result.stdout if result.stdout else result.stderr
            self.summary_content = response

            # Save to storage
            save_lecture_summary(
                self.lecture_name,
                self.summary_content,
                key_concepts=self.topics
            )

            # Update UI on main thread
            def update_ui():
                self.content_text.config(state=tk.NORMAL)
                self.render_markdown(self.summary_content)

            self.window.after(0, update_ui)

        except Exception as e:
            logging.error(f"Error generating lecture summary: {e}")

            def show_error():
                self.content_text.config(state=tk.NORMAL)
                self.content_text.delete(1.0, tk.END)
                self.content_text.insert(tk.END, f"Failed to generate summary: {e}\n\n", "h2")
                self.content_text.insert(tk.END, "Click 'Regenerate' to try again.", "body")
                self.content_text.config(state=tk.DISABLED)

            self.window.after(0, show_error)

    def regenerate_content(self):
        """Delete cached content and regenerate."""
        delete_lecture_summary(self.lecture_name)
        self.summary_content = ""
        self.content_text.config(state=tk.NORMAL)
        self.load_lecture_content()

    def quiz_lecture(self):
        """Open a quiz covering all topics in this lecture."""
        # Import here to avoid circular imports
        from quiz_system import open_quiz

        # Create a combined topic string for the quiz
        combined_topic = f"{self.lecture_name} (All Topics)"

        # Close this window and open quiz
        self.window.destroy()
        open_quiz(self.parent, combined_topic, self.colors)


def open_lecture_study(parent, lecture_name: str, lecture_data: dict, colors: dict = None):
    """
    Open a lecture study window.

    Args:
        parent: Parent tkinter window
        lecture_name: e.g., "Lecture 1: Introduction and Probability"
        lecture_data: Dict with 'icon', 'color', 'topics'
        colors: Theme colors dict
    """
    return LectureStudyWindow(parent, lecture_name, lecture_data, colors)
