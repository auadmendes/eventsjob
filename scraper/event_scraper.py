# scraper/event_scraper.py
import requests
import urllib3
from bs4 import BeautifulSoup

from database.db_operations import save_events_bulk

import time # Good for adding pauses if needed
import traceback # For detailed error reporting



from datetime import datetime
import locale

# Selenium specific imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By # To specify element selection method
from selenium.webdriver.support.ui import WebDriverWait # To wait for elements to appear
from selenium.webdriver.support import expected_conditions as EC # Conditions for waiting
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager





# chrome_options = Options()
# chrome_options.add_argument("--headless")
# Add other options...

# Replace with your actual path to chromedriver.exe
#driver_path = "C:/Users/Luciano.Horta/Documents/Luciano/chrome-win64/chromedriver.exe"


#service = Service(driver_path)

#driver = webdriver.Chrome(service=service, options=chrome_options)



urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

categories = {
    "Esporte": [
        "corrida", "futebol", "bike", "esporte", "atleta", "volei", "skate", "campeonato",
        "trilha", "ciclismo", "basquete", "esportiva"
    ],
    "Teatro": [
        "peça", "drama", "ator", "palco", "teatro", "atriz", "espetáculo", "monólogo", 
        "encenação", "cena"
    ],
    "Música": [
        "show", "música", "musica", "concerto", "banda", "pagode", "samba", "rock", "dj",
        "festival", "sertanejo", "dança", "bailão", "mpb", "funk", "eletrônica"
    ],
    "Stand Up Comedy": [
        "stand up", "comédia", "humor", "piada", "comico", "engraçado", "risada", "humorista"
    ],
    "Gastronomia": [
        "gastronomia", "culinária", "comida", "boteco", "degustação", "vinho", "cozinha", "chef",
        "churrasco", "cerveja", "feira gastronômica"
    ],
    "Digital": [
        "podcast", "vídeo", "video", "entrevista", "audiovisual", "rádio", "online", "streaming",
        "sympla play", "transmissão", "plataforma"
    ],
    "Cursos e Workshops": [
        "curso", "workshop", "aula", "oficina", "treinamento", "capacitação", "mentoria", 
        "aprendizado", "formação"
    ],
    "Congressos e Palestras": [
        "palestra", "congresso", "debate", "seminário", "mesa redonda", "talk", "evento técnico"
    ],
    "Passeios e Tours": [
        "tour", "passeio", "visita guiada", "excursão", "trilha", "bike tour", "viagem"
    ],
    "Infantil": [
        "infantil", "criança", "kids", "palhaço", "desenho", "brinquedo", "família", "família"
    ],
    "Religião e Espiritualidade": [
        "religião", "espiritualidade", "oração", "retiro", "missa", "evangelho", "culto", "fé",
        "igreja"
    ],
    "Pride": [
        "pride", "lgbt", "lgbtqia+", "diversidade", "parada", "orgulho", "inclusão"
    ],
    "Eventos Online": [
        "evento online", "online", "ao vivo", "remoto", "streaming", "webinar"
    ]
}


def categorize_event(title):
    if not title:
        return "Outros"

    title_lower = title.lower()
    for category, keywords in categories.items():
        if any(keyword in title_lower for keyword in keywords):
            return category
    return "Outros"

from datetime import datetime
import re

