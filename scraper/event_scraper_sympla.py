
from datetime import datetime
from utils.categorize import categorize_event
from bs4 import BeautifulSoup
from database.db_operations import save_events_bulk
import requests
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

                # Title: H3
                title_tag = card.select_one("h3.pn67h1a") or card.select_one("h3")
                title = title_tag.text.strip() if title_tag else "Evento sem título"

                # Location: P
                location_tag = card.select_one("p.pn67h1c") or card.select_one("p")
                location = location_tag.text.strip() if location_tag else "Local não informado"

                # Image: IMG
                img_tag = card.select_one("img.pn67h17") or card.select_one("img")
                img_src = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

                # Date: Div
                date_tag = card.select_one("div.qtfy415.qtfy413.qtfy416")
                date_text = date_tag.text.strip() if date_tag else None

                if not date_text:
                    print("⚠️ Skipped: Missing date text")
                    continue

                parsed_dates = parse_sympla_date(date_text)
                if not parsed_dates:
                    print(f"⏩ Skipped: Invalid date format '{date_text}'")
                    continue

                start_date, end_date = parsed_dates
                if end_date < today:
                    print(f"⏩ Skipped past event: {title} ({date_text})")
                    continue

                event_data = {
                    "title": title,
                    "location": location,
                    "date": start_date.isoformat(),
                    "end_date": end_date.isoformat() if start_date != end_date else None,
                    "link": href,
                    "image": img_src,
                    "font": "Sympla",
                    "highlighted": False,
                    "category": categorize_event(title + location),
                    "UF": "ES"
                }

                all_events_to_save.append(event_data)

                # print(f"📌 {title} | 📍 {location} | 🕒 {start_date} → {end_date}")
                # print(f"🔗 {href}")
                # print(f"🖼️ {img_src}")
                # print("-" * 60)

                print(f"event_data: {event_data}")  # Debugging output

            except Exception as err:
                print(f"⚠️ Error parsing event card: {err}")
                print(card.prettify())  # Useful for debugging
        # Optional: full HTML for debug


        page += 1

    if all_events_to_save:
        save_events_bulk(all_events_to_save)
        print(f"\n✅ Saved {len(all_events_to_save)} events to MongoDB.")
    else:
        print("⚠️ No events to save.")



# def scrape_and_save_events_sympla_shows_e_festas(max_pages=20):
#     base_url = "https://www.sympla.com.br/eventos/vitoria-es?s=&cl=17-festas-e-shows"
#     headers = {"User-Agent": "Mozilla/5.0"}

#     all_events_to_save = []
#     today = datetime.now()
#     page = 1

#     while page <= max_pages:
#         url = f"{base_url}?page={page}"
#         print(f"\n🔄 Scraping page {page}: {url}")

#         try:
#             response = requests.get(url, headers=headers, verify=False)
#             response.raise_for_status()
#         except requests.RequestException as e:
#             print(f"❌ Failed to fetch page {page}: {e}")
#             break

#         soup = BeautifulSoup(response.text, "html.parser")
#         event_cards = soup.select('a.sympla-card')

#         if not event_cards:
#             print("✅ No more event cards found.")
#             break

#         for card in event_cards:
#             try:
#                 href = card.get("href", "").strip()

#                 # Title: H3
#                 title_tag = card.select_one("h3.pn67h1a") or card.select_one("h3")
#                 title = title_tag.text.strip() if title_tag else "Evento sem título"

#                 # Location: P
#                 location_tag = card.select_one("p.pn67h1c") or card.select_one("p")
#                 location = location_tag.text.strip() if location_tag else "Local não informado"

#                 # Image: IMG
#                 img_tag = card.select_one("img.pn67h17") or card.select_one("img")
#                 img_src = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

#                 # Date: Div
#                 date_tag = card.select_one("div.qtfy415.qtfy413.qtfy416")
#                 date_text = date_tag.text.strip() if date_tag else None

#                 if not date_text:
#                     print("⚠️ Skipped: Missing date text")
#                     continue

#                 parsed_dates = parse_sympla_date(date_text)
#                 if not parsed_dates:
#                     print(f"⏩ Skipped: Invalid date format '{date_text}'")
#                     continue

#                 start_date, end_date = parsed_dates
#                 if end_date < today:
#                     print(f"⏩ Skipped past event: {title} ({date_text})")
#                     continue

#                 event_data = {
#                     "title": title,
#                     "location": location,
#                     "date": start_date.isoformat(),
#                     "end_date": end_date.isoformat() if start_date != end_date else None,
#                     "link": href,
#                     "image": img_src,
#                     "font": "Sympla",
#                     "highlighted": False,
#                     "category": "shows e Festas",
#                     "UF": "ES"
#                 }

#                 all_events_to_save.append(event_data)

#                 # print(f"📌 {title} | 📍 {location} | 🕒 {start_date} → {end_date}")
#                 # print(f"🔗 {href}")
#                 # print(f"🖼️ {img_src}")
#                 # print("-" * 60)

#                 print(f"event_data: {event_data}")  # Debugging output

