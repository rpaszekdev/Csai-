#!/usr/bin/env python3
"""
Study Session Window - Beautiful, focused study experience
"""

import tkinter as tk
from tkinter import scrolledtext, font as tkfont
import threading
import subprocess
import json
from pathlib import Path
import sys
import re
import logging
import tempfile
import os
import uuid

sys.path.insert(0, str(Path(__file__).parent))

from study_rag import retrieve_context
import subject_config
from content_storage import (
    save_study_session, get_study_session, study_session_exists, delete_study_session
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


class RCodeExecutor:
    """Execute R code and capture outputs including plots.

    Maintains accumulated context so code blocks can build on each other
    (e.g., first block creates data, second block uses it).
    """

    def __init__(self, temp_dir=None):
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="study_rag_r_")
        self.plot_counter = 0
        self.accumulated_code = []  # Store all previous code blocks
        self.r_data_file = os.path.join(self.temp_dir, "session_data.RData")

    R_CODE_BLOCKLIST = ['system(', 'system2(', 'shell(', 'pipe(', 'file.remove(',
                        'file.rename(', 'unlink(', 'Sys.setenv(', 'download.file(',
                        'url(', 'browseURL(', 'source(', '.Internal(', '.Call(',
                        '.External(', 'readLines(', 'writeLines(', 'cat(file=']

    def _validate_r_code(self, code):
        code_lower = code.lower()
        for blocked in self.R_CODE_BLOCKLIST:
            if blocked.lower() in code_lower:
                return False, f"Blocked R function: {blocked.rstrip('(')}"
        return True, None

    def execute(self, code, timeout=45):
        """Execute R code and return text output and any generated plot paths."""
        result = {
            'output': '',
            'plots': [],
            'error': None
        }

        safe, reason = self._validate_r_code(code)
        if not safe:
            result['error'] = f"Code blocked for safety: {reason}"
            return result

        self.plot_counter += 1
        plot_path = os.path.join(self.temp_dir, f"plot_{self.plot_counter}_{uuid.uuid4().hex[:8]}.png")

        # Build accumulated code from previous blocks
        setup_code = ""
        if os.path.exists(self.r_data_file):
            setup_code = f'load("{self.r_data_file}")\n'

        # Wrap code to capture plots and save environment
        wrapped_code = f'''
# Load previous session data if exists
{setup_code}

# Set up PNG device for any plots
png("{plot_path}", width=800, height=500, res=100)

# Suppress package loading messages and run the code
suppressPackageStartupMessages({{
{code}
}})

# Close the device - this saves the plot if one was created
dev.off()

# Check if plot file has content (was actually created)
if (file.exists("{plot_path}") && file.info("{plot_path}")$size < 1000) {{
    file.remove("{plot_path}")
}}

# Save environment for next code block
save.image(file="{self.r_data_file}")
'''

        try:
            # Run R with the wrapped code
            proc = subprocess.run(
                ['Rscript', '-e', wrapped_code],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.temp_dir
            )

            # Capture output (filter out device messages and save messages)
            output_lines = []
            for line in proc.stdout.split('\n'):
                line_stripped = line.strip()
                # Filter out PNG device messages and other noise
                if (not line_stripped.startswith('null device') and
                    not line_stripped == '1' and
                    'save.image' not in line_stripped):
                    output_lines.append(line)

            result['output'] = '\n'.join(output_lines).strip()

            # Check if plot was created
            if os.path.exists(plot_path) and os.path.getsize(plot_path) > 1000:
                result['plots'].append(plot_path)

            # Check for errors (but ignore warnings)
            if proc.stderr:
                stderr_lower = proc.stderr.lower()
                if 'error' in stderr_lower and 'warning' not in stderr_lower:
                    result['error'] = proc.stderr

        except subprocess.TimeoutExpired:
            result['error'] = "R code execution timed out (45s limit)"
        except FileNotFoundError:
            result['error'] = "R/Rscript not found. Please install R."
        except Exception as e:
            result['error'] = str(e)

        return result

    def reset(self):
        """Reset accumulated context for a new session."""
        self.accumulated_code = []
        if os.path.exists(self.r_data_file):
            try:
                os.remove(self.r_data_file)
            except:
                pass

    def cleanup(self):
        """Clean up temporary files."""
        import shutil
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception:
            pass


