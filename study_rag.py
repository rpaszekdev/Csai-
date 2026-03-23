#!/usr/bin/env python3
"""
Study RAG System
Integrated with Claude Code for Q&A and Quiz Generation

Usage (run from this directory, then use Claude Code):
    1. python study_rag.py --index    # Index your materials (run once)
    2. python study_rag.py --query "your question"
    3. python study_rag.py --quiz multiple_choice --topic "topic"
    4. python study_rag.py --quiz open_ended --topic "topic"
    5. python study_rag.py --quiz flashcard --count 10
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

import subject_config

# Rich for nice terminal output
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

console = Console()

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "materials_dirs": subject_config.MATERIALS_DIRS,
    "study_guide": subject_config.STUDY_GUIDE_PATH,
    "db_path": Path(__file__).parent / "chroma_db",
    "collection_name": f"{subject_config.SUBJECT_SHORT}_materials",
    "chunk_size": 1000,
    "chunk_overlap": 200,
}

# ============================================================================
# LECTURE-TO-PDF MAPPING - loaded from subject config
# ============================================================================

LECTURES_DIR = subject_config.LECTURES_DIR
LECTURE_PDF_MAP = subject_config.LECTURE_PDF_MAP
TOPIC_LECTURE_MAP = subject_config.TOPIC_LECTURE_MAP


def get_pdf_for_topic(topic: str) -> Optional[Path]:
    """Get the PDF path for a topic based on its parent lecture mapping."""
    parent_lecture = TOPIC_LECTURE_MAP.get(topic)
    if parent_lecture:
        pdf_filename = LECTURE_PDF_MAP.get(parent_lecture)
        if pdf_filename:
            pdf_path = LECTURES_DIR / pdf_filename
            if pdf_path.exists():
                return pdf_path
    return None


# ============================================================================
# DOCUMENT LOADING
# ============================================================================

def load_text_file(file_path: Path) -> list[dict]:
    """Load a text or markdown file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        return [{
            "content": content,
            "source": str(file_path),
            "filename": file_path.name,
            "type": file_path.suffix,
        }]
    except Exception as e:
        console.print(f"[red]Error loading {file_path}: {e}[/red]")
        return []


