import argparse
import io
import unittest
import sys
import os
from csv_show import *


class ShowCSVTests(unittest.TestCase):
    def setUp(self):
        self.ui = CsvShow()

    def test_can_read_csv_from_disk(self):
        self.ui.read_db("data/cars.csv")
        self.assertIn("Make", self.ui.db.column_names)
        self.assertEqual(self.ui.db.rows[0][0], "Ford")

    def test_can_get_csv_name_from_user(self):
        self.ui.parse_args(["cars.csv"])
        self.assertIn("csv_file", self.ui.parsed_args)

    def test_can_run_program(self):
        dir = os.path.dirname(__file__)
        save_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        self.ui.main([dir + "/data/cars.csv"])
        lines = captured_output.getvalue().splitlines(keepends=False)
        del captured_output
        sys.stdout = save_stdout
        expected_output = [
            "|Make |Model     |Year|",
            '|-----|----------|----|',
            "|Ford |Expedition|2016|",
            "|Honda|Accord    |2007|",
            "|Ford |Explorer  |2003|",
            "|Ford |Windstar  |1996|",
            "|GMC  |Safari    |2002|",
            "|Tesla|Model S   |2015|"
        ]
        self.assertEqual(expected_output, lines)


if __name__ == '__main__':
    unittest.main()
