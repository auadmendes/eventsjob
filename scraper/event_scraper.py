# scraper/event_scraper.py
import requests
import urllib3
from bs4 import BeautifulSoup

from database.db_operations import save_events_bulk

import time # Good for adding pauses if needed
import traceback # For detailed error reporting

# Selenium specific imports
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By # To specify element selection method
# from selenium.webdriver.support.ui import WebDriverWait # To wait for elements to appear
# from selenium.webdriver.support import expected_conditions as EC # Conditions for waiting

from datetime import datetime



# chrome_options = Options()
# chrome_options.add_argument("--headless")
# Add other options...

# Replace with your actual path to chromedriver.exe
#driver_path = "C:/Users/Luciano.Horta/Documents/Luciano/chrome-win64/chromedriver.exe"


#service = Service(driver_path)

#driver = webdriver.Chrome(service=service, options=chrome_options)



urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

categories = {
    "Esporte" : ["corrida","futebol", 'bike', "esporte", "atleta", "volei", "skate", "campeonato"],
    "Teatro" : ["peça","drama", 'ator', "palco", "teatro", "atriz"],
    "Música" : ["show","musica", 'concerto', "banda", "pagode", "samba", "rock", "dj", "festival", "sertanejo"],
    "Gastronomia" : ["gastronomia","culinária", 'comida', "boteco", "degustação", "vinho"],
}

def categorize_event(title):
    if not title:
        return "Outros"

    title_lower = title.lower()
    for category, keywords in categories.items():
        if any(keyword in title_lower for keyword in keywords):
            return category
    return "Outros"

def scrape_and_save_events(max_pages=5):
    base_url = "https://www.sympla.com.br/eventos/vitoria-es/mais-vistos/entretenimento-dia"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    all_events_to_save = []
    page = 1

    while page <= max_pages:
        url = f"{base_url}?ordem=start-date&page={page}"
        print(f"\n🔄 Scraping page {page}: {url}")

        try:
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"❌ Failed to fetch page {page}: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        event_cards = soup.select('div._1g71xxu0._1g71xxu2 a.sympla-card')

        if not event_cards:
            print("✅ No more event cards found.")
            break

        for card in event_cards:
            try:
                href = card.get("href", "").strip()
                img_tag = card.select_one("img._5ar7pz3")
                img_src = img_tag.get("src", "").strip() if img_tag else None

                title_tag = card.select_one("h3._5ar7pz6")
                title = title_tag.text.strip() if title_tag else None

                location_tag = card.select_one("p._5ar7pz8")
                location = location_tag.text.strip() if location_tag else None

                date_tag = card.select_one("div.qtfy415.qtfy413.qtfy416")
                date = date_tag.text.strip() if date_tag else None

                event_data = {
                    "title": title,
                    "location": location,
                    "date": date,
                    "link": href,
                    "image": img_src,
                    "font": "Sympla",
                    "category": categorize_event(title),
                    "UF": "ES"
                }

                all_events_to_save.append(event_data)

                # Print the event
                print(f"📌 {title} | 📍 {location} | 🕒 {date}")
                print(f"🔗 {href}")
                print(f"🖼️ {img_src}")
                print("-" * 60)

            except Exception as err:
                print(f"⚠️ Error parsing event card: {err}")

        page += 1

    if all_events_to_save:
        save_events_bulk(all_events_to_save)
        print(f"\n✅ Saved {len(all_events_to_save)} events to MongoDB.")
    else:
        print("⚠️ No events to save.")

def scrape_esportivo_events_sympla(max_pages=5):
    base_url = "https://www.sympla.com.br/eventos/vitoria-es/esportivo"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    all_events_to_save = []
    page = 1

    while page <= max_pages:
        url = f"{base_url}?c=em-alta&ordem=start-date&page={page}"
        print(f"\n🔄 Scraping page {page}: {url}")

        try:
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"❌ Failed to fetch page {page}: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        event_cards = soup.select('div._1g71xxu0._1g71xxu2 a.sympla-card')

        if not event_cards:
            print("✅ No more event cards found.")
            break

        for card in event_cards:
            try:
                href = card.get("href", "").strip()
                img_tag = card.select_one("img._5ar7pz3")
                img_src = img_tag.get("src", "").strip() if img_tag else None

                title_tag = card.select_one("h3._5ar7pz6")
                title = title_tag.text.strip() if title_tag else None

                location_tag = card.select_one("p._5ar7pz8")
                location = location_tag.text.strip() if location_tag else None

                date_tag = card.select_one("div.qtfy415.qtfy413.qtfy416")
                date = date_tag.text.strip() if date_tag else None

                event_data = {
                    "title": title,
                    "location": location,
                    "date": date,
                    "link": href,
                    "image": img_src,
                    "font": "Sympla",
                    "category": "Esportivo",
                    "created_at": datetime.utcnow().isoformat(),
                    "UF": "ES"
                }

                all_events_to_save.append(event_data)

                # Print the event
                print(f"📌 {title} | 📍 {location} | 🕒 {date}")
                print(f"🔗 {href}")
                print(f"🖼️ {img_src}")
                print("-" * 60)

            except Exception as err:
                print(f"⚠️ Error parsing event card: {err}")

        page += 1

    if all_events_to_save:
        save_events_bulk(all_events_to_save)
        print(f"\n✅ Saved {len(all_events_to_save)} esportivo events to MongoDB.")
    else:
        print("⚠️ No esportivo events to save.")


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

            event_data = {
                "title": title,
                "location": "Espaço Patrick Ribeiro",
                "date": None,
                "link": href,
                "image": img_src,
                "font": "Espaço Patrick Ribeiro",
                "category": categorize_event(title),
                "UF": "ES"
            }

            events_to_save.append(event_data)

            # Output
            print(f"📌 {title} | 📍 Spaço Patrick Ribeiro | 🕒 None")
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

