"""
GMail API wrapper for creating draft messages with attachment
and opening them in browser for editing and sending
"""

import os, sys, base64, httplib2
from subprocess import call

from apiclient import discovery, errors

import oauth2client
from oauth2client import client
from oauth2client import tools

import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.encoders import encode_base64

from config import my_email

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = [
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/contacts.readonly'
]

if my_email == 'marko@markoantolos.com':
    CLIENT_SECRET_FILE = 'client_secret_marko.json'
elif my_email == 'info@bilanca-usluge.hr':
    CLIENT_SECRET_FILE = 'client_secret_svjetlana.json'

APPLICATION_NAME = 'DocSender'

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


class GMail:
    def __init__(self):
        self.credentials = self.authenticate()
        http = self.credentials.authorize(httplib2.Http())
        self.service = discovery.build('gmail', 'v1', http=http)
        self.drafts = self.service.users().drafts()
        self.messages = self.service.users().messages()
        self.people = discovery.build('people', 'v1', http=http).people()
        me_query = self.people.connections().list(resourceName='people/me')
        me = me_query.execute()
        connections = me['connections']
        people = []
        for person in connections:
            print(person)
            name = person['names'][0]
            people.append({
                'name': name['displayName'],
                'resourceName': person['resourceName']
            })
        for p in people:
            print(p)


    def authenticate(self):
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir, 'DocSender.json')
        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Spremam autentikaciju u ' + credential_path)
        return credentials

    def create_message(sender, options):
        message = MIMEText(options['text'])
        message['to'] = options.get('to', my_email)
        message['from'] = options.get('sender',  my_email)
        message['subject'] = options.get('subject', '')
        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    def create_message_with_attachment(self, options):
        attachment = options['files'][0]
        directory = os.path.split(attachment)[0]
        filename = os.path.basename(attachment)

        message = MIMEMultipart()
        message['to'] = options.get('to', my_email)
        message['from'] = options.get('sender',  my_email)
        message['subject'] = options.get('subject', '')

        message_text = MIMEText(options['text'])
        content_type, encoding = mimetypes.guess_type(attachment)

        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'

        main_type, sub_type = content_type.split('/', 1)
        if main_type == 'text':
            fp = open(attachment, 'rb')
            message_text = MIMEText(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'image':
            fp = open(attachment, 'rb')
            message_text = MIMEImage(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'audio':
            fp = open(attachment, 'rb')
            message_text = MIMEAudio(fp.read(), _subtype=sub_type)
            fp.close()
        else:
            fp = open(attachment, 'rb')
            message_text = MIMEBase(main_type, sub_type)
            message_text.set_payload(fp.read())
            encode_base64(message_text)
            fp.close()

        filename = os.path.basename(attachment)
        message_text.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(message_text)
        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}


    def create_draft(self, message):
        try:
            body = {'message': message}
            draft = self.drafts.create(userId='me', body=body).execute()
            return draft
        except errors.HttpError as error:
            print('Doslo je do greske: %s' % error)
            return None


    def update_draft(self, dID, message):
        try:
            body = {'message': message}
            draft = self.drafts.update(
                userId='me',
                id=dID,
                body=message).execute()
            return draft
        except errors.HttpError as error:
            print('Doslo je do greske: %s' % error)
            return None


    def update_message(self, mID, message):
        print(message)
        message['addLabelIds'] = ['INBOX']
        message = self.messages.modify(userId='me', id=mID, body=message).execute()
        return message

    def open_draft(self, draft):
        threadId = draft['message']['id']
        url = "https://mail.google.com/mail/#drafts?compose=%s" % threadId

        # Call chrome crossplatform
        if os.name == 'nt':
            call(["chrome", url], shell=True)
        else:
            call(["google-chrome", url])
        print('\nPosiljka je spremna u browseru.')