def parse_sympla_date(date_str):
    try:
        date_str = date_str.lower()
        now = datetime.now()
        year = now.year

        months = {
            "jan": 1, "fev": 2, "mar": 3, "abr": 4,
            "mai": 5, "jun": 6, "jul": 7, "ago": 8,
            "set": 9, "out": 10, "nov": 11, "dez": 12
        }

        # Handle date range: "09 de Mar a 31 de Dez"
        range_match = re.search(r"(\d{1,2}) de (\w+)\s+a\s+(\d{1,2}) de (\w+)", date_str)
        if range_match:
            start_day, start_month, end_day, end_month = range_match.groups()
            start_month_num = months.get(start_month[:3])
            end_month_num = months.get(end_month[:3])

            if not start_month_num or not end_month_num:
                return None

            start_date = datetime(year=year, month=start_month_num, day=int(start_day), hour=8)
            end_date = datetime(year=year, month=end_month_num, day=int(end_day), hour=23, minute=59)

            return (start_date, end_date)

        # Handle single date format: "17 de Ago às 14:00"
        match = re.search(r"(\d{1,2}) de (\w+) às (\d{1,2}:\d{2})", date_str)
        if match:
            day, month_pt, time_str = match.groups()
            month = months.get(month_pt[:3])
            if not month:
                return None
            dt = datetime.strptime(f"{day}/{month}/{year} {time_str}", "%d/%m/%Y %H:%M")
            if dt < now and (now - dt).days > 180:
                dt = dt.replace(year=year + 1)
            return (dt, dt)

        return None

    except Exception as e:
        print(f"⚠️ Error parsing date '{date_str}': {e}")
        return None


def scrape_and_save_events_sympla(max_pages=20):
    base_url = "https://www.sympla.com.br/eventos/vitoria-es"
    headers = {"User-Agent": "Mozilla/5.0"}

    all_events_to_save = []
    today = datetime.now()
    page = 1

    while page <= max_pages:
        url = f"{base_url}?page={page}"
        print(f"\n🔄 Scraping page {page}: {url}")

        try:
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"❌ Failed to fetch page {page}: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        event_cards = soup.select('a.sympla-card')

        if not event_cards:
            print("✅ No more event cards found.")
            break

        for card in event_cards:
            try:
                href = card.get("href", "").strip()
                title = card.select_one("h3._5ar7pz6").text.strip()
                location = card.select_one("p._5ar7pz8").text.strip()
                img_src = card.select_one("img._5ar7pz3")["src"]
                date_text = card.select_one("div.qtfy415.qtfy413.qtfy416").text.strip()

                parsed_dates = parse_sympla_date(date_text)

                if not parsed_dates:
                    print(f"⏩None:::: Skipped DATE:::: {date_text}")
                    continue

                start_date, end_date = parsed_dates

                if end_date < today:
                    print(f"⏩ Skipped past event: {title}")
                    print(f"⏩{start_date}:::: Skipped DATE:::: {date_text}")
                    continue

                event_data = {
                    "title": title,
                    "location": location,
                    "date": start_date.isoformat(),
                    "end_date": end_date.isoformat() if start_date != end_date else None,
                    "link": href,
                    "image": img_src,
                    "font": "Sympla",
                    "category": categorize_event(title),
                    "UF": "ES"
                }

                all_events_to_save.append(event_data)

                print(f"📌 {title} | 📍 {location} | 🕒 {start_date} | End date {end_date}")
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

def scrape_comedy_events(max_pages=5):
    base_url = "https://www.sympla.com.br/eventos/vitoria-es/stand-up-comedy"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    all_events_to_save = []
    page = 1

    while page <= max_pages:
        url = f"{base_url}?c=em-alta&ordem=month_trending_score&page={page}"
        print(f"\n🔄 Scraping comedy page {page}: {url}")

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
                    "category": "Comédia",
                    "UF": "ES",
                    "created_at": datetime.utcnow().isoformat()
                }

                all_events_to_save.append(event_data)

                print(f"🎤 {title} | 📍 {location} | 🕒 {date}")
                print(f"🔗 {href}")
                print(f"🖼️ {img_src}")
                print("-" * 60)

            except Exception as err:
                print(f"⚠️ Error parsing comedy card: {err}")

        page += 1

    if all_events_to_save:
        save_events_bulk(all_events_to_save)
        print(f"\n✅ Saved {len(all_events_to_save)} comedy events to MongoDB.")
    else:
        print("⚠️ No comedy events to save.")

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

# Set Brazilian Portuguese locale to parse month names
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    # Fallback for Windows
    locale.setlocale(locale.LC_TIME, 'portuguese')

# def scrape_mapa_cultural_events():
#     url = "https://mapa.cultura.es.gov.br/eventos/#main-app"
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
#     }

#     future_events = []

