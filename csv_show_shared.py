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


#  regex input can be a string,  a tuple of the form (regex, positive_match_boolean), or a list of those tuples
#  use False in the positive_match_boolean part of the tuple to invert the match similar to grep -v
def grep_rows(rows, regex_list, regex_flags):
    regex_list = ensure_regex_list(regex_list)
    new_rows = []
    for row in rows:
        concatenated_row = " ".join(row)
        if grep_single_line(concatenated_row, regex_list, regex_flags):
            new_rows.append(row)
    return new_rows


def grep_single_line(single_line, regex_positive_match_tuples, regex_flags):
    matches_all_regex = True
    for single_regex, positive_match in regex_positive_match_tuples:
        match = re.search(single_regex, single_line, regex_flags)
        if not ((positive_match and match is not None) or (not positive_match and match is None)):
            matches_all_regex = False
    return matches_all_regex


def ensure_regex_list(regex_list):  # If regex is not a list, make it one (so we handle both)
    if not isinstance(regex_list, list):
        if isinstance(regex_list, tuple):
            regex_list = [regex_list]
        else:
            regex_list = [(regex_list, True)]
    return regex_list
