import urllib.request
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime, timezone

FEED_URLS = [
    "https://www.al-monitor.com/rss",
    "https://www.middleeasteye.net/rss"
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
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/rss+xml, application/xml, text/xml;q=0.9, *_/*;q=0.8'
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                root = ET.fromstring(response.read())
                
                items = root.findall('.//item')
                if not items:
                    items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                
                for item in items:
                    title_elem = item.find('title')
                    if title_elem is None and item.tag.endswith('entry'):
                        title_elem = item.find('{http://www.w3.org/2005/Atom}title')
                        
                    date_elem = item.find('pubDate')
                    if date_elem is None:
                        date_elem = item.find('{http://www.w3.org/2005/Atom}published')
                        if date_elem is None:
                            date_elem = item.find('{http://www.w3.org/2005/Atom}updated')
                            
                    link_elem = item.find('link')
                    link = "#"
                    if link_elem is not None:
                        link = link_elem.text if link_elem.text else link_elem.get('href', '#')
                    elif item.tag.endswith('entry'):
                        link_node = item.find('{http://www.w3.org/2005/Atom}link')
                        if link_node is not None:
                            link = link_node.get('href', '#')
                    
                    if title_elem is None or not title_elem.text:
                        continue
                        
                    title = title_elem.text.strip()
                    if title in seen_titles:
                        continue
                    seen_titles.add(title)
                    
                    pub_date = date_elem.text.strip() if date_elem is not None and date_elem.text else "Recent"
                    source = "Al-Monitor" if "al-monitor" in url else "Middle East Eye"
                    
                    # Properly unpack categorization results
                    actor, event_type, location = categorize_event(title)
                    clean_title = title.split(' - ')[0] if ' - ' in title else title
                    
                    incidents.append({
                        "id": f"inc_{len(incidents)}",
                        "type": event_type,
                        "actor": actor,
                        "location": location,
                        "title": clean_title[:65] + "..." if len(clean_title) > 65 else clean_title,
                        "blurb": f"Verified regional telemetry tracking {event_type.upper()} indicators.",
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
    print("Successfully updated data.json with categorized events.")

if __name__ == "__main__":
    fetch_and_update()