class CollapsibleGraphPanel:
    """A collapsible panel for displaying topic-related graphs and visualizations."""

    def __init__(self, parent, colors, on_toggle=None, on_refresh=None):
        self.parent = parent
        self.colors = colors
        self.is_expanded = False
        self.images = []  # List of (PhotoImage, ImageInfo)
        self.on_toggle = on_toggle
        self.on_refresh = on_refresh  # Callback to refresh/re-search images
        self.thumbnail_size = (160, 120)
        self.current_popup = None  # Reference to current popup window
        self.current_image_index = 0  # Track current image in popup

        self.create_panel()

    def create_panel(self):
        """Create the collapsible panel UI."""
        # Main container
        self.container = tk.Frame(self.parent, bg=self.colors.get("graph_panel_bg", self.colors["surface"]))

        # Header (always visible) - clickable to toggle
        self.header = tk.Frame(
            self.container,
            bg=self.colors.get("graph_panel_header", self.colors["surface"]),
            cursor="hand2"
        )
        self.header.pack(fill=tk.X)

        # Inner header padding
        header_inner = tk.Frame(self.header, bg=self.colors.get("graph_panel_header", self.colors["surface"]))
        header_inner.pack(fill=tk.X, padx=15, pady=10)

        # Toggle icon (arrow)
        self.toggle_icon = tk.Label(
            header_inner,
            text="▶",
            font=("SF Pro Display", 11),
            bg=self.colors.get("graph_panel_header", self.colors["surface"]),
            fg=self.colors.get("text_muted", "#71717a")
        )
        self.toggle_icon.pack(side=tk.LEFT, padx=(0, 10))

        # Title
        self.title_label = tk.Label(
            header_inner,
            text="Graph Overview",
            font=("SF Pro Display", 13, "bold"),
            bg=self.colors.get("graph_panel_header", self.colors["surface"]),
            fg=self.colors.get("graph_panel_text", self.colors["text"])
        )
        self.title_label.pack(side=tk.LEFT)

        # Image count badge (hidden initially)
        self.count_badge = tk.Label(
            header_inner,
            text="0",
            font=("SF Pro Display", 10, "bold"),
            bg=self.colors.get("graph_panel_badge", self.colors["primary"]),
            fg="#ffffff",
            padx=8,
            pady=2
        )

        # Loading indicator
        self.loading_label = tk.Label(
            header_inner,
            text="Loading...",
            font=("SF Pro Display", 10, "italic"),
            bg=self.colors.get("graph_panel_header", self.colors["surface"]),
            fg=self.colors.get("text_muted", "#71717a")
        )

        # Refresh button (to re-search for images)
        self.refresh_btn = tk.Label(
            header_inner,
            text="↻",
            font=("SF Pro Display", 14),
            bg=self.colors.get("graph_panel_header", self.colors["surface"]),
            fg=self.colors.get("text_muted", "#71717a"),
            cursor="hand2"
        )
        self.refresh_btn.pack(side=tk.RIGHT, padx=(10, 0))
        self.refresh_btn.bind("<Button-1>", lambda e: self._on_refresh_click())
        self.refresh_btn.bind("<Enter>", lambda e: self.refresh_btn.configure(fg=self.colors.get("primary", "#7c3aed")))
        self.refresh_btn.bind("<Leave>", lambda e: self.refresh_btn.configure(fg=self.colors.get("text_muted", "#71717a")))

        # Content area (hidden by default)
        self.content = tk.Frame(
            self.container,
            bg=self.colors.get("graph_panel_bg", self.colors["surface"])
        )

        # Scrollable canvas for images
        self.canvas = tk.Canvas(
            self.content,
            bg=self.colors.get("graph_panel_bg", self.colors["surface"]),
            height=150,
            highlightthickness=0
        )

        # Horizontal scrollbar
        self.scrollbar = tk.Scrollbar(
            self.content,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview
        )
        self.canvas.configure(xscrollcommand=self.scrollbar.set)

        # Frame inside canvas for images
        self.image_frame = tk.Frame(
            self.canvas,
            bg=self.colors.get("graph_panel_bg", self.colors["surface"])
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.image_frame, anchor="nw")

        # Bind events
        for widget in [self.header, header_inner, self.toggle_icon, self.title_label]:
            widget.bind("<Button-1>", lambda e: self.toggle())
            widget.configure(cursor="hand2")

        # Update scroll region when frame changes
        self.image_frame.bind("<Configure>", self._on_frame_configure)

        # Bind mouse wheel scrolling when hovering over the canvas/content area
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        self.image_frame.bind("<Enter>", self._bind_mousewheel)
        self.image_frame.bind("<Leave>", self._unbind_mousewheel)

    def _on_frame_configure(self, event):
        """Update scroll region when image frame size changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling (horizontal for graph panel)."""
        # On macOS, delta is already in pixels; on Windows/Linux it's in units of 120
        if event.delta:
            # Horizontal scroll with mouse wheel
            self.canvas.xview_scroll(int(-1 * (event.delta / 30)), "units")
        elif event.num == 4:  # Linux scroll up
            self.canvas.xview_scroll(-3, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.xview_scroll(3, "units")

    def _bind_mousewheel(self, event=None):
        """Bind mouse wheel when entering canvas."""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Shift-MouseWheel>", self._on_mousewheel)
        # Linux bindings
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event=None):
        """Unbind mouse wheel when leaving canvas."""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Shift-MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def pack(self, **kwargs):
        """Pack the container."""
        self.container.pack(**kwargs)

    def toggle(self):
        """Toggle the panel expanded/collapsed state."""
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.toggle_icon.config(text="▼")
            self.content.pack(fill=tk.X, padx=15, pady=(0, 15))
            self.canvas.pack(fill=tk.X, expand=True)
            # Only show scrollbar if needed
            if len(self.images) > 3:
                self.scrollbar.pack(fill=tk.X)
        else:
            self.toggle_icon.config(text="▶")
            self.scrollbar.pack_forget()
            self.canvas.pack_forget()
            self.content.pack_forget()

        if self.on_toggle:
            self.on_toggle(self.is_expanded)

    def _on_refresh_click(self):
        """Handle refresh button click."""
        if self.on_refresh:
            self.on_refresh()

    def show_loading(self):
        """Show loading indicator."""
        self.loading_label.pack(side=tk.RIGHT, padx=10)
        self.count_badge.pack_forget()

    def hide_loading(self):
        """Hide loading indicator."""
        self.loading_label.pack_forget()

    def set_images(self, image_infos):
        """
        Load and display images from ImageInfo objects.

        Args:
            image_infos: List of ImageInfo objects or dicts with 'path' and 'description'
        """
        if not HAS_PIL:
            return

        # Clear existing images
        for widget in self.image_frame.winfo_children():
            widget.destroy()
        self.images.clear()

        if not image_infos:
            self.count_badge.pack_forget()
            self.hide_loading()
            return

        # Load and display images
        for info in image_infos:
            try:
                # Handle both ImageInfo objects and dicts
                path = info.path if hasattr(info, 'path') else info.get('path', '')
                description = info.description if hasattr(info, 'description') else info.get('description', '')

                if not Path(path).exists():
                    continue

                # Load and resize image
                img = Image.open(path)
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.images.append((photo, info))

                # Create thumbnail container
                thumb_frame = tk.Frame(
                    self.image_frame,
                    bg=self.colors.get("graph_panel_bg", self.colors["surface"]),
                    padx=8,
                    pady=8
                )
                thumb_frame.pack(side=tk.LEFT)

                # Image label
                img_label = tk.Label(
                    thumb_frame,
                    image=photo,
                    bg=self.colors.get("graph_panel_bg", self.colors["surface"]),
                    cursor="hand2",
                    relief=tk.FLAT,
                    borderwidth=2
                )
                img_label.pack()

                # Bind click to show full image
                img_label.bind("<Button-1>", lambda e, i=info: self.show_full_image(i))

                # Hover effect
                img_label.bind("<Enter>", lambda e, l=img_label: l.configure(
                    relief=tk.SOLID,
                    highlightbackground=self.colors.get("primary", "#7c3aed"),
                    highlightthickness=2
                ))
                img_label.bind("<Leave>", lambda e, l=img_label: l.configure(
                    relief=tk.FLAT,
                    highlightthickness=0
                ))

                # Description tooltip (truncated)
                if description:
                    short_desc = description[:40] + "..." if len(description) > 40 else description
                    desc_label = tk.Label(
                        thumb_frame,
                        text=short_desc,
                        font=("SF Pro Display", 9),
                        bg=self.colors.get("graph_panel_bg", self.colors["surface"]),
                        fg=self.colors.get("text_muted", "#71717a"),
                        wraplength=150
                    )
                    desc_label.pack(pady=(4, 0))

            except Exception as e:
                logging.debug(f"Error loading image {path}: {e}")

        # Update badge
        count = len(self.images)
        if count > 0:
            self.count_badge.config(text=str(count))
            self.count_badge.pack(side=tk.LEFT, padx=10)
        else:
            self.count_badge.pack_forget()

        self.hide_loading()

    def show_full_image(self, info, index=None):
        """Show full-size image in a popup window with arrow key navigation."""
        if not HAS_PIL:
            return

        # Find the index if not provided
        if index is None:
            for i, (_, img_info) in enumerate(self.images):
                img_path = img_info.path if hasattr(img_info, 'path') else img_info.get('path', '')
                info_path = info.path if hasattr(info, 'path') else info.get('path', '')
                if img_path == info_path:
                    index = i
                    break
            if index is None:
                index = 0

        self.current_image_index = index

        path = info.path if hasattr(info, 'path') else info.get('path', '')
        description = info.description if hasattr(info, 'description') else info.get('description', 'Graph')

        # Close existing popup if any
        try:
            if self.current_popup and self.current_popup.winfo_exists():
                self.current_popup.destroy()
        except tk.TclError:
            pass  # Window already destroyed

        # Create popup window as transient (attached to parent)
        popup = tk.Toplevel(self.parent)
        self.current_popup = popup
        popup.title(f"Graph: {description[:50]}...")
        popup.geometry("900x700")
        popup.configure(bg=self.colors.get("bg", "#12131a"))

        # Make popup transient to parent - keeps it attached and returns focus properly
        popup.transient(self.parent)
        popup.grab_set()  # Make it modal so clicks outside don't steal focus

        # Load full-size image
        try:
            img = Image.open(path)
            # Scale to fit window while maintaining aspect ratio
            max_size = (850, 600)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            # Header with description and navigation info
            header = tk.Frame(popup, bg=self.colors.get("surface", "#1e2029"))
            header.pack(fill=tk.X, padx=20, pady=(20, 10))

            # Navigation indicator (e.g., "3 of 7")
            nav_text = f"{index + 1} of {len(self.images)}"
            nav_label = tk.Label(
                header,
                text=nav_text,
                font=("SF Pro Display", 11),
                bg=self.colors.get("surface", "#1e2029"),
                fg=self.colors.get("text_muted", "#71717a")
            )
            nav_label.pack(anchor="e", padx=15, pady=(5, 0))

            tk.Label(
                header,
                text=description,
                font=("SF Pro Display", 14),
                bg=self.colors.get("surface", "#1e2029"),
                fg=self.colors.get("text", "#f8fafc"),
                wraplength=800,
                justify=tk.LEFT
            ).pack(fill=tk.X, padx=15, pady=(5, 10))

            # Image container with navigation buttons
            img_container = tk.Frame(popup, bg=self.colors.get("bg", "#12131a"))
            img_container.pack(expand=True, fill=tk.BOTH, padx=20)

            # Left arrow button
            left_btn = tk.Label(
                img_container,
                text="◀",
                font=("SF Pro Display", 24),
                bg=self.colors.get("bg", "#12131a"),
                fg=self.colors.get("text_muted", "#71717a") if index > 0 else self.colors.get("surface", "#1e2029"),
                cursor="hand2" if index > 0 else "arrow"
            )
            left_btn.pack(side=tk.LEFT, padx=10)
            if index > 0:
                left_btn.bind("<Button-1>", lambda e: self._navigate_image(-1))
                left_btn.bind("<Enter>", lambda e: left_btn.configure(fg=self.colors.get("primary", "#7c3aed")))
                left_btn.bind("<Leave>", lambda e: left_btn.configure(fg=self.colors.get("text_muted", "#71717a")))

            # Image frame
            img_frame = tk.Frame(img_container, bg=self.colors.get("bg", "#12131a"))
            img_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

            img_label = tk.Label(img_frame, image=photo, bg=self.colors.get("bg", "#12131a"))
            img_label.image = photo  # Keep reference to prevent garbage collection
            img_label.pack(expand=True)

            # Right arrow button
            right_btn = tk.Label(
                img_container,
                text="▶",
                font=("SF Pro Display", 24),
                bg=self.colors.get("bg", "#12131a"),
                fg=self.colors.get("text_muted", "#71717a") if index < len(self.images) - 1 else self.colors.get("surface", "#1e2029"),
                cursor="hand2" if index < len(self.images) - 1 else "arrow"
            )
            right_btn.pack(side=tk.RIGHT, padx=10)
            if index < len(self.images) - 1:
                right_btn.bind("<Button-1>", lambda e: self._navigate_image(1))
                right_btn.bind("<Enter>", lambda e: right_btn.configure(fg=self.colors.get("primary", "#7c3aed")))
                right_btn.bind("<Leave>", lambda e: right_btn.configure(fg=self.colors.get("text_muted", "#71717a")))

            # Bottom bar with close button and keyboard hint
            bottom_bar = tk.Frame(popup, bg=self.colors.get("bg", "#12131a"))
            bottom_bar.pack(fill=tk.X, pady=20)

            # Keyboard hint
            hint_label = tk.Label(
                bottom_bar,
                text="Use ← → arrow keys to navigate",
                font=("SF Pro Display", 10),
                bg=self.colors.get("bg", "#12131a"),
                fg=self.colors.get("text_muted", "#71717a")
            )
            hint_label.pack()

            # Close button
            close_btn = tk.Button(
                bottom_bar,
                text="Close",
                command=popup.destroy,
                bg=self.colors.get("primary", "#7c3aed"),
                fg="#ffffff",
                font=("SF Pro Display", 12),
                relief=tk.FLAT,
                padx=30,
                pady=10,
                cursor="hand2"
            )
            close_btn.pack(pady=(10, 0))

            # Bind keyboard navigation
            popup.bind("<Left>", lambda e: self._navigate_image(-1))
            popup.bind("<Right>", lambda e: self._navigate_image(1))
            popup.bind("<Escape>", lambda e: popup.destroy())

            # Focus the popup for keyboard events
            popup.focus_set()

        except Exception as e:
            logging.error(f"Error displaying full image: {e}")
            tk.Label(
                popup,
                text=f"Error loading image: {e}",
                font=("SF Pro Display", 12),
                bg=self.colors.get("bg", "#12131a"),
                fg=self.colors.get("danger", "#ef4444")
            ).pack(expand=True)

    def _navigate_image(self, direction):
        """Navigate to the next or previous image in the popup."""
        new_index = self.current_image_index + direction
        if 0 <= new_index < len(self.images):
            _, info = self.images[new_index]
            self.show_full_image(info, new_index)


