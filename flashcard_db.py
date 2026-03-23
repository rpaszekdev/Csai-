#!/usr/bin/env python3
"""
Flashcard Database - Storage and spaced repetition logic
"""

import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import uuid

# Database file
DB_FILE = Path(__file__).parent / "flashcards.json"


def load_db() -> dict:
    """Load the flashcard database."""
    if DB_FILE.exists():
        try:
            return json.loads(DB_FILE.read_text())
        except:
            pass
    return {"decks": {}, "cards": {}}


def save_db(db: dict):
    """Save the flashcard database."""
    DB_FILE.write_text(json.dumps(db, indent=2, default=str))


def create_deck(name: str, topic: str = "") -> str:
    """Create a new deck and return its ID."""
    db = load_db()
    deck_id = str(uuid.uuid4())[:8]

    db["decks"][deck_id] = {
        "id": deck_id,
        "name": name,
        "topic": topic,
        "created": datetime.now().isoformat(),
        "card_ids": []
    }

    save_db(db)
    return deck_id


def add_card(deck_id: str, front: str, back: str, example: str = "") -> str:
    """Add a flashcard to a deck."""
    db = load_db()
    card_id = str(uuid.uuid4())[:8]

    db["cards"][card_id] = {
        "id": card_id,
        "deck_id": deck_id,
        "front": front,
        "back": back,
        "example": example,
        "created": datetime.now().isoformat(),
        # Spaced repetition fields
        "ease_factor": 2.5,  # Starting ease
        "interval": 0,  # Days until next review
        "repetitions": 0,
        "next_review": datetime.now().isoformat(),
        "last_review": None
    }

    if deck_id in db["decks"]:
        db["decks"][deck_id]["card_ids"].append(card_id)

    save_db(db)
    return card_id


def get_deck(deck_id: str) -> Optional[dict]:
    """Get a deck by ID."""
    db = load_db()
    return db["decks"].get(deck_id)


def get_all_decks() -> list:
    """Get all decks."""
    db = load_db()
    return list(db["decks"].values())


def get_cards_for_deck(deck_id: str) -> list:
    """Get all cards in a deck."""
    db = load_db()
    deck = db["decks"].get(deck_id)
    if not deck:
        return []

    cards = []
    for card_id in deck["card_ids"]:
        if card_id in db["cards"]:
            cards.append(db["cards"][card_id])
    return cards


def get_due_cards(deck_id: str = None) -> list:
    """Get cards due for review."""
    db = load_db()
    now = datetime.now()
    due_cards = []

    for card_id, card in db["cards"].items():
        if deck_id and card["deck_id"] != deck_id:
            continue

        next_review = datetime.fromisoformat(card["next_review"])
        if next_review <= now:
            due_cards.append(card)

    return due_cards


def review_card(card_id: str, quality: int):
    """
    Update card after review using SM-2 algorithm.

    Quality ratings:
    0 - Again (complete failure)
    1 - Hard (difficult, with hesitation)
    2 - Good (correct with some effort)
    3 - Easy (perfect response)
    """
    db = load_db()
    card = db["cards"].get(card_id)
    if not card:
        return

    # SM-2 Algorithm adaptation
    if quality < 1:  # Again
        card["repetitions"] = 0
        card["interval"] = 0
    else:
        if card["repetitions"] == 0:
            card["interval"] = 1
        elif card["repetitions"] == 1:
            card["interval"] = 3
        else:
            card["interval"] = int(card["interval"] * card["ease_factor"])

        card["repetitions"] += 1

    # Update ease factor
    card["ease_factor"] = max(1.3, card["ease_factor"] + (0.1 - (3 - quality) * (0.08 + (3 - quality) * 0.02)))

    # Adjust interval based on quality
    if quality == 1:  # Hard
        card["interval"] = max(1, int(card["interval"] * 0.8))
    elif quality == 3:  # Easy
        card["interval"] = int(card["interval"] * 1.3)

    # Set next review date
    card["next_review"] = (datetime.now() + timedelta(days=card["interval"])).isoformat()
    card["last_review"] = datetime.now().isoformat()

    db["cards"][card_id] = card
    save_db(db)


def delete_deck(deck_id: str):
    """Delete a deck and all its cards."""
    db = load_db()

    deck = db["decks"].get(deck_id)
    if deck:
        # Delete all cards in deck
        for card_id in deck["card_ids"]:
            if card_id in db["cards"]:
                del db["cards"][card_id]

        del db["decks"][deck_id]
        save_db(db)


def delete_card(card_id: str):
    """Delete a single card."""
    db = load_db()

    card = db["cards"].get(card_id)
    if card:
        # Remove from deck
        deck_id = card["deck_id"]
        if deck_id in db["decks"]:
            db["decks"][deck_id]["card_ids"].remove(card_id)

        del db["cards"][card_id]
        save_db(db)


def parse_claude_flashcards(text: str, deck_name: str, topic: str = "") -> str:
    """
    Parse Claude's flashcard output and save to database.
    Returns the deck_id of the created deck.
    """
    # Create deck
    deck_id = create_deck(deck_name, topic)

    # Parse cards - look for patterns like:
    # **Card N** or Card N:
    # Front: ... or 📝 Front: ...
    # Back: ... or 💡 Back: ...
    # Example: ... or 📌 Example: ...

    # Split by card markers
    card_patterns = [
        r'\*\*Card\s*\d+\*\*',
        r'Card\s*\d+:?',
        r'#\s*Card\s*\d+',
    ]

    combined_pattern = '|'.join(card_patterns)
    parts = re.split(combined_pattern, text, flags=re.IGNORECASE)

    for part in parts[1:]:  # Skip first empty part
        if not part.strip():
            continue

        # Extract front
        front_match = re.search(r'(?:📝\s*)?(?:Front|Question|Term):\s*(.+?)(?=(?:💡|Back|Answer|Definition|📌|Example|$))', part, re.DOTALL | re.IGNORECASE)
        front = front_match.group(1).strip() if front_match else ""

        # Extract back
        back_match = re.search(r'(?:💡\s*)?(?:Back|Answer|Definition):\s*(.+?)(?=(?:📌|Example|$|\*\*Card))', part, re.DOTALL | re.IGNORECASE)
        back = back_match.group(1).strip() if back_match else ""

        # Extract example
        example_match = re.search(r'(?:📌\s*)?Example:\s*(.+?)(?=$|\*\*Card)', part, re.DOTALL | re.IGNORECASE)
        example = example_match.group(1).strip() if example_match else ""

        # Clean up
        front = re.sub(r'\n+', ' ', front).strip()
        back = re.sub(r'\n+', ' ', back).strip()
        example = re.sub(r'\n+', ' ', example).strip()

        if front and back:
            add_card(deck_id, front, back, example)

    return deck_id


def get_deck_stats(deck_id: str) -> dict:
    """Get statistics for a deck."""
    cards = get_cards_for_deck(deck_id)
    now = datetime.now()

    due = 0
    learning = 0
    mastered = 0

    for card in cards:
        next_review = datetime.fromisoformat(card["next_review"])
        if next_review <= now:
            due += 1

        if card["interval"] < 7:
            learning += 1
        else:
            mastered += 1

    return {
        "total": len(cards),
        "due": due,
        "learning": learning,
        "mastered": mastered
    }