#     try:
#         # Set locale to Portuguese for correct month parsing
#         # This might vary based on your OS. Common ones are 'pt_BR.UTF-8', 'pt_BR', 'Portuguese_Brazil'
#         try:
#             locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
#         except locale.Error:
#             try:
#                 locale.setlocale(locale.LC_TIME, 'pt_BR')
#             except locale.Error:
#                 try:
#                     locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
#                 except locale.Error:
#                     logger.warning("Could not set locale for Portuguese. Month parsing might fail.")

#         logger.info(f"Attempting to fetch URL: {url}")
#         response = requests.get(url, headers=headers, timeout=15)
#         response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

#         soup = BeautifulSoup(response.text, "html.parser")
#         logger.info("Successfully fetched page content.")

#         # The main container for all events
#         event_container = soup.find("div", class_="col-9 search-list__cards")
#         if not event_container:
#             logger.error("❌ Could not find the main event container (div.col-9.search-list__cards). Check selector.")
#             # Print a snippet of the soup if the container isn't found, for debugging
#             logger.debug(f"Soup head for debugging (if container not found):\n{soup.prettify()[:1000]}")
#             return []

#         # Each event card is within a 'col-12' div, possibly preceded by a date header
#         # We'll target the 'entity-card occurrence-card' which represents an actual event entry.
#         # This is more precise than just 'col-12' because some 'col-12' might just be date headers.
#         all_event_cards = event_container.find_all("div", class_="entity-card occurrence-card")
        
#         if not all_event_cards:
#             logger.warning("No event cards found with class 'entity-card occurrence-card'.")
#             return []

#         logger.info(f"Found {len(all_event_cards)} potential event cards.")

#         current_year = datetime.now().year # Assume events are in the current year
#         current_date_today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

#         for event_card in all_event_cards:
#             try:
#                 # --- Extract Day and Month from the preceding date block or assume "Hoje" (Today) ---
#                 # The date is usually in a div.search-list__cards--date sibling
#                 # We need to find the closest date header for this event card
                
#                 # Check for an 'actual-date' within the same event_card first (unlikely but robust)
#                 day_tag = event_card.find_previous_sibling("div", class_="search-list__cards--date")
                
#                 if day_tag:
#                     day_text = day_tag.select_one("h2.actual-date").text.strip()
#                     month_text = day_tag.select_one("label.month").text.strip()
#                 else:
#                     # If an event card directly follows another without a date header, it's the same day.
#                     # Or, if it's the very first event, it might be "Hoje" and the date header would be external.
#                     # Let's try to get it from the internal 'occurrence-data' which is more reliable
#                     pass # We'll parse full date from occurrence-data later

#                 # The 'occurrence-data' contains the full date and time string
#                 datetime_tag = event_card.select_one(".entity-card__content--occurrence-data")
#                 date_time_raw = datetime_tag.text.strip() if datetime_tag else None

#                 if not date_time_raw:
#                     logger.warning(f"Could not find datetime for an event card. Skipping. Card snippet: {event_card.prettify()[:200]}")
#                     continue
                
#                 # Example: "18 de junho às 18:30"
#                 # Remove the SVG icon text if present
#                 date_time_raw = date_time_raw.replace('1em', '').strip() # Remove '1em' if it's part of the text from the SVG
                
#                 # Remove icon-related text at the beginning like "1em 1em preserveAspectRatio" etc.
#                 # Find the first digit to assume the start of the date string
#                 date_time_parts = date_time_raw.split(" ", 1) # Split only once to get rid of potential icon artifacts
#                 if len(date_time_parts) > 1 and date_time_parts[0].strip().isdigit():
#                     date_time_str = date_time_raw.strip()
#                 else:
#                     # If the first part is not a digit, it's likely leading icon text. Try to find date
#                     import re
#                     match = re.search(r'(\d{1,2}\s+de\s+\w+\s+às\s+\d{1,2}:\d{2})', date_time_raw)
#                     if match:
#                         date_time_str = match.group(1).strip()
#                     else:
#                         logger.warning(f"Could not parse full date/time string from: '{date_time_raw}'. Skipping.")
#                         continue