#             except Exception as err:
#                 print(f"⚠️ Error parsing event card: {err}")
#                 print(card.prettify())  # Useful for debugging
#         # Optional: full HTML for debug


#         page += 1

#     if all_events_to_save:
#         save_events_bulk(all_events_to_save)
#         print(f"\n✅ Saved {len(all_events_to_save)} events to MongoDB.")
#     else:
#         print("⚠️ No events to save.")

# def scrape_and_save_events_sympla_cursos_e_workshops(max_pages=20):
#     base_url = "https://www.sympla.com.br/eventos/vitoria-es?s=&cl=8-curso-e-workshops"
#     headers = {"User-Agent": "Mozilla/5.0"}

#     all_events_to_save = []
#     today = datetime.now()
#     page = 1

#     while page <= max_pages:
#         url = f"{base_url}?page={page}"
#         print(f"\n🔄 Scraping page {page}: {url}")

#         try:
#             response = requests.get(url, headers=headers, verify=False)
#             response.raise_for_status()
#         except requests.RequestException as e:
#             print(f"❌ Failed to fetch page {page}: {e}")
#             break

#         soup = BeautifulSoup(response.text, "html.parser")
#         event_cards = soup.select('a.sympla-card')

#         if not event_cards:
#             print("✅ No more event cards found.")
#             break

#         for card in event_cards:
#             try:
#                 href = card.get("href", "").strip()

#                 # Title: H3
#                 title_tag = card.select_one("h3.pn67h1a") or card.select_one("h3")
#                 title = title_tag.text.strip() if title_tag else "Evento sem título"

#                 # Location: P
#                 location_tag = card.select_one("p.pn67h1c") or card.select_one("p")
#                 location = location_tag.text.strip() if location_tag else "Local não informado"

#                 # Image: IMG
#                 img_tag = card.select_one("img.pn67h17") or card.select_one("img")
#                 img_src = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

#                 # Date: Div
#                 date_tag = card.select_one("div.qtfy415.qtfy413.qtfy416")
#                 date_text = date_tag.text.strip() if date_tag else None

#                 if not date_text:
#                     print("⚠️ Skipped: Missing date text")
#                     continue

#                 parsed_dates = parse_sympla_date(date_text)
#                 if not parsed_dates:
#                     print(f"⏩ Skipped: Invalid date format '{date_text}'")
#                     continue

#                 start_date, end_date = parsed_dates
#                 if end_date < today:
#                     print(f"⏩ Skipped past event: {title} ({date_text})")
#                     continue

#                 event_data = {
#                     "title": title,
#                     "location": location,
#                     "date": start_date.isoformat(),
#                     "end_date": end_date.isoformat() if start_date != end_date else None,
#                     "link": href,
#                     "image": img_src,
#                     "font": "Sympla",
#                     "highlighted": False,
#                     "category": "Cursos e Workshops",
#                     "UF": "ES"
#                 }

#                 all_events_to_save.append(event_data)

#                 # print(f"📌 {title} | 📍 {location} | 🕒 {start_date} → {end_date}")
#                 # print(f"🔗 {href}")
#                 # print(f"🖼️ {img_src}")
#                 # print("-" * 60)

#                 print(f"event_data: {event_data}")  # Debugging output

#             except Exception as err:
#                 print(f"⚠️ Error parsing event card: {err}")
#                 print(card.prettify())  # Useful for debugging
#         # Optional: full HTML for debug


#         page += 1

#     if all_events_to_save:
#         save_events_bulk(all_events_to_save)
#         print(f"\n✅ Saved {len(all_events_to_save)} events to MongoDB.")
#     else:
#         print("⚠️ No events to save.")

# def scrape_and_save_events_sympla_congressos_e_palestras(max_pages=20):
#     base_url = "https://www.sympla.com.br/eventos/vitoria-es?s=&cl=4-congressos-e-palestras"
#     headers = {"User-Agent": "Mozilla/5.0"}

#     all_events_to_save = []
#     today = datetime.now()
#     page = 1

#     while page <= max_pages:
#         url = f"{base_url}?page={page}"
#         print(f"\n🔄 Scraping page {page}: {url}")

#         try:
#             response = requests.get(url, headers=headers, verify=False)
#             response.raise_for_status()
#         except requests.RequestException as e:
#             print(f"❌ Failed to fetch page {page}: {e}")
#             break

#         soup = BeautifulSoup(response.text, "html.parser")
#         event_cards = soup.select('a.sympla-card')

#         if not event_cards:
#             print("✅ No more event cards found.")
#             break

#         for card in event_cards:
#             try:
#                 href = card.get("href", "").strip()

#                 # Title: H3
#                 title_tag = card.select_one("h3.pn67h1a") or card.select_one("h3")
#                 title = title_tag.text.strip() if title_tag else "Evento sem título"

#                 # Location: P
#                 location_tag = card.select_one("p.pn67h1c") or card.select_one("p")
#                 location = location_tag.text.strip() if location_tag else "Local não informado"

#                 # Image: IMG
#                 img_tag = card.select_one("img.pn67h17") or card.select_one("img")
#                 img_src = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

