#!/usr/bin/env python3
"""
Q&A Window - Beautiful, focused window for search results and AI explanations
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import subprocess
import re

from config import CLAUDE_MODELS, DEFAULT_MODEL, DEFAULT_OUTPUT_WORDS, MIN_OUTPUT_WORDS, MAX_OUTPUT_WORDS
from themes import DARK_THEME
import subject_config


class QAWindow:
    """A beautiful window for Q&A - shows sources first, then AI explanation."""

    def __init__(self, parent, question, contexts, model_key=DEFAULT_MODEL, word_count=DEFAULT_OUTPUT_WORDS, colors=None):
        self.parent = parent
        self.question = question
        self.contexts = contexts
        self.model_key = model_key
        self.word_count = word_count
        self.ai_response = None
        self.showing_sources = True

        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Q&A: {question[:50]}...")
        self.window.geometry("1100x800")

        # Use passed colors or default to dark theme
        self.colors = colors if colors else DARK_THEME

        self.window.configure(bg=self.colors["bg"])

        # Font settings
        self.base_font_size = 14
        self.font_size = 14
        self.min_font_size = 11
        self.max_font_size = 22

        self.create_ui()
        self.setup_bindings()
        self.render_sources()

    def create_ui(self):
        """Create the Q&A window UI."""
        # ═══════════════════════════════════════════════════════════
        # HEADER
        # ═══════════════════════════════════════════════════════════
        header = tk.Frame(self.window, bg=self.colors["surface"], height=90)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        header_inner = tk.Frame(header, bg=self.colors["surface"])
        header_inner.pack(fill=tk.BOTH, expand=True, padx=35, pady=18)

        # Left: Question
        title_frame = tk.Frame(header_inner, bg=self.colors["surface"])
        title_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(title_frame, text="🔍  YOUR QUESTION",
                font=("SF Pro Display", 10, "bold"),
                bg=self.colors["surface"],
                fg=self.colors["text_muted"]).pack(anchor="w")

        question_display = self.question if len(self.question) < 70 else self.question[:67] + "..."
        tk.Label(title_frame, text=question_display,
                font=("SF Pro Display", 17, "bold"),
                bg=self.colors["surface"],
                fg=self.colors["text"]).pack(anchor="w", pady=(5, 0))

        # Right: Source count
        info_frame = tk.Frame(header_inner, bg=self.colors["surface"])
        info_frame.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(info_frame, text=f"📚 {len(self.contexts)} sources found",
                font=("SF Pro Display", 12),
                bg=self.colors["surface"],
                fg=self.colors["secondary"]).pack(anchor="e")

        # ═══════════════════════════════════════════════════════════
        # TAB NAVIGATION
        # ═══════════════════════════════════════════════════════════
        nav_frame = tk.Frame(self.window, bg=self.colors["bg"])
        nav_frame.pack(fill=tk.X, padx=35, pady=(15, 0))

        self.sources_tab = tk.Button(nav_frame, text="📄  Sources",
                                     command=self.show_sources,
                                     bg=self.colors["primary"],
                                     fg="white",
                                     font=("SF Pro Display", 12, "bold"),
                                     padx=20, pady=8,
                                     relief=tk.FLAT,
                                     cursor="hand2",
                                     activebackground=self.colors["primary_glow"],
                                     activeforeground="white")
        self.sources_tab.pack(side=tk.LEFT)

        self.ai_tab = tk.Button(nav_frame, text="✨  AI Explanation",
                                command=self.show_ai_response,
                                bg=self.colors["surface"],
                                fg=self.colors["text_muted"],
                                font=("SF Pro Display", 12, "bold"),
                                padx=20, pady=8,
                                relief=tk.FLAT,
                                cursor="hand2",
                                activebackground="#252530",
                                activeforeground=self.colors["text"])
        self.ai_tab.pack(side=tk.LEFT, padx=(8, 0))

        # Status indicator
        self.status_label = tk.Label(nav_frame, text="",
                                     font=("SF Pro Display", 11),
                                     bg=self.colors["bg"],
                                     fg=self.colors["text_muted"])
        self.status_label.pack(side=tk.RIGHT)

        # ═══════════════════════════════════════════════════════════
        # SETTINGS BAR - Model selection and word count (BEFORE content)
        # ═══════════════════════════════════════════════════════════
        settings_bar = tk.Frame(self.window, bg=self.colors["surface"])
        settings_bar.pack(fill=tk.X, padx=35, pady=(15, 0))

        settings_inner = tk.Frame(settings_bar, bg=self.colors["surface"])
        settings_inner.pack(fill=tk.X, padx=25, pady=15)

        # --- Column 1: Model Selection ---
        model_col = tk.Frame(settings_inner, bg=self.colors["surface"])
        model_col.pack(side=tk.LEFT)

        tk.Label(model_col, text="🤖  AI Model",
                font=("SF Pro Display", 11, "bold"),
                bg=self.colors["surface"],
                fg=self.colors["text_muted"]).pack(anchor="w")

        # Model dropdown using ttk.Combobox
        from tkinter import ttk
        model_values = [CLAUDE_MODELS[m]["display_name"] for m in ["haiku", "sonnet", "opus"]]
        self.model_combo = ttk.Combobox(model_col, values=model_values,
                                         state="readonly",
                                         font=("SF Pro Display", 11),
                                         width=18)
        self.model_combo.set(CLAUDE_MODELS[self.model_key]["display_name"])
        self.model_combo.pack(anchor="w", pady=(6, 0))
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_change)

        # Model description
        self.model_desc_label = tk.Label(model_col,
                                          text=CLAUDE_MODELS[self.model_key]["description"],
                                          font=("SF Pro Display", 10),
                                          bg=self.colors["surface"],
                                          fg=self.colors["text_muted"])
        self.model_desc_label.pack(anchor="w", pady=(4, 0))

        # --- Column 2: Response Length ---
        length_col = tk.Frame(settings_inner, bg=self.colors["surface"])
        length_col.pack(side=tk.LEFT, padx=(50, 0))

        tk.Label(length_col, text="📏  Response Length",
                font=("SF Pro Display", 11, "bold"),
                bg=self.colors["surface"],
                fg=self.colors["text_muted"]).pack(anchor="w")

        # Slider row
        slider_row = tk.Frame(length_col, bg=self.colors["surface"])
        slider_row.pack(anchor="w", pady=(6, 0))

        self.word_slider = tk.Scale(slider_row,
                                    from_=MIN_OUTPUT_WORDS,
                                    to=MAX_OUTPUT_WORDS,
                                    orient=tk.HORIZONTAL,
                                    bg=self.colors["surface"],
                                    fg=self.colors["text"],
                                    troughcolor=self.colors["content_bg"],
                                    highlightthickness=0,
                                    sliderrelief=tk.FLAT,
                                    activebackground=self.colors["primary"],
                                    font=("SF Pro Display", 9),
                                    length=180,
                                    showvalue=False,
                                    command=self.on_word_count_change)
        self.word_slider.set(self.word_count)
        self.word_slider.pack(side=tk.LEFT)

        self.word_count_label = tk.Label(slider_row,
                                          text=f"{self.word_count} words",
                                          font=("SF Pro Display", 11, "bold"),
                                          bg=self.colors["surface"],
                                          fg=self.colors["text"])
        self.word_count_label.pack(side=tk.LEFT, padx=(12, 0))

        # Preset buttons
        presets_row = tk.Frame(length_col, bg=self.colors["surface"])
        presets_row.pack(anchor="w", pady=(6, 0))

        for label, value in [("Brief", 100), ("Medium", 250), ("Detailed", 500), ("Long", 800)]:
            btn = tk.Button(presets_row, text=label,
                            command=lambda v=value: self.set_word_count(v),
                            bg="#2a2a3a",
                            fg=self.colors["text_muted"],
                            font=("SF Pro Display", 9),
                            padx=8, pady=2,
                            relief=tk.FLAT,
                            cursor="hand2",
                            activebackground="#3a3a4a",
                            activeforeground=self.colors["text"])
            btn.pack(side=tk.LEFT, padx=(0, 5))

        # --- Column 3: Ask AI Button ---
        action_col = tk.Frame(settings_inner, bg=self.colors["surface"])
        action_col.pack(side=tk.RIGHT)

        self.ask_ai_btn = tk.Button(action_col, text="✨  Ask AI to Explain",
                                    command=self.ask_ai,
                                    bg=self.colors["primary"],
                                    fg="white",
                                    font=("SF Pro Display", 12, "bold"),
                                    padx=20, pady=10,
                                    relief=tk.FLAT,
                                    cursor="hand2",
                                    activebackground=self.colors["primary_glow"],
                                    activeforeground="white")
        self.ask_ai_btn.pack(pady=(10, 0))

        # Copy button (hidden initially, shown after AI response)
        self.copy_btn = tk.Button(action_col, text="📋  Copy",
                                  command=self.copy_response,
                                  bg="#2a2a3a",
                                  fg=self.colors["text_muted"],
                                  font=("SF Pro Display", 10),
                                  padx=10, pady=4,
                                  relief=tk.FLAT,
                                  cursor="hand2",
                                  activebackground="#3a3a4a",
                                  activeforeground=self.colors["text"])

        # ═══════════════════════════════════════════════════════════
        # CONTENT AREA
        # ═══════════════════════════════════════════════════════════
        content_container = tk.Frame(self.window, bg=self.colors["bg"])
        content_container.pack(fill=tk.BOTH, expand=True, padx=35, pady=(15, 15))

        content_card = tk.Frame(content_container, bg=self.colors["content_bg"],
                                highlightbackground=self.colors["content_border"],
                                highlightthickness=1)
        content_card.pack(fill=tk.BOTH, expand=True)

        self.content_text = scrolledtext.ScrolledText(
            content_card,
            font=("Georgia", self.font_size),
            bg=self.colors["content_bg"],
            fg=self.colors["text_reading"],
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=35,
            pady=25,
            spacing1=6,
            spacing2=3,
            spacing3=6,
            insertbackground=self.colors["primary"],
            selectbackground=self.colors["highlight"],
            selectforeground=self.colors["text"],
            cursor="arrow"
        )
        self.content_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.content_text.vbar.configure(
            bg=self.colors["content_bg"],
            troughcolor=self.colors["content_bg"],
            activebackground=self.colors["text_muted"]
        )

        self.configure_text_tags()

        # ═══════════════════════════════════════════════════════════
        # BOTTOM BAR - Zoom controls
        # ═══════════════════════════════════════════════════════════
        bottom_bar = tk.Frame(self.window, bg=self.colors["bg"])
        bottom_bar.pack(fill=tk.X, padx=35, pady=(0, 15))

        # Left: empty for balance
        tk.Frame(bottom_bar, bg=self.colors["bg"]).pack(side=tk.LEFT, expand=True)

        # Center: Zoom controls
        zoom_frame = tk.Frame(bottom_bar, bg=self.colors["bg"])
        zoom_frame.pack(side=tk.LEFT)

        self.create_icon_button(zoom_frame, "−", self.zoom_out).pack(side=tk.LEFT)

        self.zoom_label = tk.Label(zoom_frame, text="100%",
                                   font=("SF Pro Display", 10),
                                   bg=self.colors["bg"],
                                   fg=self.colors["text_muted"],
                                   width=5)
        self.zoom_label.pack(side=tk.LEFT, padx=4)

        self.create_icon_button(zoom_frame, "+", self.zoom_in).pack(side=tk.LEFT)

        # Right: close button
        tk.Frame(bottom_bar, bg=self.colors["bg"]).pack(side=tk.LEFT, expand=True)
        self.create_icon_button(bottom_bar, "✕", self.window.destroy,
                               tooltip="Close").pack(side=tk.RIGHT)

    def create_icon_button(self, parent, text, command, tooltip=None):
        """Create a minimal icon button."""
        btn = tk.Button(parent, text=text,
                       command=command,
                       bg=self.colors["bg"],
                       fg=self.colors["text_muted"],
                       font=("SF Pro Display", 14),
                       relief=tk.FLAT,
                       padx=8, pady=4,
                       cursor="hand2",
                       activebackground=self.colors["surface"],
                       activeforeground=self.colors["text"])
        return btn

    def configure_text_tags(self):
        """Configure text tags for rendering."""
        self.content_text.tag_configure("h1",
            font=("SF Pro Display", 22, "bold"),
            foreground="#c4b5fd",
            spacing1=18, spacing3=10)

        self.content_text.tag_configure("h2",
            font=("SF Pro Display", 18, "bold"),
            foreground="#67e8f9",
            spacing1=15, spacing3=8)

        self.content_text.tag_configure("h3",
            font=("SF Pro Display", 15, "bold"),
            foreground="#6ee7b7",
            spacing1=12, spacing3=6)

        self.content_text.tag_configure("bold",
            font=("Georgia", self.font_size, "bold"),
            foreground="#ffffff")

        self.content_text.tag_configure("source_header",
            font=("SF Pro Display", 15, "bold"),
            foreground="#a78bfa",
            spacing1=12, spacing3=4)

        self.content_text.tag_configure("filename",
            font=("SF Pro Display", 13, "bold"),
            foreground="#ffffff")

        self.content_text.tag_configure("page_info",
            font=("SF Pro Display", 11),
            foreground="#fbbf24")

        self.content_text.tag_configure("relevance",
            font=("SF Pro Display", 11),
            foreground="#22c55e")

        self.content_text.tag_configure("content",
            font=("Georgia", self.font_size),
            foreground="#e2e8f0",
            background="#1e1e28",
            lmargin1=15, lmargin2=15,
            rmargin=15,
            spacing1=8, spacing3=8)

        self.content_text.tag_configure("divider",
            font=("SF Pro Display", 10),
            foreground="#3f3f50")

        self.content_text.tag_configure("normal",
            font=("Georgia", self.font_size),
            foreground=self.colors["text_reading"])

        self.content_text.tag_configure("code_block",
            font=("JetBrains Mono", self.font_size - 1),
            background="#1e1e2e",
            foreground="#fbbf24",
            spacing1=8, spacing3=8,
            lmargin1=15, lmargin2=15)

        self.content_text.tag_configure("bullet",
            font=("Georgia", self.font_size),
            lmargin1=25, lmargin2=45,
            foreground=self.colors["text_secondary"])

    def render_sources(self):
        """Render the RAG sources."""
        self.content_text.configure(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)

        self.content_text.insert(tk.END, "📚 Sources from Your Study Materials\n\n", "h2")

        for i, ctx in enumerate(self.contexts, 1):
            source = ctx['metadata'].get('filename', 'unknown')
            page = ctx['metadata'].get('page', '')
            relevance = ctx['relevance'] * 100

            # Source header
            self.content_text.insert(tk.END, f"━━━ SOURCE {i} ", "source_header")
            self.content_text.insert(tk.END, "━" * 40 + "\n", "divider")

            # Filename
            self.content_text.insert(tk.END, f"📄 {source}\n", "filename")

            # Page and relevance
            info_parts = []
            if page:
                info_parts.append(f"📍 Page {page}")
            info_parts.append(f"✓ {relevance:.0f}% match")
            self.content_text.insert(tk.END, "   " + "   ".join(info_parts) + "\n\n", "relevance")

            # Content
            content = ctx['content'].strip()
            self.content_text.insert(tk.END, content + "\n\n", "content")

        self.content_text.insert(tk.END, "\n", "normal")
        self.content_text.configure(state=tk.DISABLED)

    def render_ai_response(self):
        """Render the AI response."""
        self.content_text.configure(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)

        if not self.ai_response:
            self.content_text.insert(tk.END, "No AI response yet. Click 'Ask AI to Explain'.", "normal")
            self.content_text.configure(state=tk.DISABLED)
            return

        lines = self.ai_response.split('\n')
        in_code_block = False

        for line in lines:
            # Code block handling
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                if in_code_block:
                    self.content_text.insert(tk.END, "\n")
                continue

            if in_code_block:
                self.content_text.insert(tk.END, line + "\n", "code_block")
                continue

            # Headers
            if line.startswith('### '):
                self.content_text.insert(tk.END, line[4:] + "\n", "h3")
            elif line.startswith('## '):
                self.content_text.insert(tk.END, line[3:] + "\n", "h2")
            elif line.startswith('# '):
                self.content_text.insert(tk.END, line[2:] + "\n", "h1")
            # Bullets
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                bullet_text = "  •  " + line.strip()[2:]
                self.content_text.insert(tk.END, bullet_text + "\n", "bullet")
            elif re.match(r'^\d+\.\s', line.strip()):
                self.content_text.insert(tk.END, "  " + line.strip() + "\n", "bullet")
            elif line.strip():
                clean_text = self.clean_inline_markdown(line)
                self.content_text.insert(tk.END, clean_text + "\n", "normal")
            else:
                self.content_text.insert(tk.END, "\n")

        self.content_text.configure(state=tk.DISABLED)

    def clean_inline_markdown(self, text):
        """Clean inline markdown."""
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'[\1]', text)
        return text

    def show_sources(self):
        """Show the sources tab."""
        self.showing_sources = True
        self.sources_tab.config(bg=self.colors["primary"], fg="white",
                                activebackground=self.colors["primary_glow"], activeforeground="white")
        self.ai_tab.config(bg=self.colors["surface"], fg=self.colors["text_muted"],
                           activebackground="#252530", activeforeground=self.colors["text"])
        self.render_sources()

    def show_ai_response(self):
        """Show the AI response tab."""
        self.showing_sources = False
        self.ai_tab.config(bg=self.colors["primary"], fg="white",
                           activebackground=self.colors["primary_glow"], activeforeground="white")
        self.sources_tab.config(bg=self.colors["surface"], fg=self.colors["text_muted"],
                                activebackground="#252530", activeforeground=self.colors["text"])
        self.render_ai_response()

    def on_model_change(self, event=None):
        """Handle model selection change."""
        selected_display = self.model_combo.get()
        for key, config in CLAUDE_MODELS.items():
            if config["display_name"] == selected_display:
                self.model_key = key
                self.model_desc_label.config(text=config["description"])
                break

    def on_word_count_change(self, value):
        """Handle word count slider change."""
        self.word_count = int(float(value))
        self.word_count_label.config(text=f"{self.word_count} words")

    def set_word_count(self, value):
        """Set word count from preset button."""
        self.word_count = value
        self.word_slider.set(value)
        self.word_count_label.config(text=f"{value} words")

    def ask_ai(self):
        """Ask AI to explain based on the sources."""
        # Update UI to show loading
        self.ask_ai_btn.config(text="⏳ Thinking...", state=tk.DISABLED, bg=self.colors["text_muted"])
        self.status_label.config(text=f"Asking {CLAUDE_MODELS[self.model_key]['display_name']}...",
                                 fg=self.colors["warning"])

        # Build context
        context_text = "\n\n".join([
            f"[Source: {ctx['metadata'].get('filename', 'unknown')}]\n{ctx['content']}"
            for ctx in self.contexts
        ])

        model_config = CLAUDE_MODELS[self.model_key]

        full_prompt = f"""Based on these study materials from my {subject_config.COURSE_NAME} course:

