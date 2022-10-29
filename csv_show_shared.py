import re


class CSVShowError(Exception):
    pass


# Returns None is a number is not recognized
hex_regex = re.compile("^(\d*'[Hh]|0X|0x)")


def string_to_number(str_in):
    value = None
    radix = -1
    if re.match(hex_regex, str_in):
        str_in = re.sub(hex_regex, "", str_in)
        radix = 16
    if re.fullmatch("[0-9]+", str_in):
        radix = 10
    if radix > 0:
        try:
            value = int(str_in, radix)
        except ValueError:
            None
    return value


def string_is_number(str_in):
    return string_to_number(str_in) is not None


def get_regex(string_input):
    for regex_delimiter in ["/", "|"]:
        if string_input[0] == regex_delimiter and string_input[len(string_input)-1] == regex_delimiter:
            return string_input[1:len(string_input)-1]
    return None


class RowComparable:
    def __init__(self, row, sort_keys, detect_numbers=True):
        self.row = row
        self.sort_keys = sort_keys
        self.detect_numbers = detect_numbers

    def __lt__(self, other):
        for key in self.sort_keys:
            lhs = self.row[key]
            rhs = other.row[key]
            if self.detect_numbers:
                left_num = string_to_number(lhs)
                right_num = string_to_number(rhs)
                if left_num is not None and right_num is not None:
                    lhs = left_num
                    rhs = right_num
            if not lhs == rhs:
                return lhs < rhs
        return False

    def __eq__(self, other):
        for key in self.sort_keys:
            lhs = self.row[key]
            rhs = other.row[key]
            if self.detect_numbers:
                left_num = string_to_number(lhs)
                right_num = string_to_number(rhs)
                if left_num is not None and right_num is not None:
                    lhs = left_num
                    rhs = right_num
            if not lhs == rhs:
                return False
        return True