#                 # Date: Div
#                 date_tag = card.select_one("div.qtfy415.qtfy413.qtfy416")
#                 date_text = date_tag.text.strip() if date_tag else None

#                 if not date_text:
#                     print("⚠️ Skipped: Missing date text")
#                     continue

#                 parsed_dates = parse_sympla_date(date_text)
#                 if not parsed_dates:
#                     print(f"⏩ Skipped: Invalid date format '{date_text}'")
#                     continue

#                 start_date, end_date = parsed_dates
#                 if end_date < today:
#                     print(f"⏩ Skipped past event: {title} ({date_text})")
#                     continue

#                 event_data = {
#                     "title": title,
#                     "location": location,
#                     "date": start_date.isoformat(),
#                     "end_date": end_date.isoformat() if start_date != end_date else None,
#                     "link": href,
#                     "image": img_src,
#                     "font": "Sympla",
#                     "highlighted": False,
#                     "category": "Palestras e Congressos",
#                     "UF": "ES"
#                 }

#                 all_events_to_save.append(event_data)

#                 # print(f"📌 {title} | 📍 {location} | 🕒 {start_date} → {end_date}")
#                 # print(f"🔗 {href}")
#                 # print(f"🖼️ {img_src}")
#                 # print("-" * 60)

#                 print(f"event_data: {event_data}")  # Debugging output

#             except Exception as err:
#                 print(f"⚠️ Error parsing event card: {err}")
#                 print(card.prettify())  # Useful for debugging
#         # Optional: full HTML for debug


#         page += 1

#     if all_events_to_save:
#         save_events_bulk(all_events_to_save)
#         print(f"\n✅ Saved {len(all_events_to_save)} events to MongoDB.")
#     else:
#         print("⚠️ No events to save.")

# def scrape_and_save_events_sympla_esportes(max_pages=20):
#     base_url = "https://www.sympla.com.br/eventos/vitoria-es?s=&cl=2-esportes"
#     headers = {"User-Agent": "Mozilla/5.0"}

#     all_events_to_save = []
#     today = datetime.now()
#     page = 1

#     while page <= max_pages:
#         url = f"{base_url}?page={page}"
#         print(f"\n🔄 Scraping page {page}: {url}")

#         try:
#             response = requests.get(url, headers=headers, verify=False)
#             response.raise_for_status()
#         except requests.RequestException as e:
#             print(f"❌ Failed to fetch page {page}: {e}")
#             break

#         soup = BeautifulSoup(response.text, "html.parser")
#         event_cards = soup.select('a.sympla-card')

#         if not event_cards:
#             print("✅ No more event cards found.")
#             break

#         for card in event_cards:
#             try:
#                 href = card.get("href", "").strip()

#                 # Title: H3
#                 title_tag = card.select_one("h3.pn67h1a") or card.select_one("h3")
#                 title = title_tag.text.strip() if title_tag else "Evento sem título"

#                 # Location: P
#                 location_tag = card.select_one("p.pn67h1c") or card.select_one("p")
#                 location = location_tag.text.strip() if location_tag else "Local não informado"

#                 # Image: IMG
#                 img_tag = card.select_one("img.pn67h17") or card.select_one("img")
#                 img_src = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

#                 # Date: Div
#                 date_tag = card.select_one("div.qtfy415.qtfy413.qtfy416")
#                 date_text = date_tag.text.strip() if date_tag else None

#                 if not date_text:
#                     print("⚠️ Skipped: Missing date text")
#                     continue

#                 parsed_dates = parse_sympla_date(date_text)
#                 if not parsed_dates:
#                     print(f"⏩ Skipped: Invalid date format '{date_text}'")
#                     continue

#                 start_date, end_date = parsed_dates
#                 if end_date < today:
#                     print(f"⏩ Skipped past event: {title} ({date_text})")
#                     continue

#                 event_data = {
#                     "title": title,
#                     "location": location,
#                     "date": start_date.isoformat(),
#                     "end_date": end_date.isoformat() if start_date != end_date else None,
#                     "link": href,
#                     "image": img_src,
#                     "font": "Sympla",
#                     "highlighted": False,
#                     "category": "Esportes",
#                     "UF": "ES"
#                 }

#                 all_events_to_save.append(event_data)

#                 # print(f"📌 {title} | 📍 {location} | 🕒 {start_date} → {end_date}")
#                 # print(f"🔗 {href}")
#                 # print(f"🖼️ {img_src}")
#                 # print("-" * 60)

#                 print(f"event_data: {event_data}")  # Debugging output

#             except Exception as err:
#                 print(f"⚠️ Error parsing event card: {err}")
#                 print(card.prettify())  # Useful for debugging
#         # Optional: full HTML for debug


#         page += 1

#     if all_events_to_save:
#         save_events_bulk(all_events_to_save)
#         print(f"\n✅ Saved {len(all_events_to_save)} events to MongoDB.")
#     else:
#         print("⚠️ No events to save.")

# def scrape_and_save_events_sympla_gastronomia(max_pages=20):
#     base_url = "https://www.sympla.com.br/eventos/vitoria-es?s=&cl=1-gastronomia"
#     headers = {"User-Agent": "Mozilla/5.0"}

