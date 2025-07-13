
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import time

def parse_onticket_date(day_str, month_str):
    month_map = {
        "jan.": 1, "fev.": 2, "mar.": 3, "abr.": 4,
        "mai.": 5, "jun.": 6, "jul.": 7, "ago": 8,
        "set.": 9, "out.": 10, "nov.": 11, "dez.": 12
    }
    try:
        day = int(day_str)
        month = month_map[month_str.strip().lower()]
        year = datetime.now().year
        return datetime(year, month, day)
    except Exception as e:
        print(f"❌ Date error: {day_str} {month_str} -> {e}")
        return None

def scrape_onticket_with_selenium():
    print("⏳ Scraping OnTicket with Selenium...")

    url = "https://onticket.com.br/eventos/5784"

    options = Options()
    options.add_argument("--headless=new")  # se der problema, use "--headless"
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    try:
        # Espera o carrossel aparecer
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "carousel-inner")))

        # Rola a página até o carrossel
        driver.execute_script("window.scrollBy(0, 600);")
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        cards = soup.select(".carousel-inner .col-sm-6.item")

        events = []
        for card in cards:
            try:
                image = card.select_one("img")["src"]
                title = card.select_one("h3").text.strip()
                location = card.select_one("#local").text.strip()
                city = card.select_one("#cidade").text.strip()
                day = card.select_one("#dia").text.strip()
                month = card.select_one("#mes").text.strip()

                date = parse_onticket_date(day, month)
                if not date or date < datetime.now():
                    continue

                events.append({
                    "title": title,
                    "image": image,
                    "location": location,
                    "city": city.replace(" - ES", ""),
                    "UF": "ES",
                    "date": date.isoformat(),
                    "font": "OnTicket",
                    "category": "Shows e Festas",
                    "link": url
                })

                print(f"✅ Event parsed: {title}")
            except Exception as e:
                print(f"⚠️ Failed to parse event: {e}")
                continue

        print(f"✅ Total events found: {len(events)}")
        return events

    finally:
        driver.quit()



        
    print("⏳ Scraping OnTicket with Selenium...")

    url = "https://onticket.com.br/eventos/5784?utm_medium=paid&utm_source=ig&utm_id=6770444452737&utm_content=6770444455337&utm_term=6770444453737&utm_campaign=6770444452737&fbclid=PAQ0xDSwLE15pleHRuA2FlbQEwAGFkaWQAAAYoXfOuoQGnLc_131UVZa8U90HknXQgnFbya8hivgEz3jec9fnD92hP7ItKRV1JumHOGYI_aem_knAjTpPg9U17V9MCcWvfEg"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)  # Espera o JS carregar

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    events = []
    cards = soup.select(".carousel-inner .item .col-sm-6.item")

    for card in cards:
        try:
            image = card.select_one("img")["src"]
            title = card.select_one("h3").text.strip()
            location = card.select_one("#local").text.strip()
            city = card.select_one("#cidade").text.strip()
            day = card.select_one("#dia").text.strip()
            month = card.select_one("#mes").text.strip()

            date = parse_onticket_date(day, month)
            if not date or date < datetime.now():
                continue

            event_data = {
                "title": title,
                "image": image,
                "location": location,
                "city": city.replace(" - ES", "").strip(),
                "UF": "ES",
                "date": date.isoformat(),
                "font": "OnTicket",
                "category": "Shows e Festas",
                "link": url
            }

            events.append(event_data)
            print(f"✅ Parsed: {title}")
        except Exception as e:
            print(f"⚠️ Skipped one due to: {e}")
            continue

    print(f"✅ Total events parsed: {len(events)}")
    return events
    print("⏳ Scraping OnTicket event page...")
    url = "https://onticket.com.br/eventos/5784"  # URL limpa
    try:
        response = requests.get(url, timeout=10, verify=False)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    carousel = soup.find("div", class_="carousel-inner")
    if not carousel:
        print("❌ Couldn't find carousel section.")
        return []

    cards = carousel.find_all("div", class_="col-sm-6 item")
    future_events = []

    for card in cards:
        try:
            title = card.find("h3").text.strip()
            city = card.find("h4", id="cidade").text.strip()
            venue = card.find("h4", id="local").text.strip()
            day = card.find("h4", id="dia").text.strip()
            month = card.find("h4", id="mes").text.strip()
            image = card.find("img")["src"]

            date = parse_onticket_date(day, month)
            if not date or date < datetime.now():
                continue

            event_data = {
                "title": title,
                "location": city,
                "venue": venue,
                "image": image,
                "date": date.isoformat(),
                "font": "OnTicket",
                "category": "Shows e Festas",
                "UF": "ES"
            }

            future_events.append(event_data)
            print(f"✅ Parsed: {title}")
            print(event_data)
        except Exception as e:
            print(f"⚠️ Failed to parse card: {e}")
            continue

    print(f"✅ Total events parsed: {len(future_events)}")
    return future_events

    url = "https://onticket.com.br/eventos/5784?utm_medium=paid&utm_source=ig&utm_id=6770444452737&utm_content=6770444455337&utm_term=6770444453737&utm_campaign=6770444452737&fbclid=PAQ0xDSwLE15pleHRuA2FlbQEwAGFkaWQAAAYoXfOuoQGnLc_131UVZa8U90HknXQgnFbya8hivgEz3jec9fnD92hP7ItKRV1JumHOGYI_aem_knAjTpPg9U17V9MCcWvfEg"
    print("⏳ Scraping OnTicket event page...")

    try:
        #response = requests.get(url, timeout=10)
        response = requests.get(url, timeout=10, verify=False)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    event_blocks = soup.select("div.carousel-inner div.row div.item")

    if not event_blocks:
        print("❌ No events found.")
        return []

    events = []

    for block in event_blocks:
        try:
            image = block.select_one("img")["src"]
            title = block.select_one("h3").text.strip()
            day = block.select_one("h4#dia").text.strip()
            month = block.select_one("h4#mes").text.strip()
            city = block.select_one("h4#cidade").text.strip()
            venue = block.select_one("h4#local").text.strip()

            date = parse_onticket_date(day, month)
            if not date or date < datetime.now():
                continue

            event_data = {
                "title": title,
                "image": image,
                "location": city,
                "venue": venue,
                "date": date.isoformat(),
                "font": "OnTicket",
                "category": "Shows e Festas",
                "UF": "ES"
            }

            print(f"✅ Parsed: {title}")
            print(event_data)
            events.append(event_data)
        except Exception as e:
            print(f"⚠️ Failed to parse event: {e}")
            continue

    print(f"✅ Total events parsed: {len(events)}")
    return events