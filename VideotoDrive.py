import base64
import os
import pickle
import time
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

# Setup the Gmail API
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

#GMAIL SCRAPING
#get gmail service first
def get_gmail_service():
    creds = None
    if os.path.exists('token_gmail.pickle'):
        with open('token_gmail.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('YOUR CREDENTIALS FILE', GMAIL_SCOPES)   #my credentials and scopes
            creds = flow.run_local_server(port=0)
        with open('token_gmail.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('gmail', 'v1', credentials=creds)
    return service

#create a list of messages in inbox
def list_messages(service, user_id='me'):
    results = service.users().messages().list(userId=user_id, labelIds=['INBOX', 'UNREAD']).execute() #only read unread
    messages = results.get('messages', [])
    return messages

def get_message(service, user_id, msg_id):
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    return message

#scrape attatchments from an email and return the path to attatchment
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

def mark_as_read(service, user_id, msg_id):
    service.users().messages().modify(userId=user_id, id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()






#set up drive API
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.file']

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
            flow = InstalledAppFlow.from_client_secrets_file('YOUR CREDENTIALS FILE', DRIVE_SCOPES) #PUT YOUR CREDENTIAL FILE HERE
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
                mark_as_read(gmail_service, 'me', message['id'])
        time.sleep(60)  # Check for new emails every minute

if __name__ == '__main__':
    main()
