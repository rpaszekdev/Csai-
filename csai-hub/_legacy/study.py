#!/usr/bin/env python3
"""
📚 Study Assistant
Interactive study tool with RAG-powered Q&A and quizzes.

Run this for an interactive study session!
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from study_rag import (
    retrieve_context,
    generate_quiz_prompt,
    get_vector_store,
    index_documents,
    CONFIG
)

import subject_config

console = Console()


def show_menu():
    """Display the main menu."""
    console.print(Panel.fit("""
📚 [bold blue]{subject_config.SUBJECT_NAME} Study Assistant[/bold blue]

[green]1.[/green] Ask a question (Q&A mode)
[green]2.[/green] Take a quiz
[green]3.[/green] Flashcard practice
[green]4.[/green] Review specific topic
[green]5.[/green] Re-index materials
[green]6.[/green] Show indexed stats
[green]q.[/green] Quit
""", title="Menu"))


def ask_question_mode():
    """Interactive Q&A mode."""
    console.print("\n[bold blue]📝 Q&A Mode[/bold blue]")
    console.print("[dim]Type your question, or 'back' to return to menu[/dim]\n")

    while True:
        question = Prompt.ask("[green]Your question[/green]")

        if question.lower() in ['back', 'quit', 'q', 'exit']:
            break

        contexts = retrieve_context(question, n_results=4)

        console.print(f"\n[bold]Found {len(contexts)} relevant sections:[/bold]\n")

        for i, ctx in enumerate(contexts, 1):
            source = ctx['metadata'].get('filename', 'unknown')
            relevance = ctx['relevance']
            content_preview = ctx['content'][:500] + "..." if len(ctx['content']) > 500 else ctx['content']

            console.print(Panel(
                content_preview,
                title=f"[{i}] {source} (relevance: {relevance:.1%})",
                border_style="blue"
            ))

        console.print("\n[yellow]💡 Use this context with Claude Code for a detailed answer![/yellow]")
        console.print("[dim]Run: Ask Claude Code your question - it will use this context[/dim]\n")


def quiz_mode():
    """Interactive quiz mode."""
    console.print("\n[bold blue]🎯 Quiz Mode[/bold blue]\n")

    quiz_type = Prompt.ask(
        "Quiz type",
        choices=["multiple_choice", "open_ended", "flashcard"],
        default="multiple_choice"
    )

    topics = [t["name"] for t in subject_config.API_TOPICS]

    console.print("\n[dim]Available topics:[/dim]")
    for t in topics:
        console.print(f"  • {t}")

    topic = Prompt.ask("\nTopic (or press Enter for mixed)", default="")
    count = int(Prompt.ask("Number of questions", default="5"))

    console.print("\n[blue]Generating quiz prompt...[/blue]\n")

    prompt = generate_quiz_prompt(quiz_type, topic if topic else None, count)

    console.print(Panel(
        Markdown(prompt),
        title="📋 Quiz Prompt for Claude Code",
        border_style="green"
    ))

    console.print("\n[bold yellow]📌 Next steps:[/bold yellow]")
    console.print("1. Copy the quiz prompt above")
    console.print("2. Paste it to Claude Code")
    console.print("3. Claude will generate your quiz based on your study materials!\n")


def flashcard_mode():
    """Quick flashcard practice."""
    console.print("\n[bold blue]🃏 Flashcard Mode[/bold blue]\n")

    topic = Prompt.ask("Topic to study (or Enter for all)", default="")
    count = int(Prompt.ask("Number of flashcards", default="10"))

    prompt = generate_quiz_prompt("flashcard", topic if topic else None, count)

    console.print(Panel(
        Markdown(prompt),
        title="🃏 Flashcard Generation Prompt",
        border_style="cyan"
    ))


def topic_review():
    """Deep dive into a specific topic."""
    console.print("\n[bold blue]📖 Topic Review[/bold blue]\n")

    topics = {
        str(i + 1): (t["name"], t["name"].lower())
        for i, t in enumerate(subject_config.API_TOPICS)
    }

    console.print("[bold]Available topics:[/bold]\n")
    for key, (name, _) in topics.items():
        console.print(f"  [{key}] {name}")

    choice = Prompt.ask("\nSelect topic number", choices=list(topics.keys()))
    topic_name, search_query = topics[choice]

    console.print(f"\n[blue]Retrieving content about {topic_name}...[/blue]\n")

    contexts = retrieve_context(search_query, n_results=6)

    for ctx in contexts:
        source = ctx['metadata'].get('filename', 'unknown')
        console.print(Panel(
            ctx['content'],
            title=f"📄 {source}",
            border_style="blue"
        ))


def show_stats():
    """Show index statistics."""
    try:
        collection = get_vector_store()
        count = collection.count()

        console.print(Panel.fit(f"""
[bold]📊 Index Statistics[/bold]

Total chunks indexed: [green]{count}[/green]
Database location: [dim]{CONFIG['db_path']}[/dim]

[bold]Configured sources:[/bold]
""" + "\n".join([f"  • {d}" for d in CONFIG['materials_dirs']]) + f"""
  • {CONFIG['study_guide']}
""", title="Stats"))

        if count > 0:
            sample = collection.peek(limit=min(count, 100))
            sources = set()
            for meta in sample["metadatas"]:
                sources.add(meta.get("filename", "unknown"))

            console.print(f"\n[bold]Indexed files ({len(sources)}):[/bold]")
            for source in sorted(sources):
                console.print(f"  ✓ {source}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Run option 5 to index materials first.[/yellow]")


def main():
    console.print(Panel.fit(
        f"[bold]📚 {subject_config.SUBJECT_NAME} Study Assistant[/bold]\n\n"
        "RAG-powered study tool integrated with Claude Code",
        style="blue"
    ))

    # Check if indexed
    try:
        collection = get_vector_store()
        if collection.count() == 0:
            console.print("\n[yellow]⚠️  No materials indexed yet![/yellow]")
            if Confirm.ask("Would you like to index your study materials now?"):
                index_documents()
    except Exception:
        console.print("\n[yellow]⚠️  First run - let's index your materials![/yellow]")
        if Confirm.ask("Index study materials now?"):
            index_documents()

    while True:
        show_menu()
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6", "q"])

        if choice == "1":
            ask_question_mode()
        elif choice == "2":
            quiz_mode()
        elif choice == "3":
            flashcard_mode()
        elif choice == "4":
            topic_review()
        elif choice == "5":
            if Confirm.ask("Re-index all materials?"):
                index_documents()
        elif choice == "6":
            show_stats()
        elif choice == "q":
            console.print("\n[green]Good luck with your studies! 📚✨[/green]\n")
            break


if __name__ == "__main__":
    main()
