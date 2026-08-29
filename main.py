"""
main.py — The Crafters Hub Agentic Suite CLI
Entry point for all three ADK 2.7.1 agents.

Commands:
    python main.py ingest  --source <youtube_url_or_local_path>
    python main.py research --question "How do I sharpen a bowl gouge?"
    python main.py sentinel [--days 7]
    python main.py test-db

Usage examples:
    python main.py ingest --source "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    python main.py research --question "What wood is best for bowl turning?"
    python main.py sentinel --days 14
    python main.py test-db
"""

import argparse
import logging
import sys
import os

# ── Ensure repo root is on path ───────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("tch.main")

# ── Rich console (optional — graceful fallback) ────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    console = Console()
    USE_RICH = True
except ImportError:
    USE_RICH = False


def _print(msg: str, style: str = ""):
    if USE_RICH:
        console.print(msg, style=style)
    else:
        print(msg)


def _panel(title: str, content: str):
    if USE_RICH:
        console.print(Panel(content, title=title, border_style="cyan"))
    else:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        print(content)
        print(f"{'='*60}\n")


# ── Command handlers ──────────────────────────────────────────────────────────

def cmd_test_db():
    """Verify database connectivity and table existence."""
    from db.connection import test_connection, get_connection

    _print("Testing database connection...", style="yellow")
    ok = test_connection()

    if not ok:
        _print("[FAIL] Database connection FAILED", style="red bold")
        sys.exit(1)

    _print("[OK] Database connection OK", style="green bold")

    # Check teacher_student_knowledge table
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM teacher_student_knowledge")
            count = cur.fetchone()[0]
            _print(f"[DB] teacher_student_knowledge rows: {count}", style="cyan")

            cur.execute("SELECT COUNT(*) FROM knowledge_base")
            kb_count = cur.fetchone()[0]
            _print(f"[DB] knowledge_base rows: {kb_count}", style="cyan")

    _panel("DB Status", f"Connection: OK\nLesson entries: {count}\nCabinet KB entries: {kb_count}")


def cmd_ingest(source: str):
    """Run the Lesson Ingest Agent."""
    from agents.ingest_agent import run_ingest_agent

    _print(f"\n[INGEST] Starting Lesson Ingest Agent", style="cyan bold")
    _print(f"   Source: {source}", style="dim")

    try:
        result = run_ingest_agent(source)
        _panel("Ingest Agent Result", result)
    except Exception as e:
        _print(f"[FAIL] Ingest failed: {e}", style="red bold")
        logger.exception("Ingest agent error")
        sys.exit(1)


def cmd_research(question: str):
    """Run the Research & Answer Agent."""
    from agents.research_agent import run_research_agent

    _print(f"\n[RESEARCH] Craft Research Agent", style="cyan bold")
    _print(f"   Question: {question}", style="dim")

    try:
        answer = run_research_agent(question)
        _panel("Research Agent Answer", answer)
    except Exception as e:
        _print(f"[FAIL] Research failed: {e}", style="red bold")
        logger.exception("Research agent error")
        sys.exit(1)


def cmd_sentinel(days_back: int):
    """Run the Finance Sentinel Agent."""
    from agents.sentinel_agent import run_sentinel_agent

    _print(f"\n[SENTINEL] Finance Sentinel Agent -- scanning last {days_back} days", style="cyan bold")
    _print("   WhatsApp approval requests will be sent to Hosam for matches.", style="dim")

    try:
        summary = run_sentinel_agent(days_back=days_back)
        _panel("Sentinel Run Complete", summary)
    except Exception as e:
        _print(f"[FAIL] Sentinel failed: {e}", style="red bold")
        logger.exception("Sentinel agent error")
        sys.exit(1)


# ── CLI argument parsing ──────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tch-agents",
        description=(
            "The Crafters Hub Agentic Suite — "
            "Knowledge Flywheel, Research AI, Finance Sentinel"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py test-db
  python main.py ingest --source "https://www.youtube.com/watch?v=VIDEO_ID"
  python main.py ingest --source "C:/Videos/bowl_turning_class.mp4"
  python main.py research --question "How do I avoid catches on the lathe?"
  python main.py sentinel --days 7
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # test-db
    subparsers.add_parser("test-db", help="Test database connectivity")

    # ingest
    p_ingest = subparsers.add_parser("ingest", help="Ingest a YouTube video or local file")
    p_ingest.add_argument(
        "--source", required=True,
        help="YouTube URL (e.g. https://www.youtube.com/watch?v=VIDEO_ID). Local file paths are not supported in cloud mode."
    )

    # research
    p_research = subparsers.add_parser("research", help="Answer a woodworking question")
    p_research.add_argument(
        "--question", required=True,
        help='Question to research (e.g. "How do I sharpen a bowl gouge?")'
    )

    # sentinel
    p_sentinel = subparsers.add_parser("sentinel", help="Run Finance Sentinel scan")
    p_sentinel.add_argument(
        "--days", type=int, default=7,
        help="Number of days to scan back (default: 7)"
    )

    return parser


def main():
    parser = build_parser()
    args   = parser.parse_args()

    if args.command == "test-db":
        cmd_test_db()
    elif args.command == "ingest":
        cmd_ingest(args.source)
    elif args.command == "research":
        cmd_research(args.question)
    elif args.command == "sentinel":
        cmd_sentinel(args.days)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