def load_pdf_file(file_path: Path) -> list[dict]:
    """Load a PDF file and extract text."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        documents = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text.strip():
                documents.append({
                    "content": text,
                    "source": str(file_path),
                    "filename": file_path.name,
                    "page": i + 1,
                    "type": ".pdf",
                })

        return documents
    except Exception as e:
        console.print(f"[red]Error loading PDF {file_path}: {e}[/red]")
        return []


def load_all_documents() -> list[dict]:
    """Load all documents from configured directories."""
    all_docs = []

    # Load from directories
    for dir_path in CONFIG["materials_dirs"]:
        if not dir_path.exists():
            console.print(f"[yellow]Directory not found: {dir_path}[/yellow]")
            continue

        console.print(f"[blue]Loading from: {dir_path}[/blue]")

        for file_path in dir_path.iterdir():
            if file_path.suffix.lower() == ".pdf":
                docs = load_pdf_file(file_path)
            elif file_path.suffix.lower() in [".txt", ".md"]:
                docs = load_text_file(file_path)
            else:
                continue

            all_docs.extend(docs)
            console.print(f"  ✓ Loaded: {file_path.name} ({len(docs)} chunks)")

    # Load study guide
    if CONFIG["study_guide"].exists():
        docs = load_text_file(CONFIG["study_guide"])
        all_docs.extend(docs)
        console.print(f"  ✓ Loaded: {CONFIG['study_guide'].name}")

    return all_docs


# ============================================================================
# TEXT CHUNKING
# ============================================================================

def chunk_documents(documents: list[dict]) -> list[dict]:
    """Split documents into smaller chunks for better retrieval."""
    chunks = []

    for doc in documents:
        content = doc["content"]
        chunk_size = CONFIG["chunk_size"]
        overlap = CONFIG["chunk_overlap"]

        # Split by paragraphs first, then by size
        paragraphs = content.split("\n\n")
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk.strip():
                    chunk_doc = doc.copy()
                    chunk_doc["content"] = current_chunk.strip()
                    chunks.append(chunk_doc)

                # Start new chunk with overlap
                words = current_chunk.split()
                overlap_text = " ".join(words[-overlap//5:]) if len(words) > overlap//5 else ""
                current_chunk = overlap_text + " " + para + "\n\n"

        # Don't forget the last chunk
        if current_chunk.strip():
            chunk_doc = doc.copy()
            chunk_doc["content"] = current_chunk.strip()
            chunks.append(chunk_doc)

    return chunks


# ============================================================================
# VECTOR STORE
# ============================================================================

def get_vector_store():
    """Initialize or load the ChromaDB vector store."""
    import chromadb
    from chromadb.utils import embedding_functions

    # Use sentence-transformers for embeddings
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=str(CONFIG["db_path"]))

    # Get or create collection
    collection = client.get_or_create_collection(
        name=CONFIG["collection_name"],
        embedding_function=embedding_fn,
        metadata={"description": f"{subject_config.SUBJECT_NAME} study materials"}
    )

    return collection


def index_documents():
    """Index all documents into the vector store."""
    console.print(Panel.fit("📚 Indexing Study Materials", style="bold blue"))

    # Load documents
    documents = load_all_documents()
    console.print(f"\n[green]Loaded {len(documents)} documents[/green]")

    # Chunk documents
    chunks = chunk_documents(documents)
    console.print(f"[green]Created {len(chunks)} chunks[/green]")

    # Get vector store
    console.print("\n[blue]Initializing vector store...[/blue]")
    collection = get_vector_store()

    # Clear existing data
    existing = collection.count()
    if existing > 0:
        console.print(f"[yellow]Clearing {existing} existing entries...[/yellow]")
        collection.delete(where={"source": {"$ne": ""}})

    # Add chunks to collection
    console.print("[blue]Adding documents to vector store...[/blue]")

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    contents = [c["content"] for c in chunks]
    metadatas = [{k: v for k, v in c.items() if k != "content"} for c in chunks]

    # Add in batches
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        end = min(i + batch_size, len(chunks))
        collection.add(
            ids=ids[i:end],
            documents=contents[i:end],
            metadatas=metadatas[i:end]
        )
        console.print(f"  Added batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")

    console.print(f"\n[green]✓ Successfully indexed {len(chunks)} chunks![/green]")
    console.print(f"[dim]Database stored at: {CONFIG['db_path']}[/dim]")


# ============================================================================
# RETRIEVAL
# ============================================================================

def retrieve_context(query: str, n_results: int = 5) -> list[dict]:
    """Retrieve relevant context for a query."""
    collection = get_vector_store()

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    contexts = []
    for i, doc in enumerate(results["documents"][0]):
        contexts.append({
            "content": doc,
            "metadata": results["metadatas"][0][i],
            "relevance": 1 - results["distances"][0][i],  # Convert distance to similarity
        })

    return contexts


def retrieve_from_file(filename_pattern: str, query: str = None, n_results: int = 10) -> list[dict]:
    """
    Retrieve content from a specific file by filename pattern.

    Args:
        filename_pattern: Part of the filename to match (e.g., "exam_concepts")
        query: Optional query for semantic search within matched files
        n_results: Max results to return

    Returns:
        List of context dicts from matching files
    """
    collection = get_vector_store()

    # Use query if provided, otherwise use fallback from subject config
    search_query = query if query else subject_config.FALLBACK_QUERY

    # Get all documents and filter by filename
    # ChromaDB where clause doesn't support $contains, so we get more results and filter
    results = collection.query(
        query_texts=[search_query],
        n_results=200,  # Get many results to filter
        include=["documents", "metadatas", "distances"]
    )

    contexts = []
    for i, doc in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i]
        # Check if filename matches pattern (case-insensitive)
        if filename_pattern.lower() in metadata.get("filename", "").lower():
            contexts.append({
                "content": doc,
                "metadata": metadata,
                "relevance": 1 - results["distances"][0][i],
            })
            if len(contexts) >= n_results:
                break

    return contexts


def retrieve_context_smart(topic: str, n_results: int = 5) -> list[dict]:
    """
    Smart retrieval that handles special topics like 'Exam Concepts'.

    For 'Exam Concepts', retrieves directly from exam_concepts.txt.
    For other topics, uses standard semantic search.
    """
    # Special handling for Exam Concepts - retrieve from the specific file
    if topic and "exam" in topic.lower() and "concept" in topic.lower():
        contexts = retrieve_from_file("exam_concepts", query=topic, n_results=n_results)
        if contexts:
            return contexts
        # Fallback to semantic search if file not found

    # Standard semantic search for other topics
    return retrieve_context(topic, n_results=n_results)


def retrieve_images_for_topic(topic: str, n_results: int = 5) -> dict:
    """
    Retrieve relevant images for a study topic.

    Returns both:
    1. PDF paths/pages that are relevant to the topic (for image extraction)
    2. Topic keywords for graph generation

    Priority: Direct lecture mapping > RAG semantic search

    Args:
        topic: The study topic
        n_results: Number of context results to check

    Returns:
        Dict with 'pdf_sources' (list of {path, pages}) and 'keywords' (list)
    """
    # Extract keywords from topic for graph generation
    topic_lower = topic.lower()
    topic_keywords = subject_config.TOPIC_KEYWORDS
    found_keywords = [kw for kw in topic_keywords if kw in topic_lower]

    # PRIORITY 1: Check for direct lecture-to-PDF mapping
    # This ensures topics pull from their correct parent lecture
    target_pdf = get_pdf_for_topic(topic)
    if target_pdf:
        console.print(f"[green]Using mapped PDF for topic:[/green] {target_pdf.name}")
        return {
            "pdf_sources": [{"path": str(target_pdf), "pages": []}],  # Empty pages = extract all
            "keywords": found_keywords,
            "topic": topic
        }

    # PRIORITY 2: Fall back to RAG semantic search for unknown topics
    contexts = retrieve_context(topic, n_results=n_results)

    # Extract PDF sources and relevant pages
    pdf_sources = {}
    for ctx in contexts:
        metadata = ctx.get("metadata", {})
        source = metadata.get("source", "")
        page = metadata.get("page")

        if source.endswith(".pdf"):
            if source not in pdf_sources:
                pdf_sources[source] = {"path": source, "pages": []}
            if page and page not in pdf_sources[source]["pages"]:
                pdf_sources[source]["pages"].append(page)

    return {
        "pdf_sources": list(pdf_sources.values()),
        "keywords": found_keywords,
        "topic": topic
    }


def retrieve_r_content(topic: str = None, n_results: int = 10) -> list[dict]:
    """Retrieve R code and output from lecture materials.

    Uses enhanced query to find R-related content:
    - R function calls (lm, summary, cor.test, etc.)
    - R output patterns (Coefficients:, p-value, etc.)
    - Code blocks with R syntax

    Args:
        topic: Optional topic to focus the search (e.g., "linear regression")
        n_results: Number of results to retrieve before filtering

    Returns:
        List of context dicts containing R code/output
    """
    # Build query targeting R content
    base_query = "R code output summary coefficients p-value"
    if topic:
        r_query = f"R output {topic} {base_query}"
    else:
        r_query = base_query

    # Retrieve from vector store
    results = retrieve_context(r_query, n_results=n_results)

    # Post-filter for R content indicators
    r_patterns = [
        'summary(', 'lm(', 'Coefficients:', 'p-value', 'Pr(>',
        'cor.test', 'anova(', 't.test', '> ', 'Residuals:',
        'Estimate', 'Std. Error', 'F-statistic', 'Multiple R-squared',
        'Adjusted R-squared', 'glm(', 'lmer(', 'aov('
    ]

    r_content = []
    for r in results:
        content = r.get('content', '')
        if any(pattern in content for pattern in r_patterns):
            r_content.append(r)

    return r_content


# ============================================================================
# QUERY INTERFACE (for Claude Code integration)
# ============================================================================

def query_materials(question: str) -> str:
    """
    Query the materials and return context for Claude Code.

    This outputs structured context that Claude Code can use to answer questions.
    """
    contexts = retrieve_context(question, n_results=5)

    output = {
        "question": question,
        "retrieved_contexts": [],
        "sources": set(),
    }

    for ctx in contexts:
        output["retrieved_contexts"].append({
            "content": ctx["content"],
            "source": ctx["metadata"].get("filename", "unknown"),
            "relevance_score": round(ctx["relevance"], 3),
        })
        output["sources"].add(ctx["metadata"].get("filename", "unknown"))

    output["sources"] = list(output["sources"])

    # Format for Claude Code
    result = f"""
