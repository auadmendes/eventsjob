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
                "link": href,
                "image": img_src,
                "font": "Espaço Patrick Ribeiro",
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

# Set Brazilian Portuguese locale to parse month names
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    # Fallback for Windows
    locale.setlocale(locale.LC_TIME, 'portuguese')


MONTHS_PT_EXT = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
}

def parse_mapa_date(date_str):
    """
    Converts a date string like "20 de junho às 19:00" into a datetime object.
    Assumes the event is in the current year unless the date has already passed (then assumes next year).
    """
    try:
        match = re.search(r"(\d{1,2}) de (\w+) às (\d{1,2}:\d{2})", date_str.lower())
        if not match:
            return None

        day = int(match.group(1))
        month_name = match.group(2)
        time_part = match.group(3)

        month = MONTHS_PT_EXT.get(month_name)
        if not month:
            return None

        hour, minute = map(int, time_part.split(":"))
        now = datetime.now()
        parsed = datetime(now.year, month, day, hour, minute)

        # If parsed date already passed, assume it's for the next year
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

            # 🔍 Extract and parse the date
            date_element = card.select_one(".entity-card__content--occurrence-data")
            date_text = date_element.text.strip() if date_element else None
            parsed_date = parse_mapa_date(date_text) if date_text else None

            if parsed_date and parsed_date < datetime.now():
                print(f"⏩ Skipped past event: {title} ({parsed_date})")
                continue

            event_data = {
                "title": title,
                "location": location_text,
                "date": parsed_date.isoformat() if parsed_date else None,
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

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def parse_beacons_date(raw_text):
    try:
        # Expected format: "28.JUN" or "28.JUN | Event Title"
        raw_date = raw_text.split("|")[0].strip().replace(".", "")
        day, month_abbr = raw_date[:2], raw_date[2:]
        month_map = {
            'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
            'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12
        }
        month = month_map.get(month_abbr.upper())
        if not month:
            return None
        year = datetime.now().year
        parsed_date = datetime(year, month, int(day))
        if parsed_date < datetime.now():
            parsed_date = parsed_date.replace(year=year + 1)  # Assume it's next year
        return parsed_date
    except Exception as e:
        print(f"❌ Failed to parse date from '{raw_text}': {e}")
        return None

def scrape_beacons_with_selenium():
    options = Options()
    options.add_argument("--headless=new")  # Optional: run in background
    options.add_argument("--window-size=1920,1080")

    # 👇 Update the path to your actual chromedriver location
    #driver_path = "C:/Users/Luciano.Horta/Documents/chromedriver.exe"
    driver_path = "C:/Users/Luciano.Horta/Documents/chromedriver-win64/chromedriver.exe"
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    url = "https://beacons.ai/melhoreseventosdoes?fbclid=PAZXh0bgNhZW0CMTEAAae9mErKM_MpJc1iQscQWA9Dc1Hn7HQ9xAJMNI2PECVPt0aM4qB7DzyCBKOAQQ_aem_ksFKDl5k3XV4l5T4qfSoWQ"
    
    # # Configure Chrome options
    # chrome_options = Options()
    # # Run Chrome in headless mode (without a visible browser UI)
    # chrome_options.add_argument("--headless")
    # # Recommended arguments for headless mode, especially in Docker/CI environments
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # # Set a user-agent to mimic a real browser
    # chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    # driver = None # Initialize driver to None for proper cleanup in finally block
    events_to_save = []

    print(f"Starting Selenium to fetch URL: {url}")
    try:
        # Initialize the Chrome WebDriver using webdriver_manager
        # service = Service(ChromeDriverManager().install())
        #driver = webdriver.Chrome(service=service, options=chrome_options)
        driver = webdriver.Chrome(service=service, options=options)
        
        # Navigate to the URL
        driver.get(url)

        # --- IMPORTANT: Wait for the dynamic content to load ---
        # We need to wait until the event links (or their containers) are present on the page.
        # Based on your previous HTML, 'a.css-f9dlpb' and 'div.Links.imageGrid.grid a.no-underline'
        # are good candidates. We'll wait until AT LEAST ONE of them is visible.
        
        # You can adjust the timeout (e.g., 20 seconds) if the page loads slowly
        print("Waiting for dynamic content to load...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a.css-f9dlpb, div.Links.imageGrid.grid a.no-underline'))
        )
        print("Dynamic content appears to be loaded.")

        # Now that the page is fully rendered by the browser, get its source HTML
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")

        # --- Scrape events from the "imageGrid" layout ---
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
                        print("Could not parse image URL from style attribute for imageGrid.")
                
                text_container = link_tag.select_one("div.whitespace-pre-wrap")
                title_tag = text_container.select_one("div.text-md-strong") if text_container else None
                title = title_tag.text.strip() if title_tag else "No Title Found"
                desc_tag = text_container.select_one("div.mt-1.text-sm-normal") if text_container else None
                description = desc_tag.text.strip() if desc_tag else ""

                location = description.split("\n")[-1].strip() if "\n" in description else description.split(",")[-1].strip()
                #date = title.split("|")[0].strip() if title and "|" in title else None

                # Try to parse a date like '28.JUN'
                raw_date = title.split("|")[0].strip() if title and "|" in title else None
                iso_date = None
                try:
                    # Assuming events are in 2025. You could dynamically use datetime.now().year if needed.
                    parsed_date = datetime.strptime(raw_date + ".2025", "%d.%b.%Y")
                    iso_date = parsed_date.strftime("%Y-%m-%dT00:00:00")
                except Exception as e:
                    print(f"⚠️ Could not parse date from: {raw_date}")

                event_data = {
                    "title": title,
                    "location": location,
                    "date": iso_date,
                    "end_date": None,  # You can extract this later if needed
                    "link": href,
                    "image": img_src,
                    "font": "Melhores Eventos ES",
                    "category": categorize_event(title),
                    "UF": "ES"
                }


                events_to_save.append(event_data)
                # print(f"📌 {title} | 📍 {location} | 🕒 {date}")
                # print(f"🔗 {href}")
                # print(f"🖼️ {img_src}")
                # print("-" * 60)
                #print(f"::::::::{iso_date}")

            except Exception as err:
                print(f"⚠️ Error parsing imageGrid event card (Selenium): {err}. Skipping this event.")
                traceback.print_exc()

        # --- Scrape events from the "classic" layout ---
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
                raw_date = title.split("|")[0].strip() if title and "|" in title else None
                iso_date = None
                try:
                    parsed_date = datetime.strptime(raw_date + ".2025", "%d.%b.%Y")
                    iso_date = parsed_date.strftime("%Y-%m-%dT00:00:00")
                except Exception as e:
                    print(f"⚠️ Could not parse date from: {raw_date}")

                event_data = {
                    "title": title, 
                    "location": location, 
                    "date": iso_date, 
                    "end_date": None,
                    "link": href,
                    "image": img_src, 
                    "font": "Melhores Eventos ES", 
                    "category": categorize_event(title), 
                    "UF": "ES"
                }

                events_to_save.append(event_data)
                print(f"📌 {title} | 📍 {location} | 🕒 {date}")
                print(f"🔗 {href}")
                print(f"🖼️ {img_src}")
                print("-" * 60)

            except Exception as err:
                print(f"⚠️ Error parsing classic event card (Selenium): {err}. Skipping this event.")
                traceback.print_exc()

        if events_to_save:
            save_events_bulk(events_to_save) # Uncomment and implement your saving mechanism
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
        # Ensure the browser is closed even if errors occur
        if driver:
            driver.quit()
            print("Selenium browser closed.")

def parse_date(text):
    """
    Convert date string like '23 junho - 08:00' to datetime object.
    """
    try:
        parts = text.strip().split(" - ")
        day_month = parts[0].strip()  # e.g., "23 junho"
        hour = parts[1].strip() if len(parts) > 1 else "00:00"

        day, month_str = day_month.split()
        month_map = {
            "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5,
            "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
            "outubro": 10, "novembro": 11, "dezembro": 12
        }
        month = month_map.get(month_str.lower())
        if not month:
            return None

        year = datetime.now().year
        date_str = f"{day}/{month}/{year} {hour}"
        return datetime.strptime(date_str, "%d/%m/%Y %H:%M")
    except Exception as e:
        print(f"⚠️ Could not parse date from '{text}': {e}")
        return None

def scrape_craes_events():
    url = "https://www.craes.org.br/evento/lista/"
    print(f"🔍 Fetching CRAES events from {url}")
    
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, verify=False)
        #response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch CRAES events: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    event_blocks = soup.select("div.tribe-events-calendar-list__event-row")

    if not event_blocks:
        print("⚠️ No events found on CRAES.")
        return []

    events_to_save = []
    for block in event_blocks:
        try:
            # Title & Link
            title_tag = block.select_one("h3 a")
            title = title_tag.text.strip()
            link = title_tag["href"].strip()

            # Image
            img_tag = block.select_one("img.tribe-events-calendar-list__event-featured-image")
            img_src = img_tag["src"].strip() if img_tag else None

            # Raw date
            date_text_tag = block.select_one("span.tribe-event-date-start")
            date_str = date_text_tag.text.strip() if date_text_tag else None
            parsed_date = parse_date(date_str) if date_str else None

            # Skip past events
            if parsed_date and parsed_date < datetime.now():
                continue

            event_data = {
                "title": title,
                "location": "CRAES",
                "date": parsed_date.strftime("%Y-%m-%d %H:%M") if parsed_date else None,
                "link": link,
                "image": img_src,
                "font": "CRA-ES",
                "category": categorize_event(title),
                "UF": "ES"
            }

            events_to_save.append(event_data)

            print(f"📌 {title} | 🕒 {event_data['date']}")
            print(f"🔗 {link}")
            print(f"🖼️ {img_src}")
            print("-" * 60)

        except Exception as e:
            print(f"⚠️ Error parsing CRAES event: {e}")
            continue

    if events_to_save:
        save_events_bulk(events_to_save)
        print(f"✅ Saved {len(events_to_save)} CRAES events.")
    else:
        print("⚠️ No future events to save.")

    return events_to_save

