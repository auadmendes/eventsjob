import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pymongo.errors import BulkWriteError
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError  # ✅ correct


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Missing DATABASE_URL in .env")

client = MongoClient(DATABASE_URL)
db = client.get_default_database()
events_collection = db['events']

# Create a compound index on title + date + link to prevent duplicates
events_collection.create_index(
    [("title", 1), ("date", 1), ("link", 1)],
    unique=True
)

def event_exists(title, date, link):
    """Check if an event with the same title, date, and link already exists."""
    return events_collection.find_one({
        "title": title,
        "date": date,
        "link": link
    }) is not None

def save_event(event_data):
    """Insert a single event dictionary into the 'events' collection."""
    if not event_exists(event_data["title"], event_data["date"], event_data["link"]):
        events_collection.insert_one(event_data)
        print(f"✅ Saved event: {event_data['title']}")
    else:
        print(f"🔁 Duplicate (single): {event_data['title']} on {event_data['date']}")

# def save_events_bulk(events):
#     """Insert multiple event dictionaries, skipping duplicates."""
#     to_insert = []
#     for event in events:
#         if not event_exists(event["title"], event["date"], event["link"]):
#             to_insert.append(event)
#         else:
#             print(f"🔁 Duplicate skipped: {event['title']} on {event['date']}")
#     if to_insert:
#         try:
#             events_collection.insert_many(to_insert)
#             print(f"✅ Inserted {len(to_insert)} new events.")
#         except BulkWriteError as bwe:
#             print(f"❌ Bulk write error: {bwe.details}")


def save_events_bulk(events):
    """
    Upsert multiple events into the database.
    - If an event with the same title + date + link exists, update it.
    - Otherwise, insert it.
    """
    operations = []

    for event in events:
        # Filter to match existing events
        filter_ = {
            "title": event["title"],
            "date": event["date"],
            #"link": event["link"]
        }

        # Update with the new data (insert if not exists)
        update = {"$set": event}
        operations.append(UpdateOne(filter_, update, upsert=True))

    if operations:
        try:
            result = events_collection.bulk_write(operations, ordered=False)
            print(f"✅ Upserted {result.upserted_count} | Modified {result.modified_count} | Matched {result.matched_count}")
        except BulkWriteError as bwe:
            print(f"❌ Bulk write error: {bwe.details}")


def deduplicate_events(events):
    seen = set()
    unique = []
    for event in events:
        key = (event['title'], event['date'], event['link'])
        if key not in seen:
            seen.add(key)
            unique.append(event)
    return unique