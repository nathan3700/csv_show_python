import unittest
from csv_show import *


class MyTestCase(unittest.TestCase):

    def setUp(self):
        self.show = CsvShow()

    def test_show_null_csv(self):
        db = []
        self.show.set_db(db)
        result = self.show.format_output()
        self.assertEqual(result, "")

    def test_show_one_line_db(self):
        db = [["item1", "item2"]]
        self.show.has_header = False
        self.show.set_db(db)
        result = self.show.format_output()
        self.assertEqual(result, "|item1|item2|")

    def test_show_two_line_db_no_header(self):
        db = [["itemA1", "itemB1"], ["itemA2", "itemB2"]]
        self.show.has_header = False
        self.show.set_db(db)
        result = self.show.format_output()
        self.assertEqual(result,
                         "|itemA1|itemB1|\n" +
                         "|itemA2|itemB2|"
                         )

    def test_show_two_line_db_header(self):
        db = [["headA ", "headB "], ["itemA1", "itemB1"]]
        self.show.set_db(db)
        result = self.show.format_output()
        self.assertEqual(result,
                         "|headA |headB |\n" +
                         "|------|------|\n" +
                         "|itemA1|itemB1|"
                         )

    def test_find_longest_info(self):
        db = [["itemA1", "itemB1"], ["long_itemA2", "longer_itemB2"]]
        self.show.set_db(db)
        longest_widths = self.show.find_longest_column_widths()
        self.assertEqual(longest_widths, [11, 13])

    def test_show_variable_data_len1(self):
        db = [["itemA1", "itemB1"], ["long_itemA2", "long_itemB2"]]
        self.show.has_header = False
        self.show.set_db(db)
        result = self.show.format_output()
        self.assertEqual(result,
                         "|itemA1     |itemB1     |\n" +
                         "|long_itemA2|long_itemB2|"
                         )


if __name__ == '__main__':
    unittest.main()
