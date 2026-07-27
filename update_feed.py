import urllib.request
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime, timezone

# 1. Live Data Source (Google News RSS for Middle East Conflict)
RSS_URL = "https://news.google.com/rss/search?q=Iran+OR+Israel+OR+Lebanon+OR+Syria+OR+Yemen+strike+OR+missile+OR+drone+OR+attack&hl=en-US&gl=US&ceid=US:en"

CITIES = [
    "Tehran", "Natanz", "Fordow", "Isfahan", "Bushehr", "Bandar Abbas", 
    "Tel Aviv", "Jerusalem", "Haifa", "Eilat", "Gaza City", "Rafah", 
    "Golan Heights", "Beirut", "Tyre", "Damascus", "Baghdad", "Erbil", 
    "Amman", "Riyadh", "Sanaa", "Hodeidah", "Aden", "Strait of Hormuz"
]

def categorize_event(text):
    text_lower = text.lower()
    
    # --- 1. DETERMINE ACTOR ---
    actor = "host"
    if any(x in text_lower for x in ["iran", "irgc", "tehran"]): 
        actor = "iran"
    elif any(x in text_lower for x in ["israel", "idf", "tel aviv"]): 
        actor = "israel"
    elif any(x in text_lower for x in ["us ", "u.s.", "american", "usnt", "pentagon"]): 
        actor = "usa"
    elif any(x in text_lower for x in ["hezbollah", "houthi", "hamas", "proxy", "militia"]): 
        actor = "proxy"
    
    # --- 2. DETERMINE EVENT TYPE (Precise Matching to avoid Drone lock) ---
    if any(x in text_lower for x in ["airstrike", "air strike", "bombed", "bombing", "strike", "jets", "warplane", "fighter jet", "air raid", "blast"]): 
        event_type = "airstrike"
    elif any(x in text_lower for x in ["drone", "uav", "unmanned", "quadcopter", "kamikaze", "loitering"]): 
        event_type = "drone"
    elif any(x in text_lower for x in ["missile", "rocket", "iron dome", "ballistic", "artillery", "shelling", "barrage"]): 
        event_type = "missile"
    elif any(x in text_lower for x in ["ship", "naval", "red sea", "gulf", "tanker", "vessel", "maritime", "boat", "destroyer", "frigate", "strait"]): 
        event_type = "naval"
    elif any(x in text_lower for x in ["troops", "ground", "raid", "soldiers", "infantry", "border clash", "forces", "army", "commandos"]): 
        event_type = "ground"
    elif any(x in text_lower for x in ["hack", "cyber", "ddos", "malware", "outage", "network", "disrupted"]): 
        event_type = "cyber"
    else:
        event_type = "diplomatic"
    
    # --- 3. DETERMINE LOCATION ---
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
        else:
            location = "Eastern Med"
            
    return actor, event_type, location

def fetch_and_update():
    try:
        req = urllib.request.Request(RSS_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        items = root.findall('.//item')
        incidents = []
        
        for i, item in enumerate(items[:12]):
            title = item.find('title').text
            pub_date = item.find('pubDate').text
            link = item.find('link').text
            
            clean_title = title.split(' - ')[0] if ' - ' in title else title
            source = title.split(' - ')[-1] if ' - ' in title else "News Source"
            
            actor, event_type, location = categorize_event(title)
            
            incident = {
                "id": f"inc_{i}",
                "type": event_type,
                "actor": actor,
                "location": location,
                "title": clean_title[:65] + "..." if len(clean_title) > 65 else clean_title,
                "blurb": f"Reported {event_type.upper()} activity involving {actor.upper()} forces.",
                "time": pub_date,
                "source": source,
                "url": link
            }
            incidents.append(incident)
            
        feed_data = {
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
            "incidents": incidents,
            "movements": []
        }
        
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(feed_data, f, indent=2)
            
        print("Successfully updated data.json")
    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    fetch_and_update()