import os
os.environ['WDM_SSL_VERIFY'] = '0'

# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager

# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

def scrape_zig_tickets():

    options = Options()
    options.add_argument("--headless=new")  # Optional: run in background
    options.add_argument("--window-size=1920,1080")

    # 👇 Update the path to your actual chromedriver location
    #driver_path = "C:/Users/Luciano.Horta/Documents/chromedriver.exe"
    driver_path = "C:/Users/Luciano.Horta/Documents/chromedriver-win64/chromedriver.exe"
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        url = "https://zig.tickets/pt-BR"
        driver.get(url)

        # Scroll loop
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # wait for events to load
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        cards = driver.find_elements(By.CSS_SELECTOR, "div[id^='card']")

        events = []
        for card in cards:
            try:
                title = card.find_element(By.CSS_SELECTOR, "strong").text
                date = card.find_element(By.TAG_NAME, "time").text
                address = card.find_element(By.TAG_NAME, "p").text
                link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                image = card.find_element(By.TAG_NAME, "img").get_attribute("src")
                events.append({
                    "title": title,
                    "date": date,
                    "address": address,
                    "link": link,
                    "image": image,
                })
                print(events)
            except Exception as e:
                print(f"Error parsing card: {e}")

        # Do something with `events`
        print(f"Found {len(events)} events")
        for event in events:
            print(event)

    finally:
        driver.quit()