## Retrieved Context for: "{question}"

**Sources used:** {', '.join(output['sources'])}

---

"""
    for i, ctx in enumerate(output["retrieved_contexts"], 1):
        result += f"""### Context {i} (relevance: {ctx['relevance_score']:.1%})
**Source:** {ctx['source']}

{ctx['content']}

---

"""

    result += """
**Instructions for Claude Code:**
Use the above context from the student's {subject_config.SUBJECT_NAME} study materials to answer their question.
If the context doesn't contain enough information, say so and provide what you can.
Always cite which source(s) you used in your answer.
"""

    return result


# ============================================================================
# QUIZ GENERATION
# ============================================================================

def generate_quiz_prompt(quiz_type: str, topic: Optional[str] = None, count: int = 5) -> str:
    """
    Generate a prompt for Claude Code to create quiz questions.

    Quiz types:
    - multiple_choice: 4 options, one correct
    - open_ended: Short answer questions
    - flashcard: Term/definition pairs
    """

    # Get relevant context
    search_query = topic if topic else subject_config.FALLBACK_QUERY
    contexts = retrieve_context(search_query, n_results=8)

    context_text = "\n\n---\n\n".join([
        f"**From {ctx['metadata'].get('filename', 'unknown')}:**\n{ctx['content']}"
        for ctx in contexts
    ])

    quiz_instructions = {
        "multiple_choice": f"""
