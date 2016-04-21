#! /usr/bin/python

import sys, time, warnings
warnings.filterwarnings("ignore")

import documents as docs
from interface import UserInterface
from gmail import GMail

# Ask if n docs should be merged or a group od docs
# scanned in given time. (default: time bound sequence)

# Merge and write those docs in specified location.
# Archive (move) original scans to configured archive dir

# Ask if we mail now, if yes then gmail api is used to
# create draft with attachment which is then opened in
# the browser (new tab) for editing and sending


def main():
    # Authenticate with GMail by creating it
    gmail = GMail()
    print('moving on')

    # To talk to user via command line
    user = UserInterface()  

    # Get all scanned files in reverse cronological order
    # or quit if none exist
    filenames = docs.get_reversed_files()
    if not filenames:
        print('Nema skeniranih dokumenata')
        sys.exit()

    # Ask for input on what to merge
    # Either howmany or minutes or neither but never both
    howmany, minutes, title = user.get_input()

    # Filter them acording to user input
    if howmany:
        # Pick last n files
        filenames = filenames[:howmany]  
    elif minutes:
        # Last files with gap between consequent files
        # no longer than n[seconds]
        filenames = docs.get_last_period(filenames, minutes * 60)
    else:
        # Last group of scanned files
        filenames = docs.get_last_files(filenames)

    # Merge pages from scanned docs
    pages = docs.pages_from_files(reversed(filenames))
    output = docs.merge_pages(pages)
    print('Spojio sam', output.getNumPages(), 'str u', title)

    # Write the merged PDF file
    output_path = docs.write_pdf(output, title)

    # Archive merged files
    docs.archive_files(filenames)
    
    # Are we done or do we email this PDF with GMail?
    if not user.ask.mail_now():
        options = {
            'to': '',
            'subject': '',
            'text': 'PDF je u privitku...',
            'files': [],
        }

        gmail.create_message_with_attachment(options)
        return


    # Finished
    time.sleep(1)


if __name__ == '__main__':
    main()
