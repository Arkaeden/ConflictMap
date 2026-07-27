import urllib.request
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime, timezone

# 1. The Live Data Source (Google News RSS for Middle East Conflict)
RSS_URL = "https://news.google.com/rss/search?q=Iran+OR+Israel+OR+Lebanon+OR+Syria+OR+Yemen+strike+OR+missile&hl=en-US&gl=US&ceid=US:en"

# 2. Matching dictionaries based on your HTML map
CITIES = ["Tehran", "Natanz", "Fordow", "Isfahan", "Bushehr", "Bandar Abbas", "Tel Aviv", "Jerusalem", "Haifa", "Eilat", "Gaza City", "Rafah", "Golan Heights", "Beirut", "Tyre", "Damascus", "Baghdad", "Erbil", "Amman", "Riyadh", "Sanaa", "Hodeidah", "Aden"]

def categorize_event(text):
    text_lower = text.lower()
    
    # Determine Actor
    actor = "host"
    if any(x in text_lower for x in ["iran", "irgc", "tehran"]): actor = "iran"
    elif any(x in text_lower for x in ["israel", "idf", "tel aviv"]): actor = "israel"
    elif any(x in text_lower for x in ["us ", "u.s.", "american"]): actor = "usa"
    elif any(x in text_lower for x in ["hezbollah", "houthi", "hamas", "proxy"]): actor = "proxy"
    
    # Determine Type
    event_type = "diplomatic"
    if any(x in text_lower for x in ["airstrike", "bombed", "strike"]): event_type = "airstrike"
    elif any(x in text_lower for x in ["missile", "rocket", "intercepted"]): event_type = "missile"
    elif any(x in text_lower for x in ["drone", "uav"]): event_type = "drone"
    elif any(x in text_lower for x in ["ship", "naval", "red sea"]): event_type = "naval"
    elif any(x in text_lower for x in ["troops", "ground", "raid"]): event_type = "ground"
    elif any(x in text_lower for x in ["hack", "cyber", "ddos"]): event_type = "cyber"
    
    # Determine Location
    location = "Eastern Med" # Fallback
    for city in CITIES:
        if city.lower() in text_lower:
            location = city
            break
            
    return actor, event_type, location

def fetch_and_update():
    try:
        # Fetch RSS data
        req = urllib.request.Request(RSS_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        items = root.findall('.//item')
        
        incidents = []
        
        # Process the 10 most recent news items
        for i, item in enumerate(items[:10]):
            title = item.find('title').text
            pub_date = item.find('pubDate').text
            link = item.find('link').text
            
            # Clean up Google News title formatting
            clean_title = title.split(' - ')[0] if ' - ' in title else title
            source = title.split(' - ')[-1] if ' - ' in title else "News Source"
            
            actor, event_type, location = categorize_event(title)
            
            incident = {
                "id": f"inc_{i}",
                "type": event_type,
                "actor": actor,
                "location": location,
                "title": clean_title[:60] + "..." if len(clean_title) > 60 else clean_title,
                "blurb": f"Reported activity involving {actor.upper()} forces.",
                "time": pub_date,
                "source": source,
                "url": link
            }
            incidents.append(incident)
            
        # Structure exactly as your HTML expects
        feed_data = {
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
            "incidents": incidents,
            "movements": [] # Optional: Can add logic for this later
        }
        
        # Write to data.json
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(feed_data, f, indent=2)
            
        print("Successfully updated data.json")
        
    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    fetch_and_update()
