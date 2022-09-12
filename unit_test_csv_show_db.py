import unittest
from csv_show_db import *


class ShowCSVDBTests(unittest.TestCase):
    def setUp(self):
        self.db = CSVShowDB()

    def setUPDefaultData(self):
        self.db.set_column_names(["Name", "Age", "Height"])
        self.db.add_rows([["Tom", "25", "5 feet"],
                          ["Ella", "30", "4.5 feet"],
                          ["Richard", "50", "6 feet"],
                          ["Katy", "50", "5 feet"]
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

    def test_get_col_number_with_bad_name(self):
        self.setUPDefaultData()
        caught_exception = False
        try:
            col_num = self.db.get_col_number("ColumnDoesNotExist")
        except CSVShowError as e:
            caught_exception = True
            self.assertIn("Column name not found", e.args[0])
        self.assertTrue(caught_exception)

    def test_insert_new_column(self):
        self.db.set_column_names(["ItemA", "ItemC"])
        self.db.add_rows([["AA0", "CC0"], ["AA1", "CC1"]])
        self.db.insert_column("ItemB", 1)
        self.assertEqual(["ItemA", "ItemB", "ItemC"], self.db.column_names)
        self.assertEqual([["AA0", "", "CC0"], ["AA1", "", "CC1"]], self.db.rows)
        self.db.set_data_at_col_row(1, 0, "BB0")  # By col and row number
        self.assertEqual([["AA0", "BB0", "CC0"], ["AA1", "", "CC1"]], self.db.rows)
        self.db.set_data("ItemB", 1, "BB1")  # By row and name
        self.assertEqual([["AA0", "BB0", "CC0"], ["AA1", "BB1", "CC1"]], self.db.rows)

    def test_insert_new_row(self):
        self.db.set_column_names(["ItemA", "ItemB"])
        self.db.add_rows([["AA0", "BB0"], ["AA2", "BB2"]])
        self.assertEqual([["AA0", "BB0"], ["AA2", "BB2"]], self.db.rows)
        self.db.insert_row(1, ["AA1", "BB1"])
        self.assertEqual([["AA0", "BB0"], ["AA1", "BB1"], ["AA2", "BB2"]], self.db.rows)

    def test_get_length_and_width(self):
        self.setUPDefaultData()
        self.assertEqual(self.db.get_length(), 4)
        self.assertEqual(self.db.get_width(), 3)
        self.db.add_rows([["thing", "item", "something"]] * 50)
        self.db.set_column_name(52, "Color")
        self.assertEqual(self.db.get_length(), 54)
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

    def test_lookup_not_found(self):
        self.setUPDefaultData()
        caught_exception = False
        try:
            item = self.db.lookup_item("Height", {"Name": "Denise"}, fail_if_not_found=True)
        except CSVShowError as e:
            caught_exception = True
            self.assertIn("did not yield a match", e.args[0])
        self.assertTrue(caught_exception)

    def test_look_up_item_regex(self):
        self.setUPDefaultData()
        item = self.db.lookup_item("Age", {"Name": "/.*E.*/"})
        self.assertEqual("30", item)
        item = self.db.lookup_item("Age", {"Name": "|.*a|", "Age": "|5|"}, fail_if_not_found=True)
        self.assertEqual("50", item)

    def test_select_rows(self):
        self.setUPDefaultData()
        rows = self.db.select_rows({"Age": "50"})
        expected = [["Richard", "50", "6 feet"],
                    ["Katy", "50", "5 feet"]]
        self.assertEqual(expected, rows)

    # More features to add
    # filter columns
    # update items that match criteria

if __name__ == '__main__':
    unittest.main()
