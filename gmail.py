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

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://mail.google.com/'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'DocSender'

class GMail:
    def __init__(self):
        self.credentials = self.authenticate()
        http = self.credentials.authorize(httplib2.Http())
        try:
            self.service = discovery.build('gmail', 'v1', http=http)
        except Exception as e:
            print('Problem', e)
            sys.exit()

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

    def create_message_with_attachment(self, to, subject, text, files):
        sender = my_email
        # to = 'info@bilanca-usluge.hr'
        to = my_email

        directory = os.path.split(attachment)[0]
        filename = os.path.basename(attachment)
        body = create_message(sender, to, subject, text, directory, filename)

        message = MIMEMultipart()
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject

        message_text = MIMEText(text)
        message.attach(msg)

        path = os.path.join(file_dir, filename)
        content_type, encoding = mimetypes.guess_type(path)

        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'

        main_type, sub_type = content_type.split('/', 1)

        if main_type == 'text':
            fp = open(path, 'rb')
            msg = MIMEText(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'image':
            fp = open(path, 'rb')
            msg = MIMEImage(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'audio':
            fp = open(path, 'rb')
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
            fp.close()
        else:
            fp = open(path, 'rb')
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
            encode_base64(msg)
            fp.close()

        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(msg)

        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    def create_draft(service, message_body):
        try:
            message = {'message': message_body}
            draft = service.users().drafts().create(userId='me', body=message).execute()
            draft = service.users().drafts().update(userId='me', id=draft['id'], body=message).execute()
            return draft
        except errors.HttpError as error:
            print('Doslo je do greske: %s' % error)
            return None

def gmail(attachment):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    sender = 'marko@markoantolos.com'
    # to = 'info@bilanca-usluge.hr'
    to = 'marko@markoantolos.com'
    subject = ''
    text = ''
    directory = os.path.split(attachment)[0]
    filename = os.path.basename(attachment)

    body = create_message(sender, to, subject, text, directory, filename)
    draft = create_draft(service, body)
    threadId = draft['message']['id']
    url = "https://mail.google.com/mail/#drafts?compose=%s" % threadId

    # Call chrome crossplatform
    if os.name == 'nt':
        call(["chrome", url], shell=True)
    else:
        call(["google-chrome", url])

    print('\nPosiljka je spremna u browseru.')

    #send(service, body)
