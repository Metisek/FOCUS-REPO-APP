import json
import os
from lib.api_service import create_gmail_service
from email.mime.text import MIMEText
import base64
from tkinter import messagebox


config_path = os.path.join('config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

gmail_service = create_gmail_service()

# Wyślij e-mail za pomocą Gmail API
def send_email(to_email, subject, status):
    html_template = ""
    match status:
        case "ACCEPT":
            html_template = config["email-accept"]
        case "REJECT":
            html_template = config["email-reject"]

    with open(html_template, 'r') as f:
        html_content = f.read()

    try:
        message = MIMEText(html_content, 'html')
        message['to'] = to_email
        message['subject'] = subject

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        message_body = {'raw': raw_message}

        gmail_service.users().messages().send(userId="me", body=message_body).execute()
        messagebox.showinfo("Sukces", f"E-mail wysłany do: {to_email}")
    except Exception as e:
        messagebox.showerror("Błąd", f"Nie udało się wysłać e-maila: {e}")