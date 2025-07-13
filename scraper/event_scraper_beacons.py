import traceback # For detailed error reporting
from datetime import datetime
from bs4 import BeautifulSoup
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By # To specify element selection method
from selenium.webdriver.support.ui import WebDriverWait # To wait for elements to appear
from selenium.webdriver.support import expected_conditions as EC # Conditions for waiting

from selenium.webdriver.chrome.service import Service

from database.db_operations import save_events_bulk
from utils.categorize import categorize_event



import re

from datetime import datetime
import locale

PT_BR_MONTHS_NUM = {
    "JAN": "01", "FEV": "02", "MAR": "03",
    "ABR": "04", "MAI": "05", "JUN": "06",
    "JUL": "07", "AGO": "08", "SET": "09",
    "OUT": "10", "NOV": "11", "DEZ": "12"
}

def parse_beacons_date_range(raw):
    """
    Handles:
    - '22 E 23.AGO' → ('2025-08-22T00:00:00', '2025-08-23T00:00:00')
    - '20.SET' → ('2025-09-20T00:00:00', None)
    """
    try:
        raw = raw.replace("\xa0", " ")  # non-breaking space
        raw = raw.replace(" ", "")      # remove all spaces
        raw = raw.upper().strip()

        current_year = datetime.now().year

        # Multi-day format: 22E23.AGO
        match = re.match(r"^(\d{1,2})E(\d{1,2})\.(\w+)$", raw)
        if match:
            start_day, end_day, pt_month = match.groups()
            month_num = PT_BR_MONTHS_NUM.get(pt_month)
            if not month_num:
                raise ValueError(f"Unrecognized PT month: {pt_month}")
            start_date = datetime.strptime(f"{start_day}.{month_num}.{current_year}", "%d.%m.%Y")
            end_date = datetime.strptime(f"{end_day}.{month_num}.{current_year}", "%d.%m.%Y")
            return start_date.strftime("%Y-%m-%dT00:00:00"), end_date.strftime("%Y-%m-%dT00:00:00")

        # Single-day format: 20.SET
        match = re.match(r"^(\d{1,2})\.(\w+)$", raw)
        if match:
            day, pt_month = match.groups()
            month_num = PT_BR_MONTHS_NUM.get(pt_month)
            if not month_num:
                raise ValueError(f"Unrecognized PT month: {pt_month}")
            date = datetime.strptime(f"{day}.{month_num}.{current_year}", "%d.%m.%Y")
            return date.strftime("%Y-%m-%dT00:00:00"), None

        # If no format matched
        raise ValueError(f"Unrecognized date format: {raw}")

    except Exception as e:
        print(f"⚠️ Could not parse date from: {raw} -> {e}")
        return None, None

