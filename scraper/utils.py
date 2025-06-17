import logging
import os
import re
from datetime import datetime, time, date

# --- 1. Logging Setup ---
# This function centralizes your logging configuration.
# You can call this once at the start of your main script.
def setup_logger(name, log_file, level=logging.INFO):
    """
    Sets up a logger with both console and file handlers.

    Args:
        name (str): The name of the logger (e.g., 'event_scraper_log').
        log_file (str): The path to the log file (e.g., 'logs/app.log').
        level (int): The logging level (e.g., logging.INFO, logging.DEBUG, logging.ERROR).

    Returns:
        logging.Logger: The configured logger instance.
    """
    # Ensure the log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False # Prevent messages from being passed to the root logger

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create console handler (for printing to terminal)
    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    # Create file handler (for writing to a file)
    if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

# --- 2. Date and Time Handling Utilities ---
# Events often have tricky date/time formats.
def parse_event_datetime(date_str, time_str=None):
    """
    Attempts to parse various date and optional time string formats into a datetime object.

    Args:
        date_str (str): The date string (e.g., "Dec 25, 2024", "2024-12-25", "Tomorrow").
        time_str (str, optional): The time string (e.g., "7:00 PM", "19:00"). Defaults to None.

    Returns:
        datetime.datetime or None: Parsed datetime object, or None if parsing fails.
    """
    # Common date formats to try
    date_formats = [
        "%B %d, %Y", # December 25, 2024
        "%b %d, %Y", # Dec 25, 2024
        "%Y-%m-%d",  # 2024-12-25
        "%m/%d/%Y",  # 12/25/2024
        "%d-%m-%Y",  # 25-12-2024
        "%d/%m/%Y",  # 25/12/2024
    ]

    # Handle relative dates (simple example, can be expanded)
    lower_date_str = date_str.lower()
    today = date.today()
    if "today" in lower_date_str:
        event_date = today
    elif "tomorrow" in lower_date_str:
        event_date = today + timedelta(days=1)
    else:
        event_date = None
        for fmt in date_formats:
            try:
                event_date = datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue

    if not event_date:
        # If no common format matches, try to parse with general dateutil parser if available
        # You'd need to install `python-dateutil`: pip install python-dateutil
        try:
            from dateutil.parser import parse as dateutil_parse
            event_date = dateutil_parse(date_str, fuzzy=True).date()
        except ImportError:
            pass # dateutil not installed, skip
        except Exception:
            event_date = None # Still couldn't parse

    if not event_date:
        return None # Failed to parse date

    # Common time formats to try
    if time_str:
        time_formats = [
            "%I:%M %p", # 7:00 PM
            "%H:%M",    # 19:00
            "%I:%M%p",  # 7:00PM
            "%I %p",    # 7 PM (without minutes)
            "%I%p",     # 7PM (without minutes)
        ]
        event_time = None
        for fmt in time_formats:
            try:
                event_time = datetime.strptime(time_str, fmt).time()
                break
            except ValueError:
                continue
        if event_time:
            return datetime.combine(event_date, event_time)
        else:
            # If time parsing fails, combine with a default time (e.g., midnight)
            return datetime.combine(event_date, time(0, 0)) # Default to midnight if time fails
    else:
        # If no time string, return date with default midnight time
        return datetime.combine(event_date, time(0, 0))


def format_datetime_for_db(dt_obj):
    """
    Formats a datetime object into a string suitable for database storage (e.g., ISO format).
    """
    if dt_obj:
        return dt_obj.isoformat()
    return None

# --- 3. String Cleaning and Manipulation ---
def clean_text(text):
    """
    Removes common issues from scraped text (e.g., extra whitespace, newlines).

    Args:
        text (str): The input text.

    Returns:
        str: Cleaned text.
    """
    if not isinstance(text, str):
        return ""
    # Replace multiple spaces/newlines with a single space, strip leading/trailing whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def slugify(text):
    """
    Converts a string into a URL-friendly slug.
    Useful for creating unique identifiers if needed, or clean titles.
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text) # Remove non-word chars except spaces and hyphens
    text = re.sub(r'[\s_-]+', '-', text) # Replace spaces/underscores with single hyphen
    text = text.strip('-') # Remove leading/trailing hyphens
    return text

# --- 4. Configuration Loading (Alternative/Complement to .env) ---
# If you have static configuration like CSS selectors for specific sites,
# or default values, this could be a place to load them.
# For sensitive data (DB creds, API keys), .env is still preferred.
def load_scraper_configs(config_file="scraper_configs.json"):
    """
    Loads specific scraping configurations from a JSON file.
    Example for storing CSS selectors for different websites.
    """
    import json
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Configuration file '{config_file}' not found. Using defaults or empty config.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON from '{config_file}'.")
        return {}


# --- 5. URL Normalization ---
def normalize_url(url):
    """
    Normalizes a URL by removing fragments, sorting query parameters, etc.
    Useful for deduplicating links.
    """
    from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
    if not url:
        return None
    parsed_url = urlparse(url)
    # Remove fragment
    path = parsed_url.path
    query = parsed_url.query
    # Sort query parameters for consistent URLs
    if query:
        query_params = parse_qs(query)
        sorted_query = urlencode(sorted(query_params.items()), doseq=True)
        return urlunparse(parsed_url._replace(query=sorted_query, fragment=''))
    return urlunparse(parsed_url._replace(fragment=''))