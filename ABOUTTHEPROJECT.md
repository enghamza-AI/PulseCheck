# 📖 About The Project — PulseCheck

> A deep dive into the design decisions, architecture, and learning objectives behind the Reddit Trend Tracker.

---

## 🎯 What Problem Does This Solve?

Reddit is one of the largest real-time discussion platforms on the internet — a genuine pulse of what people are thinking, debating, and sharing right now. But browsing Reddit manually is noisy and time-consuming.

**PulseCheck** automates that signal extraction:
- What topics are trending in a given community?
- Are people talking positively or negatively about those topics?
- How does sentiment shift over time across multiple runs?



---

## 🏗️ Architecture Overview

```
CLI (main.py)
     │
     ▼
 scraper.py  ──────────►  Reddit JSON API (no key needed)
     │                    https://www.reddit.com/r/{sub}/top.json
     │
     ▼
 analyzer.py ──────────►  TextBlob (sentiment per title)
     │                    Collections.Counter (keyword frequency)
     │
     ▼
  SQLite DB  ──────────►  output/reddit_data.db
  CSV File   ──────────►  output/reddit_data.csv
     │
     ▼
 reporter.py ──────────►  Jinja2 + Chart.js → output/report.html
```

Each module is independently testable and has a single responsibility. This follows the **Single Responsibility Principle** — a core software engineering concept.

---

## 🔍 Key Design Decisions

### 1. No API Key Required
Reddit exposes a public JSON API by simply appending `.json` to any Reddit URL. This keeps the project beginner-friendly — no OAuth flow, no account registration, no secrets management.

The tradeoff: the public API is rate-limited and returns a maximum of 100 posts per request. PulseCheck handles this with pagination using Reddit's `after` token.

### 2. Polite Scraping
The scraper includes:
- A **2-second delay** between paginated requests (`time.sleep(2)`)
- A custom **User-Agent header** identifying the bot (Reddit requires this and will block generic agents)



### 3. SQLite for Historical Data
SQLite was chosen over a plain CSV for the run history feature. Each execution inserts rows tagged with a `run_timestamp`, so the database grows over time. This lets the HTML report show a **run history table** — useful for spotting trends across days or weeks.

SQLite is built into Python (`import sqlite3`) — zero extra dependencies.

### 4. Self-Contained HTML Report
The HTML report uses Chart.js loaded via CDN in a `<script>` tag, with all chart data embedded as JSON inside the page. This means:
- One file, no external dependencies at render time
- Can be emailed, shared, or archived

Jinja2 was used for templating because it keeps Python logic cleanly separated from HTML structure.

### 5. TextBlob for Sentiment
TextBlob gives a polarity score between -1.0 (very negative) and +1.0 (very positive) for any string. It's not perfect for slang-heavy Reddit titles, but it's fast, dependency-light, and good enough for a first pass.

Posts are bucketed into three categories:
- **Positive**: polarity > 0.05
- **Negative**: polarity < -0.05
- **Neutral**: everything in between

---

## 📊 What the Report Contains

| Section | Description |
|---|---|
| Top 10 Posts Table | Title, score, comments, sentiment score, URL |
| Sentiment Pie Chart | Distribution of positive / neutral / negative posts |
| Trending Keywords Bar Chart | Top 15 most frequent non-stopword title words |
| Run History Table | Timestamp, subreddit, post count per historical run |

---

## 🧪 Testing Strategy

Tests are written with **pytest** and cover three areas:

- `test_scraper.py` — mocks HTTP responses to test pagination logic and data extraction without hitting Reddit
- `test_analyzer.py` — checks that sentiment scores are in range and keyword extraction filters stopwords correctly
- `test_cleaner.py` — validates that malformed or missing fields are handled gracefully

Run all tests with:
```bash
pytest tests/ -v
```

---

## 🔮 Potential Extensions

If in future I want to take this further:

- **Scheduled runs** — Use `cron` or `schedule` library to run PulseCheck daily automatically
- **Multi-subreddit comparison** — Compare sentiment across r/politics vs r/news
- **Topic modelling** — Replace keyword counting with LDA (Latent Dirichlet Allocation) for richer themes
- **Alerting** — Email yourself when sentiment drops sharply (e.g., community crisis)
- **PRAW integration** — Switch to the official Reddit API (PRAW) for authenticated, higher rate-limit access

---

## 👤 Author

**HAMZA**  
Student ID: 2520240008  
Course: GJXX302J20 — Artificial Intelligence Design Project  
Instructor: Dr. Li

---

## 📄 License

This project is submitted as academic coursework. Do not redistribute without permission.
