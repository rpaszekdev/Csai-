"""
Configuration settings for the Study RAG system.

Subject-specific settings live in subject_config.py.
This file contains app-level settings (models, quiz, theme).
"""
import os
import json
from pathlib import Path

import subject_config

# Base paths
BASE_DIR = Path(__file__).parent
HOME_DIR = Path.home()

# Material paths - loaded from subject config
MATERIALS_PATHS = subject_config.MATERIALS_DIRS

# Vector database settings
CHROMA_DB_PATH = BASE_DIR / "chroma_db"
COLLECTION_NAME = f"{subject_config.SUBJECT_SHORT}_materials"

# Document processing settings
CHUNK_SIZE = 800  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks for context

# Embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, efficient sentence transformer

# Claude Code integration
# The system will use the Claude Code CLI for generating responses
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"

# Claude Model Options for Q&A
# Uses aliases supported by Claude Code CLI (haiku, sonnet, opus)
CLAUDE_MODELS = {
    "haiku": {
        "id": "haiku",
        "display_name": "Haiku (Fast)",
        "description": "Quick responses, best for simple questions",
        "context_chunks": 3,
        "timeout": 60
    },
    "sonnet": {
        "id": "sonnet",
        "display_name": "Sonnet (Balanced)",
        "description": "Good balance of speed and quality",
        "context_chunks": 5,
        "timeout": 120
    },
    "opus": {
        "id": "opus",
        "display_name": "Opus (Thorough)",
        "description": "Most comprehensive, best for complex topics",
        "context_chunks": 8,
        "timeout": 180
    }
}

DEFAULT_MODEL = "sonnet"
DEFAULT_OUTPUT_WORDS = 250
MIN_OUTPUT_WORDS = 50
MAX_OUTPUT_WORDS = 1000

# Quiz settings
QUIZ_TYPES = ["multiple_choice", "open_ended", "flashcard"]
DEFAULT_QUIZ_LENGTH = 5

# Theme settings
DEFAULT_THEME = "dark"
USER_PREFERENCES_FILE = BASE_DIR / "user_preferences.json"


def get_user_preferences() -> dict:
    """Load user preferences from file.

    Returns:
        Dictionary with user preferences (theme, onboarding_complete, etc.)
    """
    if USER_PREFERENCES_FILE.exists():
        try:
            return json.loads(USER_PREFERENCES_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    return {"theme": DEFAULT_THEME, "onboarding_complete": False}


def save_user_preferences(prefs: dict) -> None:
    """Save user preferences to file.

    Args:
        prefs: Dictionary of user preferences to save
    """
    try:
        USER_PREFERENCES_FILE.write_text(json.dumps(prefs, indent=2))
    except IOError:
        pass
