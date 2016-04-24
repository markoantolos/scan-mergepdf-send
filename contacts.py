import sys, os

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
