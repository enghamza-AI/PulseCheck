"""
tests/test_scraper.py
---------------------
Unit tests for scraper.py

We use unittest.mock to patch requests.get so we never actually hit Reddit
during testing — tests should be fast, offline, and repeatable.
"""

import pytest
from unittest.mock import patch, MagicMock

# Import the functions we want to test.
from scraper import fetch_posts, _clean_post


# ---------------------------------------------------------------------------
# Tests for _clean_post (the data-cleaning helper)
# ---------------------------------------------------------------------------

class TestCleanPost:
    """Tests for the _clean_post function."""

    def test_extracts_basic_fields(self):
        """All expected keys should be present in the cleaned dict."""
        raw = {
            "id": "abc123",
            "title": "  Hello Reddit  ",
            "score": 1500,
            "upvote_ratio": 0.95,
            "num_comments": 42,
            "author": "redditor123",
            "url": "https://example.com",
            "permalink": "/r/python/comments/abc123/hello",
            "subreddit": "python",
            "created_utc": 1700000000,
            "is_self": False,
            "link_flair_text": "Discussion",
        }
        result = _clean_post(raw)

        assert result["id"] == "abc123"
        assert result["title"] == "Hello Reddit"  # stripped whitespace
        assert result["score"] == 1500
        assert result["upvote_ratio"] == 0.95
        assert result["num_comments"] == 42
        assert result["author"] == "redditor123"
        assert result["flair"] == "Discussion"
        # permalink should have the Reddit base URL prepended
        assert result["permalink"].startswith("https://www.reddit.com")

    def test_handles_missing_fields_gracefully(self):
        """A completely empty dict should not raise an exception."""
        result = _clean_post({})

        assert result["id"] == ""
        assert result["title"] == ""
        assert result["score"] == 0
        assert result["num_comments"] == 0
        assert result["author"] == "[deleted]"
        assert result["flair"] == ""

    def test_none_flair_becomes_empty_string(self):
        """link_flair_text is often None; it should become an empty string."""
        raw = {"link_flair_text": None}
        result = _clean_post(raw)
        assert result["flair"] == ""

    def test_score_is_integer(self):
        """Score should always be cast to int."""
        raw = {"score": "999"}   # Sometimes values come as strings
        result = _clean_post(raw)
        assert isinstance(result["score"], int)


# ---------------------------------------------------------------------------
# Tests for fetch_posts (the main scraping function)
# ---------------------------------------------------------------------------

def _make_reddit_response(posts_data: list[dict], after: str = None) -> dict:
    """
    Helper to build a fake Reddit JSON response.
    Reddit wraps everything in data.children, each with a data key.
    """
    children = [{"kind": "t3", "data": p} for p in posts_data]
    return {
        "kind": "Listing",
        "data": {
            "children": children,
            "after": after,
            "before": None,
        }
    }


class TestFetchPosts:
    """Tests for the fetch_posts function."""

    @patch("scraper.requests.get")
    def test_returns_list_of_posts(self, mock_get):
        """fetch_posts should return a list of cleaned post dicts."""
        fake_post = {
            "id": "test1",
            "title": "A great Python library",
            "score": 500,
            "upvote_ratio": 0.92,
            "num_comments": 30,
            "author": "user1",
            "url": "https://example.com",
            "permalink": "/r/python/comments/test1/",
            "subreddit": "python",
            "created_utc": 1700000000,
            "is_self": True,
            "link_flair_text": None,
        }

        mock_response = MagicMock()
        mock_response.json.return_value = _make_reddit_response([fake_post], after=None)
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_posts("python", limit=5)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "test1"

    @patch("scraper.time.sleep")  # Patch sleep so tests run instantly
    @patch("scraper.requests.get")
    def test_paginates_with_after_token(self, mock_get, mock_sleep):
        """
        If the first response has an 'after' token and we haven't hit our limit,
        fetch_posts should make a second request.
        """
        post_page1 = {"id": "p1", "title": "Post 1", "score": 100, "upvote_ratio": 0.9,
                      "num_comments": 5, "author": "u1", "url": "", "permalink": "/r/x/p1",
                      "subreddit": "x", "created_utc": 0, "is_self": False, "link_flair_text": None}
        post_page2 = {"id": "p2", "title": "Post 2", "score": 200, "upvote_ratio": 0.8,
                      "num_comments": 10, "author": "u2", "url": "", "permalink": "/r/x/p2",
                      "subreddit": "x", "created_utc": 0, "is_self": False, "link_flair_text": None}

        # First call returns after="t3_next", second call returns after=None (end)
        mock_get.side_effect = [
            MagicMock(
                json=MagicMock(return_value=_make_reddit_response([post_page1], after="t3_next")),
                raise_for_status=MagicMock(return_value=None)
            ),
            MagicMock(
                json=MagicMock(return_value=_make_reddit_response([post_page2], after=None)),
                raise_for_status=MagicMock(return_value=None)
            ),
        ]

        result = fetch_posts("testsubreddit", limit=200)

        assert len(result) == 2
        assert mock_get.call_count == 2  # Two HTTP requests were made

    @patch("scraper.requests.get")
    def test_handles_request_error_gracefully(self, mock_get):
        """If a network error occurs, fetch_posts should return an empty list (not crash)."""
        import requests as req
        mock_get.side_effect = req.exceptions.ConnectionError("No internet")

        result = fetch_posts("python", limit=10)

        assert result == []
