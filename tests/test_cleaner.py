"""
tests/test_cleaner.py
---------------------
Unit tests focused specifically on data cleaning edge cases.

These tests verify that the scraper handles malformed, missing, or
unexpected data gracefully — a critical requirement for any real-world
scraper since APIs can return surprising things.
"""

import pytest
from scraper import _clean_post


class TestDataCleaning:
    """Edge-case tests for the _clean_post data cleaning function."""

    def test_title_whitespace_stripped(self):
        """Titles with leading/trailing whitespace should be cleaned."""
        raw = {"title": "   \t Hello World \n  "}
        result = _clean_post(raw)
        assert result["title"] == "Hello World"

    def test_score_defaults_to_zero_when_missing(self):
        """Missing score should default to 0, not raise a KeyError."""
        result = _clean_post({})
        assert result["score"] == 0

    def test_score_cast_to_int(self):
        """Score should always be an integer regardless of input type."""
        result = _clean_post({"score": 1234.7})
        assert result["score"] == 1234
        assert isinstance(result["score"], int)

    def test_upvote_ratio_cast_to_float(self):
        """upvote_ratio should always be a float."""
        result = _clean_post({"upvote_ratio": "0.95"})
        assert isinstance(result["upvote_ratio"], float)
        assert result["upvote_ratio"] == 0.95

    def test_num_comments_defaults_to_zero(self):
        """Missing num_comments should default to 0."""
        result = _clean_post({})
        assert result["num_comments"] == 0
        assert isinstance(result["num_comments"], int)

    def test_deleted_author_handled(self):
        """Reddit shows '[deleted]' for removed accounts — should pass through."""
        result = _clean_post({"author": "[deleted]"})
        assert result["author"] == "[deleted]"

    def test_missing_author_defaults_to_deleted(self):
        """A missing author field should default to '[deleted]'."""
        result = _clean_post({})
        assert result["author"] == "[deleted]"

    def test_permalink_gets_base_url_prepended(self):
        """Permalink from Reddit is relative; we should prepend the full domain."""
        raw = {"permalink": "/r/python/comments/abc123/title/"}
        result = _clean_post(raw)
        assert result["permalink"] == "https://www.reddit.com/r/python/comments/abc123/title/"

    def test_empty_permalink_becomes_base_url(self):
        """An empty permalink should become just the base URL."""
        result = _clean_post({"permalink": ""})
        assert result["permalink"] == "https://www.reddit.com"

    def test_none_flair_becomes_empty_string(self):
        """Reddit returns None for posts with no flair; should become empty string."""
        result = _clean_post({"link_flair_text": None})
        assert result["flair"] == ""

    def test_is_self_defaults_to_false(self):
        """Missing is_self should default to False."""
        result = _clean_post({})
        assert result["is_self"] is False

    def test_is_self_cast_to_bool(self):
        """is_self should be a proper Python bool."""
        result = _clean_post({"is_self": 1})  # 1 is truthy
        assert isinstance(result["is_self"], bool)
        assert result["is_self"] is True

    def test_created_utc_defaults_to_zero(self):
        """Missing created_utc should default to 0."""
        result = _clean_post({})
        assert result["created_utc"] == 0

    def test_all_expected_keys_present(self):
        """The cleaned dict should always have all expected keys."""
        expected_keys = {
            "id", "title", "score", "upvote_ratio", "num_comments",
            "author", "url", "permalink", "subreddit", "created_utc",
            "is_self", "flair"
        }
        result = _clean_post({})
        assert expected_keys == set(result.keys())

    def test_unicode_title_handled(self):
        """Non-ASCII titles (emoji, Chinese, Arabic etc.) should not crash."""
        result = _clean_post({"title": "Python 🐍 and AI 人工智能 مرحبا"})
        assert "Python" in result["title"]

    def test_very_long_title_not_truncated(self):
        """The cleaner should NOT truncate titles — that's the reporter's job."""
        long_title = "A" * 500
        result = _clean_post({"title": long_title})
        assert len(result["title"]) == 500
