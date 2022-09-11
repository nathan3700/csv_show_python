import unittest
from csv_show import *


class ShowCSVPrintFormatterTests(unittest.TestCase):
    def setUp(self):
        self.show = CsvPrintFormatter()

    def test_show_null_csv(self):
        db = CSVShowDB([], has_header=False)
        self.show.set_db(db)
        self.show.has_header = False
        result = self.show.format_output()
        self.assertEqual(result, "")

    def test_show_one_line_db(self):
        db = CSVShowDB([["item1", "item2"]], has_header=False)
        self.show.set_db(db)
        self.show.has_header = False
        result = self.show.format_output()
        self.assertEqual(result, "|item1|item2|")

    def test_show_two_line_db_no_header(self):
        db = CSVShowDB([["itemA1", "itemB1"], ["itemA2", "itemB2"]], has_header=False)
        self.show.has_header = False
        self.show.set_db(db)
        result = self.show.format_output()
        self.assertEqual(result,
                         "|itemA1|itemB1|\n" +
                         "|itemA2|itemB2|"
                         )

    def test_show_two_line_db_header(self):
        db = CSVShowDB([["headA ", "headB "], ["itemA1", "itemB1"]])
        self.show.set_db(db)
        result = self.show.format_output()
        self.assertEqual(result,
                         "|headA |headB |\n" +
                         "|------|------|\n" +
                         "|itemA1|itemB1|"
                         )

    def test_find_longest_info(self):
        db = CSVShowDB([["itemA1", "itemB1"], ["long_itemA2", "longer_itemB2"]], has_header=False)
        self.show.set_db(db)
        self.show.has_header = False
        longest_widths = self.show.find_longest_column_widths()
        self.assertEqual(longest_widths, [11, 13])

    def test_show_variable_data_len1(self):
        db = CSVShowDB([["itemA1", "itemB1"], ["long_itemA2", "longer_itemB2"]], has_header=False)
        self.show.has_header = False
        self.show.set_db(db)
        result = self.show.format_output()
        self.assertEqual(result,
                         "|itemA1     |itemB1       |\n" +
                         "|long_itemA2|longer_itemB2|"
                         )

    def test_column_names_with_header(self):
        db = CSVShowDB([["Name", "Age", "Address"], ["Marty", "25", "4000 Spruce Lane"]])
        self.show.set_db(db)
        self.assertEqual(self.show.db.column_names, ["Name", "Age", "Address"])

    def test_column_names_with_surprise_new_col(self):
        db = CSVShowDB([["Name", "Age", "Address"], ["Marty", "25", "4000 Spruce Lane", "Surprise new information"]])
        self.show.set_db(db)
        self.assertEqual(self.show.db.column_names, ["Name", "Age", "Address", "Col3"])

    def test_column_names_without_header(self):
        db = CSVShowDB([["Marty", "25", "4000 Spruce Lane"]], has_header=False)
        self.show.has_header = False
        self.show.set_db(db)
        self.assertEqual(self.show.db.column_names, ["Col0", "Col1", "Col2"])
        # Now check surprise more info
        db.add_row(["Jack", "31", "65 Oak Court", "Surprise new Column3"])
        self.assertEqual(self.show.db.column_names, ["Col0", "Col1", "Col2", "Col3"])

    def test_find_longest_with_width_capped(self):
        db = CSVShowDB([["Name", "Quantity"], ["Fork", "2"], ["Spoon", "3000"],
                        ["LongThing123", "1234567890123456789"]])
        self.show.set_db(db)
        self.show.max_width_by_name["Name"] = 9
        self.show.max_width_by_name["Quantity"] = 8
        longest_widths = self.show.find_longest_column_widths()
        self.assertEqual(longest_widths, [9, 8])
        # Now test the final output string
        result = self.show.format_output()
        self.assertEqual("|Name     |Quantity|\n" +
                         "|---------|--------|\n" +
                         "|Fork     |2       |\n" +
                         "|Spoon    |3000    |\n" +
                         "|LongThin*|1234567*|", result
                         )

    def test_width_histogram(self):
        db = CSVShowDB([["Name", "Quantity"], ["Forks", "2000"], ["Spoon", "3000"],
                        ["LongThing123", "1234567890123456789", "Surprise Data"]])
        self.show.set_db(db)
        expected_histograms = {"Name": {4: 1, 5: 2, 12: 1},
                               "Quantity": {8: 1, 4: 2, 19: 1},
                               "Col2": {13: 1, 4: 1}  # Implicit "Col2" is counted as well
                               }
        self.show.find_longest_column_widths()
        self.assertEqual(expected_histograms, self.show.width_histograms)


