"""
Functions for picking scans cronologicaly and working with pdf files

  get_reversed_files()
  get_last_files()
  get_last_period()

  pages_from_files()
  merge_pages()
  write_pdf()
  archive_files()
"""

import os, shutil
from PyPDF2 import PdfFileReader, PdfFileWriter
import extract_images

from config import username, scans_directory, merge_directory, archive_directory


scans_directory = os.path.abspath(scans_directory)
merge_directory = os.path.abspath(merge_directory)
archive_directory = os.path.abspath(archive_directory)

if not os.path.exists(merge_directory):
    os.makedirs(merge_directory)
    
if not os.path.exists(archive_directory):
    os.makedirs(archive_directory)
    
if not os.path.exists(scans_directory):
    os.makedirs(scans_directory)

SPEED = 5 * 60  # 5 min
FILES = []  # For closing filepointers after merge and write

def get_reversed_files():
    filenames = os.listdir(scans_directory)
    filenames = [ os.path.join(scans_directory, f)
            for f in filenames
            if f.lower().startswith('scan')
            and f.lower().endswith('.pdf')
    ]
    filenames = sorted(filenames, key = os.path.getmtime, reverse = True)
    
    if not len(filenames):
        return None
    return filenames


def get_last_files(filenames):
    last = filenames[0]
    last_time = os.path.getmtime(last)
    result = [last]
    for fname in filenames[1:]:
        modified = os.path.getmtime(fname)
        diff = abs(last_time - modified)
        if diff < SPEED:
            result.append(fname)
        else:
            break
        last = fname
        last_time = os.path.getmtime(last)
    return result


def get_last_period(filenames, seconds):
    last = filenames[0]
    result = [last]
    t1 = os.path.getmtime(last)
    for fname in filenames[1:]:
        modified = os.path.getmtime(fname)
        if abs(modified - t1) <= seconds:
            result.append(fname)
        else:
            break
    return result


def pages_from_files(filenames):
    for filename in filenames:
        f = open(filename, 'rb')
        FILES.append(f)
        pdf = PdfFileReader(f, strict=False)
        for i in range(pdf.getNumPages()):
            yield pdf.getPage(i)


def merge_pages(pages):
    output = PdfFileWriter()
    for page in pages:
        output.addPage(page)
    return output


def write_preview(pdf, path):
    images = extract_images.from_pdf(pdf)
    for im in images:
        print(im)
    return images


def write_pdf(pdf, name):
    path = os.path.join(merge_directory, name)
    with open(path, 'wb') as f:
        pdf.write(f)

    # Close all opened files
    for fp in FILES:
        fp.close()

    return path
        
    
def archive_files(paths):
    for path in paths:
        shutil.move(path, archive_directory)
