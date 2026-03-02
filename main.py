import feedparser
import requests
import os
from datetime import datetime, timedelta, timezone
from time import mktime

# 1. Map your feeds to the GitHub Secrets we created
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

def send_to_discord(webhook_url, entry, feed_name):
    # This formats the message to look like the Rich Embed you wanted
    embed = {
        "title": entry.title,
        "url": entry.link,
        "description": entry.get("summary", "")[:300] + "...", # Grabs a snippet of the article
        "color": 3447003, # A nice blue color
        "author": {"name": feed_name}
    }
    
    # Check if there is a media thumbnail attached to the RSS entry
    if 'media_content' in entry and len(entry.media_content) > 0:
        embed["image"] = {"url": entry.media_content[0]['url']}
    
    payload = {"embeds": [embed]}
    requests.post(webhook_url, json=payload)

def main():
    now = datetime.now(timezone.utc)
    time_window = timedelta(minutes=20) # Only look at the last 20 minutes

    for name, data in FEEDS.items():
        if not data["webhook"]:
            continue
            
        feed = feedparser.parse(data["url"])
        
        for entry in feed.entries:
            if hasattr(entry, 'published_parsed'):
                # Convert RSS time to a usable Python datetime object
                published_time = datetime.fromtimestamp(mktime(entry.published_parsed), timezone.utc)
                
                # If the article is newer than 20 minutes ago, send it!
                if now - published_time <= time_window:
                    send_to_discord(data["webhook"], entry, name)

if __name__ == "__main__":
    main()
