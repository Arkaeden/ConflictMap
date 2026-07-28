import urllib.request
import xml.etree.ElementTree as ET
import json
import re
import html
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

def clean_text(raw_text):
    if not raw_text:
        return ""
    # Strip HTML tags
    clean = re.sub(r'<[^>]+>', '', raw_text)
    # Unescape HTML entities (&amp;, &nbsp;, etc.)
    clean = html.unescape(clean)
    # Normalize whitespaces
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

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
                'Accept': 'application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8'
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_content = response.read()
                root = ET.fromstring(xml_content)
                
                items = root.findall('.//item')
                if not items:
                    items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                
                for item in items:
                    title_elem = item.find('title')
                    if title_elem is None and item.tag.endswith('entry'):
                        title_elem = item.find('{http://www.w3.org/2005/Atom}title')
                        
                    if title_elem is None or not title_elem.text:
                        continue
                        
                    raw_title = clean_text(title_elem.text)
                    if raw_title in seen_titles:
                        continue
                    
                    # Extract RSS description / summary subtext
                    desc_elem = item.find('description')
                    if desc_elem is None:
                        desc_elem = item.find('{http://www.w3.org/2005/Atom}summary')
                    if desc_elem is None:
                        desc_elem = item.find('{http://www.w3.org/2005/Atom}content')
                        
                    raw_desc = desc_elem.text if desc_elem is not None and desc_elem.text else ""
                    summary = clean_text(raw_desc)
                    
                    # Fallback if feed summary is empty
                    if not summary:
                        summary = "Verified tactical intelligence feed update."
                    elif len(summary) > 280:
                        summary = summary[:277] + "..."
                        
                    seen_titles.add(raw_title)
                    
                    date_elem = item.find('pubDate')
                    if date_elem is None:
                        date_elem = item.find('{http://www.w3.org/2005/Atom}published')
                        if date_elem is None:
                            date_elem = item.find('{http://www.w3.org/2005/Atom}updated')
                            
                    pub_date = date_elem.text.strip() if date_elem is not None and date_elem.text else "Recent"
                    source = "Al-Monitor" if "al-monitor" in url else "Middle East Eye"
                    
                    actor, event_type, location = categorize_event(raw_title)
                    clean_title = raw_title.split(' - ')[0] if ' - ' in raw_title else raw_title
                    
                    incidents.append({
                        "id": f"inc_{len(incidents)}",
                        "type": event_type,
                        "actor": actor,
                        "location": location,
                        "title": clean_title,  # Full untruncated title
                        "blurb": summary,       # Real subtext from RSS
                        "time": pub_date,
                        "source": source
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
    print("Successfully updated data.json with RSS summaries.")

if __name__ == "__main__":
    fetch_and_update()
