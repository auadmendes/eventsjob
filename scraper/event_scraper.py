# scraper/event_scraper.py
import requests
import urllib3
from bs4 import BeautifulSoup
import os
from database.db_operations import save_events_bulk, event_exists, deduplicate_events
from utils.categorize import categorize_event
import time # Good for adding pauses if needed


import re

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

# categories = {
#     "Esporte": [
#         "corrida", "futebol", "bike", "esporte", "atleta", "volei", "skate", "campeonato",
#         "trilha", "ciclismo", "basquete", "esportiva"
#     ],
#     "Teatro": [
#         "peça", "drama", "ator", "palco", "teatro", "atriz", "espetáculo", "monólogo", 
#         "encenação", "cena"
#     ],
#     "Música": [
#         "show", "música", "musica", "concerto", "banda", "pagode", "samba", "rock", "dj",
#         "festival", "sertanejo", "dança", "bailão", "mpb", "funk", "eletrônica"
#     ],
#     "Stand Up Comedy": [
#         "stand up", "comédia", "humor", "piada", "comico", "engraçado", "risada", "humorista"
#     ],
#     "Gastronomia": [
#         "gastronomia", "culinária", "comida", "boteco", "degustação", "vinho", "cozinha", "chef",
#         "churrasco", "cerveja", "feira gastronômica"
#     ],
#     "Digital": [
#         "podcast", "vídeo", "video", "entrevista", "audiovisual", "rádio", "online", "streaming",
#         "sympla play", "transmissão", "plataforma"
#     ],
#     "Cursos e Workshops": [
#         "curso", "workshop", "aula", "oficina", "treinamento", "capacitação", "mentoria", 
#         "aprendizado", "formação"
#     ],
#     "Congressos e Palestras": [
#         "palestra", "congresso", "debate", "seminário", "mesa redonda", "talk", "evento técnico"
#     ],
#     "Passeios e Tours": [
#         "tour", "passeio", "visita guiada", "excursão", "trilha", "bike tour", "viagem"
#     ],
#     "Infantil": [
#         "infantil", "criança", "kids", "palhaço", "desenho", "brinquedo", "família", "família"
#     ],
#     "Religião e Espiritualidade": [
#         "religião", "espiritualidade", "oração", "retiro", "missa", "evangelho", "culto", "fé",
#         "igreja"
#     ],
#     "Pride": [
#         "pride", "lgbt", "lgbtqia+", "diversidade", "parada", "orgulho", "inclusão"
#     ],
#     "Eventos Online": [
#         "evento online", "online", "ao vivo", "remoto", "streaming", "webinar"
#     ]
# }

MONTHS_PT = {
    "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4, "MAI": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12
}


# Set Brazilian Portuguese locale to parse month names
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    # Fallback for Windows
    locale.setlocale(locale.LC_TIME, 'portuguese')



from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager




# PT_BR_MONTHS_NUM = {
#     "JAN": "01", "FEV": "02", "MAR": "03",
#     "ABR": "04", "MAI": "05", "JUN": "06",
#     "JUL": "07", "AGO": "08", "SET": "09",
#     "OUT": "10", "NOV": "11", "DEZ": "12"
# }

# def parse_beacons_date_range(raw):
#     """
#     Parses:
#     - '22 E 23.AGO' -> ('2025-08-22T00:00:00', '2025-08-23T00:00:00')
#     - '11.JUL' -> ('2025-07-11T00:00:00', None)
#     """
#     try:
#         raw = raw.replace("\xa0", " ")  # non-breaking space
#         raw = raw.replace(" ", "")      # remove all spaces
#         raw = raw.upper().strip()

#         current_year = datetime.now().year
#         parts = raw.split("E")

#         if len(parts) == 2:
#             start_day = parts[0].strip()
#             end_part = parts[1].strip()

#             if "." not in end_part:
#                 raise ValueError(f"Missing '.' in end part: {end_part}")

#             end_day, pt_month = end_part.split(".")
#             pt_month = pt_month.strip().upper()
#             month_num = PT_BR_MONTHS_NUM.get(pt_month)

#             if not month_num:
#                 raise ValueError(f"Unrecognized PT month: {pt_month}")

#             start_date = datetime.strptime(f"{start_day}.{month_num}.{current_year}", "%d.%m.%Y")
#             end_date = datetime.strptime(f"{end_day}.{month_num}.{current_year}", "%d.%m.%Y")

