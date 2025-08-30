import requests
from bs4 import BeautifulSoup
from datetime import datetime
from utils.categorize import categorize_event
from database.db_operations import save_events_bulk

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


def scrape_lebillet_events_domingos_martins():
    print("⏳ Scraping LeBillet for ES events...")
    try:
        response = requests.get("https://lebillet.com.br/search?city=45", timeout=10, verify=False)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch LeBillet page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Restrict to only ES-related section
    next_shows_section = soup.find("div", class_="next-shows-inner")
    if not next_shows_section:
        print("❌ Could not find the 'next-shows-inner' container.")
        return []

    event_cards = next_shows_section.find_all("div", class_="show-card")
    future_events = []

    for card in event_cards:
        try:
            title = card.select_one("h3.title").text.strip()
            link = card.select_one("a.card-link")["href"]
            image = card.select_one("img.image")["src"]
            location = card.select_one("p.data-text.location").text.strip()
            date_str = card.select_one("p.data-text.datetime").text.strip()

            parsed_date = parse_brazilian_date(date_str)
            if not parsed_date or parsed_date < datetime.now():
                continue  # Skip past or unparseable events

            event_data = {
                "title": title,
                "link": link,
                "image": image,
                "location": location.replace(", ES", "").strip(),
                "date": parsed_date.isoformat(),
                "end_date": parsed_date.isoformat(),
                "font": "LeBillet",
                #"category": "Shows e Festas",
                "category": categorize_event(title + " " + location),
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

def scrape_lebillet_events_cariacica():
    print("⏳ Scraping LeBillet for ES events...")
    try:
        response = requests.get("https://lebillet.com.br/search?city=29", timeout=10, verify=False)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch LeBillet page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Restrict to only ES-related section
    next_shows_section = soup.find("div", class_="next-shows-inner")
    if not next_shows_section:
        print("❌ Could not find the 'next-shows-inner' container.")
        return []

    event_cards = next_shows_section.find_all("div", class_="show-card")
    future_events = []

    for card in event_cards:
        try:
            title = card.select_one("h3.title").text.strip()
            link = card.select_one("a.card-link")["href"]
            image = card.select_one("img.image")["src"]
            location = card.select_one("p.data-text.location").text.strip()
            date_str = card.select_one("p.data-text.datetime").text.strip()

            parsed_date = parse_brazilian_date(date_str)
            if not parsed_date or parsed_date < datetime.now():
                continue  # Skip past or unparseable events

            event_data = {
                "title": title,
                "link": link,
                "image": image,
                "location": location.replace(", ES", "").strip(),
                "date": parsed_date.isoformat(),
                "end_date": parsed_date.isoformat(),
                "highlighted": False,
                "font": "LeBillet",
                "category": categorize_event(title + " " + location),
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

def scrape_lebillet_events_guacui():
    print("⏳ Scraping LeBillet for ES events...")
    try:
        response = requests.get("https://lebillet.com.br/search?city=42", timeout=10, verify=False)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch LeBillet page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Restrict to only ES-related section
    next_shows_section = soup.find("div", class_="next-shows-inner")
    if not next_shows_section:
        print("❌ Could not find the 'next-shows-inner' container.")
        return []

    event_cards = next_shows_section.find_all("div", class_="show-card")
    future_events = []

    for card in event_cards:
        try:
            title = card.select_one("h3.title").text.strip()
            link = card.select_one("a.card-link")["href"]
            image = card.select_one("img.image")["src"]
            location = card.select_one("p.data-text.location").text.strip()
            date_str = card.select_one("p.data-text.datetime").text.strip()

            parsed_date = parse_brazilian_date(date_str)
            if not parsed_date or parsed_date < datetime.now():
                continue  # Skip past or unparseable events

            event_data = {
                "title": title,
                "link": link,
                "image": image,
                "location": location.replace(", ES", "").strip(),
                "date": parsed_date.isoformat(),
                "end_date": parsed_date.isoformat(),
                "highlighted": False,
                "font": "LeBillet",
                "category": categorize_event(title + " " + location),
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

def scrape_lebillet_events_guarapari():
    print("⏳ Scraping LeBillet for ES events...")
    try:
        response = requests.get("https://lebillet.com.br/search?city=30", timeout=10, verify=False)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch LeBillet page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Restrict to only ES-related section
    next_shows_section = soup.find("div", class_="next-shows-inner")
    if not next_shows_section:
        print("❌ Could not find the 'next-shows-inner' container.")
        return []

    event_cards = next_shows_section.find_all("div", class_="show-card")
    future_events = []

    for card in event_cards:
        try:
            title = card.select_one("h3.title").text.strip()
            link = card.select_one("a.card-link")["href"]
            image = card.select_one("img.image")["src"]
            location = card.select_one("p.data-text.location").text.strip()
            date_str = card.select_one("p.data-text.datetime").text.strip()

            parsed_date = parse_brazilian_date(date_str)
            if not parsed_date or parsed_date < datetime.now():
                continue  # Skip past or unparseable events

            event_data = {
                "title": title,
                "link": link,
                "image": image,
                "location": location.replace(", ES", "").strip(),
                "date": parsed_date.isoformat(),
                "end_date": parsed_date.isoformat(),
                "highlighted": False,
                "font": "LeBillet",
                "category": categorize_event(title + " " + location),
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

def scrape_lebillet_events_linhares():
    print("⏳ Scraping LeBillet for ES events...")
    try:
        response = requests.get("https://lebillet.com.br/search?city=25", timeout=10, verify=False)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch LeBillet page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Restrict to only ES-related section
    next_shows_section = soup.find("div", class_="next-shows-inner")
    if not next_shows_section:
        print("❌ Could not find the 'next-shows-inner' container.")
        return []

    event_cards = next_shows_section.find_all("div", class_="show-card")
    future_events = []

    for card in event_cards:
        try:
            title = card.select_one("h3.title").text.strip()
            link = card.select_one("a.card-link")["href"]
            image = card.select_one("img.image")["src"]
            location = card.select_one("p.data-text.location").text.strip()
            date_str = card.select_one("p.data-text.datetime").text.strip()

            parsed_date = parse_brazilian_date(date_str)
            if not parsed_date or parsed_date < datetime.now():
                continue  # Skip past or unparseable events

            event_data = {
                "title": title,
                "link": link,
                "image": image,
                "location": location.replace(", ES", "").strip(),
                "date": parsed_date.isoformat(),
                "end_date": parsed_date.isoformat(),
                "highlighted": False,
                "font": "LeBillet",
                "category": categorize_event(title + " " + location),
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

def scrape_lebillet_events_serra():
    print("⏳ Scraping LeBillet for ES events...")
    try:
        response = requests.get("https://lebillet.com.br/search?city=32", timeout=10, verify=False)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch LeBillet page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Restrict to only ES-related section
    next_shows_section = soup.find("div", class_="next-shows-inner")
    if not next_shows_section:
        print("❌ Could not find the 'next-shows-inner' container.")
        return []

    event_cards = next_shows_section.find_all("div", class_="show-card")
    future_events = []

    for card in event_cards:
        try:
            title = card.select_one("h3.title").text.strip()
            link = card.select_one("a.card-link")["href"]
            image = card.select_one("img.image")["src"]
            location = card.select_one("p.data-text.location").text.strip()
            date_str = card.select_one("p.data-text.datetime").text.strip()

            parsed_date = parse_brazilian_date(date_str)
            if not parsed_date or parsed_date < datetime.now():
                continue  # Skip past or unparseable events

            event_data = {
                "title": title,
                "link": link,
                "image": image,
                "location": location.replace(", ES", "").strip(),
                "date": parsed_date.isoformat(),
                "end_date": parsed_date.isoformat(),
                "highlighted": False,
                "font": "LeBillet",
                "category": categorize_event(title + " " + location),
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

def scrape_lebillet_events_viana():
    print("⏳ Scraping LeBillet for ES events...")
    try:
        response = requests.get("https://lebillet.com.br/search?city=114", timeout=10, verify=False)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch LeBillet page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Restrict to only ES-related section
    next_shows_section = soup.find("div", class_="next-shows-inner")
    if not next_shows_section:
        print("❌ Could not find the 'next-shows-inner' container.")
        return []

    event_cards = next_shows_section.find_all("div", class_="show-card")
    future_events = []

    for card in event_cards:
        try:
            title = card.select_one("h3.title").text.strip()
            link = card.select_one("a.card-link")["href"]
            image = card.select_one("img.image")["src"]
            location = card.select_one("p.data-text.location").text.strip()
            date_str = card.select_one("p.data-text.datetime").text.strip()

            parsed_date = parse_brazilian_date(date_str)
            if not parsed_date or parsed_date < datetime.now():
                continue  # Skip past or unparseable events

            event_data = {
                "title": title,
                "link": link,
                "image": image,
                "location": location.replace(", ES", "").strip(),
                "date": parsed_date.isoformat(),
                "end_date": parsed_date.isoformat(),
                "highlighted": False,
                "font": "LeBillet",
                "category": categorize_event(title + " " + location),
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

def scrape_lebillet_events_vilha_velha():
    print("⏳ Scraping LeBillet for ES events...")
    try:
        response = requests.get("https://lebillet.com.br/search?city=24", timeout=10, verify=False)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch LeBillet page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Restrict to only ES-related section
    next_shows_section = soup.find("div", class_="next-shows-inner")
    if not next_shows_section:
        print("❌ Could not find the 'next-shows-inner' container.")
        return []

    event_cards = next_shows_section.find_all("div", class_="show-card")
    future_events = []

    for card in event_cards:
        try:
            title = card.select_one("h3.title").text.strip()
            link = card.select_one("a.card-link")["href"]
            image = card.select_one("img.image")["src"]
            location = card.select_one("p.data-text.location").text.strip()
            date_str = card.select_one("p.data-text.datetime").text.strip()

            parsed_date = parse_brazilian_date(date_str)
            if not parsed_date or parsed_date < datetime.now():
                continue  # Skip past or unparseable events

            event_data = {
                "title": title,
                "link": link,
                "image": image,
                "location": location.replace(", ES", "").strip(),
                "date": parsed_date.isoformat(),
                "end_date": parsed_date.isoformat(),
                "highlighted": False,
                "font": "LeBillet",
                "category": categorize_event(title + " " + location),
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

def scrape_lebillet_events_vitoria():
    print("⏳ Scraping LeBillet for ES events...")
    try:
        response = requests.get("https://lebillet.com.br/search?city=20", timeout=10, verify=False)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch LeBillet page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Restrict to only ES-related section
    next_shows_section = soup.find("div", class_="next-shows-inner")
    if not next_shows_section:
        print("❌ Could not find the 'next-shows-inner' container.")
        return []

    event_cards = next_shows_section.find_all("div", class_="show-card")
    future_events = []

    for card in event_cards:
        try:
            title = card.select_one("h3.title").text.strip()
            link = card.select_one("a.card-link")["href"]
            image = card.select_one("img.image")["src"]
            location = card.select_one("p.data-text.location").text.strip()
            date_str = card.select_one("p.data-text.datetime").text.strip()

            parsed_date = parse_brazilian_date(date_str)
            if not parsed_date or parsed_date < datetime.now():
                continue  # Skip past or unparseable events

            event_data = {
                "title": title,
                "link": link,
                "image": image,
                "location": location.replace(", ES", "").strip(),
                "date": parsed_date.isoformat(),
                "end_date": parsed_date.isoformat(),
                "highlighted": False,
                "font": "LeBillet",
                "category": categorize_event(title + " " + location),
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
