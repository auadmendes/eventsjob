# database/db_operations.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pymongo.errors import BulkWriteError

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Missing DATABASE_URL in .env")

client = MongoClient(DATABASE_URL)
db = client.get_default_database()  # Or replace with your database name: client['your-db-name']
events_collection = db['events']

events_collection.create_index("link", unique=True)

def save_event(event_data):
    """Insert a single event dictionary into the 'events' collection."""
    events_collection.insert_one(event_data)

# database/db_operations.py
def save_events_bulk(events):
    if not events:
        print("⚠️ No events to save.")
        return

    # Deduplicate based on title + date + location
    unique_events = {}
    for event in events:
        title = event.get("title", "").lower().strip()
        date = event.get("date", "").strip()
        location = event.get("location", "").lower().strip()
        dedup_key = f"{title}_{date}_{location}"

        if dedup_key not in unique_events:
            unique_events[dedup_key] = event
        else:
            print(f"🔁 Duplicate skipped: {event['title']} on {event['date']} at {event.get('location', '')}")

    to_insert = list(unique_events.values())

    if to_insert:
        events_collection.insert_many(to_insert)
        print(f"✅ Saved {len(to_insert)} unique events to MongoDB.")
    else:
        print("⚠️ No unique events to insert.")