from bs4 import BeautifulSoup
from datetime import datetime
import time
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By # To specify element selection method
from selenium.webdriver.support.ui import WebDriverWait # To wait for elements to appear
from selenium.webdriver.support import expected_conditions as EC # Conditions for waiting

from database.db_operations import save_events_bulk, event_exists, deduplicate_events

from utils.categorize import categorize_event

PT_BR_MONTHS = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
    "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
}


def parse_mapa_date(date_str):
    """
    Converts a date string like "27 de junho às 18:00" into a datetime object.
    """
    try:
        match = re.search(r"(\d{1,2}) de (\w+) às (\d{1,2}:\d{2})", date_str.lower())
        if not match:
            print(f"❌ Regex did not match: {date_str}")
            return None

        day, month_name, time_part = match.groups()
        month = PT_BR_MONTHS.get(month_name.lower())

        if not month:
            print(f"❌ Unrecognized month name: {month_name}")
            return None

        now = datetime.now()
        parsed = datetime(now.year, month, int(day), *map(int, time_part.split(":")))

        if parsed < now:
            parsed = parsed.replace(year=now.year + 1)

        return parsed
    except Exception as e:
        print(f"⚠️ Failed to parse MAPA date '{date_str}': {e}")
        return None



def scrape_mapa_events():
    print("⏳ Scraping MAPA Cultura with Selenium...")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://mapa.cultura.es.gov.br/eventos/#main-app")

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-list__cards"))
        )
    except Exception:
        print("❌ Could not find event container.")
        driver.quit()
        return []

    time.sleep(2)

    # ⬇️ Load more events by clicking the button until it's gone
    while True:
        try:
            load_more = driver.find_element(By.XPATH, '//button[contains(text(), "Carregar mais")]')
            driver.execute_script("arguments[0].click();", load_more)
            time.sleep(2)  # Wait for the next batch to load
        except Exception:
            break  # Button not found or finished

    # ⬇️ Only parse after all cards are loaded
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    event_blocks = soup.select(".entity-card.occurrence-card")
    future_events = []

    for card in event_blocks:
        try:
            title = card.select_one(".user-info h2").text.strip()
            img_tag = card.select_one(".mc-avatar img")
            image = img_tag["src"] if img_tag else ""
            category_text = card.select_one("p.terms").text.strip()

            footer = card.select_one(".entity-card__footer--action a")
            link = footer["href"] if footer else None

            location = card.select_one(".space-adress__name")
            location_text = location.text.strip() if location else "Mapa Cultural ES"

            date_element = card.select_one(".entity-card__content--occurrence-data")
            date_text = date_element.text.strip() if date_element else None
            parsed_date = parse_mapa_date(date_text) if date_text else None

            if not link or not parsed_date:
                continue

            if parsed_date < datetime.now():
                print(f"⏩ Skipped past event: {title} ({parsed_date})")
                continue

            event_data = {
                "title": title,
                "location": location_text,
                "date": parsed_date.isoformat(),
                "end_date": parsed_date.isoformat(),
                "link": link,
                "image": image,
                "font": "Mapa Cultural ES",
                "highlighted": False,
                "category": categorize_event(category_text),
                "UF": "ES"
            }

            if event_exists(event_data["title"], event_data["date"], event_data["link"]):
                print(f"🔁 Duplicate skipped: {event_data['title']} on {event_data['date']} at {location_text}")
                continue

            future_events.append(event_data)
            print(f"✅ Parsed: {event_data}")
            print(f"✅ Parsed: {link}")

        except Exception as e:
            print(f"⚠️ Skipped card due to error: {e}")
            continue

    print(f"✅ Total events found: {len(future_events)}")

    if future_events:
        events = deduplicate_events(future_events)
        save_events_bulk(events)
    else:
        print("⚠️ No valid events to save.")

    return future_events