{context_text}

---

Please answer this question in approximately {self.word_count} words:
{self.question}

If relevant, include formulas, R code examples, or practical explanations.
Keep your response focused and around {self.word_count} words."""

        def run_claude():
            try:
                result = subprocess.run(
                    ["claude", "-p", full_prompt, "--model", model_config["id"]],
                    capture_output=True,
                    text=True,
                    timeout=model_config["timeout"]
                )

                # Check if the command succeeded
                if result.returncode != 0:
                    error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                    def show_error():
                        self.ask_ai_btn.config(text="✨  Ask AI to Explain", state=tk.NORMAL, bg=self.colors["primary"])
                        self.status_label.config(text="Error occurred", fg=self.colors["warning"])
                        messagebox.showerror("Claude Error", f"Claude CLI returned an error:\n\n{error_msg}")
                    self.window.after(0, show_error)
                    return

                response = result.stdout.strip() if result.stdout else ""
                if not response:
                    def show_error():
                        self.ask_ai_btn.config(text="✨  Ask AI to Explain", state=tk.NORMAL, bg=self.colors["primary"])
                        self.status_label.config(text="Empty response", fg=self.colors["warning"])
                        messagebox.showerror("Error", "Claude returned an empty response. Please try again.")
                    self.window.after(0, show_error)
                    return

                self.ai_response = response

                def update_ui():
                    self.ask_ai_btn.config(text="✓ Asked AI", state=tk.NORMAL, bg=self.colors["success"])
                    self.status_label.config(text="AI response ready!", fg=self.colors["success"])
                    self.copy_btn.pack(pady=(8, 0))
                    # Auto-switch to AI tab
                    self.show_ai_response()

                self.window.after(0, update_ui)

            except subprocess.TimeoutExpired:
                def show_error():
                    self.ask_ai_btn.config(text="✨  Ask AI to Explain", state=tk.NORMAL, bg=self.colors["primary"])
                    self.status_label.config(text="Timeout - try a faster model", fg=self.colors["warning"])
                    messagebox.showerror("Error", "Request timed out. Try a faster model.")
                self.window.after(0, show_error)

            except FileNotFoundError:
                def show_error():
                    self.ask_ai_btn.config(text="✨  Ask AI to Explain", state=tk.NORMAL, bg=self.colors["primary"])
                    self.status_label.config(text="Claude CLI not found", fg=self.colors["warning"])
                    messagebox.showerror("Error", "Claude CLI not found. Please install it with: npm install -g @anthropic-ai/claude-code")
                self.window.after(0, show_error)

            except Exception as e:
                def show_error():
                    self.ask_ai_btn.config(text="✨  Ask AI to Explain", state=tk.NORMAL, bg=self.colors["primary"])
                    self.status_label.config(text="Error occurred", fg=self.colors["warning"])
                    messagebox.showerror("Error", f"Failed to get AI response: {str(e)}")
                self.window.after(0, show_error)

        threading.Thread(target=run_claude, daemon=True).start()

    def copy_response(self):
        """Copy AI response to clipboard."""
        if self.ai_response:
            self.window.clipboard_clear()
            self.window.clipboard_append(self.ai_response)
            self.status_label.config(text="Copied to clipboard!", fg=self.colors["success"])

    def setup_bindings(self):
        """Setup keyboard bindings."""
        self.window.bind("<Command-plus>", lambda e: self.zoom_in())
        self.window.bind("<Command-equal>", lambda e: self.zoom_in())
        self.window.bind("<Command-minus>", lambda e: self.zoom_out())
        self.window.bind("<Command-0>", lambda e: self.zoom_reset())
        self.window.bind("<Escape>", lambda e: self.window.destroy())

    def zoom_in(self):
        if self.font_size < self.max_font_size:
            self.font_size += 1
            self.update_font_size()

    def zoom_out(self):
        if self.font_size > self.min_font_size:
            self.font_size -= 1
            self.update_font_size()

    def zoom_reset(self):
        self.font_size = self.base_font_size
        self.update_font_size()

    def update_font_size(self):
        zoom_percent = int((self.font_size / self.base_font_size) * 100)
        self.zoom_label.config(text=f"{zoom_percent}%")
        self.configure_text_tags()
        if self.showing_sources:
            self.render_sources()
        else:
            self.render_ai_response()


def open_qa_window(parent, question, contexts, model_key=DEFAULT_MODEL, word_count=DEFAULT_OUTPUT_WORDS, colors=None):
    """Open a Q&A window with sources."""
    return QAWindow(parent, question, contexts, model_key, word_count, colors)


# Keep old function for compatibility
def open_qa_result(parent, question, response, sources="", model_name="", colors=None):
    """Open a Q&A result window (legacy - opens window with AI response directly)."""
    # Create a minimal window for direct AI response display
    window = QAWindow(parent, question, [], DEFAULT_MODEL, DEFAULT_OUTPUT_WORDS, colors)
    window.ai_response = response
    window.show_ai_response()
    return window
