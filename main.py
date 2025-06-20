# main.py
import schedule
import time
from scraper.event_scraper import (
    scrape_and_save_events_sympla,
    scrape_and_save_patrick_events,
    scrape_mapa_events,
    scrape_beacons_with_selenium,
    scrape_craes_events,
    scrape_zig_tickets,
    scrape_senac_courses
) # Assuming you move the core scraping logic here

from scraper.utils import setup_logger # Assuming you have a logging setup

# Setup logging (e.g., to file or console)
logger = setup_logger('event_scraper_log', 'logs/app.log')

def run_event_scraping_job():
    logger.info("Starting scheduled event scraping job...")
    try:
        scrape_and_save_events_sympla() # Call your main scraping function
        logger.info("Event scraping SYMPLA job completed successfully.")
        # # enviar email /whatsApp ou sms pra mim mesmo
        
        scrape_and_save_patrick_events()
        logger.info("Event scraping PATRICK RIBEIRO job completed successfully.")
        # #enviar email /whatsApp ou sms pra mim mesmo

        scrape_mapa_events()
        logger.info("Event scraping MAPA CULTURAL job completed successfully.")
        # #enviar email /whatsApp ou sms pra mim mesmo

        scrape_craes_events()
        logger.info("Event scraping CRA-ES job completed successfully.")
        # #enviar email /whatsApp ou sms pra mim mesmo

        scrape_zig_tickets()
        logger.info("Event scraping CRA-ES job completed successfully.")
        # #enviar email /whatsApp ou sms pra mim mesmo

        
        scrape_beacons_with_selenium()
        logger.info("Event scraping Beacons events job completed successfully.")
        # # enviar email /whatsApp ou sms pra mim mesmo

        scrape_senac_courses()
        logger.info("Event scraping Senac Courses job completed successfully.")
        # enviar email /whatsApp ou sms pra mim mesmo

    except Exception as e:
        logger.error(f"Error during event scraping job: {e}", exc_info=True)

# Schedule the scraping job
# Schedule to run every 48 hours for your project
#schedule.every(48).hours.do(run_event_scraping_job)
schedule.every(1).minutes.do(run_event_scraping_job)
# For testing, you might use: schedule.every(5).seconds.do(run_event_scraping_job)

logger.info("Event scraper scheduler started. Waiting for next scheduled run.")

while True:
    try:
        schedule.run_pending()
        time.sleep(1) # Sleep for a short duration
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")
        break
    except Exception as e:
        logger.critical(f"Unhandled error in main scheduler loop: {e}", exc_info=True)
        time.sleep(5) # Wait before potentially crashing or retrying