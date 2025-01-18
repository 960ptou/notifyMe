from selenium import webdriver
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



def scan_site(url, driver, extraction_fn = None):
    driver.get(url)
    current_page = driver.execute_script("return document.documentElement.outerHTML;")
    soup = BeautifulSoup(current_page, 'html.parser')

    # this operation is time consuming & it's unlikely to change
    if extraction_fn is None:
        result = apply_extraction(url, soup.body) # NOTE body use avoid script tags etc..
    else:
        result = extraction_fn(url, soup.body)
    return soup, result


last_sent = datetime.now()
def run(db : NotifyDB, pending_db : PoppingDB, force_notify : 'hour' = 1):
    global last_sent
    # driver will live and die in the function
    driver = webdriver.Chrome()

    messages = []
    construct_message = ""
    all_current_stored_sites = db.get_all_links()

    # checking if pending DB has anything
    new_counter = 0
    for site in pending_db:
        print(f"Adding {site=}")
        new_counter += 1
        try:
            soup, current_values = scan_site(site, driver)
            db.post(site, soup.title.text, current_values)
            construct_message += f"Site : {site} Added\n\n"
        except Exception as e:
            print(f"ERROR {e=}")
        print(f"{site} Added")


    for site in all_current_stored_sites:
        try:
            previous_values = db.get(site)

            previous_values_content = previous_values["latest-search-content"]
            extraction_function = quick_extract(previous_values_content[0])
            soup, current_values = scan_site(site, driver, extraction_function)
            is_same = comparer(previous_values_content[0], current_values[0])
            
            db.put(site) if is_same else db.put(site, soup.title.text, current_values)

            messages.append({
                "same" : is_same,
                "url" : site,
                "title" : soup.title.text,
                "latest_update" : previous_values["latest-updated-date"]
            })
        except Exception as e:
            print(f"ERROR {e=}")
            

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

    # Not sending if
    time_elapsed_since_last_sent = (datetime.now() - last_sent).total_seconds() / (60 * 60)
    
    if update_counter == 0 and new_counter == 0 and (time_elapsed_since_last_sent <= force_notify * 0.9): # every n hours => 0.9 to make 1h => 54min so it doesn't happen on 1h failing
        return 

    last_sent = datetime.now()

    print("Sending")
    send_email(sender_email, app_password, recipient_email, subject_message,construct_message)

def conditional_run(active_hours : range, force_notify_period: 'hour'):
    if (datetime.now().hour not in active_hours):
        return
    
    run(database, pending_db, force_notify_period)

def run_web():
    uvicorn.run(webapp, host="localhost", port=3000)



if __name__ == "__main__":
    # chromedriver_autoinstaller.install()
    webapp.mount("/", StaticFiles(directory="static",html=True), name="static")


    Thread(target=run_web, daemon=True).start()

    atexit.register(lambda : print('Application is ending!'))

    sleep_until_next_interval(15)


    while True:
        conditional_run(range(5,22+1), 1) # from 5AM to 10 PM
        sleep_until_next_interval(30)