def scrape_beacons_with_selenium():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")

    driver_path = "C:/Users/Luciano.Horta/Documents/chromedriver-win64/chromedriver.exe"
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    url = "https://beacons.ai/melhoreseventosdoes?fbclid=PAZXh0bgNhZW0CMTEAAae9mErKM_MpJc1iQscQWA9Dc1Hn7HQ9xAJMNI2PECVPt0aM4qB7DzyCBKOAQQ_aem_ksFKDl5k3XV4l5T4qfSoWQ"

    events_to_save = []
    print(f"Starting Selenium to fetch URL: {url}")

    try:
        driver.get(url)
        print("Waiting for dynamic content to load...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a.css-f9dlpb, div.Links.imageGrid.grid a.no-underline'))
        )
        print("Dynamic content appears to be loaded.")

        soup = BeautifulSoup(driver.page_source, "html.parser")

        print("\n--- Attempting to find imageGrid events using Selenium ---")
        image_grid_links = soup.select('div.Links.imageGrid.grid a.no-underline')
        print(f"Selenium found {len(image_grid_links)} potential imageGrid links.")

        for i, link_tag in enumerate(image_grid_links):
            try:
                print(f"\n--- Processing imageGrid event {i + 1} (Selenium) ---")
                href = link_tag.get("href", "").strip()
                img_tag = link_tag.select_one("div[role='figure']")
                img_src = None
                if img_tag and "background-image" in img_tag.get("style", ""):
                    try:
                        img_src = img_tag.get("style").split("url(\"")[1].split("\")")[0].strip()
                    except IndexError:
                        print("Could not parse image URL.")

                text_container = link_tag.select_one("div.whitespace-pre-wrap")
                title_tag = text_container.select_one("div.text-md-strong") if text_container else None
                title = title_tag.text.strip() if title_tag else "No Title Found"
                desc_tag = text_container.select_one("div.mt-1.text-sm-normal") if text_container else None
                description = desc_tag.text.strip() if desc_tag else ""
                location = description.split("\n")[-1].strip() if "\n" in description else description.split(",")[-1].strip()

                raw_date = title.split("|")[0].strip() if "|" in title else None
                iso_date, iso_end_date = parse_beacons_date_range(raw_date) if raw_date else (None, None)
                if not iso_date:
                    print(f"⚠️ Skipping event due to unparsable date: {title}")
                    continue

                event_data = {
                    "title": title,
                    "location": location,
                    "date": iso_date,
                    "end_date": iso_end_date,
                    "link": href,
                    "image": img_src,
                    "font": "Melhores Eventos ES",
                    "highlighted": False,
                    "category": categorize_event(title),
                    "UF": "ES"
                }

                events_to_save.append(event_data)

            except Exception as err:
                print(f"⚠️ Error parsing imageGrid event card (Selenium): {err}. Skipping this event.")
                traceback.print_exc()

        print("\n--- Attempting to find classic events using Selenium ---")
        classic_event_links = soup.select('div.Links.classic.mt-4 a.css-f9dlpb')
        print(f"Selenium found {len(classic_event_links)} potential classic links.")

        for i, link_tag in enumerate(classic_event_links):
            try:
                print(f"\n--- Processing classic event {i + 1} (Selenium) ---")
                href = link_tag.get("href", "").strip()
                img_tag = link_tag.select_one("img")
                img_src = img_tag.get("src", "").strip() if img_tag else None

                title_tag = link_tag.select_one("div.text-16")
                title = title_tag.text.strip() if title_tag else "No Title Found"

                desc_tag = link_tag.select_one("div.text-sm-normal")
                description = desc_tag.text.strip() if desc_tag else ""
                location = description.split("\n")[-1].strip() if "\n" in description else description.split(",")[-1].strip()

                raw_date = title.split("|")[0].strip() if "|" in title else None
                iso_date, iso_end_date = parse_beacons_date_range(raw_date) if raw_date else (None, None)

                event_data = {
                    "title": title,
                    "location": location,
                    "date": iso_date,
                    "end_date": iso_end_date,
                    "link": href,
                    "image": img_src,
                    "font": "Melhores Eventos ES",
                    "highlighted": False,
                    "category": categorize_event(title),
                    "UF": "ES"
                }

                events_to_save.append(event_data)
                print(f"📌 {title} | 📍 {location} | 🕒 {iso_date} → {iso_end_date}")
                print(f"🔗 {href}")
                print(f"🖼️ {img_src}")
                print("-" * 60)

            except Exception as err:
                print(f"⚠️ Error parsing classic event card (Selenium): {err}. Skipping this event.")
                traceback.print_exc()

        if events_to_save:
            save_events_bulk(events_to_save)
            print(f"\n✅ Successfully scraped {len(events_to_save)} Beacons events using Selenium.")
            return events_to_save
        else:
            print("\n⚠️ No valid events found to scrape using Selenium.")
            return []

    except Exception as e:
        print(f"\n❌ An error occurred during Selenium scraping: {e}")
        traceback.print_exc()
        return []
    finally:
        driver.quit()
        print("Selenium browser closed.")