#                 # Add current year to the date string for parsing if it's not explicit (which it often isn't on these sites)
#                 # The format is "18 de junho às 18:30" -> "%d de %B às %H:%M"
#                 # We need to explicitly add the current year for strptime
#                 date_time_to_parse = f"{date_time_str} {current_year}"
                
#                 try:
#                     # Parse the date and time string
#                     # Use locale.LC_TIME to handle Portuguese month names
#                     event_datetime = datetime.strptime(date_time_to_parse, "%d de %B às %H:%M %Y")
#                 except ValueError as ve:
#                     # Handle "Hoje" case - this is tricky because "Hoje" means today,
#                     # but if the actual-date is "Hoje", the occurrence-data still has the date
#                     if "Hoje" in day_text and "junho" in month_text.lower():
#                         # We are currently in June 2025. If an event is "Hoje" in June, it's today.
#                         event_datetime = datetime.now().replace(
#                             hour=int(date_time_str.split('às')[1].split(':')[0]),
#                             minute=int(date_time_str.split('às')[1].split(':')[1]),
#                             second=0, microsecond=0
#                         )
#                     else:
#                         logger.error(f"Error parsing date/time '{date_time_to_parse}': {ve}. Skipping event.")
#                         continue

#                 # Filter future events
#                 if event_datetime < datetime.now():
#                     logger.info(f"Skipping past event: {date_time_str} ({event_datetime.strftime('%Y-%m-%d %H:%M')})")
#                     continue

#                 # Extract title
#                 title_tag = event_card.select_one("h2.mc-title")
#                 title = title_tag.text.strip() if title_tag else "No Title Found"

#                 # Extract link (the 'a' tag around the title is a good target)
#                 link_tag = event_card.select_one("div.user-info a[href]")
#                 link = link_tag['href'] if link_tag else None
#                 if link and not link.startswith("http"): # Ensure absolute URL
#                     link = f"https://mapa.cultura.es.gov.br{link}"


#                 # Extract location (can be just name or name + address)
#                 location_name_tag = event_card.select_one("span.space-adress__name")
#                 location_address_tag = event_card.select_one("span.space-adress__adress")
                
#                 location = location_name_tag.text.strip() if location_name_tag else "No Location Found"
#                 if location_address_tag:
#                     location_full = f"{location} {location_address_tag.text.strip()}".strip()
#                 else:
#                     location_full = location

#                 # Extract image
#                 img_tag = event_card.select_one("div.mc-avatar--medium img")
#                 img_src = img_tag['src'] if img_tag else None
#                 if img_src and not img_src.startswith("http"): # Ensure absolute URL
#                     img_src = f"https://mapa.cultura.es.gov.br{img_src}"


#                 event_data = {
#                     "title": title,
#                     "link": link,
#                     "location": location_full,
#                     "date_time": event_datetime.isoformat(), # Store as ISO format
#                     "image": img_src,
#                     "category": "Cultural", # Based on the source
#                     "UF": "ES", # Based on the source
#                     "font": "Mapa Cultural ES", # Add source font
#                     "created_at": datetime.utcnow().isoformat()
#                 }

#                 future_events.append(event_data)

#                 logger.info(f"📅 {event_data['title']} | {event_datetime.strftime('%d/%m/%Y %H:%M')} | 📍 {event_data['location']}")
#                 logger.info(f"🔗 {event_data['link']}")
#                 # logger.info(f"🖼️ {event_data['image']}") # Uncomment if you want to see image URLs
#                 logger.info("-" * 60)

#             except Exception as e:
#                 logger.error(f"⚠️ Error parsing an event card: {e}", exc_info=True) # exc_info for full traceback
#                 # logger.debug(f"Problematic event card HTML:\n{event_card.prettify()[:500]}") # Print problematic card HTML
#                 continue

#     except requests.exceptions.RequestException as e:
#         logger.error(f"❌ Failed to fetch page from {url}: {e}", exc_info=True)
#     except Exception as e:
#         logger.critical(f"An unexpected error occurred during scraping: {e}", exc_info=True)
#     finally:
#         # Reset locale to default after scraping if it was changed
#         try:
#             locale.setlocale(locale.LC_TIME, '')
#         except locale.Error:
#             logger.warning("Could not reset locale.")

