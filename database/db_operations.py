# database/db_operations.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv

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
    """Insert only new events based on unique 'link' field."""
    new_events = []
    for event in events:
        if not events_collection.find_one({"link": event["link"]}):
            new_events.append(event)

    if new_events:
        events_collection.insert_many(new_events)
        print(f"✅ Inserted {len(new_events)} new event(s).")
    else:
        print("🔁 No new events to insert.")