Generate {count} multiple choice questions based on the study materials below.

For each question:
1. Write a clear question testing understanding (not just recall)
2. Provide 4 options (A, B, C, D)
3. Mark the correct answer
4. Include a brief explanation of why it's correct

**CRITICAL - Answer Option Rules:**
- ALL options (correct AND incorrect) MUST be approximately the same length
- ALL options must use the same level of detail and technical language
- DO NOT make the correct answer longer, more detailed, or more "complete-sounding"
- DO NOT use hedging words like "always", "never", "only" as giveaways
- Incorrect options should be plausible and well-crafted, not obviously wrong
- Avoid patterns like "all of the above" or "none of the above"
- Each distractor should represent a common misconception or related concept

Format each question as:

**Question N:**
[Question text]

A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]

**Correct Answer:** [Letter]
**Explanation:** [Why this is correct]

---
""",
        "open_ended": f"""
Generate {count} open-ended/short answer questions based on the study materials below.

For each question:
1. Ask a question that requires understanding and explanation
2. Provide a model answer
3. List key points the student should mention

Format each question as:

**Question N:**
[Question text]

**Model Answer:**
[Comprehensive answer]

**Key Points to Include:**
- [Point 1]
- [Point 2]
- [Point 3]

---
""",
        "flashcard": f"""
Generate {count} flashcards based on the study materials below.

For each flashcard:
1. Front: A term, concept, or question
2. Back: Definition, explanation, or answer
3. Include an example if applicable

Format each flashcard as:

**Flashcard N:**
📝 **Front:** [Term/Question]
💡 **Back:** [Definition/Answer]
📌 **Example:** [Practical example if applicable]

---
"""
    }

    topic_text = f" about **{topic}**" if topic else ""

    prompt = f"""
