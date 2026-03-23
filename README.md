# Study RAG - Subject-Agnostic Study Assistant

A RAG (Retrieval-Augmented Generation) powered study application that works with **any subject**. It indexes your lecture materials (PDFs, transcripts, markdown notes) and provides an interactive study interface with quizzes, flashcards, and Q&A powered by Claude.

## Quick Start

1. **Edit `subject_config.py`** — set your subject name, materials paths, and lecture structure
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Index your materials**: `python study_rag.py --index`
4. **Launch the UI**: `python ui.py`

## Configuring for Your Subject

The **only file you need to edit** is `subject_config.py`. It contains:

- `SUBJECT_NAME` / `COURSE_NAME` — displayed throughout the app
- `MATERIALS_DIRS` — paths to your lecture PDFs, transcripts, notes
- `STUDY_GUIDE` — your lecture/topic structure (drives the UI)
- `LECTURE_PDF_MAP` — optional direct lecture-to-PDF mapping
- `TOPIC_KEYWORDS` — keywords for smart search and graph generation
- `FALLBACK_QUERY` — default search query for your subject
- `API_TOPICS` — topic list for the web UI

See `subject_configs/` for complete examples:
- `cognitive_neuroscience.py` — cognitive neuroscience course
- `statistics.py` — statistics course

## Features

- **Document Indexing**: Automatically indexes PDFs, markdown files, and text transcripts
- **Semantic Search**: Find relevant content using natural language queries
- **AI-Powered Q&A**: Ask questions and get answers grounded in your study materials
- **Quiz System**: Generate quizzes (multiple choice, open-ended) from your content
- **Flashcard Review**: Spaced repetition flashcard system
- **Progress Tracking**: Track your study sessions and quiz performance
- **Pomodoro Timer**: Built-in focus timer

## Prerequisites

- Python 3.10+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated

## Installation

```bash
git clone <repo-url>
cd study-rag
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Terminal UI (Recommended)

```bash
python ui.py
```

### Web Interface

```bash
python app.py
```

### CLI

```bash
python study_rag.py --index                    # Index materials
python study_rag.py --query "your question"    # Query
python study_rag.py --quiz multiple_choice     # Generate quiz
python study_rag.py --list-topics              # List topics
```

## Project Structure

```
study-rag/
├── subject_config.py      # YOUR CONFIG — edit this for your subject
├── subject_configs/        # Example configs for different subjects
├── study_rag.py           # Core RAG engine
├── ui.py                  # Desktop UI (tkinter)
├── app.py                 # Web UI (Flask)
├── config.py              # App-level settings (models, theme)
├── quiz_system.py         # Quiz generation and scoring
├── flashcard_db.py        # Flashcard storage
├── flashcard_review.py    # Spaced repetition
├── study_session.py       # Study session tracking
├── lecture_study.py       # Lecture summary generation
├── document_loader.py     # Document parsing (PDF, MD, TXT)
├── graph_manager.py       # Visualization generation
└── requirements.txt       # Python dependencies
```

## License

MIT
# Csai-
