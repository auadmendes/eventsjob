import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re

from database.db_operations import save_events_bulk
from utils.categorize import categorize_event  # optional, if you have this

# Portuguese months mapping
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
        raw = date_str.replace("\xa0", " ").strip().lower()
        # Match pattern: 15 julho - 19:00
        match = re.match(r"(\d{1,2})\s+(\w+)\s*-\s*(\d{1,2}:\d{2})", raw)
        if not match:
            return None

        day, pt_month, time_part = match.groups()
        month = PT_MONTHS.get(pt_month)
        if not month:
            return None

        year = datetime.now().year
        date_formatted = f"{year}-{month}-{int(day):02d} {time_part}"
        return datetime.strptime(date_formatted, "%Y-%m-%d %H:%M")

    except Exception as e:
        print(f"❌ Failed to parse date '{date_str}': {e}")
        return None

def scrape_sesc_es():
    start_url = "https://sesc-es.com.br/servicos/programacao-cultural/"
    print(f"🔍 Fetching SESC-ES events from {start_url}")

    try:
        response = requests.get(start_url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch SESC-ES events: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Find first event link
    first_event_tag = soup.select_one(".wpem-event-single-image a, .wpem-event-layout-wrapper a.wpem-event-action-url")
    if not first_event_tag:
        print("⚠️ No events found.")
        return []

    next_link = first_event_tag.get("href")
    events_to_save = []

    while next_link:
        try:
            ev_resp = requests.get(next_link, headers={"User-Agent": "Mozilla/5.0"})
            ev_resp.raise_for_status()
            ev_soup = BeautifulSoup(ev_resp.text, "html.parser")

            wrapper = ev_soup.select_one(".wpem-single-event-wrapper")
            if not wrapper:
                break

            # Title
            title_tag = wrapper.select_one(".wpem-event-title h3")
            title = title_tag.text.strip() if title_tag else None

            # Image
            img_tag = wrapper.select_one(".wpem-event-single-image img, .wpem-event-single-image link[rel='image_src']")
            image = img_tag.get("src") or img_tag.get("href") if img_tag else None

            # Description
            desc_tag = wrapper.select_one(".wpem-single-event-body-content")
            description = desc_tag.get_text(" ", strip=True) if desc_tag else None

            # Location
            loc_tag = wrapper.select_one(".wpem-event-location a, .wpem-single-event-sidebar-info h3:contains('Local') + div")
            location = loc_tag.text.strip() if loc_tag else "SESC-ES"

            # Category
            cat_tag = wrapper.select_one(".wpem-event-category span")
            category = cat_tag.text.strip() if cat_tag else categorize_event(title) if 'categorize_event' in globals() else "Cultural"

            # Date
            date_tag = wrapper.select_one(".wpem-event-date-time-text")
            raw_date = date_tag.text.strip() if date_tag else None
            parsed_date = parse_portuguese_date(raw_date) if raw_date else None
            if parsed_date:
                iso_date = parsed_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            else:
                # fallback: last day of current year at 00:00
                current_year = datetime.now().year
                iso_date = f"{current_year}-12-31T00:00:00.000Z"

            event_data = {
                "title": title,
                "location": location or "SESC-ES",
                "date": iso_date,
                "end_date": iso_date,
                "link": next_link,
                "image": image,
                "font": "SESC-ES",
                "category": category,
                "highlighted": False,
                "UF": "ES",
                "description": description,
            }

            events_to_save.append(event_data)
            print(f"📌 {event_data['title']} | 🕒 {event_data['date']}")
            print("-" * 50)

            # Find next event link
            next_btn = ev_soup.select_one(".post-nav a.next")
            next_link = next_btn["href"] if next_btn else None

            time.sleep(1)  # polite delay

        except Exception as e:
            print(f"⚠️ Error parsing event {next_link}: {e}")
            break

    if events_to_save:
        save_events_bulk(events_to_save)
        print(f"✅ Saved {len(events_to_save)} SESC-ES events.")
    else:
        print("⚠️ No events saved.")

    return events_to_save