#     if future_events:
#         logger.info(f"\n✅ Scraped {len(future_events)} future cultural events from Mapa Cultural ES.")
#         return future_events
#     else:
#         logger.warning("\n⚠️ No valid future events found to scrape from Mapa Cultural ES.")
#         return []

# def scrape_mapa_events():
#     url = "https://mapa.cultura.es.gov.br/eventos/#main-app"
#     headers = {"User-Agent": "Mozilla/5.0"}

#     response = requests.get(url, headers=headers)
#     soup = BeautifulSoup(response.text, "html.parser")

#     col_12_blocks = soup.find_all("div", class_="col-12")
#     today = datetime.now()
#     future_events = []

#     for block in col_12_blocks:
#         try:
#             # Parse date (day + month)
#             # date_tag = block.select_one("h2.actual-date")
#             # month_tag = block.select_one("label.month")
#             # if not date_tag or not month_tag:
#             #     continue

#             # date_str = f"{date_tag.text.strip()} {month_tag.text.strip()} {today.year}"
#             # event_date = datetime.strptime(date_str, "%d %B %Y")

#             # if event_date < today:
#             #     continue  # Skip past events

#             # Get all event cards under this date
#             cards = block.select("div.entity-card.occurrence-card")

#             for card in cards:
#                 title_tag = card.select_one("h2.mc-title")
#                 link_tag = card.select_one("a[href]")
#                 img_tag = card.select_one("img")
#                 location_tag = card.select_one("span.space-adress__name")
#                 datetime_tag = card.select_one(".entity-card__content--occurrence-data")

#                 event_data = {
#                     "title": title_tag.text.strip() if title_tag else None,
#                     "link": link_tag["href"] if link_tag else None,
#                     "image": img_tag["src"] if img_tag else None,
#                     "location": location_tag.text.strip() if location_tag else None,
#                     "date_time": datetime_tag.text.strip() if datetime_tag else event_date.strftime("%d/%m/%Y"),
#                     "category": "Cultural",
#                     "UF": "ES",
#                     "created_at": datetime.utcnow().isoformat()
#                 }

#                 future_events.append(event_data)

#                 print(f"🎭 {event_data['title']}")
#                 print(f"📅 {event_data['date_time']} | 📍 {event_data['location']}")
#                 print(f"🔗 {event_data['link']}\n")

#         except Exception as e:
#             print(f"⚠️ Error parsing a block: {e}")

#     print(f"✅ Found {len(future_events)} future events.")
#     return future_events

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
    except Exception as e:
        print("❌ Could not find event container.")
        driver.quit()
        return []

    time.sleep(2)  # Wait for full JS rendering

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    event_blocks = soup.select(".entity-card.occurrence-card")
    future_events = []

    for card in event_blocks:
        try:
            title = card.select_one(".user-info h2").text.strip()
            link = card.select_one(".user-info a")["href"]
            image = card.select_one(".mc-avatar img")["src"]
            category_text = card.select_one("p.terms").text.strip()
            location = card.select_one(".space-adress__name")
            location_text = location.text.strip() if location else "Mapa Cultural ES"

            # Optional: parse date
            date_element = card.select_one(".entity-card__content--occurrence-data")
            date_text = date_element.text.strip() if date_element else None

            event_data = {
                "title": title,
                "location": location_text,
                "date": date_text,
                "link": link,
                "image": image,
                "font": "Mapa Cultural ES",
                "category": categorize_event(category_text),
                "UF": "ES"
            }

            future_events.append(event_data)
            print(f"✅ Parsed: {title}")

        except Exception as e:
            print(f"⚠️ Skipped card due to error: {e}")
            continue

    print(f"✅ Total events found: {len(future_events)}")

    if future_events:
        save_events_bulk(future_events)
        print(f"✅ Saved {len(future_events)} Mapa Cultural events to MongoDB.")
    else:
        print("⚠️ No valid events to save.")

    return future_events

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