# Quiz Generation Request{topic_text}

## Quiz Type: {quiz_type.replace('_', ' ').title()}

## Study Material Context:

{context_text}

---

## Instructions:

{quiz_instructions.get(quiz_type, quiz_instructions['multiple_choice'])}

Generate questions that:
- Test understanding, not just memorization
- Cover different difficulty levels
- Are based ONLY on the provided study materials
- Include relevant formulas or concepts where applicable
- {"Focus specifically on: " + topic if topic else "Cover a variety of topics from the materials"}
"""

    return prompt


def retrieve_context_with_emphasis(query: str, n_results: int = 10) -> list[dict]:
    """
    Retrieve context sorted by emphasis indicators.

    Analyzes retrieved content for signs of teacher emphasis:
    - "important", "remember", "key point"
    - "common mistake", "students often"
    - Repeated concepts

    Args:
        query: Search query
        n_results: Number of results to retrieve

    Returns:
        List of context dicts sorted by emphasis score (highest first)
    """
    contexts = retrieve_context(query, n_results=n_results)

    emphasis_patterns = [
        "important", "remember", "key", "crucial", "essential",
        "note that", "make sure", "don't forget", "always",
        "common mistake", "students often", "don't confuse",
        "be careful", "pay attention", "critical", "fundamental",
        "this is", "you must", "never", "watch out"
    ]

    for ctx in contexts:
        content = ctx["content"].lower()
        # Count emphasis pattern matches
        emphasis_score = sum(
            1 for pattern in emphasis_patterns
            if pattern in content
        )
        ctx["emphasis_score"] = emphasis_score

    # Sort by emphasis score (highest first)
    contexts.sort(key=lambda x: x.get("emphasis_score", 0), reverse=True)
    return contexts


def generate_teacher_mind_prompt(
    topic: str,
    count: int,
    lecture_content: str,
    existing_hashes: set = None
) -> str:
    """
    Generate questions predicting what the teacher will ask on the exam.

    Analyzes lecture materials to identify:
    1. Topics the teacher emphasized/repeated
    2. Exam-style patterns from examples
    3. Common misconceptions highlighted
    4. Teacher's question complexity/style

    Args:
        topic: The topic to generate questions for
        count: Number of questions to generate
        lecture_content: Combined lecture content text
        existing_hashes: Set of existing question hashes to avoid duplicates

    Returns:
        Prompt string for Claude to generate exam-prediction questions
    """
    dedup_note = ""
    if existing_hashes and len(existing_hashes) > 0:
        dedup_note = f"""
**IMPORTANT - Question Uniqueness:**
You have already generated {len(existing_hashes)} questions in previous tests.
Generate COMPLETELY NEW questions that test different aspects of the concepts.
Do NOT rephrase or slightly modify previous questions - create genuinely new ones.
"""

    prompt = f"""You are analyzing lecture materials to predict what the teacher will ask on the exam.

## Topic: {topic}

## Lecture Content:
{lecture_content}

---

## Analysis Instructions:

### 1. Identify Emphasized Concepts
Look for phrases indicating importance:
- "this is important", "remember this", "key point", "make sure you understand"
- Concepts mentioned multiple times across the material
- Topics with detailed worked examples
- Areas where the teacher spent extra time explaining

### 2. Detect Exam-Style Patterns
Notice the teacher's question style:
- How problems are typically presented
- Types of calculations or interpretations shown
- Common question formats used in examples
- Level of detail expected in answers

### 3. Target Common Misconceptions
Find areas where students struggle:
- "Students often confuse...", "A common mistake is..."
- Clarifications between similar concepts (e.g., correlation vs causation)
- Warnings about interpretation errors
- Tricky edge cases mentioned
{dedup_note}
---

## Generate {count} Exam-Prediction Questions

For each question:
- **Mimic the teacher's question style** from the materials
- **Focus on concepts that were emphasized** (repeated, marked important)
- **Test understanding of misconception areas** the teacher highlighted
- **Match the complexity level** of examples given in lectures

