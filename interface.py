"""
Simple command line user interface
"""

import datetime, time, re

# Syntactic sugar functions container
class Ask:
    def __init__(self):
        pass

    def mail_now(self):
        answer = input('Mailam odmah? (da) ')
        if 'n' in answer.lower():
            return False

        return {
            'to': input('Kome: '),
            'subject': input('Naslov: '),
            'text': input('Poruka: ')
        }

    def confirm_message(self, options):
        print('Pripremam email za', options['to'])
        print('-' * 80)
        print('Prima:', options['to'])
        print('Naslov:', options['subject'])
        print('Poruka:', options['text'])
        print('Prilog:', options['files'])
        answer = input('(otvori GMail) ili odmah (p)osalji? ')
        return bool(answer)


class UserInterface:
    def __init__(self):
        self.ask = Ask()

    def get_input(self):
        minutes = None
        numfiles = None
        title = 'Untitled'

        # Get input like 3 or 30min 
        userinput = input('Broj scanova ili period u minutama: ') or None
        
        if userinput and 'm' in userinput:    
            numfiles = int(''.join(re.findall(r'\d+', userinput)))
        elif userinput:
            numfiles = int(userinput)

        title = input('Ime dokumenta: ')
        if title and not title.lower().endswith('.pdf'):
            title += '.pdf'
        else:
            digits = str(int(time.time()))[-5:]
            title = 'dokument_' + digits + '.pdf'

        return (numfiles, minutes, title)
