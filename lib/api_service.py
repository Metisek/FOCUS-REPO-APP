import json
import os
from google.oauth2.credentials import Credentials
import google.auth
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors


# Wczytaj konfigurację z pliku config.json
api_config_path = os.path.join('api_config.json')
with open(api_config_path, 'r') as f:
    api_config = json.load(f)

# Ustawienia OAuth do Google Sheets i Gmail
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Utworzenie obiektu usługi Google Sheets
def create_sheets_service():
    creds = None
    if os.path.exists(api_config['token_file']):
        creds = Credentials.from_authorized_user_file(api_config['token_file'], SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                api_config['client_secret_file'], SCOPES)
            creds = flow.run_local_server(port=0)
        with open(api_config['token_file'], 'w') as token:
            token.write(creds.to_json())
    service = googleapiclient.discovery.build('sheets', 'v4', credentials=creds)
    return service

# Utworzenie obiektu usługi Gmail
def create_gmail_service():
    creds = None
    if os.path.exists(api_config['gmail_token_file']):
        creds = Credentials.from_authorized_user_file(api_config['gmail_token_file'], GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                api_config['client_secret_file'], GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(api_config['gmail_token_file'], 'w') as token:
            token.write(creds.to_json())
    service = googleapiclient.discovery.build('gmail', 'v1', credentials=creds)
    return service
