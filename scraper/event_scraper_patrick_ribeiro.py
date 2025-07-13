import requests
from datetime import datetime
import re
from bs4 import BeautifulSoup

from database.db_operations import save_events_bulk
from utils.categorize import categorize_event



MONTHS_PT = {
    "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4, "MAI": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12
}


def extract_date_from_image(img_url):
    # Example: .../2024/12/18JUN-ROUPA.png
    match = re.search(r"/(\d{2})([A-Z]{3})-", img_url.upper())
    year_match = re.search(r"/(\d{4})/", img_url)
    
    if match:
        day = int(match.group(1))
        month_str = match.group(2)
        month = MONTHS_PT.get(month_str)
        
        if month and year_match:
            year = int(year_match.group(1))
            try:
                return datetime(year, month, day)
            except ValueError:
                return None
    return None


def scrape_and_save_patrick_events():
    url = "https://patrickribeiro.com.br/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Failed to fetch page: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # 🔍 Find ALL event cards directly, not just inside one container
    event_cards = soup.select('div.e-loop-item[data-elementor-type="loop-item"][data-elementor-id="247"]')

    if not event_cards:
        print("⚠️ No events found.")
        return

    events_to_save = []

    for i, card in enumerate(event_cards):
        try:
            print(f"--- Processing card {i + 1} ---")

            # Title
            title_tag = card.select_one("h3.elementor-heading-title")
            title = title_tag.text.strip() if title_tag else None

            # Image
            img_tag = card.select_one("img")
            img_src = img_tag["src"].strip() if img_tag and "src" in img_tag.attrs else None

            # Link
            link_tag = card.select_one("a.elementor-button")
            href = link_tag["href"].strip() if link_tag and "href" in link_tag.attrs else None

            parsed_date = extract_date_from_image(img_src)
            if parsed_date and parsed_date < datetime.now():
                print(f"⏩ Skipping past event: {title} ({parsed_date})")
                continue

            event_data = {
                "title": title,
                "location": "Espaço Patrick Ribeiro",
                "date": parsed_date.isoformat() if parsed_date else None,
                "end_date": parsed_date.isoformat() if parsed_date else None,
                "link": href,
                "image": img_src,
                "font": "Espaço Patrick Ribeiro",
                "highlighted": False,
                "category": categorize_event(title),
                "UF": "ES"
            }


            events_to_save.append(event_data)

            # Output
            print(f"📌 {title} | 📍 Espaço Patrick Ribeiro | 🕒 None")
            print(f"🔗 {href}")
            print(f"🖼️ {img_src}")
            print("-" * 60)

        except Exception as err:
            print(f"⚠️ Error parsing event card: {err}")

    if events_to_save:
        save_events_bulk(events_to_save)
        print(f"✅ Saved {len(events_to_save)} Patrick Ribeiro events to MongoDB.")
    else:
        print("⚠️ No valid events to save.")