class ShowCSVDBTests(unittest.TestCase):
    def setUp(self):
        self.db = CSVShowDB()

    def setUPDefaultData(self):
        self.db.set_column_names(["Name", "Age", "Height"])
        self.db.add_rows([["Tom", "25", "5 feet"],
                          ["Ella", "30", "4.5 feet"],
                          ["Richard", "50", "6 feet"]
                          ])

    def test_can_add_names_and_data(self):
        self.db.set_column_names(["Name", "Age"])
        self.assertEqual(self.db.column_names,["Name", "Age"])
        self.db.add_row(["Jake", "40"])
        self.assertEqual(self.db.rows[0], ["Jake", "40"])

    def test_auto_create_names_if_non_given(self):
        self.db.add_row(["Jake", "40"])
        self.assertEqual(self.db.column_names, ["Col0", "Col1"])

    def test_update_names_after_auto_names(self):
        self.db.add_row(["Jake", "40", "6 feet"])
        self.assertEqual(self.db.column_names, ["Col0", "Col1", "Col2"])
        # Now update the first two names to better ones
        self.db.set_column_names(["Name", "Age"])
        self.assertEqual(self.db.column_names, ["Name", "Age", "Col2"])
        self.db.set_column_name(2, "Height")
        self.assertEqual(self.db.column_names, ["Name", "Age", "Height"])
        self.db.set_column_name(5, "Width")
        self.assertEqual(self.db.column_names, ["Name", "Age", "Height", "Col3", "Col4", "Width"])

    def test_get_col_number_by_name(self):
        self.setUPDefaultData()
        col_num = self.db.get_col_number("Height")
        self.assertEqual(col_num, 2)
    def test_get_length_and_width(self):
        self.setUPDefaultData()
        self.assertEqual(self.db.get_length(), 3)
        self.assertEqual(self.db.get_width(), 3)
        self.db.add_rows([["thing", "item", "something"]] * 50)
        self.db.set_column_name(52, "Color")
        self.assertEqual(self.db.get_length(), 53)
        self.assertEqual(self.db.get_width(), 53)

    def test_look_up_row(self):
        self.setUPDefaultData()
        row = self.db.lookup_row({"Name": "Ella"})
        self.assertEqual(row, ["Ella", "30", "4.5 feet"])

    def test_look_up_item(self):
        self.setUPDefaultData()
        item = self.db.lookup_item("Age", {"Name": "Ella"})
        self.assertEqual(item, "30")

    def test_look_up_item_multi_criteria(self):
        self.setUPDefaultData()
        self.db.add_row(["Ella", "25", "72 inches"])  # Add a row that can false match if only one criterion used
        item = self.db.lookup_item("Height", {"Name": "Ella", "Age": "25"})
        self.assertEqual(item, "72 inches")

    # More features to add
    # look up with regex
    # filter columns
    # filter rows
    # insert row at position x
    # insert column at position x
    # update update items that match criteria


class ShowCSVTests(unittest.TestCase):
    def setUp(self):
        self.ui = CsvShow()

    def test_can_read_csv_from_disk(self):
        self.ui.read_db("data/cars.csv")
        self.assertIn("Make", self.ui.column_names)
        self.assertEqual(self.ui.db[0][0], "Ford")


if __name__ == '__main__':
    unittest.main()
