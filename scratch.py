import os.path
import requests
import base64
import argparse
import logging
import time

from datetime import datetime

from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
REQUEST_STRING = 'https://www.migracija.lt/external/tickets/classif/KL45_10/KL02_88/dates?t={}'

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def get_migris_book_visit_time(alert_day: int) -> str:
    """
    Sends request to migris for receive book a visit time.
    """
    time_now = datetime.now()
    logger.info(F'Request to Migris - : {time_now}')
    try:
        request = REQUEST_STRING.format(time_now.ctime())
        return ''.join(
            sorted([
                time_book.strftime('%Y-%m-%d %H:%M:%S\n') for time_book in (
                    datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S') for time_str in requests.get(request).json()
                ) if (time_book - time_now).days < alert_day
            ])
        )
    except requests.exceptions.RequestException as e:
        logger.error(e)
    return ''


def send_email(to_: str, from_: str, subject: str, text: str) -> None:
    """
    Send email via gmail API.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()

        message.set_content(text)

        message['To'] = to_
        message['From'] = from_
        message['Subject'] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {
            'raw': encoded_message
        }

        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        logger.info(F'Message Id: {send_message["id"]}')
    except HttpError as error:
        logger.error(f'An error occurred: {error}')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Migris book a visit time')
    parser.add_argument('--to_email', help='Email to', type=str, required=True)
    parser.add_argument('--from_email', help='Email from', type=str, required=True)
    parser.add_argument('--day', help='Alert day', type=int, required=True)
    parser.add_argument('--sleep', help='Sleep seconds', type=int, required=True)

    args = parser.parse_args()
    logger.info('Start script with parameters - {}'.format(args))
    while True:
        respons = get_migris_book_visit_time(args.day)
        if respons:
            send_email(args.to_email, args.from_email, 'Migris book a visit', respons)
        logger.info('Sleep - {} sec.'.format(args.sleep))
        time.sleep(args.sleep)
