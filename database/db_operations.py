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
    """Insert only new events based on unique 'link' field."""
    new_events = []
    existing_links = set(
        events_collection.find(
            {"link": {"$in": [e["link"] for e in events]}},
            {"link": 1, "_id": 0}
        ).distinct("link")
    )

    for event in events:
        if event["link"] not in existing_links:
            new_events.append(event)

    if new_events:
        try:
            events_collection.insert_many(new_events, ordered=False)
            print(f"✅ Inserted {len(new_events)} new event(s).")
        except BulkWriteError as bwe:
            print(f"⚠️ Duplicate(s) skipped during insert_many: {bwe.details}")
    else:
        print("🔁 No new events to insert.")