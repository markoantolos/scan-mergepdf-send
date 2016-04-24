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


class Contact:
    def __init__(self, data):
        self.data = data = self.parse(data)
        self.first_name = data.get('first_name')
        self.last_name = data.get('last_name')
        self.display_name = data.get('display_name')
        self.email = data.get('email')
        self.resource_name = data.get('resource_name')

    def parse(self, data):
        fields = {
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'display_name': data.get('display_name'),
            'email': data.get('email'),
            'resource_name': data.get('resource_name'),
        }

        if any(fields.values()):
            return fields

        # Pick a primary email
        emails = data.get('emailAddresses', [])
        for mail in emails:
            value = mail.get('value')
            if not value:
                continue
            meta = mail.get('metadata')
            if meta and meta.get('primary') and mail.get('value'):
                email = value
                break
        else:
            email = None

        # Pick a primary name
        names = data.get('names', [])
        for name in names:
            display_name = name.get('displayName')
            first_name = name.get('firstName')
            last_name = name.get('lastName')
            if not display_name:
                continue
            meta = name.get('metadata')
            if meta and meta.get('primary'):
                break
        else:
            return None

        # Resource name
        resource_name = data.get('resourceName')

        fields = {
            'first_name': first_name,
            'last_name': last_name,
            'display_name': display_name,
            'email': email,
            'resource_name': resource_name,
        }
        return fields

    def serialize(self):
        return {
            'display_name': self.display_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'resurce_name': self.resource_name
        }

    def __str__(self):
        return self.display_name + '(%s)' % self.email

    def __len__(self):
        return len(str(self))

class Contacts:
    def __init__(self, path, people):
        self.file_path = path
        self.people = people
        self._contacts = []
        if not os.path.exists(self.file_path):
            self.write()

    def match(self, name):
        maxratio = 0
        best_match = None
        for contact in self:
            ratio = fuzz.partial_ratio(contact, name)
            if ratio > maxratio:
                maxratio = ratio
                best_match = contact
        return best_match

    def read(self):
        with open(self.file_path, encoding='utf-8') as f:
            text = f.read()
            if text and len(text) > 1:
                data = json.loads(text)
                if data and len(data):
                    return self.parse(data)
            return None

    def write(self):
        with open(self.file_path, 'w+') as f:
            json.dump([c.serialize() for c in self.contacts], f)

    def parse(self, data):
        people = [Contact(person) for person in data]
        return [c for c in people if c.email]

    def fetch(self):
        print('fetching')
        me_query = self.people.connections().list(
            resourceName='people/me',
            requestMask_includeField='person.names,person.emailAddresses'
        )
        me = me_query.execute()
        connections = me['connections']
        return self.parse(connections)

    @property
    def contacts(self):
        if self._contacts and len(self._contacts):
            return self._contacts

        from_file = self.read()
        if from_file:
            return from_file
        else:
            self._contacts = self.fetch()
            self.write()
            return self._contacts

    def __iter__(self):
        for contact in self.contacts:
            yield contact

    def __len__(self):
        return len(self._contacts)

class GMail:
    def __init__(self, options=None):
        defaults = {
            'contacts_file': os.path.join(DATA_DIR, 'contacts.json'),
        }
        if not options:
            options = defaults

        # Auth
        self.credentials = self.authenticate()
        http = self.credentials.authorize(httplib2.Http())

        # Try to instantiate services (requires internet connection)
        try:
            self.service = discovery.build('gmail', 'v1', http=http)
            self.drafts = self.service.users().drafts()
            self.people = discovery.build('people', 'v1', http=http).people()
        except Exception as e:
            print('Google API je nedostupan:', e)
            self.ok = False

        # Prepare contacts
        self.contacts = Contacts(options.get('contacts_file'), self.people)

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

