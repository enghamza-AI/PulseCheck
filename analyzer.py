"""
analyzer.py
-----------
Performs sentiment analysis on post titles using TextBlob,
and extracts trending keywords by frequency.

Usage (from main.py):
    from analyzer import analyze_posts, get_trending_keywords
    posts = analyze_posts(posts)
    keywords = get_trending_keywords(posts, top_n=15)
"""

import re
from collections import Counter

from textblob import TextBlob

# Words to ignore when counting keywords — common English words that carry
# no meaningful signal (called "stopwords").
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "i", "you", "he",
    "she", "it", "we", "they", "my", "your", "his", "her", "its", "our",
    "their", "this", "that", "these", "those", "not", "no", "nor", "so",
    "yet", "both", "either", "each", "few", "more", "most", "other",
    "some", "such", "than", "too", "very", "just", "about", "after",
    "what", "how", "why", "when", "who", "which", "if", "as", "up",
    "out", "get", "got", "new", "use", "used", "using", "make", "made",
    "now", "one", "two", "into", "also", "any", "all", "like", "me",
    "s", "t", "don", "im", "its", "ve", "re", "ll", "d",
}


def analyze_posts(posts: list[dict]) -> list[dict]:
    """
    Add sentiment fields to each post by analysing the post title.

    TextBlob gives a polarity score from -1.0 (very negative) to +1.0
    (very positive). We also assign a human-readable sentiment label.

    Args:
        posts: List of post dicts (as returned by scraper.fetch_posts).

    Returns:
        The same list with three new keys added to each dict:
            - sentiment_score:  float in [-1.0, 1.0]
            - sentiment_label:  "Positive", "Neutral", or "Negative"
            - subjectivity:     float in [0.0, 1.0] (0=factual, 1=opinionated)
    """
    for post in posts:
        title = post.get("title", "")

        # TextBlob analyses the text and returns a Sentiment namedtuple.
        blob = TextBlob(title)
        polarity = blob.sentiment.polarity          # -1.0 to +1.0
        subjectivity = blob.sentiment.subjectivity  # 0.0 to 1.0

        # Bucket the score into three human-readable categories.
        # Thresholds chosen to avoid mislabelling near-neutral text.
        if polarity > 0.05:
            label = "Positive"
        elif polarity < -0.05:
            label = "Negative"
        else:
            label = "Neutral"

        post["sentiment_score"] = round(polarity, 4)
        post["sentiment_label"] = label
        post["subjectivity"] = round(subjectivity, 4)

    return posts


def get_trending_keywords(posts: list[dict], top_n: int = 15) -> list[tuple[str, int]]:
    """
    Find the most frequently occurring meaningful words across all post titles.

    Steps:
        1. Concatenate all post titles.
        2. Lowercase and strip punctuation.
        3. Split into words (tokens).
        4. Remove stopwords and very short words (< 3 chars).
        5. Count frequencies and return the top_n most common.

    Args:
        posts:  List of post dicts with a "title" field.
        top_n:  How many top keywords to return. Defaults to 15.

    Returns:
        A list of (word, count) tuples, sorted by count descending.
        Example: [("python", 12), ("library", 8), ...]
    """
    all_words = []

    for post in posts:
        title = post.get("title", "")

        # Lowercase everything for consistent counting.
        title = title.lower()

        # Remove punctuation and special characters, keep only letters/spaces.
        title = re.sub(r"[^a-z\s]", " ", title)

        # Split into individual words.
        words = title.split()

        # Filter: skip stopwords and very short words (e.g., "a", "is", "ok").
        meaningful = [w for w in words if w not in STOPWORDS and len(w) >= 3]
        all_words.extend(meaningful)

    # Count each word's frequency and return the most common ones.
    counter = Counter(all_words)
    return counter.most_common(top_n)


def get_sentiment_summary(posts: list[dict]) -> dict:
    """
    Count how many posts fall into each sentiment category.

    Args:
        posts: List of analysed post dicts (must have "sentiment_label" key).

    Returns:
        Dict with counts: {"Positive": int, "Neutral": int, "Negative": int}
    """
    summary = {"Positive": 0, "Neutral": 0, "Negative": 0}

    for post in posts:
        label = post.get("sentiment_label", "Neutral")
        if label in summary:
            summary[label] += 1

    return summary
