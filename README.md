# 🔴 PulseCheck

> Track what the internet is talking about — scrape Reddit's top posts, analyze sentiment, spot trending keywords, and generate a beautiful HTML report. Built with Python.

**University Course Assignment**
**Each student had to build a completely unique project and here is what I built in 2 hours**

**Project:** Reddit Trend Tracker  
**Student:** HAMZA | **ID:** 2520240008  
**Course:** GJXX302J20 — Artificial Intelligence Design Project  
**Instructor:** Dr. Li

---

## 📁 Folder Structure

```
pulsecheck/
│
├── main.py              # Entry point — CLI interface, orchestrates everything
├── scraper.py           # Fetches posts from Reddit's public JSON API
├── analyzer.py          # Sentiment analysis (TextBlob) + keyword extraction
├── reporter.py          # Builds the self-contained HTML report with Chart.js
│
├── requirements.txt     # All pip dependencies
├── README.md            # This file
├── ABOUTTHEPROJECT.md   # Deep-dive into design decisions and architecture
│
├── tests/
│   ├── test_scraper.py  # Unit tests for scraper functions
│   ├── test_analyzer.py # Unit tests for sentiment + keyword logic
│   └── test_cleaner.py  # Unit tests for data cleaning helpers
│
└── output/              # Auto-created on first run
    ├── reddit_data.csv  # Raw scraped post data
    ├── reddit_data.db   # SQLite database (builds up across runs)
    └── report.html      # Self-contained HTML report (no external files)
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run it

```bash
# Scrape top 100 posts from r/python
python main.py --subreddit python --limit 100

# Scrape r/technology with 50 posts
python main.py --subreddit technology --limit 50

# Scrape r/worldnews (uses default limit of 25)
python main.py --subreddit worldnews
```

### 3. View your report

Open `output/report.html` in any browser. No internet needed — it's fully self-contained.

---

## ⚙️ How It Works

1. **Scrape** — `scraper.py` hits `https://www.reddit.com/r/{subreddit}/top.json` with polite delays and handles pagination via Reddit's `after` token.
2. **Analyze** — `analyzer.py` runs TextBlob sentiment on each post title and counts keyword frequencies.
3. **Store** — Data is saved to both a `.csv` and a `.db` (SQLite). Each run gets a timestamp so historical data accumulates.
4. **Report** — `reporter.py` uses Jinja2 to render a self-contained HTML page with Chart.js charts baked in.

---

## 📦 Dependencies

| Package     | Purpose                        |
|-------------|-------------------------------|
| requests    | HTTP calls to Reddit API       |
| pandas      | Data manipulation and CSV I/O  |
| textblob    | Sentiment analysis             |
| jinja2      | HTML report templating         |

> `sqlite3` is part of Python's standard library — no install needed.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 📝 Notes

- No API key required — uses Reddit's public `.json` endpoints.
- Respects Reddit's rate limits with a 2-second delay between paginated requests.
- Sends a descriptive `User-Agent` header as per Reddit's API guidelines.
- The `output/` folder is created automatically if it doesn't exist.
