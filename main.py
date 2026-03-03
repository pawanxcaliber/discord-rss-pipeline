import feedparser
import requests
import os
import re # We added 're' (Regular Expressions) to hunt for hidden image links
from datetime import datetime, timedelta, timezone
from time import mktime

FEEDS = {
    "AI News": {
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*'
}

def extract_image_url(entry):
    """Hunts down the image URL no matter where the website hides it."""
    # 1. Check standard media_content
    if 'media_content' in entry and len(entry.media_content) > 0:
        return entry.media_content[0]['url']
    
    # 2. Check media_thumbnail
    if 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        return entry.media_thumbnail[0]['url']
        
    # 3. Check enclosures (often used by news sites)
    if 'links' in entry:
        for link in entry.links:
            if 'type' in link and link.type.startswith('image/'):
                return link.href
                
    # 4. Search the raw summary text for an HTML <img> tag
    if 'summary' in entry:
        match = re.search(r'<img[^>]+src="([^">]+)"', entry.summary)
        if match:
            return match.group(1)
            
    return None

def send_to_discord(webhook_url, entry, feed_name):
    # This strips out ugly HTML code (<p>, <br>, etc.) from the text preview
    raw_summary = entry.get("summary", "")
    clean_description = re.sub(r'<[^>]+>', '', raw_summary)

    embed = {
        "title": entry.title,
        "url": entry.link,
        "description": clean_description[:300] + "...",
        "color": 3447003,
        "author": {"name": feed_name}
    }
    
    # Run our new image hunter function!
    image_url = extract_image_url(entry)
    if image_url:
        embed["image"] = {"url": image_url}
    
    payload = {"embeds": [embed]}
    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send to Discord: {e}")

def main():
    now = datetime.now(timezone.utc)
    # I've left this at 1 day so you can immediately see the new photos drop in!
    time_window = timedelta(days=1) 

    for name, data in FEEDS.items():
        if not data["webhook"]:
            continue
            
        print(f"Fetching {name}...")
        try:
            response = requests.get(data["url"], headers=HEADERS, timeout=15)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                if hasattr(entry, 'published_parsed') and entry.published_parsed is not None:
                    published_time = datetime.fromtimestamp(mktime(entry.published_parsed), timezone.utc)
                    
                    if now - published_time <= time_window:
                        print(f"Sending new article: {entry.title}")
                        send_to_discord(data["webhook"], entry, name)
                        
        except Exception as e:
            print(f"Error processing {name}: {e}")

if __name__ == "__main__":
    main()