# def scrape_and_save_beacons_events():
#     import requests
#     from bs4 import BeautifulSoup

#     url = "https://beacons.ai/melhoreseventosdoes"
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
#     }

#     try:
#         response = requests.get(url, headers=headers, verify=False)
#         response.raise_for_status()
#     except requests.RequestException as e:
#         print(f"❌ Failed to fetch page: {e}")
#         return

#     soup = BeautifulSoup(response.text, "html.parser")

#     # ✅ Correct selector based on the real structure
#     event_links = soup.select('a.css-f9dlpb')

#     if not event_links:
#         print("⚠️ No events found.")
#         return

#     events_to_save = []

#     for i, link_tag in enumerate(event_links):
#         try:
#             print(f"--- Processing event {i + 1} ---")

#             href = link_tag.get("href", "").strip()

#             # Image
#             img_tag = link_tag.select_one("img")
#             img_src = img_tag.get("src", "").strip() if img_tag else None

#             # Title and date
#             title_tag = link_tag.select_one("div.text-16")
#             title = title_tag.text.strip() if title_tag else None

#             # Description (including location and maybe artist)
#             desc_tag = link_tag.select_one("div.text-sm-normal")
#             description = desc_tag.text.strip() if desc_tag else ""

#             # Try to extract location from description (last line usually)
#             location = description.split("\n")[-1].strip() if "\n" in description else description.split(",")[-1].strip()

#             # Extract date from title (e.g., "02.AGO | QUINTAL DO TG")
#             date = title.split("|")[0].strip() if title and "|" in title else None

#             event_data = {
#                 "title": title,
#                 "location": location,
#                 "date": date,
#                 "link": href,
#                 "image": img_src,
#                 "font": "Melhores Eventos ES",
#                 "category": categorize_event(title),
#                 "UF": "ES"
#             }

#             events_to_save.append(event_data)

#             print(f"📌 {title} | 📍 {location} | 🕒 {date}")
#             print(f"🔗 {href}")
#             print(f"🖼️ {img_src}")
#             print("-" * 60)

#         except Exception as err:
#             print(f"⚠️ Error parsing event card: {err}")

#     if events_to_save:
#         #save_events_bulk(events_to_save)
#         print(f"✅ Saved {len(events_to_save)} Beacons events to MongoDB.")
#     else:
#         print("⚠️ No valid events to save.")

# def scrape_beacons_with_selenium():
#     url = "https://beacons.ai/melhoreseventosdoes?fbclid=PAZXh0bgNhZW0CMTEAAae9mErKM_MpJc1iQscQWA9Dc1Hn7HQ9xAJMNI2PECVPt0aM4qB7DzyCBKOAQQ_aem_ksFKDl5k3XV4l5T4qfSoWQ"
    
#     # Configure Chrome options
#     chrome_options = Options()
#     # Run Chrome in headless mode (without a visible browser UI)
#     chrome_options.add_argument("--headless")
#     # Recommended arguments for headless mode, especially in Docker/CI environments
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     # Set a user-agent to mimic a real browser
#     chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
#     driver = None # Initialize driver to None for proper cleanup in finally block
#     events_to_save = []

#     print(f"Starting Selenium to fetch URL: {url}")
#     try:
#         # Initialize the Chrome WebDriver using webdriver_manager
#         service = Service(ChromeDriverManager().install())
#         driver = webdriver.Chrome(service=service, options=chrome_options)
        
#         # Navigate to the URL
#         driver.get(url)

#         # --- IMPORTANT: Wait for the dynamic content to load ---
#         # We need to wait until the event links (or their containers) are present on the page.
#         # Based on your previous HTML, 'a.css-f9dlpb' and 'div.Links.imageGrid.grid a.no-underline'
#         # are good candidates. We'll wait until AT LEAST ONE of them is visible.
        