#             return start_date.strftime("%Y-%m-%dT00:00:00"), end_date.strftime("%Y-%m-%dT00:00:00")

#         else:
#             if "." not in raw:
#                 raise ValueError(f"Missing '.' in single date: {raw}")

#             day, pt_month = raw.split(".")
#             pt_month = pt_month.strip().upper()
#             month_num = PT_BR_MONTHS_NUM.get(pt_month)

#             if not month_num:
#                 raise ValueError(f"Unrecognized PT month: {pt_month}")

#             date = datetime.strptime(f"{day}.{month_num}.{current_year}", "%d.%m.%Y")
#             return date.strftime("%Y-%m-%dT00:00:00"), None

#     except Exception as e:
#         print(f"⚠️ Could not parse date from: {raw} -> {e}")
#         return None, None



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
        # Normalize and clean input
        raw = date_str.replace("\xa0", " ")  # Replace non-breaking spaces
        raw = raw.strip().lower()

        # Match: 15 julho - 19:00
        match = re.match(r"(\d{1,2})\s+(\w+)\s*-\s*(\d{2}:\d{2})", raw)
        if not match:
            print(f"⚠️ No match pattern found in: {raw}")
            return None

        day, pt_month, time = match.groups()
        pt_month = pt_month.strip()

        month = PT_MONTHS.get(pt_month)
        if not month:
            print(f"⚠️ Month not recognized: {pt_month}")
            return None

        year = datetime.now().year
        date_formatted = f"{year}-{month}-{int(day):02d} {time}"

        return datetime.strptime(date_formatted, "%Y-%m-%d %H:%M")

    except Exception as e:
        print(f"❌ Failed to parse date: '{date_str}' | {e}")
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
            parsed_date = parse_portuguese_date(date_str) if date_str else None

            # Skip past events
            if parsed_date and parsed_date < datetime.now():
                continue

            event_data = {
                "title": title,
                "location": "CRAES",
                "date": parsed_date.isoformat() if parsed_date else None,
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


os.environ['WDM_SSL_VERIFY'] = '0'

# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager

# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

def scrape_zig_tickets():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")

    driver_path = "C:/Users/Luciano.Horta/Documents/chromedriver-win64/chromedriver.exe"
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        url = "https://zig.tickets/pt-BR"
        driver.get(url)

        wait = WebDriverWait(driver, 10)
        select_state(driver, wait)
        time.sleep(3)  # Espera os eventos carregarem

        # Scroll para carregar todos os eventos
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Pegar cards de eventos
        cards = driver.find_elements(By.CSS_SELECTOR, "div[id^='card']")
        events = []

        for card in cards:
            try:
                title = card.find_element(By.CSS_SELECTOR, "strong").text.strip()
                date = card.find_element(By.TAG_NAME, "time").text.strip()
                address = card.find_element(By.TAG_NAME, "p").text.strip()
                link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                image = card.find_element(By.TAG_NAME, "img").get_attribute("src")

                event_data = {
                    "title": title,
                    "date": date,
                    "address": address,
                    "link": link,
                    "image": image
                }
                print(f"✅ Event: {title}")
                events.append(event_data)

            except Exception as e:
                print(f"⚠️ Error parsing card: {e}")

        print(f"🎉 Total events: {len(events)}")
        return events

    finally:
        driver.quit()

def select_state(driver, wait):
    try:
        # Step 1: Click region selector (the top header button that opens the modal)
        region_selector = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(., 'Ordenar os eventos por região') or .//svg[contains(@class, 'lucide-map-pin')]]")
        ))
        region_selector.click()

        # Step 2: Wait for modal input to be visible
        search_input = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//input[@placeholder='Busque o estado']")
        ))
        search_input.send_keys("Espírito Santo")
        time.sleep(1)

        # Step 3: Select "Espírito Santo"
        state_option = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//li[normalize-space(text())='Espírito Santo']")
        ))
        state_option.click()

        # Step 4: Wait until modal closes
        wait.until(EC.invisibility_of_element_located(
            (By.XPATH, "//div[@role='dialog']")
        ))

    except Exception as e:
        print(f"❌ Failed to select state: {e}")
        driver.save_screenshot("select_state_error.png")
        raise




