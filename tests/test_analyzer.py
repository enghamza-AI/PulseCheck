"""
tests/test_analyzer.py
----------------------
Unit tests for analyzer.py

Tests cover:
    - Sentiment scoring range and label assignment
    - Keyword extraction (stopword filtering, frequency counting)
    - Sentiment summary counts
"""

import pytest
from analyzer import analyze_posts, get_trending_keywords, get_sentiment_summary


# ---------------------------------------------------------------------------
# Sample data helpers
# ---------------------------------------------------------------------------

def make_post(title: str, **kwargs) -> dict:
    """Create a minimal post dict with a given title for testing."""
    return {
        "id": "test",
        "title": title,
        "score": 100,
        "num_comments": 10,
        "permalink": "https://reddit.com/r/test",
        **kwargs
    }


# ---------------------------------------------------------------------------
# Tests for analyze_posts
# ---------------------------------------------------------------------------

class TestAnalyzePosts:
    """Tests for the analyze_posts function."""

    def test_adds_sentiment_fields(self):
        """Each post should gain sentiment_score, sentiment_label, subjectivity."""
        posts = [make_post("This is an amazing library!")]
        result = analyze_posts(posts)

        assert "sentiment_score" in result[0]
        assert "sentiment_label" in result[0]
        assert "subjectivity" in result[0]

    def test_sentiment_score_in_valid_range(self):
        """Polarity should always be between -1.0 and 1.0."""
        posts = [
            make_post("I love Python it is fantastic"),
            make_post("This is the worst thing ever terrible"),
            make_post("The function returns a value"),
        ]
        result = analyze_posts(posts)
        for post in result:
            assert -1.0 <= post["sentiment_score"] <= 1.0

    def test_positive_title_gets_positive_label(self):
        """A clearly positive title should receive the Positive label."""
        posts = [make_post("Amazing wonderful excellent fantastic great!")]
        result = analyze_posts(posts)
        assert result[0]["sentiment_label"] == "Positive"

    def test_negative_title_gets_negative_label(self):
        """A clearly negative title should receive the Negative label."""
        posts = [make_post("Terrible horrible awful disaster failure crash")]
        result = analyze_posts(posts)
        assert result[0]["sentiment_label"] == "Negative"

    def test_label_is_one_of_three_values(self):
        """sentiment_label must always be Positive, Neutral, or Negative."""
        posts = [make_post(t) for t in [
            "Hello world",
            "Great job!",
            "Everything is broken and terrible",
        ]]
        result = analyze_posts(posts)
        valid_labels = {"Positive", "Neutral", "Negative"}
        for post in result:
            assert post["sentiment_label"] in valid_labels

    def test_empty_title_does_not_crash(self):
        """An empty title should produce a Neutral result, not an exception."""
        posts = [make_post("")]
        result = analyze_posts(posts)
        assert result[0]["sentiment_label"] == "Neutral"
        assert result[0]["sentiment_score"] == 0.0

    def test_modifies_posts_in_place_and_returns_them(self):
        """analyze_posts should return the same list (mutated in place)."""
        posts = [make_post("Hello")]
        original_id = id(posts)
        result = analyze_posts(posts)
        assert id(result) == original_id


# ---------------------------------------------------------------------------
# Tests for get_trending_keywords
# ---------------------------------------------------------------------------

class TestGetTrendingKeywords:
    """Tests for the get_trending_keywords function."""

    def test_returns_list_of_tuples(self):
        """Result should be a list of (word, count) tuples."""
        posts = [make_post("Python library for data science")]
        result = get_trending_keywords(posts, top_n=5)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)
            assert isinstance(item[1], int)

    def test_stopwords_are_excluded(self):
        """Common stopwords like 'the', 'and', 'is' should not appear."""
        posts = [make_post("the and is a or but for of with by")]
        result = get_trending_keywords(posts, top_n=20)
        words = [word for word, _ in result]
        stopwords = {"the", "and", "is", "a", "or", "but", "for", "of", "with", "by"}
        for sw in stopwords:
            assert sw not in words

    def test_respects_top_n_limit(self):
        """Should return no more than top_n results."""
        titles = [f"word{i} python coding" for i in range(20)]
        posts = [make_post(t) for t in titles]
        result = get_trending_keywords(posts, top_n=5)
        assert len(result) <= 5

    def test_sorted_by_frequency_descending(self):
        """Most frequent word should come first."""
        # "python" appears 3x, "data" appears 1x
        posts = [
            make_post("python is great"),
            make_post("python rocks"),
            make_post("python data"),
        ]
        result = get_trending_keywords(posts, top_n=10)
        if result:
            assert result[0][0] == "python"
            assert result[0][1] == 3

    def test_short_words_excluded(self):
        """Words shorter than 3 characters should be filtered out."""
        posts = [make_post("hi ok no go do to up")]
        result = get_trending_keywords(posts, top_n=20)
        words = [word for word, _ in result]
        for word in words:
            assert len(word) >= 3

    def test_empty_posts_returns_empty_list(self):
        """No posts should yield no keywords."""
        result = get_trending_keywords([], top_n=10)
        assert result == []


# ---------------------------------------------------------------------------
# Tests for get_sentiment_summary
# ---------------------------------------------------------------------------

class TestGetSentimentSummary:
    """Tests for the get_sentiment_summary function."""

    def test_counts_all_categories(self):
        """Summary should include all three categories."""
        posts = [
            {**make_post("great"), "sentiment_label": "Positive"},
            {**make_post("ok"), "sentiment_label": "Neutral"},
            {**make_post("bad"), "sentiment_label": "Negative"},
        ]
        result = get_sentiment_summary(posts)
        assert result["Positive"] == 1
        assert result["Neutral"] == 1
        assert result["Negative"] == 1

    def test_empty_posts_returns_zeros(self):
        """No posts should return all zeros."""
        result = get_sentiment_summary([])
        assert result == {"Positive": 0, "Neutral": 0, "Negative": 0}

    def test_total_matches_post_count(self):
        """Sum of all categories should equal number of posts."""
        posts = [
            {**make_post("a"), "sentiment_label": "Positive"},
            {**make_post("b"), "sentiment_label": "Positive"},
            {**make_post("c"), "sentiment_label": "Neutral"},
        ]
        result = get_sentiment_summary(posts)
        total = result["Positive"] + result["Neutral"] + result["Negative"]
        assert total == len(posts)
