#!/usr/bin/env python3
"""
Study Assistant - Web UI
Flask backend for the RAG-powered study system
"""

import os
import json
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import threading

# Import RAG functions
from study_rag import (
    retrieve_context,
    get_vector_store,
    load_all_documents,
    index_documents,
    CONFIG
)

import subject_config

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:5173",
    "http://localhost:5050",
])
limiter = Limiter(get_remote_address, app=app, default_limits=["60 per minute"])
logging.basicConfig(level=logging.INFO)

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    """Get index statistics."""
    try:
        collection = get_vector_store()
        count = collection.count()

        sources = []
        if count > 0:
            sample = collection.peek(limit=min(count, 500))
            source_set = {}
            for meta in sample["metadatas"]:
                filename = meta.get("filename", "unknown")
                file_type = meta.get("type", "unknown")
                if filename not in source_set:
                    source_set[filename] = {
                        "name": filename,
                        "type": file_type,
                        "chunks": 0
                    }
                source_set[filename]["chunks"] += 1
            sources = list(source_set.values())

        return jsonify({
            "success": True,
            "total_chunks": count,
            "sources": sorted(sources, key=lambda x: x["name"]),
            "db_path": str(CONFIG["db_path"])
        })
    except Exception as e:
        logging.exception("Error in /api/stats")
        return jsonify({"success": False, "error": "An internal error occurred"}), 500


VALID_QUIZ_TYPES = {'multiple_choice', 'open_ended', 'flashcard'}

@app.route('/api/query', methods=['POST'])
def query():
    """Query the RAG system."""
    data = request.json or {}
    question = data.get('question', '')
    n_results = min(max(int(data.get('n_results', 5)), 1), 20)

    if not question:
        return jsonify({"success": False, "error": "No question provided"}), 400

    if len(question) > 2000:
        return jsonify({"success": False, "error": "Question too long (max 2000 chars)"}), 400

    try:
        contexts = retrieve_context(question, n_results=n_results)

        results = []
        for ctx in contexts:
            results.append({
                "content": ctx["content"],
                "source": ctx["metadata"].get("filename", "unknown"),
                "page": ctx["metadata"].get("page", None),
                "relevance": round(ctx["relevance"] * 100, 1)
            })

        return jsonify({
            "success": True,
            "question": question,
            "results": results
        })
    except Exception as e:
        logging.exception("Error in /api/query")
        return jsonify({"success": False, "error": "An internal error occurred"}), 500


@app.route('/api/quiz', methods=['POST'])
def generate_quiz():
    """Generate quiz questions based on context."""
    data = request.json or {}
    quiz_type = data.get('type', 'multiple_choice')
    if quiz_type not in VALID_QUIZ_TYPES:
        return jsonify({"success": False, "error": "Invalid quiz type"}), 400
    topic = data.get('topic', '')
    if topic and len(topic) > 500:
        return jsonify({"success": False, "error": "Topic too long"}), 400
    count = min(max(int(data.get('count', 5)), 1), 20)

    # Get relevant context
    search_query = topic if topic else subject_config.FALLBACK_QUERY
    contexts = retrieve_context(search_query, n_results=8)

    context_text = "\n\n".join([
        f"[From {ctx['metadata'].get('filename', 'unknown')}]\n{ctx['content']}"
        for ctx in contexts
    ])

    return jsonify({
        "success": True,
        "quiz_type": quiz_type,
        "topic": topic,
        "count": count,
        "context": context_text,
        "sources": list(set(ctx['metadata'].get('filename', 'unknown') for ctx in contexts))
    })


@app.route('/api/topics')
def get_topics():
    """Get available topics."""
    return jsonify({"success": True, "topics": subject_config.API_TOPICS})


@app.route('/api/reindex', methods=['POST'])
@limiter.limit("1 per minute")
def reindex():
    """Reindex all materials."""
    try:
        index_documents()
        return jsonify({"success": True, "message": "Reindexing complete!"})
    except Exception as e:
        logging.exception("Error in /api/reindex")
        return jsonify({"success": False, "error": "An internal error occurred"}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print(f"\n📚 {subject_config.SUBJECT_NAME} Study Assistant")
    print("=" * 40)
    print("Open http://localhost:5050 in your browser")
    print("=" * 40 + "\n")

    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", port=5050)
