from bs4 import BeautifulSoup
from datetime import datetime
import requests

from database.db_operations import save_events_bulk

import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time



from database.db_operations import save_events_bulk

def parse_eventim_date(date_str):
    """Parses formats like '05/07/2025 ─ 06/07/2025' and returns the first date as datetime."""
    try:
        first_date = date_str.split("─")[0].strip()
        return datetime.strptime(first_date, "%d/%m/%Y")
    except Exception as e:
        print(f"❌ Failed to parse date '{date_str}': {e}")
        return None

def scrape_eventim_vitoria():
    url = "https://www.eventim.com.br/city/vitoria-1747/"
    print("⏳ Scraping Eventim for Vitória events...")

    session = requests.Session()
    retries = Retry(total=3, backoff_factor=2, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        #response = requests.get(url, timeout=30, verify=False)
        #response = requests.get(url, timeout=10)
         response = session.get(url, timeout=60, verify=False, allow_redirects=True)
         response.raise_for_status()
         response.raise_for_status()

    except Exception as e:
        print(f"❌ Failed to fetch Eventim page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.find_all("product-group-item")
    
    future_events = []
    for item in results:
        try:
            # Title
            title_tag = item.select_one("div.event-listing-city span")
            title = title_tag.text.strip() if title_tag else "Unknown title"

            # Link
            link_tag = item.select_one("a.btn")
            link = "https://www.eventim.com.br" + link_tag["href"] if link_tag else ""

            # Image
            img_tag = item.select_one("img.listing-image")
            image = img_tag["src"] if img_tag else ""

            # Location (always Vitória for this page)
            location = "Vitória"

            # Date (e.g., 05/07/2025 ─ 06/07/2025)
            date_tag = item.select_one("span.listing-data span")
            date_str = date_tag.text.strip() if date_tag else ""
            parsed_date = parse_eventim_date(date_str)
            if not parsed_date or parsed_date < datetime.now():
                continue  # Skip past/unparseable

            event_data = {
                "title": title,
                "link": link,
                "image": image,
                "location": location,
                "date": parsed_date.isoformat(),
                "end_date": parsed_date.isoformat(),
                "font": "Eventim",
                "category": "Shows e Festas",
                "highlighted": False,
                "UF": "ES"
            }

            future_events.append(event_data)
            print(f"✅ Parsed: {title}")
            print(event_data)
        except Exception as e:
            print(f"⚠️ Skipped card due to error: {e}")
            continue

    print(f"✅ Total events parsed: {len(future_events)}")
    if future_events:
        save_events_bulk(future_events)
        print(f"✅ Saved {len(future_events)} LeBillet events to MongoDB.")
    return future_events

def scrape_eventim_vitoria_selenium():
    print("⏳ Scraping Eventim with Selenium...")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 ... Chrome/125")

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.eventim.com.br/city/vitoria-1747/")

    time.sleep(10)  # let content load

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all("product-group-item")

    events = []

    for item in items:
        try:
            # Title
            title_tag = item.select_one("div.event-listing-city span")
            title = title_tag.text.strip() if title_tag else "Unknown"

            # Image
            img_tag = item.select_one("img.listing-image")
            image = img_tag.get("src") or img_tag.get("data-src", "") if img_tag else ""

            # Link
            link_tag = item.select_one("a.btn")
            link = "https://www.eventim.com.br" + link_tag["href"] if link_tag else ""

            # Date
            date_tag = item.select_one("span.listing-data span")
            date_text = date_tag.text.strip() if date_tag else ""
            first_date = datetime.strptime(date_text.split("─")[0].strip(), "%d/%m/%Y")

            if first_date < datetime.now():
                continue

            # Save
            events.append({
                "title": title,
                "link": link,
                "image": image,
                "location": "Vitória",
                "date": first_date.isoformat(),
                "end_date": first_date.isoformat(),
                "font": "Eventim",
                "category": "Shows e Festas",
                "highlighted": False,
                "UF": "ES"
            })

            print(f"✅ {title}")
        except Exception as e:
            print(f"⚠️ Skipped one: {e}")
            continue


    print(f"✅ Parsed {len(events)} events from Eventim (Selenium).")
    if events:
        save_events_bulk(events)
    return events