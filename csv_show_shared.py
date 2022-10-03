import unittest
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


class ShowCSVSharedFunctionsTests(unittest.TestCase):
    def test_string_is_number(self):
        self.assertTrue(string_is_number("10"))
        self.assertFalse(string_is_number("Hello 10"))
        self.assertEqual(string_to_number("10"), 10)
        self.assertEqual(string_to_number("1234567890"), 1234567890)
        self.assertEqual(string_to_number("Hello 10"), None)
        self.assertEqual(string_to_number("bead"), None)
        self.assertEqual(string_to_number("'hbead is great"), None)

    def test_string_is_number_hex(self):
        self.assertEqual(string_to_number("0xbead"), 0xbead)
        self.assertEqual(string_to_number("0Xbead"), 0xbead)
        self.assertEqual(string_to_number("'hbead"), 0xbead)
        self.assertEqual(string_to_number("15'hbead"), 0xbead)
        self.assertEqual(string_to_number("15'Hbead"), 0xbead)
        self.assertEqual(string_to_number("'hbead"), 0xbead)
        self.assertEqual(string_to_number("264'hbead_bead"), 0xbeadbead)
        self.assertEqual(string_to_number("'hbead "), 0xbead)  # Allow space

    def test_row_comparable(self):
        row1 = RowComparable(["Car", "3", "Red"], [1], detect_numbers=False)
        row2 = RowComparable(["Truck", "20", "White"], [1], detect_numbers=False)
        self.assertTrue(row1 > row2)
        self.assertTrue(row2 < row1)
        self.assertTrue(row2 != row1)

        row1 = RowComparable(["Car", "3", "Red"], [1], detect_numbers=True)
        row2 = RowComparable(["Truck", "20", "White"], [1], detect_numbers=True)
        self.assertTrue(row1 < row2)
        self.assertTrue(row2 > row1)
        self.assertTrue(row2 != row1)

        row1 = RowComparable(["Car", "3", "Red"], [0, 2])
        row2 = RowComparable(["Car", "20", "Red"], [0, 2])
        self.assertTrue(row1 == row2)
        self.assertFalse(row1 < row2)

        row1 = RowComparable(["Car", "3", "Red"], [0, 2, 1])
        row2 = RowComparable(["Car", "20", "Red"], [0, 2, 1])
        self.assertTrue(row1 != row2)
        self.assertTrue(row1 < row2)

        row1 = RowComparable(["Car", "3", "Red"], [0, 2, 1])
        row2 = RowComparable(["Car", "20", "Red"], [0, 2, 1])
        self.assertTrue(row1 != row2)

        #  Ensure order of keys matters
        row1 = RowComparable(["Car", "3", "White"], [0, 1, 2])
        row2 = RowComparable(["Car", "20", "Red"], [0, 1, 2])
        self.assertTrue(row1 < row2)
        row1.sort_keys = [0, 2, 1]
        row2.sort_keys = [0, 2, 1]
        self.assertTrue(row1 > row2)
