import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from urllib.parse import urljoin

from database.db_operations import save_events_bulk
from utils.categorize import categorize_event  # make sure this function exists

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/139.0.0.0 Safari/537.36",
}

BASE_URL = "https://www.boulevardvilavelha.com.br"
START_URL = f"{BASE_URL}/acontece"

def get_end_of_next_month():
    today = datetime.now()
    first_of_next_month = today.replace(day=1) + relativedelta(months=1)
    end_of_next_month = (first_of_next_month + relativedelta(months=1)) - timedelta(days=1)
    return end_of_next_month

def scrape_boulevard_vila_velha():
    print(f"🔍 Fetching events from {START_URL}")

    try:
        response = requests.get(START_URL, headers=HEADERS, verify=False)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Main container
    container = soup.select_one("div.flex.w-full.flex-wrap.items-center.justify-center.gap-10.px-6.py-20")
    if not container:
        print("⚠️ Event container not found.")
        return []

    event_cards = [
        div for div in container.find_all("div", class_="flex")
        if set(["flex", "w-max", "flex-[0_0_17rem]"]).issubset(div.get("class", []))
    ]
    if not event_cards:
        print("⚠️ No events found.")
        return []

    print(f"🔗 Found {len(event_cards)} events")
    events = []

    for card in event_cards:
        try:
            # Title and full link
            link_tag = card.select_one("a.text-lg.font-bold")
            if link_tag:
                title = link_tag.get_text(strip=True)
                link = urljoin(BASE_URL, link_tag["href"])
            else:
                title = "Sem título"
                link = START_URL

            # Date
            date_tag = card.select_one("p, span")
            raw_date = date_tag.get_text(strip=True) if date_tag else None
            if raw_date:
                try:
                    event_date = datetime.strptime(raw_date, "%d/%m/%Y")
                except:
                    event_date = get_end_of_next_month()
            else:
                event_date = get_end_of_next_month()
            iso_date = event_date.strftime("%Y-%m-%dT00:00:00.000Z")

            # Image
            img_tag = card.select_one("img")
            image = urljoin(BASE_URL, img_tag["src"]) if img_tag and img_tag.has_attr("src") else None

            # Category
            try:
                category = categorize_event(title)
            except:
                category = "Outros"

            event_data = {
                "title": title,
                "location": "Boulevard Vila Velha, ES",
                "date": iso_date,
                "date_end": iso_date,
                "link": link,
                "image": image,
                "font": "Boulevard Vila Velha",
                "category": category,
                "highlighted": False,
                "UF": "ES",
            }

            events.append(event_data)
            print(f"✅ Parsed event Title: {title}")
            print(f"✅ Parsed event Date: {iso_date}")
            print(f"✅ Parsed event Category: {category}")
            print(f"✅ Parsed event Link: {link}")
            print(f"✅ Parsed event Image: {image}")
            print("-" * 50)

        except Exception as e:
            print(f"⚠️ Error parsing event card: {e}")
            continue




    # Save all events at once
    if events:
        save_events_bulk(events)
        print(f"✅ Saved {len(events)} Boulevard Vila Velha events.")
    else:
        print("⚠️ No events saved.")

    return events

if __name__ == "__main__":
    scrape_boulevard_vila_velha()

#  print(f"✅ Parsed event Title: {title}")
#             print(f"✅ Parsed event Font: Boulevard Vila Velha")
#             print(f"✅ Parsed event date: {iso_date}")
#             print(f"✅ Parsed event date end: {iso_date}")
#             print(f"✅ Parsed event Link: {link}")
#             print(f"✅ Parsed event Image: {image}")
#             print(f"✅ Parsed event Category: {category}")