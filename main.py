"""
main.py
-------
Entry point for PulseCheck — the Reddit Trend Tracker.

Run it from the command line:
    python main.py --subreddit python --limit 100
    python main.py --subreddit technology --limit 50
    python main.py --subreddit worldnews           # uses default limit of 25

What happens when you run this:
    1. Scrape top posts from the given subreddit (scraper.py)
    2. Analyse sentiment and extract keywords (analyzer.py)
    3. Save data to CSV and SQLite (this file)
    4. Generate a self-contained HTML report (reporter.py)

All output files go into the output/ folder.
"""

import argparse
import sqlite3
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from scraper import fetch_posts
from analyzer import analyze_posts, get_trending_keywords, get_sentiment_summary
from reporter import generate_report

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path("output")
CSV_PATH   = OUTPUT_DIR / "reddit_data.csv"
DB_PATH    = OUTPUT_DIR / "reddit_data.db"
HTML_PATH  = OUTPUT_DIR / "report.html"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def init_db(db_path: Path) -> sqlite3.Connection:
    """
    Create (or connect to) the SQLite database and ensure the tables exist.

    We create two tables:
        - posts: one row per scraped post (with run timestamp)
        - runs:  one row per program execution (for the run history table)

    Returns:
        An open sqlite3 connection object.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Posts table — stores all scraped post data.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id             TEXT,
            run_at         TEXT,
            subreddit      TEXT,
            title          TEXT,
            score          INTEGER,
            upvote_ratio   REAL,
            num_comments   INTEGER,
            author         TEXT,
            url            TEXT,
            permalink      TEXT,
            created_utc    INTEGER,
            flair          TEXT,
            sentiment_score REAL,
            sentiment_label TEXT,
            subjectivity   REAL
        )
    """)

    # Runs table — one row per execution, used for the run history report section.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            run_at      TEXT,
            subreddit   TEXT,
            post_count  INTEGER
        )
    """)

    conn.commit()
    return conn


def save_to_db(conn: sqlite3.Connection, posts: list[dict], subreddit: str) -> None:
    """
    Insert all posts from this run into the database.
    Also logs a summary row into the runs table.

    Args:
        conn:      Open SQLite connection.
        posts:     Analysed post dicts.
        subreddit: Subreddit name for the runs log.
    """
    run_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()

    # Insert each post.
    for post in posts:
        cursor.execute("""
            INSERT INTO posts VALUES (
                :id, :run_at, :subreddit, :title, :score, :upvote_ratio,
                :num_comments, :author, :url, :permalink, :created_utc,
                :flair, :sentiment_score, :sentiment_label, :subjectivity
            )
        """, {**post, "run_at": run_at})

    # Log this run.
    cursor.execute(
        "INSERT INTO runs VALUES (?, ?, ?)",
        (run_at, subreddit, len(posts))
    )

    conn.commit()
    print(f"[db] Saved {len(posts)} posts to database.")


def get_run_history(conn: sqlite3.Connection) -> list[dict]:
    """
    Fetch all rows from the runs table, newest first.

    Returns:
        List of dicts with keys: run_at, subreddit, post_count.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT run_at, subreddit, post_count FROM runs ORDER BY run_at DESC")
    rows = cursor.fetchall()
    return [{"run_at": r[0], "subreddit": r[1], "post_count": r[2]} for r in rows]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # ── Parse command-line arguments ─────────────────────────────────────
    parser = argparse.ArgumentParser(
        description="PulseCheck — Reddit Trend Tracker",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--subreddit", "-s",
        type=str,
        required=True,
        help="Subreddit to scrape (e.g., python, technology, worldnews)"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=25,
        help="Maximum number of posts to fetch (max 1000, Reddit allows 100/request)"
    )
    args = parser.parse_args()

    subreddit = args.subreddit.strip().lower()
    limit = max(1, min(args.limit, 1000))  # Clamp to [1, 1000]

    print(f"\n{'='*50}")
    print(f"  PulseCheck — r/{subreddit} | limit={limit}")
    print(f"{'='*50}\n")

    # ── Create output directory ──────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Scrape ───────────────────────────────────────────────────
    posts = fetch_posts(subreddit, limit=limit)

    if not posts:
        print("[main] No posts fetched. Exiting.")
        return

    # ── Step 2: Analyse ──────────────────────────────────────────────────
    posts = analyze_posts(posts)
    keywords = get_trending_keywords(posts, top_n=15)
    sentiment_summary = get_sentiment_summary(posts)

    print(f"\n[analyzer] Sentiment: {sentiment_summary}")
    print(f"[analyzer] Top keywords: {keywords[:5]}")

    # ── Step 3: Save to CSV ──────────────────────────────────────────────
    df = pd.DataFrame(posts)
    # Append to CSV if it exists, otherwise create it.
    write_header = not CSV_PATH.exists()
    df.to_csv(CSV_PATH, mode="a", header=write_header, index=False)
    print(f"[csv] Data saved → {CSV_PATH}")

    # ── Step 4: Save to SQLite ───────────────────────────────────────────
    conn = init_db(DB_PATH)
    save_to_db(conn, posts, subreddit)
    run_history = get_run_history(conn)
    conn.close()

    # ── Step 5: Generate HTML report ─────────────────────────────────────
    generate_report(
        posts=posts,
        keywords=keywords,
        sentiment_summary=sentiment_summary,
        run_history=run_history,
        output_path=str(HTML_PATH),
        subreddit=subreddit,
    )

    print(f"\n{'='*50}")
    print(f"  ✅ Done!")
    print(f"  CSV    → {CSV_PATH}")
    print(f"  DB     → {DB_PATH}")
    print(f"  Report → {HTML_PATH}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