#         # You can adjust the timeout (e.g., 20 seconds) if the page loads slowly
#         print("Waiting for dynamic content to load...")
#         WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, 'a.css-f9dlpb, div.Links.imageGrid.grid a.no-underline'))
#         )
#         print("Dynamic content appears to be loaded.")

#         # Now that the page is fully rendered by the browser, get its source HTML
#         page_source = driver.page_source
#         soup = BeautifulSoup(page_source, "html.parser")

#         # --- Scrape events from the "imageGrid" layout ---
#         print("\n--- Attempting to find imageGrid events using Selenium ---")
#         image_grid_links = soup.select('div.Links.imageGrid.grid a.no-underline')
#         print(f"Selenium found {len(image_grid_links)} potential imageGrid links.")

#         for i, link_tag in enumerate(image_grid_links):
#             try:
#                 print(f"\n--- Processing imageGrid event {i + 1} (Selenium) ---")
#                 href = link_tag.get("href", "").strip()

#                 img_tag = link_tag.select_one("div[role='figure']")
#                 img_src = None
#                 if img_tag and "background-image" in img_tag.get("style", ""):
#                     try:
#                         img_src = img_tag.get("style").split("url(\"")[1].split("\")")[0].strip()
#                     except IndexError:
#                         print("Could not parse image URL from style attribute for imageGrid.")
                
#                 text_container = link_tag.select_one("div.whitespace-pre-wrap")
#                 title_tag = text_container.select_one("div.text-md-strong") if text_container else None
#                 title = title_tag.text.strip() if title_tag else "No Title Found"
#                 desc_tag = text_container.select_one("div.mt-1.text-sm-normal") if text_container else None
#                 description = desc_tag.text.strip() if desc_tag else ""

#                 location = description.split("\n")[-1].strip() if "\n" in description else description.split(",")[-1].strip()
#                 date = title.split("|")[0].strip() if title and "|" in title else None

#                 event_data = {
#                     "title": title, "location": location, "date": date, "link": href,
#                     "image": img_src, "font": "Melhores Eventos ES", "category": categorize_event(title), "UF": "ES"
#                 }
#                 events_to_save.append(event_data)
#                 print(f"📌 {title} | 📍 {location} | 🕒 {date}")
#                 print(f"🔗 {href}")
#                 print(f"🖼️ {img_src}")
#                 print("-" * 60)

#             except Exception as err:
#                 print(f"⚠️ Error parsing imageGrid event card (Selenium): {err}. Skipping this event.")
#                 traceback.print_exc()

#         # --- Scrape events from the "classic" layout ---
#         print("\n--- Attempting to find classic events using Selenium ---")
#         classic_event_links = soup.select('div.Links.classic.mt-4 a.css-f9dlpb')
#         print(f"Selenium found {len(classic_event_links)} potential classic links.")

#         for i, link_tag in enumerate(classic_event_links):
#             try:
#                 print(f"\n--- Processing classic event {i + 1} (Selenium) ---")
#                 href = link_tag.get("href", "").strip()

#                 img_tag = link_tag.select_one("img")
#                 img_src = img_tag.get("src", "").strip() if img_tag else None

#                 title_tag = link_tag.select_one("div.text-16")
#                 title = title_tag.text.strip() if title_tag else "No Title Found"

#                 desc_tag = link_tag.select_one("div.text-sm-normal")
#                 description = desc_tag.text.strip() if desc_tag else ""

#                 location = description.split("\n")[-1].strip() if "\n" in description else description.split(",")[-1].strip()
#                 date = title.split("|")[0].strip() if title and "|" in title else None

#                 event_data = {
#                     "title": title, "location": location, "date": date, "link": href,
#                     "image": img_src, "font": "Melhores Eventos ES", "category": categorize_event(title), "UF": "ES"
#                 }
#                 events_to_save.append(event_data)
#                 print(f"📌 {title} | 📍 {location} | 🕒 {date}")
#                 print(f"🔗 {href}")
#                 print(f"🖼️ {img_src}")
#                 print("-" * 60)

#             except Exception as err:
#                 print(f"⚠️ Error parsing classic event card (Selenium): {err}. Skipping this event.")
#                 traceback.print_exc()

#         if events_to_save:
#             # save_events_bulk(events_to_save) # Uncomment and implement your saving mechanism
#             print(f"\n✅ Successfully scraped {len(events_to_save)} Beacons events using Selenium.")
#             return events_to_save
#         else:
#             print("\n⚠️ No valid events found to scrape using Selenium.")
#             return []

#     except Exception as e:
#         print(f"\n❌ An error occurred during Selenium scraping: {e}")
#         traceback.print_exc()
#         return []
#     finally:
#         # Ensure the browser is closed even if errors occur
#         if driver:
#             driver.quit()
#             print("Selenium browser closed.")



# Manual run
if __name__ == "__main__":
    scrape_and_save_events()
