#! /usr/local/bin/python3.4

import shutil, os
import sys, time, warnings
warnings.filterwarnings("ignore")

from fuzzywuzzy import fuzz
import documents as docs
from interface import UserInterface
from gmail import GMail

DEBUG = True
if DEBUG:
    from config import archive_directory, scans_directory

# Ask if n docs should be merged or a group od docs
# scanned in given time. (default: time bound sequence)

# Merge and write those docs in specified location.
# Archive (move) original scans to configured archive dir

# Ask if we mail now, if yes then gmail api is used to
# create draft with attachment which is then opened in
# the browser (new tab) for editing and sending

def get_all_scanned_files():
    # Get all scanned files in reverse cronological order
    # or quit if none exist
    filenames = docs.get_reversed_files()
    if not filenames:
        print('Nema skeniranih dokumenata')
        sys.exit()
    return filenames

def filter_files(filenames, howmany, minutes):
    if howmany:
        return filenames[:howmany]  # Pick last n files
    elif minutes:
        # Last files with gap between consequent files
        # no longer than n[seconds]
        return docs.get_last_period(filenames, minutes * 60)
    else:
        # Last group of scanned files
        return docs.get_last_files(filenames)

def main():
    # Authenticate with GMail by creating it
    gmail = GMail()

    # To talk to user via command line
    user = UserInterface()  

    filenames = get_all_scanned_files()

    # Ask for input on what to merge
    howmany, minutes, title = user.get_input()
    filenames = filter_files(filenames, howmany, minutes)

    # Merge pages from scanned docs
    pages = docs.pages_from_files(reversed(filenames))
    output = docs.merge_pages(pages)
    print('Spojio sam', output.getNumPages(), 'str u', title)

    # Write the merged PDF file
    output_path = docs.write_pdf(output, title)

    # image = docs.write_preview(output, 'preview.pdf')
    # print('Image:', image)

    # Archive merged files
    docs.archive_files(filenames)
    
    # Are we done or do we email this PDF with GMail?
    email_options = user.ask.mail_now()
    if not email_options:
        return

    # Fuzzy match the 'to' field against contacts
    name = email_options['to']
    maxratio = 0
    best_match = None
    for person in gmail.contacts:
        emails = person['email']
        print(person, '\n')

        ratio = fuzz.partial_ratio(person['name'], name)
        if ratio > maxratio:
            maxratio = ratio
            best_match = person

    print('BEST_MATCH:', best_match)
    email_options['to'] = best_match['email']
    print('EMAIL_OPTIONS:', email_options)

    # Create email with attachment and open it in GMail
    email_options['files'] = [output_path]
    message = gmail.create_message_with_attachment(email_options)
    draft = gmail.create_draft(message)
    gmail.open_draft(draft)

    # Finished
    time.sleep(1)


if __name__ == '__main__':
    main()
