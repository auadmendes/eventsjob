import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re

from database.db_operations import save_events_bulk
from utils.categorize import categorize_event

PT_MONTHS = {
    "janeiro": "01", "fevereiro": "02", "marco": "03", "março": "03", "abril": "04",
    "maio": "05", "junho": "06", "julho": "07", "agosto": "08",
    "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"
}


def parse_portuguese_date(date_str):
    """
    Parses strings like '15 julho - 19:00' → datetime(2025, 07, 15, 19, 00)
    Returns None if parsing fails.
    """
    try:
        # Normalize and clean input
        raw = date_str.replace("\xa0", " ")  # Replace non-breaking spaces
        raw = raw.strip().lower()

        # Match: 15 julho - 19:00
        match = re.match(r"(\d{1,2})\s+(\w+)\s*-\s*(\d{2}:\d{2})", raw)
        if not match:
            print(f"⚠️ No match pattern found in: {raw}")
            return None

        day, pt_month, time = match.groups()
        pt_month = pt_month.strip()

        month = PT_MONTHS.get(pt_month)
        if not month:
            print(f"⚠️ Month not recognized: {pt_month}")
            return None

        year = datetime.now().year
        date_formatted = f"{year}-{month}-{int(day):02d} {time}"

        return datetime.strptime(date_formatted, "%Y-%m-%d %H:%M")

    except Exception as e:
        print(f"❌ Failed to parse date: '{date_str}' | {e}")
        return None
       
def scrape_craes_events():
    url = "https://www.craes.org.br/evento/lista/"
    print(f"🔍 Fetching CRAES events from {url}")
    
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, verify=False)
        #response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch CRAES events: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    event_blocks = soup.select("div.tribe-events-calendar-list__event-row")

    if not event_blocks:
        print("⚠️ No events found on CRAES.")
        return []

    events_to_save = []
    for block in event_blocks:
        try:
            # Title & Link
            title_tag = block.select_one("h3 a")
            title = title_tag.text.strip()
            link = title_tag["href"].strip()

            # Image
            img_tag = block.select_one("img.tribe-events-calendar-list__event-featured-image")
            img_src = img_tag["src"].strip() if img_tag else None

            # Raw date
            date_text_tag = block.select_one("span.tribe-event-date-start")
            date_str = date_text_tag.text.strip() if date_text_tag else None
            parsed_date = parse_portuguese_date(date_str) if date_str else None

            # Skip past events
            if parsed_date and parsed_date < datetime.now():
                continue

            event_data = {
                "title": title,
                "location": "CRAES",
                "date": parsed_date.isoformat() if parsed_date else None,
                "link": link,
                "image": img_src,
                "font": "CRA-ES",
                "category": categorize_event(title),
                "UF": "ES"
            }

            events_to_save.append(event_data)

            print(f"📌 {title} | 🕒 {event_data['date']}")
            print(f"🔗 {link}")
            print(f"🖼️ {img_src}")
            print("-" * 60)

        except Exception as e:
            print(f"⚠️ Error parsing CRAES event: {e}")
            continue

    if events_to_save:
        save_events_bulk(events_to_save)
        print(f"✅ Saved {len(events_to_save)} CRAES events.")
    else:
        print("⚠️ No future events to save.")

    return events_to_save
