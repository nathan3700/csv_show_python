import unittest
from csv_show_shared import *


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

    def test_string_is_number_place_separators(self):
        self.assertEqual(string_to_number("0xbead_bead"), 0xbeadbead)
        self.assertEqual(string_to_number("  10  "), 10)
        self.assertEqual(string_to_number("  44,60__0  "), 44600)

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


if __name__ == '__main__':
    unittest.main()
