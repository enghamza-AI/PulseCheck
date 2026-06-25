"""
reporter.py
-----------
Generates a fully self-contained HTML report using Jinja2 for templating
and Chart.js (loaded via CDN) for interactive charts.

The report includes:
  - Top 10 posts table (title, score, comments, sentiment)
  - Sentiment pie chart (Positive / Neutral / Negative distribution)
  - Trending keywords bar chart (top 15 words by frequency)
  - Run history table (all previous runs from the SQLite database)

Usage (from main.py):
    from reporter import generate_report
    generate_report(posts, keywords, sentiment_summary, run_history, output_path)
"""

import json
from datetime import datetime
from pathlib import Path

from jinja2 import Template

# ---------------------------------------------------------------------------
# HTML template — written as a Python string so the file is self-contained.
# Chart.js is loaded from CDN; all chart data is embedded as JSON.
# ---------------------------------------------------------------------------
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PulseCheck Report — r/{{ subreddit }}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0f1117;
      color: #e2e8f0;
      padding: 2rem;
    }
    h1 { font-size: 2rem; color: #ff4500; margin-bottom: 0.25rem; }
    h2 { font-size: 1.1rem; color: #94a3b8; font-weight: 400; margin-bottom: 2rem; }
    h3 { font-size: 1rem; color: #cbd5e1; text-transform: uppercase;
         letter-spacing: 0.08em; margin-bottom: 1rem; }
    .meta { color: #64748b; font-size: 0.85rem; margin-bottom: 2.5rem; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem; }
    .card {
      background: #1e2130;
      border: 1px solid #2d3148;
      border-radius: 12px;
      padding: 1.5rem;
    }
    .card.full { grid-column: 1 / -1; }
    .chart-wrap { position: relative; height: 280px; }
    table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    thead th {
      background: #252840;
      color: #94a3b8;
      text-align: left;
      padding: 0.6rem 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      font-size: 0.75rem;
    }
    tbody tr:hover { background: #252840; }
    tbody td { padding: 0.55rem 0.8rem; border-bottom: 1px solid #2d3148; }
    a { color: #ff6b35; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .badge {
      display: inline-block;
      padding: 0.15rem 0.55rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .badge-pos { background: #14532d; color: #4ade80; }
    .badge-neg { background: #450a0a; color: #f87171; }
    .badge-neu { background: #1e293b; color: #94a3b8; }
    footer { text-align: center; color: #475569; font-size: 0.8rem; margin-top: 2rem; }
  </style>
</head>
<body>

  <h1>🔴 PulseCheck</h1>
  <h2>Reddit Trend Tracker — r/{{ subreddit }}</h2>
  <p class="meta">
    Generated: {{ generated_at }} &nbsp;|&nbsp;
    Posts analysed: {{ total_posts }} &nbsp;|&nbsp;
    Student: HAMZA (2520240008)
  </p>

  <div class="grid">

    <!-- Sentiment Pie Chart -->
    <div class="card">
      <h3>Sentiment Distribution</h3>
      <div class="chart-wrap">
        <canvas id="sentimentChart"></canvas>
      </div>
    </div>

    <!-- Trending Keywords Bar Chart -->
    <div class="card">
      <h3>Trending Keywords</h3>
      <div class="chart-wrap">
        <canvas id="keywordsChart"></canvas>
      </div>
    </div>

    <!-- Top 10 Posts Table -->
    <div class="card full">
      <h3>Top 10 Posts</h3>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Title</th>
            <th>Score</th>
            <th>Comments</th>
            <th>Sentiment</th>
          </tr>
        </thead>
        <tbody>
          {% for post in top_posts %}
          <tr>
            <td>{{ loop.index }}</td>
            <td><a href="{{ post.permalink }}" target="_blank">{{ post.title[:90] }}{% if post.title|length > 90 %}…{% endif %}</a></td>
            <td>{{ "{:,}".format(post.score) }}</td>
            <td>{{ "{:,}".format(post.num_comments) }}</td>
            <td>
              {% if post.sentiment_label == "Positive" %}
                <span class="badge badge-pos">Positive</span>
              {% elif post.sentiment_label == "Negative" %}
                <span class="badge badge-neg">Negative</span>
              {% else %}
                <span class="badge badge-neu">Neutral</span>
              {% endif %}
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <!-- Run History Table -->
    <div class="card full">
      <h3>Run History</h3>
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Subreddit</th>
            <th>Posts Scraped</th>
          </tr>
        </thead>
        <tbody>
          {% for run in run_history %}
          <tr>
            <td>{{ run.run_at }}</td>
            <td>r/{{ run.subreddit }}</td>
            <td>{{ run.post_count }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

  </div>

  <footer>
    PulseCheck · GJXX302J20 Artificial Intelligence Design Project · Dr. Li
  </footer>

  <script>
    // ── Sentiment Pie Chart ──────────────────────────────────────────────
    const sentimentData = {{ sentiment_json }};
    new Chart(document.getElementById("sentimentChart"), {
      type: "doughnut",
      data: {
        labels: ["Positive", "Neutral", "Negative"],
        datasets: [{
          data: [
            sentimentData.Positive,
            sentimentData.Neutral,
            sentimentData.Negative
          ],
          backgroundColor: ["#4ade80", "#64748b", "#f87171"],
          borderWidth: 0,
          hoverOffset: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#cbd5e1" } }
        }
      }
    });

    // ── Trending Keywords Bar Chart ──────────────────────────────────────
    const kwData = {{ keywords_json }};
    new Chart(document.getElementById("keywordsChart"), {
      type: "bar",
      data: {
        labels: kwData.map(k => k[0]),
        datasets: [{
          label: "Mentions",
          data: kwData.map(k => k[1]),
          backgroundColor: "#ff4500cc",
          borderRadius: 4
        }]
      },
      options: {
        indexAxis: "y",   // Horizontal bars — easier to read long words
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#94a3b8" }, grid: { color: "#2d3148" } },
          y: { ticks: { color: "#cbd5e1" }, grid: { color: "#2d3148" } }
        }
      }
    });
  </script>

</body>
</html>
"""


def generate_report(
    posts: list[dict],
    keywords: list[tuple[str, int]],
    sentiment_summary: dict,
    run_history: list[dict],
    output_path: str,
    subreddit: str,
) -> None:
    """
    Render and save the HTML report.

    Args:
        posts:            All analysed post dicts.
        keywords:         List of (word, count) tuples from analyzer.
        sentiment_summary: Dict with Positive/Neutral/Negative counts.
        run_history:      List of dicts from the DB runs table.
        output_path:      Where to write the .html file.
        subreddit:        Subreddit name (for the page title).
    """
    # Sort posts by score and take the top 10 for the table.
    top_posts = sorted(posts, key=lambda p: p["score"], reverse=True)[:10]

    # Render the Jinja2 template with all the data.
    template = Template(HTML_TEMPLATE)
    html = template.render(
        subreddit=subreddit,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_posts=len(posts),
        top_posts=top_posts,
        run_history=run_history,
        # Embed data as JSON strings so Chart.js can read them.
        sentiment_json=json.dumps(sentiment_summary),
        keywords_json=json.dumps(keywords),
    )

    # Write the file — ensure the output directory exists first.
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[reporter] Report saved → {output_path}")
