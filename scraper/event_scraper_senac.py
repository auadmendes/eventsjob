
import requests
import urllib3
from bs4 import BeautifulSoup
import os
from database.db_operations import save_events_bulk, event_exists, deduplicate_events
from datetime import datetime
import time # Good for adding pauses if needed
import traceback # For detailed error reporting

import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By # To specify element selection method
from selenium.webdriver.support.ui import WebDriverWait # To wait for elements to appear
from selenium.webdriver.support import expected_conditions as EC # Conditions for waiting
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # ✅ Sem precisar baixar ou indicar caminho manualmente
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

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
                        "end_date": date,
                        "duration_hours": duration,
                        "category": "Cursos e Workshops",
                        "font": "Senac ES",
                        "highlighted": False,
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
