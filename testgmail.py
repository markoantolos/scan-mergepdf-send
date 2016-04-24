from gmail import GMail

mail = GMail()
options = {
        'to': 'info@bilanca-usluge.hr',
        'subject': 'Naslov',
        'text': 'Poruka u textu',
        'files': ['/home/marko/dev/scan-mergepdf-send/scans/ScanPages.pdf']
}
msg = mail.create_message_with_attachment(options)
draft = mail.create_draft(msg)
mail.open_draft(draft)