#     all_events_to_save = []
#     today = datetime.now()
#     page = 1

#     while page <= max_pages:
#         url = f"{base_url}?page={page}"
#         print(f"\n🔄 Scraping page {page}: {url}")

#         try:
#             response = requests.get(url, headers=headers, verify=False)
#             response.raise_for_status()
#         except requests.RequestException as e:
#             print(f"❌ Failed to fetch page {page}: {e}")
#             break

#         soup = BeautifulSoup(response.text, "html.parser")
#         event_cards = soup.select('a.sympla-card')

#         if not event_cards:
#             print("✅ No more event cards found.")
#             break

#         for card in event_cards:
#             try:
#                 href = card.get("href", "").strip()

#                 # Title: H3
#                 title_tag = card.select_one("h3.pn67h1a") or card.select_one("h3")
#                 title = title_tag.text.strip() if title_tag else "Evento sem título"

#                 # Location: P
#                 location_tag = card.select_one("p.pn67h1c") or card.select_one("p")
#                 location = location_tag.text.strip() if location_tag else "Local não informado"

#                 # Image: IMG
#                 img_tag = card.select_one("img.pn67h17") or card.select_one("img")
#                 img_src = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

#                 # Date: Div
#                 date_tag = card.select_one("div.qtfy415.qtfy413.qtfy416")
#                 date_text = date_tag.text.strip() if date_tag else None

#                 if not date_text:
#                     print("⚠️ Skipped: Missing date text")
#                     continue

#                 parsed_dates = parse_sympla_date(date_text)
#                 if not parsed_dates:
#                     print(f"⏩ Skipped: Invalid date format '{date_text}'")
#                     continue

#                 start_date, end_date = parsed_dates
#                 if end_date < today:
#                     print(f"⏩ Skipped past event: {title} ({date_text})")
#                     continue

#                 event_data = {
#                     "title": title,
#                     "location": location,
#                     "date": start_date.isoformat(),
#                     "end_date": end_date.isoformat() if start_date != end_date else None,
#                     "link": href,
#                     "image": img_src,
#                     "font": "Sympla",
#                     "highlighted": False,
#                     "category": "Gastronomia",
#                     "UF": "ES"
#                 }

#                 all_events_to_save.append(event_data)

#                 # print(f"📌 {title} | 📍 {location} | 🕒 {start_date} → {end_date}")
#                 # print(f"🔗 {href}")
#                 # print(f"🖼️ {img_src}")
#                 # print("-" * 60)

#                 print(f"event_data: {event_data}")  # Debugging output

#             except Exception as err:
#                 print(f"⚠️ Error parsing event card: {err}")
#                 print(card.prettify())  # Useful for debugging
#         # Optional: full HTML for debug


#         page += 1

#     if all_events_to_save:
#         save_events_bulk(all_events_to_save)
#         print(f"\n✅ Saved {len(all_events_to_save)} events to MongoDB.")
#     else:
#         print("⚠️ No events to save.")

# def scrape_and_save_events_sympla_arte_cinema_e_lazer(max_pages=20):
#     base_url = "https://www.sympla.com.br/eventos/vitoria-es?s=&cl=10-arte-cinema-e-lazer"
#     headers = {"User-Agent": "Mozilla/5.0"}

#     all_events_to_save = []
#     today = datetime.now()
#     page = 1

#     while page <= max_pages:
#         url = f"{base_url}?page={page}"
#         print(f"\n🔄 Scraping page {page}: {url}")

#         try:
#             response = requests.get(url, headers=headers, verify=False)
#             response.raise_for_status()
#         except requests.RequestException as e:
#             print(f"❌ Failed to fetch page {page}: {e}")
#             break

#         soup = BeautifulSoup(response.text, "html.parser")
#         event_cards = soup.select('a.sympla-card')

#         if not event_cards:
#             print("✅ No more event cards found.")
#             break

#         for card in event_cards:
#             try:
#                 href = card.get("href", "").strip()

#                 # Title: H3
#                 title_tag = card.select_one("h3.pn67h1a") or card.select_one("h3")
#                 title = title_tag.text.strip() if title_tag else "Evento sem título"

#                 # Location: P
#                 location_tag = card.select_one("p.pn67h1c") or card.select_one("p")
#                 location = location_tag.text.strip() if location_tag else "Local não informado"

#                 # Image: IMG
#                 img_tag = card.select_one("img.pn67h17") or card.select_one("img")
#                 img_src = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

#                 # Date: Div
#                 date_tag = card.select_one("div.qtfy415.qtfy413.qtfy416")
#                 date_text = date_tag.text.strip() if date_tag else None

#                 if not date_text:
#                     print("⚠️ Skipped: Missing date text")
#                     continue

#                 parsed_dates = parse_sympla_date(date_text)
#                 if not parsed_dates:
#                     print(f"⏩ Skipped: Invalid date format '{date_text}'")
#                     continue

#                 start_date, end_date = parsed_dates
#                 if end_date < today:
#                     print(f"⏩ Skipped past event: {title} ({date_text})")
#                     continue

