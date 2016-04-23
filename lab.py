from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, cm

c = canvas.Canvas('del.pdf')
# c.drawImage('scans/Scan123456.jpg', 0, 0, 10*cm, 10*cm)
# c.drawImage('scans/Scan123456.jpg', 0, 0)
c.showPage()
c.save()
