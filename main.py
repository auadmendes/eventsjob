# main.py
import schedule
import time
from scraper.event_scraper import (
    scrape_zig_tickets,
    scrape_festival_de_inverno,
 
) # Assuming you move the core scraping logic here

from scraper.event_scraper_senac import scrape_senac_courses
from scraper.event_scraper_mapa import scrape_mapa_events
from scraper.event_scraper_eventim import scrape_eventim_vitoria, scrape_eventim_vitoria_selenium
from scraper.event_scraper_onticket import scrape_onticket_with_selenium
from scraper.event_scraper_sympla import (
    scrape_and_save_events_sympla,
    scrape_and_save_events_sympla_shows_e_festas,
    scrape_and_save_events_sympla_cursos_e_workshops,
    scrape_and_save_events_sympla_congressos_e_palestras,
    scrape_and_save_events_sympla_esportes,
    scrape_and_save_events_sympla_gastronomia,
    scrape_and_save_events_sympla_arte_cinema_e_lazer,
    scrape_and_save_events_sympla_infantil,
    scrape_and_save_events_sympla_saude_e_bem_estar,
    scrape_and_save_events_sympla_religiao_e_espiritualizade,
    scrape_and_save_events_sympla_games_e_geek,
    scrape_and_save_events_sympla_moda_e_beleza,
    scrape_and_save_events_sympla_pride
)
from scraper.event_scraper_patrick_ribeiro import scrape_and_save_patrick_events # Assuming you have a separate module for Patrick Ribeiro scraping
from scraper.event_scraper_craes import scrape_craes_events # Assuming you have a separate module for CRA-ES scraping
from scraper.event_scraper_beacons import scrape_beacons_with_selenium # Assuming you have a separate module for Beacons scraping

from scraper.event_scraper_lebillet import (
    scrape_lebillet_events_domingos_martins,
    scrape_lebillet_events_cariacica,
    scrape_lebillet_events_guacui,
    scrape_lebillet_events_guarapari,
    scrape_lebillet_events_linhares,
    scrape_lebillet_events_serra,
    scrape_lebillet_events_viana,
    scrape_lebillet_events_vilha_velha,
    scrape_lebillet_events_vitoria
) # Assuming you have a separate module for lebillet scraping

from scraper.utils import setup_logger # Assuming you have a logging setup

# Setup logging (e.g., to file or console)
logger = setup_logger('event_scraper_log', 'logs/app.log')

