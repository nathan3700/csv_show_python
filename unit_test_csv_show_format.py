import unittest
from csv_show_format import *


class ShowCSVPrintFormatterTests(unittest.TestCase):
    def setUp(self):
        self.show = CsvPrintFormatter()

    def test_show_null_csv(self):
        db = CSVShowDB([])
        self.show.set_db(db)
        self.show.has_header = False
        result = self.show.format_output_as_string()
        self.assertEqual(result, "")

    def test_show_one_line_db(self):
        db = CSVShowDB([["item1", "item2"]])
        self.show.set_db(db)
        self.show.has_header = False
        result = self.show.format_output_as_string()
        self.assertEqual(result, "|item1|item2|")

    def test_show_two_line_db_no_header(self):
        db = CSVShowDB([["itemA1", "itemB1"], ["itemA2", "itemB2"]])
        self.show.has_header = False
        self.show.set_db(db)
        result = self.show.format_output_as_string()
        self.assertEqual(result,
                         "|itemA1|itemB1|\n" +
                         "|itemA2|itemB2|"
                         )

    def test_show_two_line_db_header(self):
        rows = [["itemA1", "itemB1"]]
        db = CSVShowDB(rows, ["headA ", "headB "])
        self.show.set_db(db)
        result = self.show.format_output_as_string()
        self.assertEqual(result,
                         "|headA |headB |\n" +
                         "|------|------|\n" +
                         "|itemA1|itemB1|"
                         )

    def test_find_longest_info(self):
        db = CSVShowDB([["itemA1", "itemB1"], ["long_itemA2", "longer_itemB2"]])
        self.show.set_db(db)
        self.show.has_header = False
        self.show.find_longest_column_widths()
        self.assertEqual(self.show.longest_by_col, [11, 13])

    def test_show_variable_data_len1(self):
        db = CSVShowDB([["itemA1", "itemB1"], ["long_itemA2", "longer_itemB2"]])
        self.show.has_header = False
        self.show.set_db(db)
        result = self.show.format_output_as_string()
        self.assertEqual(result,
                         "|itemA1     |itemB1       |\n" +
                         "|long_itemA2|longer_itemB2|"
                         )

    def test_column_names_with_header(self):
        rows = [["Marty", "25", "4000 Spruce Lane"]]
        db = CSVShowDB(rows, ["Name", "Age", "Address"])
        self.show.set_db(db)
        self.assertEqual(self.show.db.column_names, ["Name", "Age", "Address"])

    def test_column_names_with_surprise_new_col(self):
        rows = [["Marty", "25", "4000 Spruce Lane", "Surprise new information"]]
        db = CSVShowDB(rows, ["Name", "Age", "Address"])
        self.show.set_db(db)
        self.assertEqual(self.show.db.column_names, ["Name", "Age", "Address", "Col3"])

    def test_column_names_without_header(self):
        db = CSVShowDB([["Marty", "25", "4000 Spruce Lane"]])
        self.show.has_header = False
        self.show.set_db(db)
        self.assertEqual(self.show.db.column_names, ["Col0", "Col1", "Col2"])
        # Now check surprise more info
        db.add_row(["Jack", "31", "65 Oak Court", "Surprise new Column3"])
        self.assertEqual(self.show.db.column_names, ["Col0", "Col1", "Col2", "Col3"])

    def test_find_longest_with_width_capped(self):
        rows = [["Fork", "2"], ["Spoon", "3000"],
                ["LongThing123", "1234567890123456789"]
                ]
        db = CSVShowDB(rows, ["Name", "Quantity"])
        self.show.set_db(db)
        self.show.max_width_by_name["Name"] = 9
        self.show.max_width_by_name["Quantity"] = 8
        self.show.find_longest_column_widths()
        self.assertEqual(self.show.longest_by_col, [9, 8])
        # Now test the final output string
        result = self.show.format_output_as_string()
        self.assertEqual("|Name     |Quantity|\n" +
                         "|---------|--------|\n" +
                         "|Fork     |2       |\n" +
                         "|Spoon    |3000    |\n" +
                         "|LongThin*|1234567*|", result
                         )

    def test_max_width(self):
        rows = [["Fork", "2"], ["Spoon", "3000"],
                ["LongThing123", "1234567890123456789"]
                ]
        db = CSVShowDB(rows, ["Name", "Quantity"])
        self.show.set_db(db)
        self.show.max_width_by_name["Name"] = 5
        self.show.max_width_by_name["Quantity"] = 7
        longest_widths = self.show.find_longest_column_widths()
        # Now test the final output string
        result = self.show.format_output_as_string()
        self.assertEqual("|Name |Quanti*|\n" +
                         "|-----|-------|\n" +
                         "|Fork |2      |\n" +
                         "|Spoon|3000   |\n" +
                         "|Long*|123456*|", result
                         )

    def test_width_histogram(self):
        rows = [["Forks", "2000"], ["Spoon", "3000"],
                ["LongThing123", "1234567890123456789", "Surprise Data"]]
        db = CSVShowDB(rows, ["Name", "Quantity"])
        self.show.set_db(db)
        expected_histograms = {"Name": {4: 1, 5: 2, 12: 1},
                               "Quantity": {8: 1, 4: 2, 19: 1},
                               "Col2": {13: 1, 4: 1}  # Implicit "Col2" is counted as well
                               }
        self.show.find_longest_column_widths()
        self.assertEqual(expected_histograms, self.show.width_histograms)



if __name__ == '__main__':
    unittest.main()
