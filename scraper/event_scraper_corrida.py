import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time

from database.db_operations import save_events_bulk
from utils.categorize import categorize_event

PT_MONTHS = {
    "janeiro": "01", "fevereiro": "02", "marco": "03", "março": "03", "abril": "04",
    "maio": "05", "junho": "06", "julho": "07", "agosto": "08",
    "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"
}


def parse_portuguese_date_range(date_str: str):
    """
    Handles formats like:
      - "30 e 31 de Agosto de 2025"
      - "15 de julho de 2025"
    Returns (start_date, end_date) as datetime or None.
    """
    try:
        raw = date_str.replace("\xa0", " ").strip().lower()

        # e.g. "30 e 31 de agosto de 2025"
        m = re.match(r"(\d{1,2})\s*e\s*(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", raw)
        if m:
            d1, d2, pt_month, year = m.groups()
            month = PT_MONTHS.get(pt_month)
            if not month:
                return None, None
            start = datetime.strptime(f"{year}-{month}-{int(d1):02d}", "%Y-%m-%d")
            end = datetime.strptime(f"{year}-{month}-{int(d2):02d}", "%Y-%m-%d")
            return start, end

        # e.g. "15 de julho de 2025"
        m = re.match(r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", raw)
        if m:
            d, pt_month, year = m.groups()
            month = PT_MONTHS.get(pt_month)
            if not month:
                return None, None
            date = datetime.strptime(f"{year}-{month}-{int(d):02d}", "%Y-%m-%d")
            return date, date

        return None, None
    except:
        return None, None


def scrape_brasilquecorre_es():
    url = "https://brasilquecorre.com/espiritosanto"
    print(f"🔍 Fetching BrasilQueCorre events from {url}")

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch BrasilQueCorre events: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    event_blocks = soup.select("section.cs-section div.cs-line div.cs-box")

    if not event_blocks:
        print("⚠️ No events found.")
        return []

    events_to_save = []

    for block in event_blocks:
        try:
            # Title + link
            title_tag = block.select_one(".cs-text-widget h5 a")
            title = title_tag.text.strip() if title_tag else None
            link = title_tag["href"].strip() if title_tag else None

            # Se não tiver título OU link, ignora o bloco
            if not title or not link:
                continue

            # Image
            img_tag = block.select_one(".cs-image-widget img")
            img_src = img_tag["src"].strip() if img_tag else None

            # Info block (date, location, distances, organizer)
            text_lines = [p.get_text(strip=True) for p in block.select(".cs-text-widget .text-editor p") if p.get_text(strip=True)]

            date_line = text_lines[0] if text_lines else None
            location = text_lines[1] if len(text_lines) > 1 else None
            distances = text_lines[2] if len(text_lines) > 2 else None
            extra = text_lines[3:] if len(text_lines) > 3 else []

            start_date, end_date = parse_portuguese_date_range(date_line) if date_line else (None, None)

            # Skip past events
            if end_date and end_date < datetime.now():
                continue


            event_data = {
                "title": title,
                "location": location,
                "date": start_date.isoformat() if start_date else None,  # usado no banco
                "end_date": end_date.isoformat() if end_date else None,  # extra opcional
                "link": link,
                "image": img_src,
                "font": "Brasil Que Corre",
                "category": "Esporte",
                "highlighted": False,
                "UF": "ES",
                "distances": distances,
                "extra": extra,
            }

      

            events_to_save.append(event_data)

            print(f"📌 {event_data}")
            # print(f"📌 {title}")
            # print(f"🗓️ {date_line}")
            # print(f"📍 {location}")
            # print(f"🔗 {link}")
            # print(f"🖼️ {img_src}")
            print("-" * 50)

        except Exception as e:
            print(f"⚠️ Error parsing event: {e}")
            continue

    if events_to_save:
        save_events_bulk(events_to_save)
        print(f"✅ Saved {len(events_to_save)} BrasilQueCorre events.")
    else:
        print("⚠️ No future events to save.")

    return events_to_save