#                 event_data = {
#                     "title": title,
#                     "location": location,
#                     "date": start_date.isoformat(),
#                     "end_date": end_date.isoformat() if start_date != end_date else None,
#                     "link": href,
#                     "image": img_src,
#                     "font": "Sympla",
#                     "highlighted": False,
#                     "category": "Arte, Cinema e Lazer",
#                     "UF": "ES"
#                 }

#                 all_events_to_save.append(event_data)

#                 # print(f"📌 {title} | 📍 {location} | 🕒 {start_date} → {end_date}")
#                 # print(f"🔗 {href}")
#                 # print(f"🖼️ {img_src}")
#                 # print("-" * 60)

#                 print(f"event_data: {event_data}")  # Debugging output

#             except Exception as err:
#                 print(f"⚠️ Error parsing event card: {err}")
#                 print(card.prettify())  # Useful for debugging
#         # Optional: full HTML for debug


#         page += 1

#     if all_events_to_save:
#         save_events_bulk(all_events_to_save)
#         print(f"\n✅ Saved {len(all_events_to_save)} events to MongoDB.")
#     else:
#         print("⚠️ No events to save.")

# def scrape_and_save_events_sympla_infantil(max_pages=20):
#     base_url = "https://www.sympla.com.br/eventos/vitoria-es?s=&cl=15-infantil"
#     headers = {"User-Agent": "Mozilla/5.0"}

#     all_events_to_save = []
#     today = datetime.now()
#     page = 1

#     while page <= max_pages:
#         url = f"{base_url}?page={page}"
#         print(f"\n🔄 Scraping page {page}: {url}")

#         try:
#             response = requests.get(url, headers=headers, verify=False)
#             response.raise_for_status()
#         except requests.RequestException as e:
#             print(f"❌ Failed to fetch page {page}: {e}")
#             break

#         soup = BeautifulSoup(response.text, "html.parser")
#         event_cards = soup.select('a.sympla-card')

#         if not event_cards:
#             print("✅ No more event cards found.")
#             break

#         for card in event_cards:
#             try:
#                 href = card.get("href", "").strip()

#                 # Title: H3
#                 title_tag = card.select_one("h3.pn67h1a") or card.select_one("h3")
#                 title = title_tag.text.strip() if title_tag else "Evento sem título"

#                 # Location: P
#                 location_tag = card.select_one("p.pn67h1c") or card.select_one("p")
#                 location = location_tag.text.strip() if location_tag else "Local não informado"

#                 # Image: IMG
#                 img_tag = card.select_one("img.pn67h17") or card.select_one("img")
#                 img_src = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

#                 # Date: Div
#                 date_tag = card.select_one("div.qtfy415.qtfy413.qtfy416")
#                 date_text = date_tag.text.strip() if date_tag else None

#                 if not date_text:
#                     print("⚠️ Skipped: Missing date text")
#                     continue

#                 parsed_dates = parse_sympla_date(date_text)
#                 if not parsed_dates:
#                     print(f"⏩ Skipped: Invalid date format '{date_text}'")
#                     continue

#                 start_date, end_date = parsed_dates
#                 if end_date < today:
#                     print(f"⏩ Skipped past event: {title} ({date_text})")
#                     continue

#                 event_data = {
#                     "title": title,
#                     "location": location,
#                     "date": start_date.isoformat(),
#                     "end_date": end_date.isoformat() if start_date != end_date else None,
#                     "link": href,
#                     "image": img_src,
#                     "font": "Sympla",
#                     "highlighted": False,
#                     "category": "Infantil",
#                     "UF": "ES"
#                 }

#                 all_events_to_save.append(event_data)

#                 # print(f"📌 {title} | 📍 {location} | 🕒 {start_date} → {end_date}")
#                 # print(f"🔗 {href}")
#                 # print(f"🖼️ {img_src}")
#                 # print("-" * 60)

#                 print(f"event_data: {event_data}")  # Debugging output

#             except Exception as err:
#                 print(f"⚠️ Error parsing event card: {err}")
#                 print(card.prettify())  # Useful for debugging
#         # Optional: full HTML for debug


#         page += 1

#     if all_events_to_save:
#         save_events_bulk(all_events_to_save)
#         print(f"\n✅ Saved {len(all_events_to_save)} events to MongoDB.")
#     else:
#         print("⚠️ No events to save.")

# def scrape_and_save_events_sympla_saude_e_bem_estar(max_pages=20):
#     base_url = "https://www.sympla.com.br/eventos/vitoria-es?s=&cl=9-saude-e-bem-estar"
#     headers = {"User-Agent": "Mozilla/5.0"}

#     all_events_to_save = []
#     today = datetime.now()
#     page = 1

#     while page <= max_pages:
#         url = f"{base_url}?page={page}"
#         print(f"\n🔄 Scraping page {page}: {url}")

#         try:
#             response = requests.get(url, headers=headers, verify=False)
#             response.raise_for_status()
#         except requests.RequestException as e:
#             print(f"❌ Failed to fetch page {page}: {e}")
#             break

#         soup = BeautifulSoup(response.text, "html.parser")
#         event_cards = soup.select('a.sympla-card')

