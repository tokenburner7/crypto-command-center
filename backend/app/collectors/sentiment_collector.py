"""Collect and score crypto sentiment from Reddit with Fear & Greed baseline."""
import json
import os
import time
from app.services.http_client import APIClient
from app.repositories.sentiment_repo import SentimentRepository

reddit = APIClient(base_url="https://www.reddit.com", rate_limit=0.5)
fear_greed_client = APIClient(base_url="https://api.alternative.me", rate_limit=0.2)

CRYPTO_SUBREDDITS = ["CryptoCurrency", "Bitcoin", "ethereum", "CryptoMarkets"]

async def fetch_fear_greed():
    """Fetch Crypto Fear & Greed Index as baseline."""
    try:
        data = await fear_greed_client.get("/fng/", params={"limit": 1})
        item = data.get("data", [{}])[0]
        return {
            "value": int(item.get("value", 50)),
            "classification": item.get("value_classification", "Neutral"),
        }
    except Exception as e:
        print(f"[sentiment] Fear & Greed error: {e}")
        return None

async def fetch_reddit_posts(subreddit: str, limit: int = 25):
    try:
        data = await reddit.get(f"/r/{subreddit}/hot.json", params={"limit": limit})
        posts = data.get("data", {}).get("children", [])
        results = []
        for p in posts:
            d = p["data"]
            results.append({
                "title": d["title"],
                "text": d.get("selftext", "")[:500],
                "score": d["score"],
                "num_comments": d["num_comments"],
                "url": f"https://reddit.com{d['permalink']}",
                "created_utc": int(d["created_utc"]),
            })
        return results
    except Exception as e:
        print(f"[sentiment] Reddit error ({subreddit}): {e}")
        return []

async def score_sentiment_batch(posts: list[dict]) -> list[dict]:
    if not posts:
        return []
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            posts_text = "\n---\n".join(
                f"[{i}] {p['title']}\n{p['text'][:300]}" 
                for i, p in enumerate(posts)
            )
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "system",
                    "content": (
                        "Score crypto sentiment for each post from -1 (extremely bearish) "
                        "to 1 (extremely bullish). Return JSON: "
                        '{"scores": [{"index": int, "score": float, "topic": str, "summary": str}]}'
                    )
                }, {
                    "role": "user",
                    "content": posts_text[:8000]
                }],
                response_format={"type": "json_object"},
            )
            result = json.loads(resp.choices[0].message.content)
            return result.get("scores", [])
        except Exception as e:
            err_msg=str(e)
            if "api_key" in err_msg.lower() or "authorization" in err_msg.lower():
                print("[sentiment] OpenAI auth error — check OPENAI_API_KEY in .env")
            else:
                print(f"[sentiment] OpenAI error: {err_msg[:100]}")
            print("[sentiment] Falling back to keyword scoring")
    
    return [keyword_score(p, i) for i, p in enumerate(posts)]

def keyword_score(post: dict, index: int) -> dict:
    bullish = ["bullish", "moon", "pump", "breakout", "rally", "buy", "long", "green",
               "wagmi", "ape", "bid", "accumulation", "undervalued", "bottom", "surge",
               "rocket", "ath", "break", "upside"]
    bearish = ["bearish", "dump", "crash", "collapse", "sell", "short", "red", "fear",
               "rekt", "ngmi", "jeet", "capitulation", "liquidated", "top", "correction",
               "bubble", "dead", "rug", "scam"]
    text = f"{post['title']} {post['text']}".lower()
    b_count = sum(1 for w in bullish if w in text)
    a_count = sum(1 for w in bearish if w in text)
    total = b_count + a_count
    score = (b_count - a_count) / max(total, 1)
    return {
        "index": index,
        "score": round(score, 3),
        "topic": "crypto",
        "summary": post["title"][:200],
    }

async def collect():
    # Fetch baseline
    fg = await fetch_fear_greed()
    baseline = fg["value"] if fg else None
    
    # Fetch posts
    posts = []
    for sub in CRYPTO_SUBREDDITS:
        posts.extend(await fetch_reddit_posts(sub, limit=10))
    
    if not posts:
        return 0
    
    # Score
    scores = await score_sentiment_batch(posts)
    
    # Save
    db_scores = []
    for s in scores:
        idx = s.get("index", 0)
        if idx < len(posts):
            post = posts[idx]
            db_scores.append({
                "source": "reddit",
                "topic": s.get("topic", "crypto"),
                "score": s["score"],
                "confidence": None,
                "summary": s.get("summary", "")[:300],
                "baseline_fear_greed": baseline,
                "url": post["url"],
                "timestamp": post["created_utc"],
            })
    
    await SentimentRepository.save_scores(db_scores)
    fg_label = f" (F&G: {baseline})" if baseline else ""
    print(f"[sentiment] Collected {len(db_scores)} posts{fg_label}")
    return len(db_scores)
