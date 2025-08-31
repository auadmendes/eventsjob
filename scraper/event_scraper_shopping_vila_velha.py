from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
import urllib3

from database.db_operations import save_events_bulk
from utils.categorize import categorize_event  # optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/139.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
}

def parse_portuguese_date(date_str):
    """
    Parses date strings like '28/07/2025 à 31/08/2025' → datetime objects
    Returns (start_date, end_date)
    """
    try:
        if not date_str:
            return datetime(datetime.now().year, 12, 31), datetime(datetime.now().year, 12, 31)

        date_str = date_str.strip()
        match = re.match(r"(\d{2}/\d{2}/\d{4})\s+à\s+(\d{2}/\d{2}/\d{4})", date_str)
        if match:
            start_str, end_str = match.groups()
            start_date = datetime.strptime(start_str, "%d/%m/%Y")
            end_date = datetime.strptime(end_str, "%d/%m/%Y")
        else:
            start_date = end_date = datetime.strptime(date_str, "%d/%m/%Y")
        return start_date, end_date
    except Exception as e:
        print(f"❌ Failed to parse date '{date_str}': {e}")
        return datetime(datetime.now().year, 12, 31), datetime(datetime.now().year, 12, 31)

def scrape_shopping_vila_velha():
    base_url = "https://shoppingvilavelha.com.br"
    start_url = f"{base_url}/eventos/"
    print(f"🔍 Fetching Shopping Vila Velha events from {start_url}")

    try:
        response = requests.get(start_url, headers=HEADERS, verify=False)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch events page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Find main container with events
    container = soup.select_one(".dsa-event-list-container")
    if not container:
        print("⚠️ Event container not found.")
        return []

    # Find all event cards inside container
    event_cards = container.select(".dsa-card-eventos-lista")
    if not event_cards:
        print("⚠️ No events found.")
        return []

    print(f"🔗 Found {len(event_cards)} events")
    events = []

    # Visit each event detail page
    for card in event_cards:
        try:
            # Title
            title_tag = card.select_one("h5.dsa-text-body-large")
            title = title_tag.get_text(strip=True) if title_tag else None

            # Category
            cat_tag = card.select_one("#event-category")
            category = cat_tag.get_text(strip=True) if cat_tag else "Cultural"
            if "categorize_event" in globals():
                category = categorize_event(title)

            # Date
            date_tag = card.select_one("p span + span")
            raw_date = date_tag.get_text(strip=True) if date_tag else None
            start_date, end_date = parse_portuguese_date(raw_date)
            iso_date = start_date.strftime("%Y-%m-%dT00:00:00.000Z")
            iso_end_date = end_date.strftime("%Y-%m-%dT00:00:00.000Z")

            # Event detail link
            link_tag = card.select_one("a.dsa-link-primary")
            link = f"{base_url}/{link_tag['href'].lstrip('../')}" if link_tag else start_url

            # Fetch event detail page
            description, image = None, None
            if link_tag:
                try:
                    detail_resp = requests.get(link, headers=HEADERS, verify=False)
                    detail_resp.raise_for_status()
                    detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
                    desc_tag = detail_soup.select_one(".dsa-text-body")
                    description = desc_tag.get_text(" ", strip=True) if desc_tag else None
                    img_tag = detail_soup.select_one("img.dsa-w-full")
                    relative_src  = img_tag["src"] if img_tag and img_tag.has_attr("src") else None
                    absolute_url = urljoin(base_url, relative_src)
                except Exception as e:
                    print(f"⚠️ Error fetching details for {title}: {e}")

            event_data = {
                "title": title,
                "location": "Shopping Vila Velha",
                "date": iso_date,
                "end_date": iso_end_date,
                "link": link,
                "image": absolute_url,
                "font": "Shopping Vila Velha",
                "category": category,
                "highlighted": False,
                "UF": "ES",
                "description": description,
            }

            events.append(event_data)
            print(f"✅ Parsed event title: {title}")
            print(f"✅ Parsed event location: Shopping Vila Velha")
            print(f"✅ Parsed event date: {iso_date}")
            print(f"✅ Parsed event date_end: {iso_end_date}")
            print(f"✅ Parsed event link: {link}")
            print(f"✅ Parsed event image: {absolute_url}")
            print(f"✅ Parsed event font: Shopping Vila Velha")
            print(f"✅ Parsed event category: {category}")
            print(f"✅ Parsed event Highlighted: false")
            print(f"✅ Parsed event description: {description}")
            print("-" * 50)
            time.sleep(0.5)  # polite delay

        except Exception as e:
            print(f"⚠️ Error parsing event card: {e}")
            continue

    if events:
        save_events_bulk(events)
        print(f"✅ Saved {len(events)} Shopping Vila Velha events.")
    else:
        print("⚠️ No events saved.")

    return events

if __name__ == "__main__":
    scrape_shopping_vila_velha()
