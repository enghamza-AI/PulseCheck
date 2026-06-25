"""
scraper.py
----------
Fetches top posts from any subreddit using Reddit's public API.

Usage (from main.py):
    from scraper import fetch_posts
    posts = fetch_posts("python", limit=100)
"""

import time
import requests

# Reddit strongly prefers a descriptive User-Agent
# Replace YOUR_REDDIT_USERNAME with your Reddit username if you have one.
HEADERS = {
    "User-Agent": "windows:pulsecheck:v1.0 (by /u/YOUR_REDDIT_USERNAME)"
}

# Use API endpoint instead of www.reddit.com
BASE_URL = "https://api.reddit.com/r/{subreddit}/top"

# Delay between requests (seconds)
REQUEST_DELAY = 2


def fetch_posts(subreddit: str, limit: int = 25) -> list[dict]:
    """
    Fetch top posts from a subreddit.

    Args:
        subreddit: Name of subreddit
        limit: Total number of posts wanted

    Returns:
        List of cleaned post dictionaries
    """

    posts = []
    seen_ids = set()

    after = None
    fetched = 0

    print(f"[scraper] Fetching up to {limit} posts from r/{subreddit}...")

    session = requests.Session()
    session.headers.update(HEADERS)

    while fetched < limit:

        batch_size = min(100, limit - fetched)

        params = {
            "limit": batch_size,
            "t": "week"
        }

        if after:
            params["after"] = after

        url = BASE_URL.format(subreddit=subreddit)

        try:
            response = session.get(
                url,
                params=params,
                timeout=15,
                allow_redirects=True
            )

            print(
                f"[scraper] HTTP {response.status_code}"
            )

            response.raise_for_status()

        except requests.exceptions.HTTPError as e:

            print(f"[scraper] HTTP Error: {e}")

            try:
                print(
                    f"[scraper] Server response:\n"
                    f"{response.text[:500]}"
                )
            except:
                pass

            break

        except requests.exceptions.ConnectionError:
            print("[scraper] Connection error.")
            break

        except requests.exceptions.Timeout:
            print("[scraper] Request timed out.")
            break

        except requests.exceptions.RequestException as e:
            print(f"[scraper] Request failed: {e}")
            break

        try:
            data = response.json()
        except ValueError:
            print("[scraper] Invalid JSON returned.")
            print(response.text[:500])
            break

        children = data.get("data", {}).get("children", [])

        if not children:
            print("[scraper] No posts returned.")
            break

        new_posts = 0

        for child in children:

            raw = child.get("data", {})

            post_id = raw.get("id")

            # Prevent duplicates across pages
            if post_id in seen_ids:
                continue

            seen_ids.add(post_id)

            cleaned = _clean_post(raw)

            posts.append(cleaned)

            fetched += 1
            new_posts += 1

            if fetched >= limit:
                break

        print(
            f"[scraper] Added {new_posts} posts "
            f"(total={fetched})"
        )

        after = data.get("data", {}).get("after")

        if not after:
            print("[scraper] Reached end of subreddit results.")
            break

        time.sleep(REQUEST_DELAY)

    print(f"[scraper] Done. Total posts fetched: {len(posts)}")

    return posts


def _clean_post(raw: dict) -> dict:
    """
    Clean Reddit post JSON into a simplified structure.
    """

    return {
        "id": raw.get("id", ""),

        "title": raw.get(
            "title",
            ""
        ).strip(),

        "score": int(
            raw.get("score", 0)
        ),

        "upvote_ratio": float(
            raw.get("upvote_ratio", 0)
        ),

        "num_comments": int(
            raw.get("num_comments", 0)
        ),

        "author": raw.get(
            "author",
            "[deleted]"
        ),

        "url": raw.get(
            "url",
            ""
        ),

        "permalink":
            "https://www.reddit.com" +
            raw.get("permalink", ""),

        "subreddit": raw.get(
            "subreddit",
            ""
        ),

        "created_utc": int(
            raw.get("created_utc", 0)
        ),

        "is_self": bool(
            raw.get("is_self", False)
        ),

        "flair":
            raw.get(
                "link_flair_text"
            ) or ""
    }