#         if not event_cards:
#             print("✅ No more event cards found.")
#             break

#         for card in event_cards:
#             try:
#                 href = card.get("href", "").strip()

#                 # Title: H3
#                 title_tag = card.select_one("h3.pn67h1a") or card.select_one("h3")
#                 title = title_tag.text.strip() if title_tag else "Evento sem título"

#                 # Location: P
#                 location_tag = card.select_one("p.pn67h1c") or card.select_one("p")
#                 location = location_tag.text.strip() if location_tag else "Local não informado"

#                 # Image: IMG
#                 img_tag = card.select_one("img.pn67h17") or card.select_one("img")
#                 img_src = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

#                 # Date: Div
#                 date_tag = card.select_one("div.qtfy415.qtfy413.qtfy416")
#                 date_text = date_tag.text.strip() if date_tag else None

#                 if not date_text:
#                     print("⚠️ Skipped: Missing date text")
#                     continue

#                 parsed_dates = parse_sympla_date(date_text)
#                 if not parsed_dates:
#                     print(f"⏩ Skipped: Invalid date format '{date_text}'")
#                     continue

#                 start_date, end_date = parsed_dates
#                 if end_date < today:
#                     print(f"⏩ Skipped past event: {title} ({date_text})")
#                     continue

#                 event_data = {
#                     "title": title,
#                     "location": location,
#                     "date": start_date.isoformat(),
#                     "end_date": end_date.isoformat() if start_date != end_date else None,
#                     "link": href,
#                     "image": img_src,
#                     "font": "Sympla",
#                     "highlighted": False,
#                     "category": "Saúde e Bem-Estar",
#                     "UF": "ES"
#                 }

#                 all_events_to_save.append(event_data)

#                 # print(f"📌 {title} | 📍 {location} | 🕒 {start_date} → {end_date}")
#                 # print(f"🔗 {href}")
#                 # print(f"🖼️ {img_src}")
#                 # print("-" * 60)

#                 print(f"event_data: {event_data}")  # Debugging output

#             except Exception as err:
#                 print(f"⚠️ Error parsing event card: {err}")
#                 print(card.prettify())  # Useful for debugging
#         # Optional: full HTML for debug


#         page += 1

#     if all_events_to_save:
#         save_events_bulk(all_events_to_save)
#         print(f"\n✅ Saved {len(all_events_to_save)} events to MongoDB.")
#     else:
#         print("⚠️ No events to save.")

# def scrape_and_save_events_sympla_religiao_e_espiritualizade(max_pages=20):
#     base_url = "https://www.sympla.com.br/eventos/vitoria-es?s=&cl=13-religiao-e-espiritualidade"
#     headers = {"User-Agent": "Mozilla/5.0"}

#     all_events_to_save = []
#     today = datetime.now()
#     page = 1

#     while page <= max_pages:
#         url = f"{base_url}?page={page}"
#         print(f"\n🔄 Scraping page {page}: {url}")

#         try:
#             response = requests.get(url, headers=headers, verify=False)
#             response.raise_for_status()
#         except requests.RequestException as e:
#             print(f"❌ Failed to fetch page {page}: {e}")
#             break

#         soup = BeautifulSoup(response.text, "html.parser")
#         event_cards = soup.select('a.sympla-card')

#         if not event_cards:
#             print("✅ No more event cards found.")
#             break

#         for card in event_cards:
#             try:
#                 href = card.get("href", "").strip()

#                 # Title: H3
#                 title_tag = card.select_one("h3.pn67h1a") or card.select_one("h3")
#                 title = title_tag.text.strip() if title_tag else "Evento sem título"

#                 # Location: P
#                 location_tag = card.select_one("p.pn67h1c") or card.select_one("p")
#                 location = location_tag.text.strip() if location_tag else "Local não informado"

#                 # Image: IMG
#                 img_tag = card.select_one("img.pn67h17") or card.select_one("img")
#                 img_src = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

#                 # Date: Div
#                 date_tag = card.select_one("div.qtfy415.qtfy413.qtfy416")
#                 date_text = date_tag.text.strip() if date_tag else None

#                 if not date_text:
#                     print("⚠️ Skipped: Missing date text")
#                     continue

#                 parsed_dates = parse_sympla_date(date_text)
#                 if not parsed_dates:
#                     print(f"⏩ Skipped: Invalid date format '{date_text}'")
#                     continue

#                 start_date, end_date = parsed_dates
#                 if end_date < today:
#                     print(f"⏩ Skipped past event: {title} ({date_text})")
#                     continue

#                 event_data = {
#                     "title": title,
#                     "location": location,
#                     "date": start_date.isoformat(),
#                     "end_date": end_date.isoformat() if start_date != end_date else None,
#                     "link": href,
#                     "image": img_src,
#                     "font": "Sympla",
#                     "highlighted": False,
#                     "category": "Religião e Espiritualidade",
#                     "UF": "ES"
#                 }

#                 all_events_to_save.append(event_data)