**CRITICAL - Answer Option Rules:**
- ALL options (correct AND incorrect) MUST be approximately the same length
- ALL options must use the same level of detail and technical language
- DO NOT make the correct answer longer, more detailed, or more "complete-sounding"
- DO NOT use hedging words like "always", "never", "only" as giveaways
- Incorrect options should represent **real misconceptions** from the material
- Each distractor should be something a student who didn't study might believe

Format each question as:

**Q1:** [Question that mimics teacher's exam style]
A) [Option - same length as others]
B) [Option - same length as others]
C) [Option - same length as others]
D) [Option - same length as others]

**Answer:** [Letter]
**Explanation:** [Why correct, and why each wrong answer is a misconception]
**Teacher Focus:** [What emphasized concept or misconception this question targets]

---
"""

    return prompt


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description=f"{subject_config.SUBJECT_NAME} RAG System - Integrated with Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python study_rag.py --index
  python study_rag.py --query "your question here"
  python study_rag.py --quiz multiple_choice --topic "topic" --count 5
  python study_rag.py --quiz flashcard --count 10
  python study_rag.py --list-topics
        """
    )

    parser.add_argument("--index", action="store_true",
                        help="Index all study materials into the vector store")
    parser.add_argument("--query", type=str,
                        help="Query the materials with a question")
    parser.add_argument("--quiz", type=str, choices=["multiple_choice", "open_ended", "flashcard"],
                        help="Generate a quiz of the specified type")
    parser.add_argument("--topic", type=str,
                        help="Focus quiz on a specific topic")
    parser.add_argument("--count", type=int, default=5,
                        help="Number of quiz questions to generate (default: 5)")
    parser.add_argument("--list-topics", action="store_true",
                        help="List available topics from indexed materials")
    parser.add_argument("--stats", action="store_true",
                        help="Show statistics about indexed materials")

    args = parser.parse_args()

    if args.index:
        index_documents()

    elif args.query:
        result = query_materials(args.query)
        console.print(Markdown(result))

    elif args.quiz:
        prompt = generate_quiz_prompt(args.quiz, args.topic, args.count)
        console.print(Panel.fit(f"🎯 Quiz Generation Prompt ({args.quiz})", style="bold green"))
        console.print(Markdown(prompt))
        console.print("\n[bold yellow]Copy the above to Claude Code or pipe this output to continue![/bold yellow]")

    elif args.stats:
        try:
            collection = get_vector_store()
            count = collection.count()
            console.print(Panel.fit("📊 Index Statistics", style="bold blue"))
            console.print(f"Total indexed chunks: [green]{count}[/green]")
            console.print(f"Database location: [dim]{CONFIG['db_path']}[/dim]")

            # Sample some metadata to show sources
            if count > 0:
                sample = collection.peek(limit=min(count, 100))
                sources = set()
                for meta in sample["metadatas"]:
                    sources.add(meta.get("filename", "unknown"))
                console.print(f"\nIndexed sources ({len(sources)}):")
                for source in sorted(sources):
                    console.print(f"  • {source}")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print("[yellow]Run --index first to create the database.[/yellow]")

    elif args.list_topics:
        console.print(Panel.fit("📚 Extracting Topics...", style="bold blue"))
        # Query for general content to extract topics
        contexts = retrieve_context(subject_config.FALLBACK_QUERY, n_results=10)
        console.print("\n[bold]Key topics found in your materials:[/bold]\n")
        topics = [t["name"] for t in subject_config.API_TOPICS]
        for topic in topics:
            console.print(f"  • {topic}")
        console.print("\n[dim]Use --topic 'topic name' with --quiz to focus on specific areas[/dim]")

    else:
        parser.print_help()
        console.print("\n[bold green]Quick Start:[/bold green]")
        console.print("  1. Run: python study_rag.py --index")
        console.print("  2. Query: python study_rag.py --query 'your question'")
        console.print("  3. Quiz: python study_rag.py --quiz multiple_choice --topic 'topic'")


if __name__ == "__main__":
    main()
