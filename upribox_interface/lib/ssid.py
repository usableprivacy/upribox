import re
import checker


class SSID(checker.Checker):
    __excluded_characters = re.escape(r'\"\'')
    __characters = '\\ -\\~'
    __min_length = 1
    __max_length = 32

    def is_valid(self):
        return re.match(r'^(?!.*(?:[%s]))[%s]{%s,%s}$' % (
            SSID.__excluded_characters, SSID.__characters, SSID.__min_length, SSID.__max_length), self.value)

    def has_only_allowed_chars(self):
        return False if not re.match(r'^(?!.*(?:[%s]))[%s]+$' % (SSID.__excluded_characters, SSID.__characters),
                                     self.value) else True

    def has_allowed_length(self):
        return False if not re.match(r'^.{%s,%s}$' % (SSID.__min_length, SSID.__max_length), self.value) else True

    def get_allowed_chars(self):
        return ''.join(
            chr(i) for i in range(32, 34)) + ''.join(chr(i) for i in range(35, 39)) + ''.join(
            chr(i) for i in range(40, 48)) + ''.join(chr(i) for i in range(58, 65)) + ''.join(
            chr(i) for i in range(91, 92)) + ''.join(chr(i) for i in range(93, 97)) + ''.join(
            chr(i) for i in range(123, 127))
