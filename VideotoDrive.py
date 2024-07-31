import base64
import os
import pickle
import time
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

# Setup the Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

#GMAIL SCRAPING
def get_gmail_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.v2.videodrive.json', SCOPES)   #my credentials and scopes
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('gmail', 'v1', credentials=creds)
    return service

def list_messages(service, user_id='me'):
    results = service.users().messages().list(userId=user_id, labelIds=['INBOX']).execute()
    messages = results.get('messages', [])
    return messages

def get_message(service, user_id, msg_id):
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    return message


def get_attachments(service, user_id, msg_id):
    message = get_message(service, user_id, msg_id)
    for part in message['payload']['parts']:
        if part['filename']:
            attachment_id = part['body']['attachmentId']
            attachment = service.users().messages().attachments().get(userId=user_id, messageId=msg_id, id=attachment_id).execute()
            data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
            path = part['filename']
            with open(path, 'wb') as f:
                f.write(data)
            return path






#set up drive API
SCOPES = ['https://www.googleapis.com/auth/drive.file']

#DRIVE STUFF
def get_drive_service():
    creds = None
    if os.path.exists('token_drive.pickle'):
        with open('token_drive.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.v2.videodrive.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token_drive.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('drive', 'v3', credentials=creds)
    return service

def upload_to_drive(service, file_path):
    file_metadata = {'name': os.path.basename(file_path)}
    media = MediaFileUpload(file_path, mimetype='application/octet-stream')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print('File ID: %s' % file.get('id'))







#MAIN
def main():
    gmail_service = get_gmail_service()
    drive_service = get_drive_service()
    
    while True:
        messages = list_messages(gmail_service)
        for message in messages:
            attachments_path = get_attachments(gmail_service, 'me', message['id'])
            if attachments_path:
                upload_to_drive(drive_service, attachments_path)
        time.sleep(60)  # Check for new emails every minute

if __name__ == '__main__':
    main()