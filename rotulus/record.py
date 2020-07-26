import base64


class Record:
    def __init__(self):
        self.username = b''
        self.domain = b''
        self.password = b''
        self.hash = ''
        self.hash_type = ''

    def set_username(self, username):
        self.username = username

    def set_domain(self, domain):
        self.domain = domain

    def set_password(self, password):
        self.password = password

    def set_password_hash(self, p_hash):
        self.hash = p_hash.decode()

    def set_hash_type(self, hash_type):
        self.hash_type = hash_type.replace(' ', '')

    def __str__(self):
        try:
            username = self.username.decode()
        except:
            username = bytes(self.username)
        try:
            domain = self.domain.decode()
        except:
            domain = bytes(self.domain)
        try:
            password = self.password.decode()
        except:
            password = bytes(self.password)
        return '{}@{} {} {} {}'.format(username, domain, password, self.hash, self.hash_type)
