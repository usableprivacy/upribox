import re
import abc


class Checker:
    __metaclass__ = abc.ABCMeta
    #__excluded_characters = re.escape(r'\"\'')
    #__characters = '\\ -\\~'
    #__min_length = 8
    #__max_length = 63

    def __init__(self, value=''):
        self.value = value

    @abc.abstractmethod
    def is_valid(self):
        pass
        # return re.match(
        #     r'^(?!.*(?:[%s]))(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[\W])[%s]{%s,%s}$' % (Checker.__excluded_characters,
        #                                                                               Checker.__characters,
        #                                                                               Checker.__min_length,
        #                                                                               Checker.__max_length),
        #     self.value)

    def has_digit(self):
        return False if not re.search(r'\d', self.value) else True

    def has_lowercase_char(self):
        return False if not re.search(r'[a-z]', self.value) else True

    def has_uppercase_char(self):
        return False if not re.search(r'[A-Z]', self.value) else True

    def has_symbol(self):
        return False if not re.search(r'\W',
                                      self.value) else True

    @abc.abstractmethod
    def has_only_allowed_chars(self):
        pass

    # return False if not re.match(r'^(?!.*(?:[%s]))[%s]+$' % (Checker.__excluded_characters, Checker.__characters),
    #                              self.value) else True
    @abc.abstractmethod
    def has_allowed_length(self):
        pass

    # return False if not re.match(r'^.{%s,%s}$' % (Checker.__min_length, Checker.__max_length),
    #                              self.value) else True
    @abc.abstractmethod
    def get_allowed_chars(self):
        pass
        # return ''.join(
        #     chr(i) for i in range(32, 34)) + ''.join(chr(i) for i in range(35, 39)) + ''.join(
        #     chr(i) for i in range(40, 49)) + ''.join(chr(i) for i in range(58, 65)) + ''.join(
        #     chr(i) for i in range(91, 92)) + ''.join(chr(i) for i in range(93, 97)) + ''.join(
        #     chr(i) for i in range(123, 127))
