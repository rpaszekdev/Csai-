#!/usr/bin/env python3
"""
Claude Code Integration Hook for Stats RAG

This script can be used as a pre-prompt hook to automatically inject
relevant context from your study materials into Claude Code conversations.

Usage:
  Set this as a hook in Claude Code settings, or run manually:
  python claude_code_hook.py "your question about statistics"
"""

import sys
import json
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from stats_rag import retrieve_context, get_vector_store, CONFIG


def format_context_for_claude(question: str, max_contexts: int = 5) -> str:
    """Format retrieved context for Claude Code."""

    try:
        contexts = retrieve_context(question, n_results=max_contexts)
    except Exception as e:
        return f"[RAG System Error: {e}. Run 'python stats_rag.py --index' first.]"

    if not contexts:
        return "[No relevant context found in study materials.]"

    output = """<study_materials_context>
The following context is retrieved from the student's Statistics exam study materials.
Use this to answer their question accurately and cite sources when possible.

"""

    for i, ctx in enumerate(contexts, 1):
        source = ctx['metadata'].get('filename', 'unknown')
        page = ctx['metadata'].get('page', '')
        page_info = f" (page {page})" if page else ""
        relevance = ctx['relevance']

        output += f"""--- Context {i} [{source}{page_info}] (relevance: {relevance:.1%}) ---
{ctx['content']}

"""

    output += "</study_materials_context>\n"
    return output


def main():
    if len(sys.argv) < 2:
        print("Usage: python claude_code_hook.py 'your question'", file=sys.stderr)
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    context = format_context_for_claude(question)
    print(context)


if __name__ == "__main__":
    main()
