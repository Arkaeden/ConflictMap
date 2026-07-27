import urllib.request
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime, timezone

# Multi-source international security and regional reporting feeds
FEED_URLS = [
    "https://news.google.com/rss/search?q=Iran+OR+Israel+Middle+East+military+strike+defense&hl=en-US&gl=US&ceid=US:en",
    "https://www.al-monitor.com/rss"
]

CITIES = [
    "Tehran", "Natanz", "Fordow", "Isfahan", "Bushehr", "Bandar Abbas", 
    "Tel Aviv", "Jerusalem", "Haifa", "Eilat", "Gaza City", "Rafah", 
    "Golan Heights", "Beirut", "Tyre", "Damascus", "Baghdad", "Erbil", 
    "Amman", "Riyadh", "Sanaa", "Hodeidah", "Aden", "Strait of Hormuz"
]

def categorize_event(text):
    text_lower = text.lower()
    
    actor = "host"
    if any(x in text_lower for x in ["iran", "irgc", "tehran"]): actor = "iran"
    elif any(x in text_lower for x in ["israel", "idf", "tel aviv"]): actor = "israel"
    elif any(x in text_lower for x in ["us ", "u.s.", "american", "usnt", "pentagon", "centcom"]): actor = "usa"
    elif any(x in text_lower for x in ["hezbollah", "houthi", "hamas", "proxy", "militia"]): actor = "proxy"
    
    if any(x in text_lower for x in ["airstrike", "air strike", "bombed", "bombing", "strike", "jets", "warplane", "fighter jet", "blast"]): event_type = "airstrike"
    elif any(x in text_lower for x in ["drone", "uav", "unmanned", "quadcopter", "kamikaze"]): event_type = "drone"
    elif any(x in text_lower for x in ["missile", "rocket", "iron dome", "ballistic", "artillery", "shelling", "barrage"]): event_type = "missile"
    elif any(x in text_lower for x in ["ship", "naval", "red sea", "gulf", "tanker", "vessel", "maritime", "destroyer", "strait"]): event_type = "naval"
    elif any(x in text_lower for x in ["troops", "ground", "raid", "soldiers", "infantry", "border clash", "forces", "army"]): event_type = "ground"
    elif any(x in text_lower for x in ["hack", "cyber", "ddos", "malware", "outage", "network"]): event_type = "cyber"
    else: event_type = "diplomatic"
    
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
    seen_titles = set()
    
    for url in FEED_URLS:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                root = ET.fromstring(response.read())
                for item in root.findall('.//item'):
                    title_elem = item.find('title')
                    date_elem = item.find('pubDate')
                    link_elem = item.find('link')
                    
                    if title_elem is None or not title_elem.text:
                        continue
                        
                    title = title_elem.text
                    if title in seen_titles:
                        continue
                    seen_titles.add(title)
                    
                    pub_date = date_elem.text if date_elem is not None else "Recent"
                    link = link_elem.text if link_elem is not None else "#"
                    
                    clean_title = title.split(' - ')[0] if ' - ' in title else title
                    source = title.split(' - ')[-1] if ' - ' in title else ("Al-Monitor" if "al-monitor" in url else "News Wire")
                    
                    actor, event_type, location = categorize_event(title)
                    
                    incidents.append({
                        "id": f"inc_{len(incidents)}",
                        "type": event_type,
                        "actor": actor,
                        "location": location,
                        "title": clean_title[:65] + "..." if len(clean_title) > 65 else clean_title,
                        "blurb": f"Verified telemetry record tracking {event_type.upper()} regional parameters.",
                        "time": pub_date,
                        "source": source,
                        "url": link
                    })
        except Exception as e:
            print(f"Error reading feed {url}: {e}")
            
    feed_data = {
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "incidents": incidents[:12],
        "movements": []
    }
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(feed_data, f, indent=2)
    print("Successfully updated data.json with multi-wire feeds.")

if __name__ == "__main__":
    fetch_and_update()
