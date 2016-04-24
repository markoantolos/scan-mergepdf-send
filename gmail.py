"""
GMail API wrapper for creating draft messages with attachment
and opening them in browser for editing and sending
"""

import os, sys, base64, httplib2
from subprocess import call
import requests
import json
from fuzzywuzzy import fuzz

from apiclient import discovery, errors

import oauth2client
from oauth2client import client
from oauth2client import tools

import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.encoders import encode_base64

from config import my_email, secret_file
from contacts import Contacts

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = [
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/contacts.readonly',
]
CLIENT_SECRET_FILE = secret_file

# Directories
APPLICATION_NAME = 'DocSender'
BASE_DIR = os.path.abspath('.')
DATA_DIR = os.path.join(BASE_DIR, 'data')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Arguments (not needed)
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


class GMail:
    def __init__(self, options=None):
        defaults = {
            'contacts_file': os.path.join(DATA_DIR, 'contacts.json'),
        }
        if not options:
            options = defaults

        # Auth
        self.credentials = self.authenticate()
        self.http = self.credentials.authorize(httplib2.Http())

        self._messages = None
        self._drafts = None
        self._people = None

        # Try to instantiate services (requires internet connection)
        try:
            self.service = discovery.build('gmail', 'v1', http=self.http)
            self.users = self.service.users()
        except Exception as e:
            print('Google API je nedostupan:', e)
            self.ok = False

        # Prepare contacts
        self.contacts = Contacts(options.get('contacts_file'), self.people)

    @property
    def messages(self):
        if self._messages:
            return self._messages
        self._messages = self.users.messages()
        return self._messages

    @property
    def drafts(self):
        if self._drafts:
            return self._drafts
        self._drafts = self.users.drafts()
        return self._drafts

    @property
    def people(self):
        if self._people:
            return self._people
        self._people = discovery.build('people', 'v1', http=self.http).people()
        return self._people

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

    def create_message_with_attachment(self, options):
        attachment = options.get('files')
        attachment = attachment[0] if attachment else ''
        directory = os.path.split(attachment)[0]
        filename = os.path.basename(attachment)

        message = MIMEMultipart()
        message['to'] = options.get('to', my_email)
        message['from'] = options.get('sender',  my_email)
        message['subject'] = options.get('subject', '')
        message_text = MIMEText(options['text'])
        message.attach(message_text)

        content_type, encoding = mimetypes.guess_type(attachment)

        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)

        if attachment:
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

    def send_message(self, message):
        try:
            message = self.messages.send(userId='me', body=message).execute()
            return message
        except Exception as error:
            print('An error occurred: %s' % error)

    def create_draft(self, message):
        try:
            body = {'message': message}
            print('Uploadam privitak...')
            draft = self.drafts.create(userId='me', body=body).execute()
            return draft
        except errors.HttpError as error:
            print('Doslo je do greske: %s' % error)
            return None

    def open_draft(self, draft):
        threadId = draft['message']['id']
        url = "https://mail.google.com/mail/#drafts?compose=%s" % threadId

        # Call chrome crossplatform
        if os.name == 'nt':
            call(["chrome", url], shell=True)
        else:
            call(["google-chrome", url])
        print('\nPosiljka je spremna u browseru.')