def run_event_scraping_job():
    logger.info("Starting scheduled event scraping job...")
    try:
       
        scrape_and_save_events_sympla()
        logger.info("Event scraping SYMPLA job completed successfully.")
        # enviar email /whatsApp ou sms pra mim mesmo
        # scrape_and_save_events_sympla_shows_e_festas()
        # logger.info("Event scraping SYMPLA job completed successfully Shows e Fetas.")
        # print("--------------------------------------------------------------------------------")
        # scrape_and_save_events_sympla_cursos_e_workshops()
        # logger.info("Event scraping SYMPLA job completed successfully Cusros e Workshops.")
        # print("--------------------------------------------------------------------------------")
        # scrape_and_save_events_sympla_congressos_e_palestras()
        # logger.info("Event scraping SYMPLA job completed successfully Congressos e Palestras.")
        # print("--------------------------------------------------------------------------------")
        # scrape_and_save_events_sympla_esportes()
        # logger.info("Event scraping SYMPLA job completed successfully Esportes.")
        # print("--------------------------------------------------------------------------------")
        # scrape_and_save_events_sympla_gastronomia()
        # logger.info("Event scraping SYMPLA job completed successfully Gastronomia.")
        # print("--------------------------------------------------------------------------------")
        # scrape_and_save_events_sympla_arte_cinema_e_lazer()
        # logger.info("Event scraping SYMPLA job completed successfully Arte, Cinema e Lazer.")
        # print("--------------------------------------------------------------------------------")
        # scrape_and_save_events_sympla_infantil()
        # logger.info("Event scraping SYMPLA job completed successfully Infantil.")
        # print("--------------------------------------------------------------------------------")
        # scrape_and_save_events_sympla_saude_e_bem_estar()
        # logger.info("Event scraping SYMPLA job completed successfully Saúde e Bem Estar.")
        # print("--------------------------------------------------------------------------------")
        # scrape_and_save_events_sympla_religiao_e_espiritualizade()
        # logger.info("Event scraping SYMPLA job completed successfully Religião e Espiritualizade.")
        # print("--------------------------------------------------------------------------------")
        # scrape_and_save_events_sympla_games_e_geek()
        # logger.info("Event scraping SYMPLA job completed successfully Games e Geek.")
        # print("--------------------------------------------------------------------------------")
        # scrape_and_save_events_sympla_moda_e_beleza()
        # logger.info("Event scraping SYMPLA job completed successfully Moda e Beleza.")
        # print("--------------------------------------------------------------------------------")
        # scrape_and_save_events_sympla_pride()
        # logger.info("Event scraping SYMPLA job completed successfully prode.")
        # print("--------------------------------------------------------------------------------")





        
        scrape_and_save_patrick_events()
        logger.info("Event scraping PATRICK RIBEIRO job completed successfully.")
        print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx Sympla ok")
        # #enviar email /whatsApp ou sms pra mim mesmo

        scrape_mapa_events()
        logger.info("Event scraping MAPA CULTURAL job completed successfully.")
        print("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM Mapa Cultural - Done refactored")
        # #enviar email /whatsApp ou sms pra mim mesmo

        scrape_craes_events()
        logger.info("Event scraping CRA-ES job completed successfully.")
        print("CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC CRA-ES - done")
        # #enviar email /whatsApp ou sms pra mim mesmo

        # # scrape_zig_tickets()
        # # logger.info("Event scraping CRA-ES job completed successfully.")
        # # # #enviar email /whatsApp ou sms pra mim mesmo

        
        scrape_beacons_with_selenium()
        logger.info("Event scraping Beacons events job completed successfully.")
        print("BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB Billet - Done refactored")
        # enviar email /whatsApp ou sms pra mim mesmo

        scrape_senac_courses()
        logger.info("Event scraping Senac Courses job completed successfully.")
        print("SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS Senac - Done refactored")
        # enviar email /whatsApp ou sms pra mim mesmo

        # # scrape_festival_de_inverno()
        # # logger.info("Event scraping Senac Courses job completed successfully.")
        # # print("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF Festival ?????????????")
        # # # enviar email /whatsApp ou sms pra mim mesmo

        scrape_lebillet_events_domingos_martins()
        logger.info("Event scraping lebillet Domingo Martins job completed successfully.")
        print("DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD Domingos done refactored")
        # enviar email /whatsApp ou sms pra mim mesmo

        scrape_lebillet_events_cariacica()
        logger.info("Event scraping lebillet Cariacíca job completed successfully.")
        print("CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC Cariacica done refactored")
        # enviar email /whatsApp ou sms pra mim mesmo

        scrape_lebillet_events_guacui()
        logger.info("Event scraping lebillet Guaçuí job completed successfully.")
        print("GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG Guaçuí done refactored")
        # enviar email /whatsApp ou sms pra mim mesmo

        scrape_lebillet_events_guarapari()
        logger.info("Event scraping lebillet Guarapari job completed successfully.")
        print("GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG Guarapari done refactored")

        # enviar email /whatsApp ou sms pra mim mesmo

        scrape_lebillet_events_linhares()
        logger.info("Event scraping lebillet Linghares job completed successfully.")
        print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL Linhares done refactored")

        # enviar email /whatsApp ou sms pra mim mesmo

        scrape_lebillet_events_serra()
        logger.info("Event scraping lebillet Serra job completed successfully.")
        print("SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS Serra done refactored")

        # enviar email /whatsApp ou sms pra mim mesmo

        scrape_lebillet_events_viana()
        logger.info("Event scraping lebillet Viana job completed successfully.")
        print("VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV Viana done refactored")

        # enviar email /whatsApp ou sms pra mim mesmo

        scrape_lebillet_events_vilha_velha()
        logger.info("Event scraping lebillet Vila Velha job completed successfully.")
        print("VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV Vila Velha done refactored")
        # enviar email /whatsApp ou sms pra mim mesmo

        scrape_lebillet_events_vitoria()
        logger.info("Event scraping lebillet Vitória job completed successfully.")
        print("VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV Vitória done refactored")
        # enviar email /whatsApp ou sms pra mim mesmo

        scrape_eventim_vitoria_selenium()
        logger.info("Event scraping lebillet Vitória job completed successfully.")
        print("EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE Eventim Vitória")
        # enviar email /whatsApp ou sms pra mim mesmo

        scrape_onticket_with_selenium()
        logger.info("Event scraping onticket job completed successfully.")
        print("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO OnTicket")        
        # enviar email /whatsApp ou sms pra mim mesmo

        # print(f" FINISED FINISED FINISED FINISED FINISED FINISED FINISED FINISED FINISED FINISED FINISED
        #       ")
        print("PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED")   
        print("PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED")   
        print("PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED")   
        print("PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED")   
        print("PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED")   
        print("PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED")   
        print("PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED PHINISHED")   
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