STATIC_IMAGE = "https://s3.sa-east-1.amazonaws.com/el.com.br-gpp/portalinstitucional/desenvolvimento-el/78f5ef95-961d-4fd0-b839-740d04ed7328_Fam-lia-Lima--77--otimizado.jpg"
FESTIVAL_TITLE = "XXIX FESTIVAL DE INVERNO + Domingos Martins"
FESTIVAL_FONT = "Festival de Inverno ES"
UF = "ES"
URL = "https://www.festivaldeinvernodm.com.br/pagina/32/programacao-artistica-completa"

def scrape_festival_de_inverno():
    print("⏳ Fetching Festival de Inverno page...")
    try:
        response = requests.get(URL, timeout=10, verify=False)  # SSL bypass
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        print(f"❌ Failed to fetch page: {e}")
        return []

    print("🔍 Scraping Festival de Inverno content...")
    soup = BeautifulSoup(html_content, "html.parser")
    container = soup.select_one("div.container.py-5")

    if not container:
        print("❌ Festival container not found.")
        return []

    year = datetime.now().year
    current_date = None
    events = []

    for tag in container.find_all(["strong", "br"]):
        if tag.name == "strong":
            date_match = re.search(r"(\d{2}/\d{2})", tag.text)
            if date_match:
                date_str = f"{date_match.group(1)}/{year}"
                try:
                    current_date = datetime.strptime(date_str, "%d/%m/%Y").isoformat()
                    continue
                except ValueError:
                    pass

            elif current_date:
                time_match = re.match(r"(\d{1,2}h(?:\d{2})?)", tag.text.strip())
                if time_match:
                    time = time_match.group(1)
                    performance = tag.next_sibling
                    if performance and isinstance(performance, str):
                        description = performance.strip(" –-:\n\t ")

                        event = {
                            "title": FESTIVAL_TITLE,
                            "location": "Domingos Martins",
                            "date": current_date,
                            "link": URL,
                            "image": STATIC_IMAGE,
                            "font": FESTIVAL_FONT,
                            "category": "Festival",
                            "UF": UF,
                            "description": f"{time} - {description}"
                        }

                        events.append(event)
                        print(f"✅ Parsed: {event['description']} on {current_date}")

    print(f"📦 Total Festival events: {len(events)}")

    if events:
        save_events_bulk(events)
        print(f"✅ Saved {len(events)} Festival events to MongoDB.")
    else:
        print("⚠️ No valid events to save.")

    return events
   




   # Domingos Martins
   # https://lebillet.com.br/search?city=45&dateOf=2025-06-22&dateUntil=


   # Cariacíca
   # https://lebillet.com.br/search?city=29&dateOf=2025-06-22&dateUntil=

   # Guaçuí
   # https://lebillet.com.br/search?city=42&dateOf=2025-06-22&dateUntil=
   
   # Guarapari
   # https://lebillet.com.br/search?city=30&dateOf=2025-06-22&dateUntil=

   # Iconha 
   # https://lebillet.com.br/search?city=69&dateOf=&dateUntil=

   # Linjares
   # https://lebillet.com.br/search?city=25&dateOf=&dateUntil=

   # marataízes
   # https://lebillet.com.br/search?city=80&dateOf=&dateUntil=

   # Nova Venécia
   # https://lebillet.com.br/search?city=111&dateOf=&dateUntil=

   # Online
   # https://lebillet.com.br/search?city=104&dateOf=&dateUntil=

   # Online 2
   # https://lebillet.com.br/search?city=28&dateOf=&dateUntil=

   # Piúma
   # https://lebillet.com.br/search?city=84&dateOf=&dateUntil=

   # Praia da Costa
   # https://lebillet.com.br/search?city=72&dateOf=&dateUntil=

   # Santa Tereza
   # https://lebillet.com.br/search?city=49&dateOf=&dateUntil=
     
   # São gabriel da Palha
   # https://lebillet.com.br/search?city=91&dateOf=&dateUntil=

   # São Mateus
   # https://lebillet.com.br/search?city=76&dateOf=&dateUntil=

   # Serra
   # https://lebillet.com.br/search?city=32&dateOf=&dateUntil=

   # Viana
   # https://lebillet.com.br/search?city=114&dateOf=&dateUntil=

   # Vila Velha
   # https://lebillet.com.br/search?city=24&dateOf=&dateUntil=

   # Vitória
   # https://lebillet.com.br/search?city=20&dateOf=&dateUntil=

   # 
   # 