#                 # print(f"📌 {title} | 📍 {location} | 🕒 {start_date} → {end_date}")
#                 # print(f"🔗 {href}")
#                 # print(f"🖼️ {img_src}")
#                 # print("-" * 60)

#                 print(f"event_data: {event_data}")  # Debugging output

#             except Exception as err:
#                 print(f"⚠️ Error parsing event card: {err}")
#                 print(card.prettify())  # Useful for debugging
#         # Optional: full HTML for debug


#         page += 1

#     if all_events_to_save:
#         save_events_bulk(all_events_to_save)
#         print(f"\n✅ Saved {len(all_events_to_save)} events to MongoDB.")
#     else:
#         print("⚠️ No events to save.")

# def scrape_and_save_events_sympla_games_e_geek(max_pages=20):
#     base_url = "https://www.sympla.com.br/eventos/vitoria-es?s=&cl=12-games-e-geek"
#     headers = {"User-Agent": "Mozilla/5.0"}

#     all_events_to_save = []
#     today = datetime.now()
#     page = 1

#     while page <= max_pages:
#         url = f"{base_url}?page={page}"
#         print(f"\n🔄 Scraping page {page}: {url}")

#         try:
#             response = requests.get(url, headers=headers, verify=False)
#             response.raise_for_status()
#         except requests.RequestException as e:
#             print(f"❌ Failed to fetch page {page}: {e}")
#             break

#         soup = BeautifulSoup(response.text, "html.parser")
#         event_cards = soup.select('a.sympla-card')

#         if not event_cards:
#             print("✅ No more event cards found.")
#             break

#         for card in event_cards:
#             try:
#                 href = card.get("href", "").strip()

#                 # Title: H3
#                 title_tag = card.select_one("h3.pn67h1a") or card.select_one("h3")
#                 title = title_tag.text.strip() if title_tag else "Evento sem título"

#                 # Location: P
#                 location_tag = card.select_one("p.pn67h1c") or card.select_one("p")
#                 location = location_tag.text.strip() if location_tag else "Local não informado"

#                 # Image: IMG
#                 img_tag = card.select_one("img.pn67h17") or card.select_one("img")
#                 img_src = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

#                 # Date: Div
#                 date_tag = card.select_one("div.qtfy415.qtfy413.qtfy416")
#                 date_text = date_tag.text.strip() if date_tag else None

#                 if not date_text:
#                     print("⚠️ Skipped: Missing date text")
#                     continue

#                 parsed_dates = parse_sympla_date(date_text)
#                 if not parsed_dates:
#                     print(f"⏩ Skipped: Invalid date format '{date_text}'")
#                     continue

#                 start_date, end_date = parsed_dates
#                 if end_date < today:
#                     print(f"⏩ Skipped past event: {title} ({date_text})")
#                     continue

#                 event_data = {
#                     "title": title,
#                     "location": location,
#                     "date": start_date.isoformat(),
#                     "end_date": end_date.isoformat() if start_date != end_date else None,
#                     "link": href,
#                     "image": img_src,
#                     "font": "Sympla",
#                     "highlighted": False,
#                     "category": "Games e Geek",
#                     "UF": "ES"
#                 }

#                 all_events_to_save.append(event_data)

#                 # print(f"📌 {title} | 📍 {location} | 🕒 {start_date} → {end_date}")
#                 # print(f"🔗 {href}")
#                 # print(f"🖼️ {img_src}")
#                 # print("-" * 60)

#                 print(f"event_data: {event_data}")  # Debugging output

#             except Exception as err:
#                 print(f"⚠️ Error parsing event card: {err}")
#                 print(card.prettify())  # Useful for debugging
#         # Optional: full HTML for debug


#         page += 1

#     if all_events_to_save:
#         save_events_bulk(all_events_to_save)
#         print(f"\n✅ Saved {len(all_events_to_save)} events to MongoDB.")
#     else:
#         print("⚠️ No events to save.")

# def scrape_and_save_events_sympla_moda_e_beleza(max_pages=20):
#     base_url = "https://www.sympla.com.br/eventos/vitoria-es?s=&cl=11-moda-e-beleza"
#     headers = {"User-Agent": "Mozilla/5.0"}

#     all_events_to_save = []
#     today = datetime.now()
#     page = 1

#     while page <= max_pages:
#         url = f"{base_url}?page={page}"
#         print(f"\n🔄 Scraping page {page}: {url}")

#         try:
#             response = requests.get(url, headers=headers, verify=False)
#             response.raise_for_status()
#         except requests.RequestException as e:
#             print(f"❌ Failed to fetch page {page}: {e}")
#             break

#         soup = BeautifulSoup(response.text, "html.parser")
#         event_cards = soup.select('a.sympla-card')

#         if not event_cards:
#             print("✅ No more event cards found.")
#             break

#         for card in event_cards:
#             try:
#                 href = card.get("href", "").strip()

#                 # Title: H3
#                 title_tag = card.select_one("h3.pn67h1a") or card.select_one("h3")
#                 title = title_tag.text.strip() if title_tag else "Evento sem título"

#                 # Location: P
#                 location_tag = card.select_one("p.pn67h1c") or card.select_one("p")
#                 location = location_tag.text.strip() if location_tag else "Local não informado"

