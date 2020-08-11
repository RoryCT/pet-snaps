from __future__ import print_function
import pickle
import os.path
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By

def take_photo(file_name):
    opts = Options()
    opts.headless = True

    #Parse config.txt file
    with open("./config.txt") as cfg:
        configlines = [line.split(":") for line in cfg.read().splitlines()]
        config = {line[0].strip():line[1].strip() for line in configlines}

    overridelink = f"{config['protocol']}://{config['username']}:{config['password']}@{config['url']}:{config['port']}/override"

    #Deal with infinite load
    capa = DesiredCapabilities.FIREFOX
    capa["pageLoadStrategy"] = "none"

    #Go to webpage
    browser = Firefox(options=opts, desired_capabilities=capa)
    wait = WebDriverWait(browser, 20)
    browser.get(overridelink) 
    wait.until(expected_conditions.visibility_of_element_located((By.XPATH, '//img[@src="/video?640x480"]')))
    time.sleep(1) #inserted because the wait.until still doesn't give enough time for the image to appear
    with open(file_name, 'wb') as file:
        file.write(browser.find_element_by_tag_name('img').screenshot_as_png)

    browser.close()

def get_service():
    """
    Gets the credentials for Google Drive.
    """
    SCOPES = ['https://www.googleapis.com/auth/drive']
    credentials = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('./token.pickle'):
        with open('./token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                './credentials.json', SCOPES)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('./token.pickle', 'wb') as token:
            pickle.dump(credentials, token)
    
    service = build('drive', 'v3', credentials=credentials)
    return(service)

def upload(file_name, service):
    """
    Uploads the file to Google Drive
    """
    # Upload file
    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_name, mimetype='image/png')
    file_up = service.files().create(body=file_metadata,
                                     media_body=media,
                                     fields='id').execute()
    return(file_up.get("id"))

def refresh_file(new_file_id, past_files, service):
    """
    Checks for previous file IDs and removes them
    """
    if os.path.exists(past_files):
        with open(past_files) as past_files_file:
            past_file_ids = [line.strip() for line in past_files_file.read().splitlines()]
        for file_id in past_file_ids:
            service.files().delete(fileId = file_id).execute()
    with open(past_files, "w") as past_files_file:
        past_files_file.write(new_file_id)

        
if __name__ == '__main__':
    service = get_service()
    take_photo("./camimg.png")
    file_id = upload("./camimg.png", service)
    refresh_file(file_id, "./pastfiles.txt", service)