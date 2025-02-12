# from selenium import webdriver
from seleniumbase import Driver
from bs4 import BeautifulSoup
from pymongo import MongoClient

from utils import sleep_until_next_interval, time_difference_description
from email_util import send_email
from algorithm import comparer, apply_extraction, quick_extract
from database import NotifyDB, PoppingDB
from web import WebApp
from fastapi.staticfiles import StaticFiles

from datetime import datetime
import atexit

import uvicorn
from threading import Thread


from dotenv import load_dotenv
import os

load_dotenv()

sender_email = os.getenv("SENDER_EMAIL")
app_password = os.getenv("APP_PASSWORD")
recipient_email = os.getenv("RECIPIENT_EMAIL")
db_client = os.getenv("DB_CLIENT")
dbname = os.getenv("DB_NAME")


client = MongoClient(db_client)  
database = NotifyDB(client, dbname)
pending_db = PoppingDB(client,dbname, database)
webapp = WebApp(database, pending_db)



def scan_site(url, driver : Driver, extraction_fn = None):
    driver.uc_open(url)
    driver.uc_gui_click_captcha()
    current_page = driver.execute_script("return document.documentElement.outerHTML;")

    soup = BeautifulSoup(current_page, 'html.parser')

    # this operation is time consuming & it's unlikely to change
    if extraction_fn is None:
        result = apply_extraction(url, soup.body) # NOTE body use avoid script tags etc..
    else:
        result = extraction_fn(url, soup.body)

    return soup, result


def run(db : NotifyDB, pending_db : PoppingDB):
    # global last_sent
    # driver will live and die in the function
    # driver = webdriver.Chrome()
    driver = Driver(uc=True)
    driver.implicitly_wait(10)

    messages = []
    construct_message = ""
    all_current_stored_sites = sorted(db.get_all_links())

    # checking if pending DB has anything
    new_counter = 0
    for site in pending_db:
        print(f"Adding {site=}")
        new_counter += 1
        for tries in range(1, 3+1):
            try:
                soup, current_values = scan_site(site, driver)
                title = soup.title.text
                
            except Exception as e:
                driver.refresh()
                print(f"Attempt {tries} on adding site : {site} Failed")
                print(f"Reason : {e}")
                continue

            db.post(site, title, current_values)
            construct_message += f"Site : {site} Added\n\n"
            break


    for site in all_current_stored_sites:
        for tries in range(1, 3+1): # 3 tries
            try:
                previous_values = db.get(site)
                previous_values_content = previous_values["latest-search-content"]

                extraction_function = quick_extract(previous_values_content[0])

                soup, current_values = scan_site(site, driver, extraction_function)
                is_same = comparer(previous_values_content[0], current_values[0])
                title = soup.title.text
            except Exception as e:
                driver.refresh()
                print(f"Attempt {tries} on site : {site} Failed")
                print(f"Reason : {e}")
                continue

            # Db
            db.put(site) if is_same else db.put(site, title, current_values)
            # message info gathering
            messages.append({
                "same" : is_same,
                "url" : site,
                "title" : title,
                "latest_update" : previous_values["latest-updated-date"]
            })
            break
            

    driver.quit()

    
    update_counter = 0
    for message in messages:
        same = message["same"]
        title = " ".join(message['title'].split()) # pretty only at output
        update_counter += not(same)
        
        update_msg = (f"--- Updated {time_difference_description(message['latest_update'])}" if message['latest_update'] else "Never - Updated") + "\n"
        
        if not same:
            update_msg = "--- Updated now\n"
            
        construct_message += f'<p><a href="{message["url"]}" target="_blank">{title}</a></p>\n{update_msg}\n'


    first_string = f"Updates : {update_counter}"

    if new_counter > 0:
        first_string += f" & {new_counter} New Sites Added"


    subject_message = f"{first_string} @ {datetime.now().strftime('%B %d, %Y - (%I:%M %p)')}"

    
    print(f"{datetime.now().strftime('%B %d, %Y - (%I:%M:%S %p)')}")

    send_email(sender_email, app_password, recipient_email, subject_message,construct_message)

def conditional_run(active_hours : range):
    if (datetime.now().hour not in active_hours):
        return
    
    run(database, pending_db)

def run_web():
    uvicorn.run(webapp, host="0.0.0.0", port=3000)



if __name__ == "__main__":
    # chromedriver_autoinstaller.install()
    webapp.mount("/", StaticFiles(directory="static",html=True), name="static")


    Thread(target=run_web, daemon=True).start()

    atexit.register(lambda : print('Application is ending!'))

    # sleep_until_next_interval(60)


    while True:
        conditional_run(range(5,22+1)) # from 5AM to 10 PM
        sleep_until_next_interval(60 * 3) # every hour