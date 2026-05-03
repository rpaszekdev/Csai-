#!/usr/bin/env python3
"""
Persistent Content Storage - Saves study sessions and quizzes to disk
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

# Storage file paths
STORAGE_DIR = Path(__file__).parent / "saved_content"
STUDY_SESSIONS_FILE = STORAGE_DIR / "study_sessions.json"
QUIZZES_FILE = STORAGE_DIR / "quizzes.json"
POMODORO_FILE = STORAGE_DIR / "pomodoro_sessions.json"
IMAGES_DIR = STORAGE_DIR / "images"
IMAGES_METADATA_FILE = STORAGE_DIR / "images_metadata.json"
COMPREHENSIVE_TESTS_FILE = STORAGE_DIR / "comprehensive_tests.json"
QUESTION_HASHES_FILE = STORAGE_DIR / "question_hashes.json"
LECTURE_SUMMARIES_FILE = STORAGE_DIR / "lecture_summaries.json"
QUESTION_NOTES_FILE = STORAGE_DIR / "question_notes.json"
TARGETED_REQUIZ_FILE = STORAGE_DIR / "targeted_requiz.json"


def ensure_storage_exists():
    """Create storage directory and files if they don't exist."""
    STORAGE_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(exist_ok=True)

    if not STUDY_SESSIONS_FILE.exists():
        STUDY_SESSIONS_FILE.write_text("{}")

    if not QUIZZES_FILE.exists():
        QUIZZES_FILE.write_text("{}")

    if not POMODORO_FILE.exists():
        POMODORO_FILE.write_text("{}")

    if not IMAGES_METADATA_FILE.exists():
        IMAGES_METADATA_FILE.write_text("{}")

    if not COMPREHENSIVE_TESTS_FILE.exists():
        COMPREHENSIVE_TESTS_FILE.write_text("{}")

    if not QUESTION_HASHES_FILE.exists():
        QUESTION_HASHES_FILE.write_text('{"hashes": []}')

    if not LECTURE_SUMMARIES_FILE.exists():
        LECTURE_SUMMARIES_FILE.write_text("{}")

    if not QUESTION_NOTES_FILE.exists():
        QUESTION_NOTES_FILE.write_text("{}")

    if not TARGETED_REQUIZ_FILE.exists():
        TARGETED_REQUIZ_FILE.write_text('{"questions": []}')