def parse_domingos_martins_date(date_str):
    """
    Converts '27 e 28 de Junho - 21:00h' or '07 de Setembro de 2025' into a datetime object.
    Returns only the **first day**.
    """
    months = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }

    try:
        # Remove time if present
        date_str = date_str.split("-")[0].strip()

        # Handle "27 e 28 de Junho"
        if " e " in date_str:
            date_str = date_str.split(" e ")[0] + " de " + date_str.split(" de ")[1]

        parts = date_str.strip().split(" de ")

        if len(parts) < 2:
            raise ValueError("Not enough parts to parse date.")

        day = int(parts[0].strip())
        month = months[parts[1].strip().lower()]
        year = datetime.now().year

        return datetime(year, month, day)

    except Exception as e:
        print(f"❌ Failed to parse date '{date_str}': {e}")
        return None

def parse_cariacica_date(date_str):
    """Parses Brazilian dates like 'Sáb, 19 de Julho de 2025' or '19 de Julho de 2025'."""
    months = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }

    try:
        # Remove weekday if present (e.g., "Sáb, ")
        if ',' in date_str:
            date_str = date_str.split(',', 1)[1].strip()

        parts = date_str.split(" de ")
        if len(parts) < 3:
            raise ValueError("Not enough parts to parse date.")

        day = int(parts[0])
        month = months[parts[1].strip().lower()]
        year = int(parts[2])
        return datetime(year, month, day)
    except Exception as e:
        print(f"❌ Failed to parse date '{date_str}': {e}")
        return None

def parse_brazilian_date(date_str: str) -> datetime | None:
    months = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }

    try:
        date_str = date_str.lower().strip()

        # Remove weekday if present
        if "," in date_str:
            date_str = date_str.split(",", 1)[1].strip()

        # Remove time info if present (e.g., "- 21:00h")
        if "-" in date_str:
            date_str = date_str.split("-")[0].strip()

        # Handle range with "a" or "e" (e.g., "03 a 06 de Julho 2025" or "27 e 28 de Junho")
        if " a " in date_str or " e " in date_str:
            if " a " in date_str:
                range_sep = " a "
            else:
                range_sep = " e "
            first_day = int(date_str.split(range_sep)[0].strip())

            rest = date_str.split(" de ", 1)[1]  # e.g. "Julho 2025" or "Junho"
            rest_parts = rest.strip().split()
            month = months[rest_parts[0]]
            year = int(rest_parts[1]) if len(rest_parts) > 1 else datetime.now().year

            return datetime(year, month, first_day)

        # Handle full date: "19 de Julho de 2025"
        parts = date_str.split(" de ")
        if len(parts) == 3:
            day = int(parts[0])
            month = months[parts[1]]
            year = int(parts[2])
            return datetime(year, month, day)

        # Handle partial date: "27 de Junho"
        if len(parts) == 2:
            day = int(parts[0])
            month = months[parts[1]]
            year = datetime.now().year
            return datetime(year, month, day)

        raise ValueError("Unsupported date format.")

    except Exception as e:
        print(f"❌ Failed to parse date '{date_str}': {e}")
        return None

# def parse_brazilian_date(date_str: str) -> datetime | None:
#     months = {
#         'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
#         'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
#         'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
#     }

#     try:
#         date_str = date_str.lower().strip()

#         # Remove weekday if present
#         if "," in date_str:
#             date_str = date_str.split(",", 1)[1].strip()

#         # Remove time info if present
#         if "-" in date_str:
#             date_str = date_str.split("-")[0].strip()

#         # Handle range: "03 a 06 de Julho 2025"
#         if " a " in date_str:
#             # Take the first day
#             day = int(date_str.split(" a ")[0].strip())
#             rest = date_str.split(" de ", 1)[1]  # "Julho 2025"
#             month_name, year = rest.strip().split()
#             month = months[month_name]
#             return datetime(int(year), month, day)

#         # Handle normal case: "19 de Julho de 2025"
#         parts = date_str.split(" de ")
#         if len(parts) == 3:
#             day = int(parts[0])
#             month = months[parts[1]]
#             year = int(parts[2])
#             return datetime(year, month, day)

#         # Handle fallback with current year: "27 de Junho"
#         if len(parts) == 2:
#             day = int(parts[0])
#             month = months[parts[1]]
#             year = datetime.now().year
#             return datetime(year, month, day)

#         raise ValueError("Unsupported date format.")

#     except Exception as e:
#         print(f"❌ Failed to parse date '{date_str}': {e}")
#         return None



# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from bs4 import BeautifulSoup
# from datetime import datetime
# import time

