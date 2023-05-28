from __future__ import print_function
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import pyttsx3
import os.path
import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

engine = pyttsx3.init()

# Set the properties for the speech
engine.setProperty('rate', 180)  # Speed of speech (words per minute)
engine.setProperty('volume', 0.8)

def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    count = 1
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
        query = f'from:morning@finshots.in'
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)

        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        count = 2
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()

            # Extract subject and body from the message
            payload = msg['payload']
            headers = payload['headers']
            subject = ''
            body = ''

            for header in headers:
                if header['name'] == 'Subject':
                    subject = header['value']

            if 'parts' in payload:
                parts = payload['parts']
                for part in parts:
                    if 'body' in part:
                        data = part['body']
                        if 'data' in data:
                            body = data['data']
                        elif 'attachmentId' in data:
                            # If the body is an attachment, retrieve the attachment data
                            attachment = service.users().messages().attachments().get(
                                userId='me',
                                messageId=message['id'],
                                id=data['attachmentId']
                            ).execute()
                            body = attachment['data']

            # Decode the body data
            if body:
                body = base64.urlsafe_b64decode(body).decode('utf-8')
            count -= 1

            soup = BeautifulSoup(body, "html.parser")
            main_text = extract_main_text(str(soup))
            print(main_text)
            print("===============================================================================================================================================")
            if count == 0:
                break
            engine.say(main_text)
            engine.runAndWait()
    except Exception as error:
        print("Error %s" % error)


def extract_main_text(html):
    article = Article('')
    article.set_html(html)
    article.parse()
    return article.text


if __name__ == '__main__':
    main()
