import re
import checker


class Password(checker.Checker):
    __excluded_characters = re.escape(r'\"\'')
    __characters = '\\ -\\~'
    __min_length = 8
    __max_length = 63

    def is_valid(self):
        return re.match(
            r'^(?!.*(?:[%s]))(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[\W])[%s]{%s,%s}$' % (Password.__excluded_characters,
                                                                                      Password.__characters,
                                                                                      Password.__min_length,
                                                                                      Password.__max_length),
            self.value)

    def has_only_allowed_chars(self):
        return False if not re.match(r'^(?!.*(?:[%s]))[%s]+$' % (Password.__excluded_characters, Password.__characters),
                                     self.value) else True

    def has_allowed_length(self):
        return False if not re.match(r'^.{%s,%s}$' % (Password.__min_length, Password.__max_length),
                                     self.value) else True

    def get_allowed_chars(self):
        return ''.join(
            chr(i) for i in range(32, 34)) + ''.join(chr(i) for i in range(35, 39)) + ''.join(
            chr(i) for i in range(40, 48)) + ''.join(chr(i) for i in range(58, 65)) + ''.join(
            chr(i) for i in range(91, 92)) + ''.join(chr(i) for i in range(93, 97)) + ''.join(
            chr(i) for i in range(123, 127))