def _load_json(file_path: Path) -> Dict:
    """Load JSON from file."""
    ensure_storage_exists()
    try:
        return json.loads(file_path.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save_json(file_path: Path, data: Dict):
    """Save JSON to file."""
    ensure_storage_exists()
    file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ============================================================================
# STUDY SESSIONS
# ============================================================================

def save_study_session(topic: str, sections: Dict[str, str],
                       my_thoughts: Optional[Dict] = None,
                       metadata: Optional[Dict] = None):
    """
    Save a study session to persistent storage.

    Args:
        topic: The topic name (used as key)
        sections: Dict with keys 'overview', 'deep_dive', 'examples', 'mnemonics'
        my_thoughts: Dict with 'raw_notes', 'summary', 'key_concepts'
        metadata: Optional additional data (completion status, etc.)
    """
    sessions = _load_json(STUDY_SESSIONS_FILE)

    # Preserve existing data if updating
    existing = sessions.get(topic, {})
    existing_created = existing.get("created_at", datetime.now().isoformat())
    existing_my_thoughts = existing.get("my_thoughts", {
        "raw_notes": "",
        "summary": "",
        "key_concepts": []
    })

    # Merge my_thoughts if provided
    if my_thoughts:
        existing_my_thoughts.update(my_thoughts)

    sessions[topic] = {
        "topic": topic,
        "sections": sections,
        "my_thoughts": existing_my_thoughts,
        "created_at": existing_created,
        "last_accessed": datetime.now().isoformat(),
        "metadata": metadata or existing.get("metadata", {})
    }

    _save_json(STUDY_SESSIONS_FILE, sessions)


def get_study_session(topic: str) -> Optional[Dict]:
    """
    Retrieve a saved study session.

    Args:
        topic: The topic name

    Returns:
        Session data dict or None if not found
    """
    sessions = _load_json(STUDY_SESSIONS_FILE)

    if topic in sessions:
        # Update last accessed time
        sessions[topic]["last_accessed"] = datetime.now().isoformat()
        _save_json(STUDY_SESSIONS_FILE, sessions)
        return sessions[topic]

    return None


def get_all_study_sessions() -> List[Dict]:
    """Get all saved study sessions, sorted by last accessed."""
    sessions = _load_json(STUDY_SESSIONS_FILE)

    session_list = list(sessions.values())
    session_list.sort(key=lambda x: x.get("last_accessed", ""), reverse=True)

    return session_list


def delete_study_session(topic: str) -> bool:
    """Delete a study session."""
    sessions = _load_json(STUDY_SESSIONS_FILE)

    if topic in sessions:
        del sessions[topic]
        _save_json(STUDY_SESSIONS_FILE, sessions)
        return True

    return False


def study_session_exists(topic: str) -> bool:
    """Check if a study session exists for a topic."""
    sessions = _load_json(STUDY_SESSIONS_FILE)
    return topic in sessions


# ============================================================================
# QUIZZES
# ============================================================================

def save_quiz(topic: str, quiz_content: str, questions: List[Dict] = None, metadata: Optional[Dict] = None):
    """
    Save a quiz to persistent storage.

    Args:
        topic: The topic name (used as key)
        quiz_content: The raw quiz text from Claude
        questions: Parsed questions list (optional)
        metadata: Optional additional data (scores, attempts, etc.)
    """
    quizzes = _load_json(QUIZZES_FILE)

    # If quiz exists, preserve history
    existing = quizzes.get(topic, {})
    attempts = existing.get("attempts", [])

    quizzes[topic] = {
        "topic": topic,
        "quiz_content": quiz_content,
        "questions": questions or [],
        "created_at": existing.get("created_at", datetime.now().isoformat()),
        "last_accessed": datetime.now().isoformat(),
        "attempts": attempts,
        "metadata": metadata or existing.get("metadata", {})
    }

    _save_json(QUIZZES_FILE, quizzes)


def add_quiz_attempt(topic: str, score: int, total: int):
    """Record a quiz attempt."""
    quizzes = _load_json(QUIZZES_FILE)

    if topic in quizzes:
        quizzes[topic]["attempts"].append({
            "score": score,
            "total": total,
            "percentage": round(score / total * 100, 1) if total > 0 else 0,
            "date": datetime.now().isoformat()
        })
        quizzes[topic]["last_accessed"] = datetime.now().isoformat()
        _save_json(QUIZZES_FILE, quizzes)


def get_quiz(topic: str) -> Optional[Dict]:
    """
    Retrieve a saved quiz.

    Args:
        topic: The topic name

    Returns:
        Quiz data dict or None if not found
    """
    quizzes = _load_json(QUIZZES_FILE)

    if topic in quizzes:
        # Update last accessed time
        quizzes[topic]["last_accessed"] = datetime.now().isoformat()
        _save_json(QUIZZES_FILE, quizzes)
        return quizzes[topic]

    return None


def get_all_quizzes() -> List[Dict]:
    """Get all saved quizzes, sorted by last accessed."""
    quizzes = _load_json(QUIZZES_FILE)

    quiz_list = list(quizzes.values())
    quiz_list.sort(key=lambda x: x.get("last_accessed", ""), reverse=True)

    return quiz_list


def delete_quiz(topic: str) -> bool:
    """Delete a quiz."""
    quizzes = _load_json(QUIZZES_FILE)

    if topic in quizzes:
        del quizzes[topic]
        _save_json(QUIZZES_FILE, quizzes)
        return True

    return False


def quiz_exists(topic: str) -> bool:
    """Check if a quiz exists for a topic."""
    quizzes = _load_json(QUIZZES_FILE)
    return topic in quizzes


# ============================================================================
# POMODORO SESSIONS
# ============================================================================

def save_pomodoro_session(
    duration_seconds: int,
    session_type: str = "work",
    topic: Optional[str] = None
):
    """
    Save a completed Pomodoro session.

    Args:
        duration_seconds: Duration of the session in seconds
        session_type: 'work', 'break', or 'long_break'
        topic: Optional topic being studied
    """
    sessions = _load_json(POMODORO_FILE)

    session_id = datetime.now().isoformat()
    sessions[session_id] = {
        "id": session_id,
        "duration_seconds": duration_seconds,
        "duration_minutes": duration_seconds // 60,
        "session_type": session_type,
        "topic": topic,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "created_at": session_id
    }

    _save_json(POMODORO_FILE, sessions)


def get_total_study_time() -> int:
    """
    Get total study time in seconds (work sessions only).

    Returns:
        Total seconds spent studying
    """
    sessions = _load_json(POMODORO_FILE)
    return sum(
        s.get("duration_seconds", 0)
        for s in sessions.values()
        if s.get("session_type") == "work"
    )


def get_total_study_hours() -> float:
    """
    Get total study time in hours.

    Returns:
        Total hours spent studying (as float)
    """
    return get_total_study_time() / 3600


def get_pomodoro_stats() -> Dict:
    """
    Get comprehensive Pomodoro statistics.

    Returns:
        Dict with total_seconds, total_hours, sessions_count, by_date breakdown
    """
    sessions = _load_json(POMODORO_FILE)

    work_sessions = [s for s in sessions.values() if s.get("session_type") == "work"]
    total_seconds = sum(s.get("duration_seconds", 0) for s in work_sessions)

    # Group by date
    by_date = {}
    for s in work_sessions:
        date = s.get("date", "unknown")
        by_date[date] = by_date.get(date, 0) + s.get("duration_seconds", 0)

    return {
        "total_seconds": total_seconds,
        "total_minutes": total_seconds // 60,
        "total_hours": round(total_seconds / 3600, 2),
        "sessions_count": len(work_sessions),
        "by_date": by_date
    }


def get_all_pomodoro_sessions() -> List[Dict]:
    """Get all Pomodoro sessions, sorted by date (newest first)."""
    sessions = _load_json(POMODORO_FILE)
    session_list = list(sessions.values())
    session_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return session_list


# ============================================================================
# UTILITY
# ============================================================================

def get_storage_stats() -> Dict:
    """Get statistics about stored content."""
    sessions = _load_json(STUDY_SESSIONS_FILE)
    quizzes = _load_json(QUIZZES_FILE)

    total_attempts = sum(len(q.get("attempts", [])) for q in quizzes.values())

    return {
        "study_sessions": len(sessions),
        "quizzes": len(quizzes),
        "total_quiz_attempts": total_attempts
    }


def clear_all_storage():
    """Clear all stored content (use with caution)."""
    _save_json(STUDY_SESSIONS_FILE, {})
    _save_json(QUIZZES_FILE, {})


# ============================================================================
# TOPIC IMAGES
# ============================================================================

def save_topic_images(topic: str, images: List[Dict], metadata: Optional[Dict] = None):
    """
    Save image metadata for a study topic.

    Args:
        topic: The topic name (used as key)
        images: List of image info dicts with keys: path, source, description, etc.
        metadata: Optional additional data
    """
    all_images = _load_json(IMAGES_METADATA_FILE)

    all_images[topic] = {
        "topic": topic,
        "images": images,
        "created_at": datetime.now().isoformat(),
        "last_accessed": datetime.now().isoformat(),
        "metadata": metadata or {}
    }

    _save_json(IMAGES_METADATA_FILE, all_images)


def get_topic_images(topic: str) -> Optional[Dict]:
    """
    Retrieve saved images for a topic.

    Args:
        topic: The topic name

    Returns:
        Dict with images list and metadata, or None if not found
    """
    all_images = _load_json(IMAGES_METADATA_FILE)

    if topic in all_images:
        # Update last accessed time
        all_images[topic]["last_accessed"] = datetime.now().isoformat()
        _save_json(IMAGES_METADATA_FILE, all_images)
        return all_images[topic]

    return None


def delete_topic_images(topic: str) -> bool:
    """Delete images for a topic (metadata only, not files)."""
    all_images = _load_json(IMAGES_METADATA_FILE)

    if topic in all_images:
        del all_images[topic]
        _save_json(IMAGES_METADATA_FILE, all_images)
        return True

    return False


def topic_images_exist(topic: str) -> bool:
    """Check if images exist for a topic."""
    all_images = _load_json(IMAGES_METADATA_FILE)
    return topic in all_images


def get_images_dir() -> Path:
    """Get the images storage directory path."""
    ensure_storage_exists()
    return IMAGES_DIR


def get_topic_images_dir(topic: str) -> Path:
    """
    Get or create a directory for a topic's images.

    Args:
        topic: The topic name

    Returns:
        Path to the topic's images directory
    """
    import hashlib
    topic_hash = hashlib.md5(topic.lower().encode()).hexdigest()[:12]
    topic_dir = IMAGES_DIR / topic_hash
    topic_dir.mkdir(parents=True, exist_ok=True)
    return topic_dir


# ============================================================================
# COMPREHENSIVE TESTS
# ============================================================================

def compute_question_hash(question_text: str) -> str:
    """
    Compute a hash for question deduplication.

    Normalizes the question text (lowercase, sorted words) to catch
    semantically similar questions even with minor wording changes.

    Args:
        question_text: The question text

    Returns:
        12-character MD5 hash of normalized text
    """
    import hashlib
    import re

    # Normalize: lowercase, remove punctuation, sort words
    normalized = question_text.lower()
    normalized = re.sub(r'[^\w\s]', '', normalized)
    words = sorted(normalized.split())
    normalized = ' '.join(words)

    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def get_question_hashes() -> set:
    """
    Load all previously asked question hashes.

    Returns:
        Set of question hashes
    """
    data = _load_json(QUESTION_HASHES_FILE)
    return set(data.get("hashes", []))


def add_question_hash(q_hash: str):
    """
    Save a question hash to prevent future duplicates.

    Args:
        q_hash: The question hash to save
    """
    data = _load_json(QUESTION_HASHES_FILE)
    if "hashes" not in data:
        data["hashes"] = []
    if q_hash not in data["hashes"]:
        data["hashes"].append(q_hash)
    _save_json(QUESTION_HASHES_FILE, data)


def add_question_hashes(hashes: List[str]):
    """
    Save multiple question hashes at once.

    Args:
        hashes: List of question hashes to save
    """
    data = _load_json(QUESTION_HASHES_FILE)
    if "hashes" not in data:
        data["hashes"] = []
    existing = set(data["hashes"])
    for h in hashes:
        if h not in existing:
            data["hashes"].append(h)
            existing.add(h)
    _save_json(QUESTION_HASHES_FILE, data)


def is_duplicate_question(question_text: str) -> bool:
    """
    Check if a question has been asked before.

    Args:
        question_text: The question text to check

    Returns:
        True if duplicate, False if new
    """
    q_hash = compute_question_hash(question_text)
    existing = get_question_hashes()
    return q_hash in existing


def save_comprehensive_test(
    test_id: str,
    questions: List[Dict],
    results: Dict,
    topics: List[str],
    use_teacher_mind: bool = False
):
    """
    Save a comprehensive test result.

    Args:
        test_id: Unique test identifier
        questions: List of question dicts with user answers
        results: Dict with 'correct', 'incorrect', 'unknown' lists of question indices
        topics: List of topics included in the test
        use_teacher_mind: Whether Teacher's Mind mode was used
    """
    tests = _load_json(COMPREHENSIVE_TESTS_FILE)

    # Calculate statistics
    total = len(questions)
    correct_count = len(results.get("correct", []))
    incorrect_count = len(results.get("incorrect", []))
    unknown_count = len(results.get("unknown", []))

    tests[test_id] = {
        "id": test_id,
        "date": datetime.now().isoformat(),
        "topics": topics,
        "use_teacher_mind": use_teacher_mind,
        "questions": questions,
        "results": results,
        "stats": {
            "total": total,
            "correct": correct_count,
            "incorrect": incorrect_count,
            "unknown": unknown_count,
            "percentage": round(correct_count / total * 100, 1) if total > 0 else 0
        }
    }

    _save_json(COMPREHENSIVE_TESTS_FILE, tests)

    # Save question hashes for deduplication
    hashes = [compute_question_hash(q.get("question", "")) for q in questions]
    add_question_hashes(hashes)


def get_comprehensive_test(test_id: str) -> Optional[Dict]:
    """
    Retrieve a comprehensive test by ID.

    Args:
        test_id: The test ID

    Returns:
        Test data dict or None if not found
    """
    tests = _load_json(COMPREHENSIVE_TESTS_FILE)
    return tests.get(test_id)


def get_all_comprehensive_tests() -> List[Dict]:
    """
    Get all comprehensive tests, sorted by date (newest first).

    Returns:
        List of test dicts
    """
    tests = _load_json(COMPREHENSIVE_TESTS_FILE)
    test_list = list(tests.values())
    test_list.sort(key=lambda x: x.get("date", ""), reverse=True)
    return test_list


def get_comprehensive_test_stats() -> Dict:
    """
    Get overall statistics for comprehensive tests.

    Returns:
        Dict with total_tests, avg_score, topics_covered, etc.
    """
    tests = _load_json(COMPREHENSIVE_TESTS_FILE)

    if not tests:
        return {
            "total_tests": 0,
            "avg_percentage": 0,
            "total_questions": 0,
            "topics_covered": []
        }

    total_tests = len(tests)
    total_questions = sum(t.get("stats", {}).get("total", 0) for t in tests.values())
    total_correct = sum(t.get("stats", {}).get("correct", 0) for t in tests.values())
    avg_percentage = round(total_correct / total_questions * 100, 1) if total_questions > 0 else 0

    # Unique topics
    all_topics = set()
    for t in tests.values():
        all_topics.update(t.get("topics", []))

    return {
        "total_tests": total_tests,
        "avg_percentage": avg_percentage,
        "total_questions": total_questions,
        "total_correct": total_correct,
        "topics_covered": list(all_topics)
    }


# ============================================================================
# LECTURE SUMMARIES
# ============================================================================

def save_lecture_summary(lecture_name: str, summary: str, key_concepts: List[str] = None,
                         study_guide_connections: List[Dict] = None, metadata: Optional[Dict] = None):
    """
    Save a lecture summary to persistent storage.

    Args:
        lecture_name: The lecture name (e.g., "Lecture 1: Introduction and Probability")
        summary: The AI-generated engaging summary
        key_concepts: List of key concepts from the lecture
        study_guide_connections: How topics connect to study guide
        metadata: Optional additional data
    """
    summaries = _load_json(LECTURE_SUMMARIES_FILE)

    existing = summaries.get(lecture_name, {})

    summaries[lecture_name] = {
        "lecture_name": lecture_name,
        "summary": summary,
        "key_concepts": key_concepts or [],
        "study_guide_connections": study_guide_connections or [],
        "created_at": existing.get("created_at", datetime.now().isoformat()),
        "last_accessed": datetime.now().isoformat(),
        "metadata": metadata or existing.get("metadata", {})
    }

    _save_json(LECTURE_SUMMARIES_FILE, summaries)


def get_lecture_summary(lecture_name: str) -> Optional[Dict]:
    """
    Retrieve a saved lecture summary.

    Args:
        lecture_name: The lecture name

    Returns:
        Summary data dict or None if not found
    """
    summaries = _load_json(LECTURE_SUMMARIES_FILE)

    if lecture_name in summaries:
        summaries[lecture_name]["last_accessed"] = datetime.now().isoformat()
        _save_json(LECTURE_SUMMARIES_FILE, summaries)
        return summaries[lecture_name]

    return None


def lecture_summary_exists(lecture_name: str) -> bool:
    """Check if a lecture summary exists."""
    summaries = _load_json(LECTURE_SUMMARIES_FILE)
    return lecture_name in summaries


def delete_lecture_summary(lecture_name: str) -> bool:
    """Delete a lecture summary."""
    summaries = _load_json(LECTURE_SUMMARIES_FILE)

    if lecture_name in summaries:
        del summaries[lecture_name]
        _save_json(LECTURE_SUMMARIES_FILE, summaries)
        return True

    return False


def get_all_lecture_summaries() -> List[Dict]:
    """Get all saved lecture summaries, sorted by lecture name."""
    summaries = _load_json(LECTURE_SUMMARIES_FILE)
    summary_list = list(summaries.values())
    summary_list.sort(key=lambda x: x.get("lecture_name", ""))
    return summary_list


# ============================================================================
# QUESTION NOTES (for wrong answers)
# ============================================================================

def save_question_note(question_hash: str, note: str, question_data: Dict = None):
    """
    Save a personal note for a specific question.

    Args:
        question_hash: Hash of the question (from compute_question_hash)
        note: The user's personal note
        question_data: Optional dict with question, topic, correct_answer
    """
    notes = _load_json(QUESTION_NOTES_FILE)
    notes[question_hash] = {
        "note": note,
        "question_data": question_data or {},
        "created_at": notes.get(question_hash, {}).get("created_at", datetime.now().isoformat()),
        "updated_at": datetime.now().isoformat()
    }
    _save_json(QUESTION_NOTES_FILE, notes)


def get_question_note(question_hash: str) -> Optional[str]:
    """
    Get the personal note for a question.

    Args:
        question_hash: Hash of the question

    Returns:
        The note text or None if not found
    """
    notes = _load_json(QUESTION_NOTES_FILE)
    if question_hash in notes:
        return notes[question_hash].get("note", "")
    return None


def get_all_question_notes() -> Dict:
    """Get all question notes."""
    return _load_json(QUESTION_NOTES_FILE)


def delete_question_note(question_hash: str) -> bool:
    """Delete a question note."""
    notes = _load_json(QUESTION_NOTES_FILE)
    if question_hash in notes:
        del notes[question_hash]
        _save_json(QUESTION_NOTES_FILE, notes)
        return True
    return False


# ============================================================================
# TARGETED RE-QUIZ
# ============================================================================

def add_to_targeted_requiz(question: Dict) -> bool:
    """
    Add a question to the targeted re-quiz list.

    Args:
        question: Full question dict

    Returns:
        True if added, False if already exists
    """
    data = _load_json(TARGETED_REQUIZ_FILE)
    if "questions" not in data:
        data["questions"] = []

    # Check for duplicate by hash
    q_hash = compute_question_hash(question.get("question", ""))
    existing_hashes = [compute_question_hash(q.get("question", "")) for q in data["questions"]]

    if q_hash not in existing_hashes:
        question_copy = question.copy()
        question_copy["added_at"] = datetime.now().isoformat()
        data["questions"].append(question_copy)
        _save_json(TARGETED_REQUIZ_FILE, data)
        return True
    return False


def get_targeted_requiz_questions() -> List[Dict]:
    """
    Get all questions in the targeted re-quiz list.

    Returns:
        List of question dicts
    """
    data = _load_json(TARGETED_REQUIZ_FILE)
    return data.get("questions", [])


def remove_from_targeted_requiz(question_hash: str) -> bool:
    """
    Remove a question from the targeted re-quiz list.

    Args:
        question_hash: Hash of the question to remove

    Returns:
        True if removed, False if not found
    """
    data = _load_json(TARGETED_REQUIZ_FILE)
    original_len = len(data.get("questions", []))
    data["questions"] = [
        q for q in data.get("questions", [])
        if compute_question_hash(q.get("question", "")) != question_hash
    ]
    if len(data["questions"]) < original_len:
        _save_json(TARGETED_REQUIZ_FILE, data)
        return True
    return False


def clear_targeted_requiz():
    """Clear all targeted re-quiz questions."""
    _save_json(TARGETED_REQUIZ_FILE, {"questions": []})


def get_targeted_requiz_count() -> int:
    """Get the count of questions in the re-quiz list."""
    data = _load_json(TARGETED_REQUIZ_FILE)
    return len(data.get("questions", []))


# ============================================================================
# UTILITY
# ============================================================================

if __name__ == "__main__":
    # Test
    ensure_storage_exists()
    print("Storage initialized")
    print(f"Stats: {get_storage_stats()}")