class StudySessionWindow:
    """A beautiful, distraction-free study window."""

    def __init__(self, parent, topic, on_complete_callback=None, timer_ref=None, colors=None):
        self.parent = parent
        self.topic = topic
        self.on_complete_callback = on_complete_callback
        self.timer_ref = timer_ref  # Reference to main app for timer state
        self.study_completed = False
        self.sections_read = 0
        self.total_sections = 4

        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Study: {topic}")
        self.window.geometry("1000x750")

        # Use passed colors or default to dark theme
        self.colors = colors if colors else DARK_THEME

        self.window.configure(bg=self.colors["bg"])

        # Zoom settings
        self.base_font_size = 15
        self.font_size = 15
        self.min_font_size = 12
        self.max_font_size = 24

        self.create_ui()
        self.create_floating_mini_timer()
        self.setup_zoom_bindings()
        self.load_study_content()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_ui(self):
        """Create the beautiful study UI."""
        # ═══════════════════════════════════════════════════════════
        # HEADER SECTION - Minimal, elegant
        # ═══════════════════════════════════════════════════════════
        header = tk.Frame(self.window, bg=self.colors["surface"], height=100)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        header_inner = tk.Frame(header, bg=self.colors["surface"])
        header_inner.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

        # Left: Topic title
        title_frame = tk.Frame(header_inner, bg=self.colors["surface"])
        title_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Small label
        tk.Label(title_frame, text="STUDYING",
                font=("SF Pro Display", 10, "bold"),
                bg=self.colors["surface"],
                fg=self.colors["text_muted"]).pack(anchor="w")

        # Topic name - elegant typography
        tk.Label(title_frame, text=self.topic,
                font=("SF Pro Display", 22, "bold"),
                bg=self.colors["surface"],
                fg=self.colors["text"]).pack(anchor="w", pady=(4, 0))

        # Right: Progress indicator
        progress_frame = tk.Frame(header_inner, bg=self.colors["surface"])
        progress_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Progress text
        self.progress_text = tk.Label(progress_frame, text="0 of 3 sections",
                                      font=("SF Pro Display", 11),
                                      bg=self.colors["surface"],
                                      fg=self.colors["text_secondary"])
        self.progress_text.pack(anchor="e")

        # Progress bar container
        progress_bar_frame = tk.Frame(progress_frame, bg=self.colors["progress_bg"],
                                      height=6, width=200)
        progress_bar_frame.pack(anchor="e", pady=(8, 0))
        progress_bar_frame.pack_propagate(False)

        # Progress bar fill
        self.progress_fill = tk.Frame(progress_bar_frame, bg=self.colors["primary"],
                                      height=6, width=0)
        self.progress_fill.place(x=0, y=0, height=6)

        # ═══════════════════════════════════════════════════════════
        # GRAPH OVERVIEW PANEL - Collapsible
        # ═══════════════════════════════════════════════════════════
        if HAS_PIL and HAS_GRAPH_MANAGER:
            self.graph_panel = CollapsibleGraphPanel(
                self.window,
                self.colors,
                on_refresh=self.refresh_graphs
            )
            self.graph_panel.pack(fill=tk.X, padx=40, pady=(15, 0))
        else:
            self.graph_panel = None

        # ═══════════════════════════════════════════════════════════
        # NAVIGATION TABS - Clean, minimal
        # ═══════════════════════════════════════════════════════════
        nav_frame = tk.Frame(self.window, bg=self.colors["bg"])
        nav_frame.pack(fill=tk.X, padx=40, pady=(20, 0))

        self.tab_buttons = []
        self.current_tab = 0

        tab_data = [
            ("Overview", "📋", "Get the big picture"),
            ("Deep Dive", "🔬", "Understand the details"),
            ("Examples", "💡", "See it in practice"),
            ("Mnemonics", "🧠", "Memory tricks"),
            ("My Thoughts", "✍️", "Reflect & synthesize")
        ]

        for i, (name, icon, desc) in enumerate(tab_data):
            tab_btn = self.create_tab_button(nav_frame, i, icon, name, desc)
            self.tab_buttons.append(tab_btn)

        # Tab indicator line
        self.tab_indicator = tk.Frame(nav_frame, bg=self.colors["primary"], height=3)
        self.tab_indicator.place(x=0, y=52, width=120)

        # ═══════════════════════════════════════════════════════════
        # SEARCH BAR - Hidden by default, toggle with Cmd/Ctrl+F
        # ═══════════════════════════════════════════════════════════
        self.search_frame = tk.Frame(self.window, bg=self.colors["surface"])
        self.search_visible = False
        self.search_matches = []
        self.current_match_index = -1

        search_inner = tk.Frame(self.search_frame, bg=self.colors["surface"])
        search_inner.pack(fill=tk.X, padx=40, pady=8)

        # Search icon
        tk.Label(search_inner, text="🔍", font=("SF Pro Display", 12),
                bg=self.colors["surface"], fg=self.colors["text_muted"]).pack(side=tk.LEFT)

        # Search entry
        self.content_search_var = tk.StringVar()
        self.content_search_entry = tk.Entry(search_inner,
            textvariable=self.content_search_var,
            font=("SF Pro Display", 12),
            bg=self.colors["input_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief=tk.FLAT,
            width=30)
        self.content_search_entry.pack(side=tk.LEFT, padx=(8, 0), ipady=4)
        self.content_search_entry.bind("<KeyRelease>", self.on_content_search_key)
        self.content_search_entry.bind("<Return>", lambda e: self.go_to_next_match())
        self.content_search_entry.bind("<Escape>", lambda e: self.hide_search())

        # Match count label
        self.match_count_label = tk.Label(search_inner, text="",
            font=("SF Pro Display", 10),
            bg=self.colors["surface"],
            fg=self.colors["text_muted"])
        self.match_count_label.pack(side=tk.LEFT, padx=(10, 0))

        # Navigation buttons
        nav_btn_frame = tk.Frame(search_inner, bg=self.colors["surface"])
        nav_btn_frame.pack(side=tk.LEFT, padx=(10, 0))

        self.prev_match_btn = tk.Label(nav_btn_frame, text="↑",
            font=("SF Pro Display", 12, "bold"),
            bg=self.colors["surface"], fg=self.colors["text_muted"],
            cursor="hand2", padx=6)
        self.prev_match_btn.pack(side=tk.LEFT)
        self.prev_match_btn.bind("<Button-1>", lambda e: self.go_to_prev_match())
        self.prev_match_btn.bind("<Enter>", lambda e: self.prev_match_btn.configure(fg=self.colors["primary"]))
        self.prev_match_btn.bind("<Leave>", lambda e: self.prev_match_btn.configure(fg=self.colors["text_muted"]))

        self.next_match_btn = tk.Label(nav_btn_frame, text="↓",
            font=("SF Pro Display", 12, "bold"),
            bg=self.colors["surface"], fg=self.colors["text_muted"],
            cursor="hand2", padx=6)
        self.next_match_btn.pack(side=tk.LEFT)
        self.next_match_btn.bind("<Button-1>", lambda e: self.go_to_next_match())
        self.next_match_btn.bind("<Enter>", lambda e: self.next_match_btn.configure(fg=self.colors["primary"]))
        self.next_match_btn.bind("<Leave>", lambda e: self.next_match_btn.configure(fg=self.colors["text_muted"]))

        # Close search button
        close_search_btn = tk.Label(search_inner, text="✕",
            font=("SF Pro Display", 12),
            bg=self.colors["surface"], fg=self.colors["text_muted"],
            cursor="hand2", padx=8)
        close_search_btn.pack(side=tk.RIGHT)
        close_search_btn.bind("<Button-1>", lambda e: self.hide_search())
        close_search_btn.bind("<Enter>", lambda e: close_search_btn.configure(fg=self.colors["text"]))
        close_search_btn.bind("<Leave>", lambda e: close_search_btn.configure(fg=self.colors["text_muted"]))

        # Keyboard shortcut hint
        shortcut = "⌘F" if sys.platform == "darwin" else "Ctrl+F"
        tk.Label(search_inner, text=shortcut,
            font=("SF Pro Display", 9),
            bg=self.colors["surface"],
            fg=self.colors["text_muted"]).pack(side=tk.RIGHT, padx=(0, 10))

        # ═══════════════════════════════════════════════════════════
        # CONTENT AREA - Reading-optimized
        # ═══════════════════════════════════════════════════════════
        content_container = tk.Frame(self.window, bg=self.colors["bg"])
        content_container.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

        # Content card with subtle border
        self.content_card = tk.Frame(content_container, bg=self.colors["content_bg"],
                                highlightbackground=self.colors["content_border"],
                                highlightthickness=1)
        self.content_card.pack(fill=tk.BOTH, expand=True)

        # Scrollable text area
        self.content_text = scrolledtext.ScrolledText(
            self.content_card,
            font=("Georgia", self.font_size),  # Serif font for better reading
            bg=self.colors["content_bg"],
            fg=self.colors["text_reading"],
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=40,
            pady=30,
            spacing1=8,
            spacing2=4,
            spacing3=8,
            insertbackground=self.colors["primary"],
            selectbackground=self.colors["highlight"],
            selectforeground=self.colors["text"],
            cursor="arrow"
        )
        self.content_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Configure scrollbar style (make it subtle)
        self.content_text.vbar.configure(
            bg=self.colors["content_bg"],
            troughcolor=self.colors["content_bg"],
            activebackground=self.colors["text_muted"]
        )

        # Configure text tags for beautiful markdown
        self.configure_text_tags()

        # ═══════════════════════════════════════════════════════════
        # BOTTOM ACTION BAR - Floating style
        # ═══════════════════════════════════════════════════════════
        action_bar = tk.Frame(self.window, bg=self.colors["bg"])
        action_bar.pack(fill=tk.X, padx=40, pady=(0, 25))

        # Left side: Main actions
        left_actions = tk.Frame(action_bar, bg=self.colors["bg"])
        left_actions.pack(side=tk.LEFT)

        # Mark as read - primary action
        self.mark_read_btn = self.create_action_button(
            left_actions, "✓ Mark as Read", self.colors["success"],
            self.mark_section_read, primary=True
        )
        self.mark_read_btn.pack(side=tk.LEFT)

        # Next section
        self.next_btn = self.create_action_button(
            left_actions, "Next →", self.colors["primary"],
            self.next_section
        )
        self.next_btn.pack(side=tk.LEFT, padx=(12, 0))

        # Complete button (hidden initially)
        self.complete_btn = self.create_action_button(
            left_actions, "✨ Complete Session", self.colors["success"],
            self.complete_study, primary=True
        )

        # Right side: Secondary actions
        right_actions = tk.Frame(action_bar, bg=self.colors["bg"])
        right_actions.pack(side=tk.RIGHT)

        # Zoom controls - minimal
        zoom_frame = tk.Frame(right_actions, bg=self.colors["bg"])
        zoom_frame.pack(side=tk.RIGHT)

        self.create_icon_button(zoom_frame, "−", self.zoom_out).pack(side=tk.LEFT)

        self.zoom_label = tk.Label(zoom_frame, text="100%",
                                   font=("SF Pro Display", 10),
                                   bg=self.colors["bg"],
                                   fg=self.colors["text_muted"],
                                   width=5)
        self.zoom_label.pack(side=tk.LEFT, padx=4)

        self.create_icon_button(zoom_frame, "+", self.zoom_in).pack(side=tk.LEFT)

        # Regenerate
        self.create_icon_button(right_actions, "↻", self.regenerate_content,
                               tooltip="Regenerate").pack(side=tk.RIGHT, padx=(0, 20))

        # Close
        self.create_icon_button(right_actions, "✕", self.on_close,
                               tooltip="Close").pack(side=tk.RIGHT, padx=(0, 8))

        # Store content
        self.section_content = ["", "", "", "", ""]  # 5 sections now
        self.sections_marked = [False, False, False, False, False]

        # My Thoughts feature data
        self.my_thoughts_content = ""      # User's raw notes
        self.my_thoughts_summary = ""      # AI-generated summary
        self.key_concepts = []             # Extracted concepts
        self.my_thoughts_container = None  # UI container reference

        # R code executor for running examples
        self.r_executor = RCodeExecutor()
        self.r_plot_images = []  # Keep references to prevent garbage collection

    def create_tab_button(self, parent, index, icon, name, desc):
        """Create a beautiful tab button."""
        btn_frame = tk.Frame(parent, bg=self.colors["bg"], cursor="hand2")
        btn_frame.pack(side=tk.LEFT, padx=(0, 30))

        # Icon
        icon_label = tk.Label(btn_frame, text=icon,
                             font=("SF Pro Display", 18),
                             bg=self.colors["bg"])
        icon_label.pack(side=tk.LEFT)

        # Text container
        text_frame = tk.Frame(btn_frame, bg=self.colors["bg"])
        text_frame.pack(side=tk.LEFT, padx=(8, 0))

        # Name
        name_label = tk.Label(text_frame, text=name,
                             font=("SF Pro Display", 13, "bold"),
                             bg=self.colors["bg"],
                             fg=self.colors["text"] if index == 0 else self.colors["text_muted"])
        name_label.pack(anchor="w")

        # Description
        desc_label = tk.Label(text_frame, text=desc,
                             font=("SF Pro Display", 9),
                             bg=self.colors["bg"],
                             fg=self.colors["text_muted"])
        desc_label.pack(anchor="w")

        # Store references
        btn_frame.name_label = name_label
        btn_frame.desc_label = desc_label
        btn_frame.icon_label = icon_label

        # Bind click events
        for widget in [btn_frame, icon_label, name_label, desc_label, text_frame]:
            widget.bind("<Button-1>", lambda e, idx=index: self.switch_tab(idx))
            widget.configure(cursor="hand2")

        return btn_frame

    def create_floating_mini_timer(self):
        """Create a subtle floating mini-timer in top-right corner."""
        # Container positioned at top-right of the window
        self.mini_timer_frame = tk.Frame(self.window, bg="#2d2d3a")
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
        self.mini_timer_label = tk.Label(inner, text="--:--",
                                         font=("Menlo", 13),
                                         bg="#2d2d3a",
                                         fg="#9ca3af")  # Subtle gray text
        self.mini_timer_label.pack(side=tk.LEFT)

        # Start updating the mini-timer
        self.update_mini_timer()

    def update_mini_timer(self):
        """Update the floating mini-timer display from main app."""
        if not hasattr(self, 'mini_timer_label'):
            return

        # Check if window still exists
        try:
            if not self.window.winfo_exists():
                return
        except:
            return

        # Get timer state from main app reference
        if self.timer_ref:
            try:
                time_remaining = self.timer_ref.time_remaining
                timer_running = self.timer_ref.timer_running
                is_break = self.timer_ref.is_break_time

                minutes = time_remaining // 60
                seconds = time_remaining % 60
                self.mini_timer_label.config(text=f"{minutes:02d}:{seconds:02d}")

                # Update status dot color based on state
                if timer_running:
                    if is_break:
                        # Green for break
                        self.mini_status_dot.config(fg="#10b981")
                        self.mini_timer_label.config(fg="#6ee7b7")
                    else:
                        # Purple for work
                        self.mini_status_dot.config(fg="#8b5cf6")
                        self.mini_timer_label.config(fg="#c4b5fd")
                else:
                    # Gray when paused/stopped
                    self.mini_status_dot.config(fg="#6b7280")
                    self.mini_timer_label.config(fg="#9ca3af")
            except:
                pass

        # Schedule next update
        self.window.after(500, self.update_mini_timer)

    def create_action_button(self, parent, text, color, command, primary=False):
        """Create a styled action button."""
        # Calculate slightly lighter active color
        active_color = self._lighten_color(color)
        btn = tk.Button(parent, text=text,
                       command=command,
                       bg=color,
                       fg="#000000",
                       activebackground=active_color,
                       activeforeground="#000000",
                       font=("SF Pro Display", 12, "bold"),
                       relief=tk.FLAT,
                       padx=20, pady=10,
                       cursor="hand2")
        return btn

    def _lighten_color(self, hex_color):
        """Lighten a hex color slightly for active state."""
        # Convert hex to RGB, lighten, convert back
        hex_color = hex_color.lstrip('#')
        r = min(255, int(hex_color[0:2], 16) + 30)
        g = min(255, int(hex_color[2:4], 16) + 30)
        b = min(255, int(hex_color[4:6], 16) + 30)
        return f"#{r:02x}{g:02x}{b:02x}"

    def create_icon_button(self, parent, icon, command, tooltip=None):
        """Create a minimal icon button."""
        btn = tk.Button(parent, text=icon,
                       command=command,
                       bg=self.colors["bg"],
                       fg=self.colors["text_muted"],
                       activebackground=self.colors["surface"],
                       activeforeground=self.colors["text"],
                       font=("SF Pro Display", 14),
                       relief=tk.FLAT,
                       padx=8, pady=4,
                       cursor="hand2",
                       borderwidth=0,
                       highlightthickness=0)

        # Hover effect
        btn.bind("<Enter>", lambda e: btn.configure(fg=self.colors["text"]))
        btn.bind("<Leave>", lambda e: btn.configure(fg=self.colors["text_muted"]))

        return btn

    def configure_text_tags(self):
        """Configure beautiful text styling tags."""
        scale = self.font_size / self.base_font_size

        # Headers - gradient of purples/cyans
        self.content_text.tag_configure("h1",
            font=("SF Pro Display", int(26 * scale), "bold"),
            foreground="#a78bfa",  # Soft purple
            spacing1=30, spacing3=15)

        self.content_text.tag_configure("h2",
            font=("SF Pro Display", int(20 * scale), "bold"),
            foreground="#22d3ee",  # Cyan
            spacing1=24, spacing3=12)

        self.content_text.tag_configure("h3",
            font=("SF Pro Display", int(17 * scale), "bold"),
            foreground="#34d399",  # Emerald
            spacing1=18, spacing3=9)

        # Text styles
        self.content_text.tag_configure("bold",
            font=("Georgia", int(self.font_size * scale), "bold"),
            foreground=self.colors["text"])

        self.content_text.tag_configure("italic",
            font=("Georgia", int(self.font_size * scale), "italic"),
            foreground=self.colors["text_secondary"])

        # Code - monospace with background
        self.content_text.tag_configure("code",
            font=("JetBrains Mono", int(13 * scale)),
            background="#1e1e2e",
            foreground="#fbbf24",
            spacing1=4, spacing3=4)

        # Lists
        self.content_text.tag_configure("bullet",
            font=("Georgia", int(self.font_size * scale)),
            lmargin1=30, lmargin2=50,
            foreground=self.colors["text_reading"])

        self.content_text.tag_configure("numbered",
            font=("Georgia", int(self.font_size * scale)),
            lmargin1=30, lmargin2=50,
            foreground=self.colors["text_reading"])

        # Highlight/important
        self.content_text.tag_configure("highlight",
            background=self.colors["highlight"],
            foreground=self.colors["text"])

        # Formula blocks - monospace with amber color
        self.content_text.tag_configure("formula",
            font=("JetBrains Mono", int(14 * scale)),
            foreground="#fbbf24",  # Amber
            background="#1e1e2e",
            spacing1=10, spacing3=10,
            lmargin1=40, lmargin2=40)

        # R output - distinguished from code input
        self.content_text.tag_configure("r_output",
            font=("Menlo", int(12 * scale)),
            foreground="#94a3b8",  # Slate gray
            background="#1a1a2e",
            spacing1=6, spacing3=6,
            lmargin1=20, lmargin2=20)

        # R output header label
        self.content_text.tag_configure("r_output_label",
            font=("SF Pro Display", int(10 * scale), "bold"),
            foreground="#6366f1",  # Indigo
            spacing1=12, spacing3=4)

        # R error output
        self.content_text.tag_configure("r_error",
            font=("Menlo", int(11 * scale)),
            foreground="#f87171",  # Red
            background="#1a1a2e",
            spacing1=4, spacing3=4,
            lmargin1=20, lmargin2=20)

        # Search highlight - bright yellow background
        self.content_text.tag_configure("search_highlight",
            background="#fbbf24",  # Amber/yellow
            foreground="#1a1a2e")  # Dark text for contrast

        # Current search match - more prominent
        self.content_text.tag_configure("search_current",
            background="#f97316",  # Orange for current match
            foreground="#ffffff")

    def switch_tab(self, index):
        """Switch to a different section."""
        # Save My Thoughts content if leaving tab 4
        if self.current_tab == 4 and hasattr(self, 'my_thoughts_text'):
            self.my_thoughts_content = self.my_thoughts_text.get("1.0", tk.END).strip()

        # Reset R session when switching tabs (each section is independent)
        if hasattr(self, 'r_executor'):
            self.r_executor.reset()
            self.r_plot_images = []  # Clear image references

        self.current_tab = index

        # Update tab button styles
        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.name_label.configure(fg=self.colors["text"])
            else:
                btn.name_label.configure(fg=self.colors["text_muted"])

        # Animate indicator (simple repositioning)
        # Calculate position based on tab widths (approximately)
        positions = [0, 140, 280, 420, 560]
        self.tab_indicator.place(x=positions[index], width=120)

        # Handle My Thoughts tab separately
        if index == 4:
            self.content_text.pack_forget()
            self.show_my_thoughts_ui()
        else:
            self.hide_my_thoughts_ui()
            self.content_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
            # Show content
            if self.section_content[index]:
                self.render_markdown(self.section_content[index])
            else:
                self.content_text.delete(1.0, tk.END)
                self.content_text.insert(tk.END, "Loading...", "italic")

        self.update_button_states()

    def mark_section_read(self):
        """Mark current section as read."""
        if not self.sections_marked[self.current_tab]:
            self.sections_marked[self.current_tab] = True
            self.sections_read += 1
            self.update_progress()
            self.update_button_states()

    def update_progress(self):
        """Update progress bar and text."""
        self.progress_text.configure(text=f"{self.sections_read} of 4 sections")

        # Animate progress bar width
        progress_width = int((self.sections_read / 4) * 200)
        self.progress_fill.configure(width=progress_width)
        self.progress_fill.place(x=0, y=0, width=progress_width, height=6)

    def next_section(self):
        """Move to next section."""
        if self.current_tab < 3:
            self.switch_tab(self.current_tab + 1)

    def update_button_states(self):
        """Update button visibility and states."""
        # Mark as read button
        if self.sections_marked[self.current_tab]:
            self.mark_read_btn.configure(
                text="✓ Read",
                bg=self.colors["text_muted"],
                state=tk.DISABLED
            )
        else:
            self.mark_read_btn.configure(
                text="✓ Mark as Read",
                bg=self.colors["success"],
                state=tk.NORMAL
            )

        # Next/Complete buttons
        if self.current_tab < 3:
            self.next_btn.pack(side=tk.LEFT, padx=(12, 0))
            self.complete_btn.pack_forget()
        else:
            self.next_btn.pack_forget()
            if self.sections_read >= 4:
                self.complete_btn.pack(side=tk.LEFT, padx=(12, 0))

    def complete_study(self):
        """Complete the study session."""
        self.study_completed = True
        if self.on_complete_callback:
            try:
                self.on_complete_callback(self.topic, self.sections_read, self.total_sections)
            except Exception:
                pass
        self.window.destroy()

    def on_close(self):
        """Handle window close."""
        # Save My Thoughts before closing
        self.save_my_thoughts()

        # Clean up R executor temp files
        if hasattr(self, 'r_executor'):
            self.r_executor.cleanup()

        if self.sections_read > 0 and not self.study_completed:
            if self.sections_read >= 2:
                if self.on_complete_callback:
                    try:
                        self.on_complete_callback(self.topic, self.sections_read, self.total_sections)
                    except Exception:
                        pass
        self.window.destroy()

    # ═══════════════════════════════════════════════════════════
    # MY THOUGHTS TAB - Reflection and Synthesis
    # ═══════════════════════════════════════════════════════════

    def create_my_thoughts_ui(self):
        """Create the My Thoughts tab UI with key concepts, text input, and summary."""
        if self.my_thoughts_container:
            return  # Already created

        # Main container for My Thoughts (inside content_card)
        self.my_thoughts_container = tk.Frame(self.content_card, bg=self.colors["content_bg"])

        # ─── KEY CONCEPTS SECTION ───
        concepts_header = tk.Frame(self.my_thoughts_container, bg=self.colors["content_bg"])
        concepts_header.pack(fill=tk.X, padx=30, pady=(20, 10))

        tk.Label(
            concepts_header,
            text="KEY CONCEPTS",
            font=("SF Pro Display", 11, "bold"),
            fg=self.colors["text_muted"],
            bg=self.colors["content_bg"]
        ).pack(side=tk.LEFT)

        # Refresh button
        refresh_btn = tk.Label(
            concepts_header,
            text="↻ Refresh",
            font=("SF Pro Display", 10),
            fg=self.colors["primary"],
            bg=self.colors["content_bg"],
            cursor="hand2"
        )
        refresh_btn.pack(side=tk.RIGHT)
        refresh_btn.bind("<Button-1>", lambda e: self.extract_key_concepts())

        # Concepts chips container (scrollable horizontally)
        self.concepts_frame = tk.Frame(self.my_thoughts_container, bg=self.colors["content_bg"])
        self.concepts_frame.pack(fill=tk.X, padx=30, pady=(0, 15))

        # Render existing concepts if any
        self.render_concept_chips()

        # ─── TEXT INPUT SECTION ───
        input_label = tk.Label(
            self.my_thoughts_container,
            text="Write your thoughts (click concepts above to insert them)",
            font=("SF Pro Display", 11),
            fg=self.colors["text_muted"],
            bg=self.colors["content_bg"]
        )
        input_label.pack(anchor=tk.W, padx=30, pady=(5, 5))

        # Text input area
        text_frame = tk.Frame(
            self.my_thoughts_container,
            bg=self.colors["surface"],
            highlightbackground=self.colors["content_border"],
            highlightthickness=1
        )
        text_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 15))

        self.my_thoughts_text = scrolledtext.ScrolledText(
            text_frame,
            font=("Georgia", self.font_size),
            bg=self.colors["surface"],
            fg=self.colors["text_reading"],
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=20,
            pady=15,
            insertbackground=self.colors["primary"],
            height=8,
            state=tk.NORMAL  # Explicitly enable editing
        )
        self.my_thoughts_text.pack(fill=tk.BOTH, expand=True)

        # Insert placeholder or existing content
        if self.my_thoughts_content:
            self.my_thoughts_text.insert("1.0", self.my_thoughts_content)
        else:
            self.my_thoughts_text.insert("1.0", "What do you remember? What concepts stood out? Write freely...")
            self.my_thoughts_text.configure(fg=self.colors["text_muted"])
            self.my_thoughts_text.bind("<FocusIn>", self._clear_placeholder)
            self.my_thoughts_text.bind("<Button-1>", self._focus_and_clear)

        # ─── ACTION BUTTONS ───
        btn_frame = tk.Frame(self.my_thoughts_container, bg=self.colors["content_bg"])
        btn_frame.pack(fill=tk.X, padx=30, pady=(0, 15))

        # Check Definitions button
        self.check_btn = tk.Label(
            btn_frame,
            text="🔍 Check My Definitions",
            font=("SF Pro Display", 12, "bold"),
            fg="#ffffff",
            bg=self.colors["primary"],
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.check_btn.pack(side=tk.LEFT)
        self.check_btn.bind("<Button-1>", lambda e: self.check_definitions())
        self.check_btn.bind("<Enter>", lambda e: self.check_btn.configure(bg="#6d28d9"))
        self.check_btn.bind("<Leave>", lambda e: self.check_btn.configure(bg=self.colors["primary"]))

        # Synthesize button
        self.synthesize_btn = tk.Label(
            btn_frame,
            text="✨ Synthesize & Create Flashcards",
            font=("SF Pro Display", 12, "bold"),
            fg="#ffffff",
            bg=self.colors["success"],
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.synthesize_btn.pack(side=tk.LEFT, padx=(15, 0))
        self.synthesize_btn.bind("<Button-1>", lambda e: self.synthesize_notes())
        self.synthesize_btn.bind("<Enter>", lambda e: self.synthesize_btn.configure(bg="#16a34a"))
        self.synthesize_btn.bind("<Leave>", lambda e: self.synthesize_btn.configure(bg=self.colors["success"]))

        # ─── VALIDATION FEEDBACK SECTION ───
        self.validation_frame = tk.Frame(self.my_thoughts_container, bg=self.colors["content_bg"])
        # Initially hidden, shown after checking definitions

        # ─── SUMMARY SECTION ───
        self.summary_frame = tk.Frame(self.my_thoughts_container, bg=self.colors["content_bg"])
        self.summary_frame.pack(fill=tk.X, padx=30, pady=(0, 20))

        tk.Label(
            self.summary_frame,
            text="YOUR SUMMARY",
            font=("SF Pro Display", 11, "bold"),
            fg=self.colors["text_muted"],
            bg=self.colors["content_bg"]
        ).pack(anchor=tk.W, pady=(0, 8))

        summary_card = tk.Frame(
            self.summary_frame,
            bg=self.colors["surface"],
            highlightbackground=self.colors["primary"],
            highlightthickness=1
        )
        summary_card.pack(fill=tk.X)

        self.summary_text = tk.Text(
            summary_card,
            font=("Georgia", self.font_size),
            bg=self.colors["surface"],
            fg=self.colors["text_reading"],
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=20,
            pady=15,
            height=5,
            state=tk.DISABLED
        )
        self.summary_text.pack(fill=tk.X)

        # Show existing summary if any
        if self.my_thoughts_summary:
            self.summary_text.configure(state=tk.NORMAL)
            self.summary_text.insert("1.0", self.my_thoughts_summary)
            self.summary_text.configure(state=tk.DISABLED)
        else:
            self.summary_frame.pack_forget()  # Hide until synthesis

    def _clear_placeholder(self, event=None):
        """Clear placeholder text on focus."""
        current = self.my_thoughts_text.get("1.0", tk.END).strip()
        if current == "What do you remember? What concepts stood out? Write freely...":
            self.my_thoughts_text.delete("1.0", tk.END)
            self.my_thoughts_text.configure(fg=self.colors["text_reading"])

    def _focus_and_clear(self, event):
        """Handle click - focus and clear placeholder."""
        self.my_thoughts_text.focus_set()
        self._clear_placeholder()

    def show_my_thoughts_ui(self):
        """Show the My Thoughts UI."""
        if not self.my_thoughts_container:
            self.create_my_thoughts_ui()
        self.my_thoughts_container.pack(fill=tk.BOTH, expand=True)

        # Auto-extract concepts if not already done and content is loaded
        if not self.key_concepts and any(self.section_content[0:4]):
            self.extract_key_concepts()

    def hide_my_thoughts_ui(self):
        """Hide the My Thoughts UI."""
        if self.my_thoughts_container:
            self.my_thoughts_container.pack_forget()

    def render_concept_chips(self):
        """Render key concepts as clickable chips."""
        # Clear existing chips
        for widget in self.concepts_frame.winfo_children():
            widget.destroy()

        if not self.key_concepts:
            # Show placeholder
            tk.Label(
                self.concepts_frame,
                text="Click 'Refresh' to extract key concepts from your study material",
                font=("SF Pro Display", 11),
                fg=self.colors["text_muted"],
                bg=self.colors["content_bg"]
            ).pack(anchor=tk.W)
            return

        # Create a row of chips
        row_frame = tk.Frame(self.concepts_frame, bg=self.colors["content_bg"])
        row_frame.pack(fill=tk.X, anchor=tk.W)

        for concept in self.key_concepts:
            chip = tk.Label(
                row_frame,
                text=concept,
                font=("SF Pro Display", 11),
                fg="#ffffff",
                bg=self.colors["primary"],
                padx=12,
                pady=6,
                cursor="hand2"
            )
            chip.pack(side=tk.LEFT, padx=(0, 8), pady=4)
            chip.bind("<Button-1>", lambda e, c=concept: self.insert_concept(c))
            chip.bind("<Enter>", lambda e, w=chip: w.configure(bg="#6d28d9"))
            chip.bind("<Leave>", lambda e, w=chip: w.configure(bg=self.colors["primary"]))

    def insert_concept(self, concept):
        """Insert a concept into the text area."""
        if hasattr(self, 'my_thoughts_text'):
            # Clear placeholder if present
            self._clear_placeholder(None)
            self.my_thoughts_text.insert(tk.INSERT, f"{concept} ")
            self.my_thoughts_text.focus_set()

    def extract_key_concepts(self):
        """Extract key concepts from all study sections using Claude."""

        # Gather content from sections 0-3
        section_names = ["Overview", "Deep Dive", "Examples", "Mnemonics"]
        combined_content = "\n\n---\n\n".join([
            f"## {name}\n{content}"
            for name, content in zip(section_names, self.section_content[0:4])
            if content
        ])

        if not combined_content.strip():
            return  # No content to extract from

        # Show loading state
        for widget in self.concepts_frame.winfo_children():
            widget.destroy()
        loading_label = tk.Label(
            self.concepts_frame,
            text="Extracting key concepts...",
            font=("SF Pro Display", 11),
            fg=self.colors["primary"],
            bg=self.colors["content_bg"]
        )
        loading_label.pack(anchor=tk.W)

        def extract_in_thread():
            prompt = f'''Analyze this study material about "{self.topic}" and extract KEY CONCEPTS.

{combined_content}

List 8-15 key concepts, terms, or ideas that a student should understand and be able to recall.
Return ONLY a JSON array of strings, each being a concept/term (2-5 words max each).
Example: ["concept 1", "concept 2", "concept 3"]

Focus on:
- Core terminology and definitions
- Important formulas or methods
- Key relationships or principles
- Common pitfalls to remember

Return ONLY the JSON array, no explanation.'''

            try:
                result = subprocess.run(
                    ["claude", "-p", prompt, "--model", "sonnet"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                output = result.stdout.strip()

                # Try to extract JSON from the response
                # Handle case where response might have extra text
                if '[' in output:
                    start = output.index('[')
                    end = output.rindex(']') + 1
                    json_str = output[start:end]
                    self.key_concepts = json.loads(json_str)
                else:
                    self.key_concepts = []

            except Exception as e:
                print(f"Error extracting concepts: {e}")
                self.key_concepts = []

            # Update UI on main thread
            self.window.after(0, self.render_concept_chips)

        thread = threading.Thread(target=extract_in_thread, daemon=True)
        thread.start()

    def synthesize_notes(self):
        """Synthesize user's raw notes into a coherent summary and create flashcards."""

        # Get user's notes
        user_notes = self.my_thoughts_text.get("1.0", tk.END).strip()

        # Check for placeholder or empty
        if not user_notes or user_notes == "What do you remember? What concepts stood out? Write freely...":
            return

        # Show loading state on button
        original_text = self.synthesize_btn.cget("text")
        self.synthesize_btn.configure(text="Synthesizing...", bg=self.colors["text_muted"])

        def synthesize_in_thread():
            concepts_str = ", ".join(self.key_concepts) if self.key_concepts else "various statistical concepts"

            # Step 1: Synthesize the notes
            prompt = f'''A student has been studying "{self.topic}" and wrote these stream-of-consciousness notes:

---
{user_notes}
---

The key concepts from this topic include: {concepts_str}

---

TASK: Synthesize these raw notes into a brief, coherent summary (3-5 sentences).

RULES:
1. Use the student's OWN words and phrases as much as possible
2. Preserve their insights and connections
3. Organize their scattered thoughts into logical flow
4. Don't add new information they didn't mention
5. Keep their voice and style
6. Make it concise but capture all their main points

Return ONLY the synthesized summary, no preamble or explanation.'''

            try:
                result = subprocess.run(
                    ["claude", "-p", prompt, "--model", "sonnet"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                self.my_thoughts_summary = result.stdout.strip()
            except Exception as e:
                print(f"Error synthesizing notes: {e}")
                self.my_thoughts_summary = "Error: Could not synthesize notes. Please try again."

            # Step 2: Create flashcards from concepts + user definitions
            flashcard_count = 0
            if self.key_concepts and user_notes:
                flashcard_count = self._create_flashcards_from_notes(user_notes)

            # Update UI on main thread
            def update_ui():
                self.synthesize_btn.configure(text=original_text, bg=self.colors["success"])

                # Show summary
                self.summary_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
                self.summary_text.configure(state=tk.NORMAL)
                self.summary_text.delete("1.0", tk.END)

                summary_with_flashcards = self.my_thoughts_summary
                if flashcard_count > 0:
                    summary_with_flashcards += f"\n\n🃏 Created {flashcard_count} flashcard(s) from your notes!"

                self.summary_text.insert("1.0", summary_with_flashcards)
                self.summary_text.configure(state=tk.DISABLED)

            self.window.after(0, update_ui)

        thread = threading.Thread(target=synthesize_in_thread, daemon=True)
        thread.start()

    def _create_flashcards_from_notes(self, user_notes):
        """Extract concept-definition pairs from user notes and create flashcards."""
        from flashcard_db import create_deck, add_card, load_db

        concepts_str = ", ".join(self.key_concepts)

        prompt = f'''Analyze these student notes about "{self.topic}":

---
{user_notes}
---

Key concepts to find definitions for: {concepts_str}

TASK: Extract concept-definition pairs where the student has written their own understanding/definition.

Return a JSON array of objects with "concept" and "definition" keys.
Only include concepts where the student actually wrote something about them.
Use the student's OWN words for the definition, not textbook definitions.

Example format:
[
  {{"concept": "p-value", "definition": "probability of getting results as extreme if null is true"}},
  {{"concept": "confidence interval", "definition": "range where true value probably lies"}}
]

Return ONLY the JSON array. If no clear definitions found, return empty array [].'''

        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--model", "sonnet"],
                capture_output=True,
                text=True,
                timeout=60
            )

            output = result.stdout.strip()

            # Parse JSON
            if '[' in output:
                start = output.index('[')
                end = output.rindex(']') + 1
                pairs = json.loads(output[start:end])
            else:
                return 0

            if not pairs:
                return 0

            # Create deck for this topic's notes
            deck_name = f"My Notes: {self.topic}"

            # Check if deck already exists
            db = load_db()
            existing_deck_id = None
            for deck_id, deck in db["decks"].items():
                if deck["name"] == deck_name:
                    existing_deck_id = deck_id
                    break

            if existing_deck_id:
                deck_id = existing_deck_id
            else:
                deck_id = create_deck(deck_name, self.topic)

            # Add flashcards
            cards_created = 0
            for pair in pairs:
                concept = pair.get("concept", "")
                definition = pair.get("definition", "")
                if concept and definition:
                    add_card(
                        deck_id,
                        front=f"What is {concept}? (Your understanding)",
                        back=definition,
                        example=f"From your notes on: {self.topic}"
                    )
                    cards_created += 1

            return cards_created

        except Exception as e:
            print(f"Error creating flashcards: {e}")
            return 0

    def check_definitions(self):
        """Check user's definitions against correct ones using AI."""

        user_notes = self.my_thoughts_text.get("1.0", tk.END).strip()

        if not user_notes or user_notes == "What do you remember? What concepts stood out? Write freely...":
            return

        if not self.key_concepts:
            return

        # Show loading state
        original_text = self.check_btn.cget("text")
        self.check_btn.configure(text="Checking...", bg=self.colors["text_muted"])

        def check_in_thread():
            concepts_str = ", ".join(self.key_concepts)

            # Get correct definitions from study content
            section_names = ["Overview", "Deep Dive", "Examples", "Mnemonics"]
            study_content = "\n\n".join([
                f"## {name}\n{content}"
                for name, content in zip(section_names, self.section_content[0:4])
                if content
            ])

            prompt = f'''Compare a student's understanding with correct definitions.

STUDY MATERIAL (correct information):
{study_content[:3000]}

STUDENT'S NOTES:
{user_notes}

KEY CONCEPTS TO CHECK: {concepts_str}

TASK: For each concept the student mentioned, evaluate if their understanding is correct.

Return a JSON array with objects containing:
- "concept": the concept name
- "status": "correct", "partially_correct", or "incorrect"
- "student_said": brief quote of what student wrote (or "not mentioned")
- "feedback": brief correction or encouragement (1 sentence max)

Example:
[
  {{"concept": "p-value", "status": "correct", "student_said": "probability under null", "feedback": "Good understanding!"}},
  {{"concept": "Type I error", "status": "incorrect", "student_said": "accepting false null", "feedback": "Type I is rejecting a TRUE null hypothesis."}}
]

Return ONLY the JSON array.'''

            validation_results = []
            try:
                result = subprocess.run(
                    ["claude", "-p", prompt, "--model", "sonnet"],
                    capture_output=True,
                    text=True,
                    timeout=90
                )

                output = result.stdout.strip()
                if '[' in output:
                    start = output.index('[')
                    end = output.rindex(']') + 1
                    validation_results = json.loads(output[start:end])

            except Exception as e:
                print(f"Error checking definitions: {e}")

            # Update UI on main thread
            def update_ui():
                self.check_btn.configure(text=original_text, bg=self.colors["primary"])
                self._show_validation_results(validation_results)

            self.window.after(0, update_ui)

        thread = threading.Thread(target=check_in_thread, daemon=True)
        thread.start()

    def _show_validation_results(self, results):
        """Display validation feedback in the UI."""
        # Clear previous results
        for widget in self.validation_frame.winfo_children():
            widget.destroy()

        if not results:
            return

        # Show the validation frame
        self.validation_frame.pack(fill=tk.X, padx=30, pady=(0, 15))

        # Header
        tk.Label(
            self.validation_frame,
            text="DEFINITION CHECK RESULTS",
            font=("SF Pro Display", 11, "bold"),
            fg=self.colors["text_muted"],
            bg=self.colors["content_bg"]
        ).pack(anchor=tk.W, pady=(0, 10))

        # Results container
        results_card = tk.Frame(
            self.validation_frame,
            bg=self.colors["surface"],
            highlightbackground=self.colors["content_border"],
            highlightthickness=1
        )
        results_card.pack(fill=tk.X)

        for item in results:
            concept = item.get("concept", "")
            status = item.get("status", "")
            feedback = item.get("feedback", "")

            # Status colors and icons
            if status == "correct":
                icon = "✓"
                color = self.colors["success"]
            elif status == "partially_correct":
                icon = "◐"
                color = "#f59e0b"  # amber
            else:
                icon = "✗"
                color = "#ef4444"  # red

            row = tk.Frame(results_card, bg=self.colors["surface"])
            row.pack(fill=tk.X, padx=15, pady=8)

            # Icon
            tk.Label(
                row,
                text=icon,
                font=("SF Pro Display", 14, "bold"),
                fg=color,
                bg=self.colors["surface"]
            ).pack(side=tk.LEFT, padx=(0, 10))

            # Concept and feedback
            text_frame = tk.Frame(row, bg=self.colors["surface"])
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

            tk.Label(
                text_frame,
                text=concept,
                font=("SF Pro Display", 12, "bold"),
                fg=self.colors["text"],
                bg=self.colors["surface"],
                anchor=tk.W
            ).pack(anchor=tk.W)

            tk.Label(
                text_frame,
                text=feedback,
                font=("SF Pro Display", 11),
                fg=self.colors["text_muted"],
                bg=self.colors["surface"],
                anchor=tk.W,
                wraplength=500
            ).pack(anchor=tk.W)

    def save_my_thoughts(self):
        """Save current My Thoughts content to storage."""
        from content_storage import save_study_session, get_study_session

        # Get current text if UI exists
        if hasattr(self, 'my_thoughts_text'):
            content = self.my_thoughts_text.get("1.0", tk.END).strip()
            if content != "What do you remember? What concepts stood out? Write freely...":
                self.my_thoughts_content = content

        # Only save if there's actual content
        if not self.my_thoughts_content and not self.my_thoughts_summary and not self.key_concepts:
            return

        # Get existing session to preserve sections
        existing = get_study_session(self.topic)
        if existing:
            sections = existing.get("sections", {})
        else:
            sections = {
                "overview": self.section_content[0],
                "deep_dive": self.section_content[1],
                "examples": self.section_content[2],
                "mnemonics": self.section_content[3]
            }

        # Save with my_thoughts
        save_study_session(
            self.topic,
            sections,
            my_thoughts={
                "raw_notes": self.my_thoughts_content,
                "summary": self.my_thoughts_summary,
                "key_concepts": self.key_concepts
            }
        )

    def render_markdown(self, text):
        """Render markdown with beautiful formatting."""
        self.content_text.delete(1.0, tk.END)

        lines = text.split('\n')
        i = 0
        prev_was_empty = False

        while i < len(lines):
            line = lines[i]

            # Skip multiple consecutive empty lines
            if not line.strip():
                if not prev_was_empty:
                    self.content_text.insert(tk.END, '\n')
                    prev_was_empty = True
                i += 1
                continue

            prev_was_empty = False

            # Headers (handle ### before ## before #)
            if line.startswith('#### '):
                self.content_text.insert(tk.END, line[5:] + '\n', "h3")
            elif line.startswith('### '):
                self.content_text.insert(tk.END, line[4:] + '\n', "h3")
            elif line.startswith('## '):
                self.content_text.insert(tk.END, line[3:] + '\n', "h2")
            elif line.startswith('# '):
                self.content_text.insert(tk.END, line[2:] + '\n', "h1")

            # LaTeX block formulas ($$...$$)
            elif line.strip().startswith('$$'):
                formula_lines = [line.strip()[2:]]  # Remove opening $$
                # Check if closing $$ is on same line
                if formula_lines[0].endswith('$$'):
                    formula_text = formula_lines[0][:-2]
                else:
                    i += 1
                    while i < len(lines) and not lines[i].strip().endswith('$$'):
                        formula_lines.append(lines[i].strip())
                        i += 1
                    if i < len(lines):
                        formula_lines.append(lines[i].strip()[:-2])  # Remove closing $$
                    formula_text = ' '.join(formula_lines)

                # Clean up LaTeX and display as formula
                formula_display = self.format_latex(formula_text)
                self.content_text.insert(tk.END, f"\n    {formula_display}\n\n", "formula")

            # Code blocks
            elif line.strip().startswith('```'):
                # Extract language identifier if present
                lang_match = re.match(r'^```(\w*)', line.strip())
                lang = lang_match.group(1).lower() if lang_match else ''

                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                code_text = '\n'.join(code_lines)

                if code_text.strip():
                    # Display the code
                    self.content_text.insert(tk.END, '\n' + code_text + '\n', "code")

                    # If this is R code and we're on the Examples tab (index 2), execute it
                    if lang in ('r', 'R', '') and self.current_tab == 2:
                        # Check if this looks like R code (has R-specific patterns)
                        is_r_code = (
                            lang in ('r', 'R') or
                            'library(' in code_text or
                            '<-' in code_text or
                            'ggplot(' in code_text or
                            'lm(' in code_text or
                            'summary(' in code_text or
                            'predict(' in code_text or
                            'data.frame(' in code_text
                        )

                        if is_r_code:
                            self.execute_and_display_r_code(code_text)

            # Bullet points
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                bullet_text = line.strip()[2:]
                bullet_text = self.process_inline_formatting(bullet_text)
                self.content_text.insert(tk.END, "  •  " + bullet_text + '\n', "bullet")

            # Numbered lists
            elif re.match(r'^\s*\d+\.\s', line):
                match = re.match(r'^\s*(\d+)\.\s(.*)$', line)
                if match:
                    num, text_content = match.groups()
                    text_content = self.process_inline_formatting(text_content)
                    self.content_text.insert(tk.END, f"  {num}.  {text_content}\n", "numbered")

            # Regular text
            else:
                processed = self.process_inline_formatting(line)
                self.content_text.insert(tk.END, processed + '\n')

            i += 1

    def execute_and_display_r_code(self, code):
        """Execute R code and display output/plots inline.

        Runs synchronously to ensure code blocks execute in order
        (so data created in one block is available in the next).
        """
        # Insert a visual separator for the output section
        self.content_text.insert(tk.END, "\n")

        try:
            result = self.r_executor.execute(code)

            has_output = result['output'] or result['plots'] or result['error']

            # Show text output if any (like summary() results)
            if result['output']:
                self.content_text.insert(tk.END, "  Output:\n", "r_output_label")
                self.content_text.insert(tk.END, result['output'] + '\n', "r_output")

            # Show error if any
            if result['error']:
                self.content_text.insert(tk.END, "  Error:\n", "r_output_label")
                # Clean up error message
                error_msg = result['error']
                if len(error_msg) > 500:
                    error_msg = error_msg[:500] + "..."
                self.content_text.insert(tk.END, error_msg + '\n', "r_error")

            # Show plots if any
            if result['plots'] and HAS_PIL:
                self.content_text.insert(tk.END, "  Plot:\n", "r_output_label")
                for plot_path in result['plots']:
                    self.display_inline_image(plot_path)

            if has_output:
                self.content_text.insert(tk.END, "\n")

        except Exception as e:
            self.content_text.insert(tk.END, f"  Could not execute R code: {e}\n", "r_error")

    def display_inline_image(self, image_path):
        """Display an image inline in the content text widget."""
        if not HAS_PIL:
            return

        try:
            # Load and resize image
            img = Image.open(image_path)

            # Scale to fit content area (max width ~700px for good display)
            max_width = 700
            max_height = 450
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)

            # Keep reference to prevent garbage collection
            self.r_plot_images.append(photo)

            # Insert image into text widget
            self.content_text.image_create(tk.END, image=photo)
            self.content_text.insert(tk.END, "\n")

        except Exception as e:
            logging.error(f"Failed to display image {image_path}: {e}")
            self.content_text.insert(tk.END, f"  [Could not display plot: {e}]\n", "r_error")

    def format_latex(self, latex):
        """Convert LaTeX to readable plain text."""
        # First pass: handle simple commands that modify single letters/words
        # These need to be processed first so \frac can work with simplified content
        latex = re.sub(r'\\bar\{([^}]+)\}', r'\1̄', latex)  # Add macron
        latex = re.sub(r'\\hat\{([^}]+)\}', r'\1̂', latex)
        latex = re.sub(r'\\tilde\{([^}]+)\}', r'\1̃', latex)
        latex = re.sub(r'\\overline\{([^}]+)\}', r'\1̄', latex)
        latex = re.sub(r'\\text\{([^}]+)\}', r'\1', latex)
        latex = re.sub(r'\\mathrm\{([^}]+)\}', r'\1', latex)
        latex = re.sub(r'\\mathbf\{([^}]+)\}', r'\1', latex)

        # Subscripts and superscripts with braces
        latex = re.sub(r'_\{([^}]+)\}', r'_\1', latex)
        latex = re.sub(r'\^\{([^}]+)\}', r'^\1', latex)

        # Now handle \frac - after inner commands are simplified
        latex = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1) / (\2)', latex)

        # Other structures
        latex = re.sub(r'\\sqrt\{([^}]+)\}', r'√(\1)', latex)
        latex = re.sub(r'\\sqrt', '√', latex)

        # Greek letters
        latex = re.sub(r'\\alpha', 'α', latex)
        latex = re.sub(r'\\beta', 'β', latex)
        latex = re.sub(r'\\gamma', 'γ', latex)
        latex = re.sub(r'\\delta', 'δ', latex)
        latex = re.sub(r'\\epsilon', 'ε', latex)
        latex = re.sub(r'\\sigma', 'σ', latex)
        latex = re.sub(r'\\mu', 'μ', latex)
        latex = re.sub(r'\\rho', 'ρ', latex)
        latex = re.sub(r'\\chi', 'χ', latex)
        latex = re.sub(r'\\pi', 'π', latex)
        latex = re.sub(r'\\lambda', 'λ', latex)
        latex = re.sub(r'\\theta', 'θ', latex)
        latex = re.sub(r'\\omega', 'ω', latex)
        latex = re.sub(r'\\eta', 'η', latex)
        latex = re.sub(r'\\tau', 'τ', latex)

        # Math operators and symbols
        latex = re.sub(r'\\sum', '∑', latex)
        latex = re.sub(r'\\prod', '∏', latex)
        latex = re.sub(r'\\int', '∫', latex)
        latex = re.sub(r'\\infty', '∞', latex)
        latex = re.sub(r'\\neq', '≠', latex)
        latex = re.sub(r'\\leq', '≤', latex)
        latex = re.sub(r'\\geq', '≥', latex)
        latex = re.sub(r'\\approx', '≈', latex)
        latex = re.sub(r'\\pm', '±', latex)
        latex = re.sub(r'\\times', '×', latex)
        latex = re.sub(r'\\cdot', '·', latex)
        latex = re.sub(r'\\ldots', '...', latex)
        latex = re.sub(r'\\dots', '...', latex)
        latex = re.sub(r'\\sim', '~', latex)
        latex = re.sub(r'\\in', '∈', latex)
        latex = re.sub(r'\\subset', '⊂', latex)
        latex = re.sub(r'\\cup', '∪', latex)
        latex = re.sub(r'\\cap', '∩', latex)

        # Clean up
        latex = re.sub(r'\\_', '_', latex)
        latex = re.sub(r'\\left', '', latex)
        latex = re.sub(r'\\right', '', latex)
        latex = re.sub(r'\\[a-zA-Z]+', '', latex)  # Remove remaining LaTeX commands
        latex = re.sub(r'[{}]', '', latex)  # Remove leftover braces
        latex = re.sub(r'\s+', ' ', latex).strip()
        return latex

    def process_inline_formatting(self, text):
        """Process inline markdown and LaTeX formatting."""
        # Handle inline LaTeX $...$
        def replace_inline_latex(match):
            return self.format_latex(match.group(1))

        text = re.sub(r'\$([^$]+)\$', replace_inline_latex, text)

        # Bold
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        # Italic
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        # Inline code
        text = re.sub(r'`([^`]+)`', r'[\1]', text)

        return text

    def setup_zoom_bindings(self):
        """Set up keyboard shortcuts for zoom and search."""
        self.window.bind("<Command-plus>", lambda e: self.zoom_in())
        self.window.bind("<Command-equal>", lambda e: self.zoom_in())
        self.window.bind("<Control-plus>", lambda e: self.zoom_in())
        self.window.bind("<Control-equal>", lambda e: self.zoom_in())
        self.window.bind("<Command-minus>", lambda e: self.zoom_out())
        self.window.bind("<Control-minus>", lambda e: self.zoom_out())
        self.window.bind("<Command-0>", lambda e: self.zoom_reset())
        self.window.bind("<Control-0>", lambda e: self.zoom_reset())
        self.window.bind("<Command-MouseWheel>", self.zoom_mousewheel)
        self.window.bind("<Control-MouseWheel>", self.zoom_mousewheel)
        # Search shortcuts
        self.window.bind("<Command-f>", lambda e: self.toggle_search())
        self.window.bind("<Control-f>", lambda e: self.toggle_search())

    def zoom_in(self):
        """Increase font size."""
        if self.font_size < self.max_font_size:
            self.font_size += 1
            self.apply_zoom()

    def zoom_out(self):
        """Decrease font size."""
        if self.font_size > self.min_font_size:
            self.font_size -= 1
            self.apply_zoom()

    def zoom_reset(self):
        """Reset to default font size."""
        self.font_size = self.base_font_size
        self.apply_zoom()

    def zoom_mousewheel(self, event):
        """Handle mouse wheel zoom."""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def apply_zoom(self):
        """Apply zoom level to content."""
        zoom_percent = int((self.font_size / self.base_font_size) * 100)
        self.zoom_label.config(text=f"{zoom_percent}%")

        # Update main font
        self.content_text.config(font=("Georgia", self.font_size))

        # Reconfigure all tags
        self.configure_text_tags()

    # ═══════════════════════════════════════════════════════════
    # SEARCH FUNCTIONALITY
    # ═══════════════════════════════════════════════════════════

    def toggle_search(self):
        """Toggle search bar visibility."""
        if self.search_visible:
            self.hide_search()
        else:
            self.show_search()
        return "break"  # Prevent default behavior

    def show_search(self):
        """Show the search bar and focus it."""
        if not self.search_visible:
            self.search_frame.pack(fill=tk.X, after=self.tab_buttons[0].master.master)
            self.search_visible = True
        self.content_search_entry.focus_set()
        self.content_search_entry.select_range(0, tk.END)

    def hide_search(self):
        """Hide the search bar and clear highlights."""
        if self.search_visible:
            self.search_frame.pack_forget()
            self.search_visible = False
        self.clear_search_highlights()
        self.content_search_var.set("")
        self.match_count_label.config(text="")
        self.search_matches = []
        self.current_match_index = -1
        # Return focus to content
        self.content_text.focus_set()

    def on_content_search_key(self, event):
        """Handle key release in search entry - live search."""
        query = self.content_search_var.get()
        if query and len(query) >= 1:
            self.perform_content_search(query)
        else:
            self.clear_search_highlights()
            self.match_count_label.config(text="")
            self.search_matches = []
            self.current_match_index = -1

    def perform_content_search(self, query):
        """Search for query in content and highlight all matches."""
        self.clear_search_highlights()
        self.search_matches = []
        self.current_match_index = -1

        if not query:
            self.match_count_label.config(text="")
            return

        # Get all text content
        content = self.content_text.get("1.0", tk.END)

        # Find all matches (case-insensitive)
        query_lower = query.lower()
        content_lower = content.lower()

        start_idx = 0
        while True:
            pos = content_lower.find(query_lower, start_idx)
            if pos == -1:
                break

            # Convert character position to text widget index
            line = content[:pos].count('\n') + 1
            col = pos - content[:pos].rfind('\n') - 1

            start_index = f"{line}.{col}"
            end_index = f"{line}.{col + len(query)}"

            self.search_matches.append((start_index, end_index))
            self.content_text.tag_add("search_highlight", start_index, end_index)

            start_idx = pos + 1

        # Update match count
        count = len(self.search_matches)
        if count == 0:
            self.match_count_label.config(text="No matches", fg="#f87171")
        else:
            self.match_count_label.config(text=f"{count} match{'es' if count != 1 else ''}", fg=self.colors["text_muted"])
            # Automatically go to first match
            self.current_match_index = 0
            self.highlight_current_match()

    def highlight_current_match(self):
        """Highlight the current match distinctly and scroll to it."""
        if not self.search_matches or self.current_match_index < 0:
            return

        # Remove previous current highlight
        self.content_text.tag_remove("search_current", "1.0", tk.END)

        # Add current highlight
        start, end = self.search_matches[self.current_match_index]
        self.content_text.tag_add("search_current", start, end)

        # Ensure search_current tag has higher priority than search_highlight
        self.content_text.tag_raise("search_current")

        # Scroll to make the match visible
        self.content_text.see(start)

        # Update match count to show position
        count = len(self.search_matches)
        self.match_count_label.config(
            text=f"{self.current_match_index + 1} of {count}",
            fg=self.colors["text_muted"]
        )

    def go_to_next_match(self):
        """Go to the next search match."""
        if not self.search_matches:
            return
        self.current_match_index = (self.current_match_index + 1) % len(self.search_matches)
        self.highlight_current_match()

    def go_to_prev_match(self):
        """Go to the previous search match."""
        if not self.search_matches:
            return
        self.current_match_index = (self.current_match_index - 1) % len(self.search_matches)
        self.highlight_current_match()

    def clear_search_highlights(self):
        """Remove all search highlights."""
        self.content_text.tag_remove("search_highlight", "1.0", tk.END)
        self.content_text.tag_remove("search_current", "1.0", tk.END)

    def regenerate_content(self):
        """Delete cached content and regenerate."""
        delete_study_session(self.topic)
        self.section_content = ["", "", "", ""]
        self.load_study_content()

    def refresh_graphs(self):
        """Clear cached graphs and re-search for images from lectures."""
        if not HAS_GRAPH_MANAGER:
            return

        # Clear the cache for this topic
        manager = GraphManager(colors=self.colors)
        manager.clear_topic_cache(self.topic)

        # Reload graphs (will re-search RAG and PDFs)
        self.load_graphs_async()

    def load_graphs_async(self):
        """Load graphs for the topic in the background."""
        if not self.graph_panel or not HAS_GRAPH_MANAGER:
            return

        self.graph_panel.show_loading()

        def load_graphs():
            try:
                # Generate graphs for this topic
                images = get_graphs_for_study_topic(self.topic, self.colors)

                # Update UI on main thread
                def update_panel():
                    if hasattr(self, 'graph_panel') and self.graph_panel:
                        self.graph_panel.set_images(images)

                self.window.after(0, update_panel)

            except Exception as e:
                logging.error(f"Error loading graphs: {e}")

                def hide_loading():
                    if hasattr(self, 'graph_panel') and self.graph_panel:
                        self.graph_panel.hide_loading()

                self.window.after(0, hide_loading)

        threading.Thread(target=load_graphs, daemon=True).start()

    def load_study_content(self):
        """Load or generate study content."""
        self.content_text.delete(1.0, tk.END)

        # Load graphs in background (non-blocking)
        self.load_graphs_async()

        saved_session = get_study_session(self.topic)

        if saved_session and saved_session.get("sections"):
            sections = saved_session["sections"]
            self.section_content[0] = sections.get("overview", "")
            self.section_content[1] = sections.get("deep_dive", "")
            self.section_content[2] = sections.get("examples", "")
            self.section_content[3] = sections.get("mnemonics", "")

            # Load My Thoughts data if available
            my_thoughts = saved_session.get("my_thoughts", {})
            self.my_thoughts_content = my_thoughts.get("raw_notes", "")
            self.my_thoughts_summary = my_thoughts.get("summary", "")
            self.key_concepts = my_thoughts.get("key_concepts", [])

            # Only use cache if all sections are present (including new mnemonics)
            if all(self.section_content[0:4]):  # Check only first 4 sections
                self.render_markdown(self.section_content[0])
                return

        # Show loading state
        self.content_text.insert(tk.END, "Preparing your study session...\n\n", "h2")
        self.content_text.insert(tk.END, "Claude is creating personalized content for you.\n", "italic")

        def load_content():
            try:
                contexts = retrieve_context(self.topic, n_results=6)
                context_text = "\n\n".join([
                    f"[{ctx['metadata'].get('filename', 'unknown')}]\n{ctx['content'][:1000]}"
                    for ctx in contexts
                ])

                prompts = [
                    f"""Based on these study materials about "{self.topic}":

{context_text}

---

Write an OVERVIEW that helps me truly UNDERSTAND this topic.

IMPORTANT: Explain this like you're teaching a friend who is smart but new to {subject_config.SUBJECT_NAME}. Avoid technical jargon - if you must use a technical term, immediately explain what it means in plain English.

Include:
1. What is this, really? (explain the core idea in simple terms, use an analogy if helpful)
2. Why should I care? (when would I actually use this?)
3. Key terms explained simply (define each one like I've never heard it before)
4. The main formula(s) - but explain what each part MEANS, not just what it is

Keep it conversational and clear. I want to understand, not just memorize.""",

                    f"""Based on these study materials about "{self.topic}":

{context_text}

---

Give me a DEEP DIVE that builds real understanding.

IMPORTANT: Write like you're explaining to someone who wants to genuinely understand, not just pass an exam. Avoid dry, textbook language. Use analogies and "think of it like..." explanations.

Cover:
1. How does this actually work? (walk me through the logic step by step)
2. What assumptions are we making? (and why do they matter - what goes wrong if they're violated?)
3. The step-by-step process (like a recipe I can follow)
4. Common mistakes and misconceptions (what do students usually get wrong?)
5. R code if relevant - but explain what each line is doing and WHY

Help me build intuition, not just knowledge.""",

                    f"""Based on these study materials about "{self.topic}":

{context_text}

---

Show me PRACTICAL EXAMPLES that make this click.

IMPORTANT: Use concrete, relatable scenarios. Explain your reasoning out loud as you work through each example, like a tutor sitting next to me.

Include:
1. 2-3 clear examples (start simple, then build complexity)
2. For each example:
   - Set up the scenario in plain language
   - Walk through the solution step by step
   - Show R code with comments explaining what's happening
   - Interpret the results - what do the numbers actually TELL us?
3. Real-world applications (where would I see this in practice?)

Make me feel like "oh, THAT'S what this means!" not just "I memorized this.\"""",

                    f"""Create MNEMONICS for THIS SPECIFIC TOPIC ONLY: "{self.topic}"

Reference materials:
{context_text}

---

STRICT RULES:
1. ONLY create mnemonics for "{self.topic}" - nothing else!
2. Do NOT include mnemonics for other topics - ONLY create mnemonics directly relevant to this specific topic
3. Keep it SHORT - maximum 5-7 mnemonics total
4. Each mnemonic should be 1-2 lines max

FORMAT (keep it brief):
## [Concept from {self.topic}]
**Mnemonic:** [the memory trick]
**Means:** [one-line explanation]

---

Focus ONLY on:
- Key formulas/thresholds specific to {self.topic}
- Steps or methods used in {self.topic}
- Important values to remember for {self.topic}

Be creative and memorable, but STAY ON TOPIC!"""
                ]

                for i, prompt in enumerate(prompts):
                    try:
                        result = subprocess.run(
                            ["claude", "-p", prompt, "--model", "opus"],
                            capture_output=True,
                            text=True,
                            timeout=180
                        )
                        response = result.stdout if result.stdout else result.stderr
                        self.section_content[i] = response

                        if i == self.current_tab:
                            def update(content=response):
                                self.render_markdown(content)
                            self.window.after(0, update)

                    except Exception as e:
                        self.section_content[i] = f"Failed to load: {e}"

                save_study_session(self.topic, {
                    "overview": self.section_content[0],
                    "deep_dive": self.section_content[1],
                    "examples": self.section_content[2],
                    "mnemonics": self.section_content[3]
                })

                def show_first():
                    self.render_markdown(self.section_content[0])
                self.window.after(0, show_first)

            except Exception as e:
                def show_error():
                    self.content_text.delete(1.0, tk.END)
                    self.content_text.insert(tk.END, f"Error: {e}", "italic")
                self.window.after(0, show_error)

        threading.Thread(target=load_content, daemon=True).start()


def open_study_session(parent, topic, on_complete_callback=None, timer_ref=None, colors=None):
    """Open a study session window for a topic."""
    return StudySessionWindow(parent, topic, on_complete_callback, timer_ref, colors)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    def on_complete(topic, sections, total):
        print(f"Completed studying {topic}: {sections}/{total} sections")
        root.quit()

    open_study_session(root, "Linear Regression", on_complete)
    root.mainloop()
