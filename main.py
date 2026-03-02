import feedparser
import requests
import os
from datetime import datetime, timedelta, timezone
from time import mktime

FEEDS = {
    "AI News": {
        "url": "https://www.artificialintelligence-news.com/feed/",
        "webhook": os.environ.get("WEBHOOK_AI")
    },
    "Computer Hardware": {
        "url": "https://www.tomshardware.com/feeds/all",
        "webhook": os.environ.get("WEBHOOK_HARDWARE")
    },
    "Geopolitics": {
        "url": "https://foreignpolicy.com/feed/",
        "webhook": os.environ.get("WEBHOOK_GEOPOLITICS")
    },
    "Military Aviation": {
        "url": "https://theaviationist.com/feed/",
        "webhook": os.environ.get("WEBHOOK_AVIATION_MIL")
    },
    "Civilian Aviation": {
        "url": "https://simpleflying.com/feed/",
        "webhook": os.environ.get("WEBHOOK_AVIATION_CIV")
    }
}

# We disguise our script as a standard Google Chrome browser on Windows
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*'
}

def send_to_discord(webhook_url, entry, feed_name):
    embed = {
        "title": entry.title,
        "url": entry.link,
        "description": entry.get("summary", "")[:300] + "...",
        "color": 3447003,
        "author": {"name": feed_name}
    }
    
    if 'media_content' in entry and len(entry.media_content) > 0:
        embed["image"] = {"url": entry.media_content[0]['url']}
    
    payload = {"embeds": [embed]}
    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send to Discord: {e}")

def main():
    now = datetime.now(timezone.utc)
    time_window = timedelta(minutes=20) 

    for name, data in FEEDS.items():
        if not data["webhook"]:
            print(f"Skipping {name}: No webhook configured.")
            continue
            
        print(f"Fetching {name}...")
        try:
            # 1. Fetch the raw XML data using requests with our fake browser headers
            response = requests.get(data["url"], headers=HEADERS, timeout=15)
            response.raise_for_status() # Check if the website returned an error (like 403 Forbidden)
            
            # 2. Pass the raw content to feedparser
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                if hasattr(entry, 'published_parsed') and entry.published_parsed is not None:
                    published_time = datetime.fromtimestamp(mktime(entry.published_parsed), timezone.utc)
                    
                    if now - published_time <= time_window:
                        print(f"Sending new article: {entry.title}")
                        send_to_discord(data["webhook"], entry, name)
                        
        except Exception as e:
            # If a site blocks us, print the error but continue to the next site
            print(f"Error processing {name}: {e}")

if __name__ == "__main__":
    main()
