import sys
import PyPDF2
from PIL import Image

def from_pdf(pdf):
    page0 = pdf.getPage(0)
    xObject = page0['/Resources']['/XObject'].getObject()

    for obj in xObject:
        if xObject[obj]['/Subtype'] == '/Image':
            size = (xObject[obj]['/Width'], xObject[obj]['/Height'])
            data = xObject[obj].getData()
            if xObject[obj]['/ColorSpace'] == '/DeviceRGB':
                mode = "RGB"
            else:
                mode = "P"

            if xObject[obj]['/Filter'] == '/FlateDecode':
                img = Image.frombytes(mode, size, data)
                img.save(obj[1:] + ".png")
            elif xObject[obj]['/Filter'] == '/DCTDecode':
                img = open(obj[1:] + ".jpg", "wb")
                img.write(data)
                img.close()
            elif xObject[obj]['/Filter'] == '/JPXDecode':
                img = open(obj[1:] + ".jp2", "wb")
                img.write(data)
                img.close()
            yield img


