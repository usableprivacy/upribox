import re
import checker
import socket

class Domain(checker.Checker):
    # __excluded_characters = re.escape(r'\"\'')
    # __characters = '\\ -\\~'
    __min_length = 1
    __max_length = 63
    __max_complete_length = 255

    def __init__(self, value=''):
        self.value = value.lower()

    def __check__(self):
        return re.match(r'\b((?=[a-z0-9-]{1,%s}\.)(xn--)?[a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,%s}\b' % (
            Domain.__max_length, Domain.__max_length), self.value)

    def is_valid(self):
        return (self.__check__() and self.has_allowed_length() or is_ip(self.value)) and self.has_only_allowed_chars()

    def get_match(self):
        #returns entire matched string
        return clear_ip(self.value) if is_ip(self.value) else self.__check__().group(0)

    def has_only_allowed_chars(self):
        return False if re.search(r'(xn--)?[^a-z0-9-.]',
                                  self.value) else True

    def has_allowed_length(self):
        return False if not re.match(r'^.{%s,%s}$' % (Domain.__min_length, Domain.__max_complete_length),
                                     self.value) else True

    def get_allowed_chars(self):
        return ''.join(
            chr(i) for i in range(48, 58)) + ''.join(
            chr(i) for i in range(97, 123)) + '-' + '.'

def is_ip(addr):
    try:
        socket.inet_aton(addr)
    except socket.error:
        return False

    return True

def clear_ip(addr):
    try:
        return socket.inet_ntoa(socket.inet_aton(addr))
    except socket.error:
        return None