#                 # Image: IMG
#                 img_tag = card.select_one("img.pn67h17") or card.select_one("img")
#                 img_src = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

#                 # Date: Div
#                 date_tag = card.select_one("div.qtfy415.qtfy413.qtfy416")
#                 date_text = date_tag.text.strip() if date_tag else None

#                 if not date_text:
#                     print("⚠️ Skipped: Missing date text")
#                     continue

#                 parsed_dates = parse_sympla_date(date_text)
#                 if not parsed_dates:
#                     print(f"⏩ Skipped: Invalid date format '{date_text}'")
#                     continue

#                 start_date, end_date = parsed_dates
#                 if end_date < today:
#                     print(f"⏩ Skipped past event: {title} ({date_text})")
#                     continue

#                 event_data = {
#                     "title": title,
#                     "location": location,
#                     "date": start_date.isoformat(),
#                     "end_date": end_date.isoformat() if start_date != end_date else None,
#                     "link": href,
#                     "image": img_src,
#                     "font": "Sympla",
#                     "highlighted": False,
#                     "category": "Moda e Beleza",
#                     "UF": "ES"
#                 }

#                 all_events_to_save.append(event_data)

#                 # print(f"📌 {title} | 📍 {location} | 🕒 {start_date} → {end_date}")
#                 # print(f"🔗 {href}")
#                 # print(f"🖼️ {img_src}")
#                 # print("-" * 60)

#                 print(f"event_data: {event_data}")  # Debugging output

#             except Exception as err:
#                 print(f"⚠️ Error parsing event card: {err}")
#                 print(card.prettify())  # Useful for debugging
#         # Optional: full HTML for debug


#         page += 1

#     if all_events_to_save:
#         save_events_bulk(all_events_to_save)
#         print(f"\n✅ Saved {len(all_events_to_save)} events to MongoDB.")
#     else:
#         print("⚠️ No events to save.")

# def scrape_and_save_events_sympla_pride(max_pages=20):
#     base_url = "https://www.sympla.com.br/eventos/vitoria-es?s=&cl=14-pride"
#     headers = {"User-Agent": "Mozilla/5.0"}

#     all_events_to_save = []
#     today = datetime.now()
#     page = 1

#     while page <= max_pages:
#         url = f"{base_url}?page={page}"
#         print(f"\n🔄 Scraping page {page}: {url}")

#         try:
#             response = requests.get(url, headers=headers, verify=False)
#             response.raise_for_status()
#         except requests.RequestException as e:
#             print(f"❌ Failed to fetch page {page}: {e}")
#             break

#         soup = BeautifulSoup(response.text, "html.parser")
#         event_cards = soup.select('a.sympla-card')

#         if not event_cards:
#             print("✅ No more event cards found.")
#             break

#         for card in event_cards:
#             try:
#                 href = card.get("href", "").strip()

#                 # Title: H3
#                 title_tag = card.select_one("h3.pn67h1a") or card.select_one("h3")
#                 title = title_tag.text.strip() if title_tag else "Evento sem título"

#                 # Location: P
#                 location_tag = card.select_one("p.pn67h1c") or card.select_one("p")
#                 location = location_tag.text.strip() if location_tag else "Local não informado"

#                 # Image: IMG
#                 img_tag = card.select_one("img.pn67h17") or card.select_one("img")
#                 img_src = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

#                 # Date: Div
#                 date_tag = card.select_one("div.qtfy415.qtfy413.qtfy416")
#                 date_text = date_tag.text.strip() if date_tag else None

#                 if not date_text:
#                     print("⚠️ Skipped: Missing date text")
#                     continue

#                 parsed_dates = parse_sympla_date(date_text)
#                 if not parsed_dates:
#                     print(f"⏩ Skipped: Invalid date format '{date_text}'")
#                     continue

#                 start_date, end_date = parsed_dates
#                 if end_date < today:
#                     print(f"⏩ Skipped past event: {title} ({date_text})")
#                     continue

#                 event_data = {
#                     "title": title,
#                     "location": location,
#                     "date": start_date.isoformat(),
#                     "end_date": end_date.isoformat() if start_date != end_date else None,
#                     "link": href,
#                     "image": img_src,
#                     "font": "Sympla",
#                     "highlighted": False,
#                     "category": "Pride",
#                     "UF": "ES"
#                 }

#                 all_events_to_save.append(event_data)

#                 # print(f"📌 {title} | 📍 {location} | 🕒 {start_date} → {end_date}")
#                 # print(f"🔗 {href}")
#                 # print(f"🖼️ {img_src}")
#                 # print("-" * 60)

#                 print(f"event_data: {event_data}")  # Debugging output

#             except Exception as err:
#                 print(f"⚠️ Error parsing event card: {err}")
#                 print(card.prettify())  # Useful for debugging
#         # Optional: full HTML for debug


#         page += 1

#     if all_events_to_save:
#         save_events_bulk(all_events_to_save)
#         print(f"\n✅ Saved {len(all_events_to_save)} events to MongoDB.")
#     else:
#         print("⚠️ No events to save.")