COURSE_LIST_URL = "https://www.es.senac.br/cursos?pagina=1&ordem=proximasturmas-desc&per_page=10"
BASE_URL = "https://www.es.senac.br"

def parse_date(date_str):
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y").strftime("%Y-%m-%dT00:00:00")
    except Exception:
        return None



BASE_URL = "https://www.es.senac.br"
COURSE_LIST_URL = f"{BASE_URL}/cursos"

def scrape_senac_courses():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")

    driver_path = "C:/Users/Luciano.Horta/Documents/chromedriver-win64/chromedriver.exe"
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        page = 1
        all_courses = []

        while True:
            url = f"{COURSE_LIST_URL}?pagina={page}&ordem=proximasturmas-desc&per_page=10"
            print(f"\n🌐 Visiting page {page}: {url}")
            driver.get(url)

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.container-cursos.row.gy-3 a.card-lancamento"))
                )
            except:
                print("⚠️ Timeout waiting for course cards — stopping.")
                break

            time.sleep(2)  # ensure full JS rendering

            soup = BeautifulSoup(driver.page_source, "html.parser")
            container = soup.select_one("div.container-cursos.row.gy-3")
            if not container:
                print("❌ Container not found — stopping.")
                break

            cards = container.select("a.card-lancamento")
            print(f"📄 Found {len(cards)} courses on page {page}")
            if not cards:
                print("📭 No more cards found — stopping.")
                break

            for card in cards:
                try:
                    title = card.select_one("p.card-lancamento__text__titulo").text.strip()
                    href = card.get("href", "").strip()
                    link = BASE_URL + href

                    img = card.select_one("img.card-lancamento__imagem--lista")
                    image = img.get("src") if img else None

                    calendar_info = card.find("i", class_="ph ph-calendar")
                    date = None
                    if calendar_info:
                        date_tag = calendar_info.find_next("p")
                        date = parse_date(date_tag.text) if date_tag else None

                    duration_tag = card.find("i", class_="ph ph-clock")
                    duration = None
                    if duration_tag:
                        duration_div = duration_tag.find_parent("div")
                        if duration_div:
                            duration = duration_div.text.strip().split()[0]

                    tags = [span.text.strip().strip(",") for span in card.select("div.card-lancamento__text--details span")]
                    category = ", ".join(tags)

                    course = {
                        "title": title,
                        "link": link,
                        "image": image,
                        "date": date,
                        "duration_hours": duration,
                        "category": "Cursos e Workshops",
                        "font": "Senac ES",
                        "UF": "ES"
                    }

                    print(f"📚 {title} | 🗓️ {date} | ⏱️ {duration}h | 🔗 {link}")
                    all_courses.append(course)

                except Exception as e:
                    print(f"⚠️ Failed to parse a course: {e}")
                    traceback.print_exc()

            page += 1

        print(f"\n✅ Total courses scraped: {len(all_courses)}")

        if all_courses:
            save_events_bulk(all_courses)
            print(f"✅ Saved {len(all_courses)} Senac courses to MongoDB.")
        else:
            print("⚠️ No valid courses to save.")

        return all_courses

    except Exception as e:
        print(f"❌ Selenium error while scraping Senac courses: {e}")
        traceback.print_exc()
        return []

    finally:
        driver.quit()
        print("✅ Selenium browser closed.")
