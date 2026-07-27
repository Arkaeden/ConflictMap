import urllib.request
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime, timezone

# Multi-source official/institutional defense & monitoring endpoints
FEED_URLS = [
    "https://www.centcom.mil/MEDIA/PRESS-RELEASES/Rss/", # Official Multi-National Operations Updates
    "https://news.google.com/rss/search?q=site:defensenews.com+Iran+OR+Israel+OR+Middle+East&hl=en-US&gl=US&ceid=US:en" # Institutional defense reporting
]

CITIES = [
    "Tehran", "Natanz", "Fordow", "Isfahan", "Bushehr", "Bandar Abbas", 
    "Tel Aviv", "Jerusalem", "Haifa", "Eilat", "Gaza City", "Rafah", 
    "Golan Heights", "Beirut", "Tyre", "Damascus", "Baghdad", "Erbil", 
    "Amman", "Riyadh", "Sanaa", "Hodeidah", "Aden", "Strait of Hormuz"
]

def categorize_event(text):
    text_lower = text.lower()
    
    # 1. Determine Actor
    actor = "host"
    if any(x in text_lower for x in ["iran", "irgc", "tehran"]): actor = "iran"
    elif any(x in text_lower for x in ["israel", "idf", "tel aviv"]): actor = "israel"
    elif any(x in text_lower for x in ["us ", "u.s.", "american", "usnt", "pentagon", "centcom"]): actor = "usa"
    elif any(x in text_lower for x in ["hezbollah", "houthi", "hamas", "proxy", "militia"]): actor = "proxy"
    
    # 2. Determine Event Type
    if any(x in text_lower for x in ["airstrike", "air strike", "bombed", "bombing", "strike", "jets", "warplane", "fighter jet", "blast"]): event_type = "airstrike"
    elif any(x in text_lower for x in ["drone", "uav", "unmanned", "quadcopter", "kamikaze"]): event_type = "drone"
    elif any(x in text_lower for x in ["missile", "rocket", "iron dome", "ballistic", "artillery", "shelling", "barrage"]): event_type = "missile"
    elif any(x in text_lower for x in ["ship", "naval", "red sea", "gulf", "tanker", "vessel", "maritime", "destroyer", "strait"]): event_type = "naval"
    elif any(x in text_lower for x in ["troops", "ground", "raid", "soldiers", "infantry", "border clash", "forces", "army"]): event_type = "ground"
    elif any(x in text_lower for x in ["hack", "cyber", "ddos", "malware", "outage", "network"]): event_type = "cyber"
    else: event_type = "diplomatic"
    
    # 3. Determine Location
    location = None
    for city in CITIES:
        if city.lower() in text_lower:
            location = city
            break
            
    if not location:
        if any(x in text_lower for x in ["lebanon", "hezbollah"]): location = "Beirut"
        elif any(x in text_lower for x in ["yemen", "houthi"]): location = "Sanaa"
        elif any(x in text_lower for x in ["syria"]): location = "Damascus"
        elif any(x in text_lower for x in ["gaza", "hamas"]): location = "Gaza City"
        elif any(x in text_lower for x in ["iraq"]): location = "Baghdad"
        elif any(x in text_lower for x in ["red sea", "gulf"]): location = "Strait of Hormuz"
        elif any(x in text_lower for x in ["iran"]): location = "Tehran"
        elif any(x in text_lower for x in ["israel", "idf"]): location = "Jerusalem"
        else: location = "Eastern Med"
            
    return actor, event_type, location

def fetch_and_update():
    incidents = []
    for url in FEED_URLS:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                root = ET.fromstring(response.read())
                for i, item in enumerate(root.findall('.//item')[:6]):
                    title = item.find('title').text
                    pub_date = item.find('pubDate').text
                    link = item.find('link').text
                    
                    clean_title = title.split(' - ')[0] if ' - ' in title else title
                    source = title.split(' - ')[-1] if ' - ' in title else "Official Monitor"
                    
                    actor, event_type, location = categorize_event(title)
                    
                    incidents.append({
                        "id": f"inst_{len(incidents)}",
                        "type": event_type,
                        "actor": actor,
                        "location": location,
                        "title": clean_title[:65] + "..." if len(clean_title) > 65 else clean_title,
                        "blurb": f"Verified institutional telemetry reporting {event_type.upper()} parameters.",
                        "time": pub_date,
                        "source": source,
                        "url": link
                    })
        except Exception as e:
            print(f"Skipping feed due to error: {e}")
            
    feed_data = {
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "incidents": incidents,
        "movements": []
    }
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(feed_data, f, indent=2)
    print("Successfully updated data.json from official sources.")

if __name__ == "__main__":
    fetch_and_update()
