# scraper/event_scraper.py
import requests
import urllib3
from bs4 import BeautifulSoup

from database.db_operations import save_events_bulk

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

# Manual run
if __name__ == "__main__":
    scrape_and_save_events()
