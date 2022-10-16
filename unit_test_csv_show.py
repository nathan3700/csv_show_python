import argparse
import io
import unittest
import sys
import os
from csv_show import *
from textwrap import dedent

class ShowCSVTests(unittest.TestCase):
    def setUp(self):
        self.dir = os.path.dirname(__file__)
        self.ui = CsvShow()
        self.ui.make_arg_parser()

    @staticmethod
    def capture_block_output(block_function):
        save_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        block_function()
        lines = captured_output.getvalue().splitlines(keepends=False)
        del captured_output
        sys.stdout = save_stdout
        return lines

    def test_can_read_csv_from_disk(self):
        self.ui.read_db("data/cars.csv")
        self.assertIn("Make", self.ui.db.column_names)
        self.assertEqual(self.ui.db.rows[0][0], "Ford")

    def test_can_get_csv_name_from_user(self):
        self.ui.parse_args(["cars.csv"])
        self.assertIn("csv_file", self.ui.parsed_args)

    def test_can_run_program(self):
        def block():
            self.ui.main([self.dir + "/data/cars.csv"])
        lines = self.capture_block_output(block)
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

    def test_sort_arguments(self):
        self.ui.parse_args(["some.csv"])
        self.assertIn("sort", self.ui.parsed_args)
        self.assertEqual(self.ui.parsed_args.sort, None)
        self.ui.parse_args(["some.csv", "-sort"])
        self.assertEqual(self.ui.parsed_args.sort, [])
        self.ui.parse_args(["some.csv", "-sort", "name"])
        self.assertEqual(self.ui.parsed_args.sort, ["name"])
        # Multiple use
        self.ui.parse_args(["some.csv", "-sort", "name", "-sort", "age"])
        self.assertEqual(self.ui.parsed_args.sort, ["name", "age"])
        # Comma separated
        self.ui.parse_args(["some.csv", "-sort", "name,age"])
        self.assertEqual(self.ui.parsed_args.sort, ["name", "age"])
        # Mix
        self.ui.parse_args(["some.csv", "-sort", "name,age", "-sort", "height,weight"])
        self.assertEqual(self.ui.parsed_args.sort, ["name", "age", "height", "weight"])

    def test_select_arguments(self):
        self.ui.parse_args(["some.csv"])
        self.assertIn("select", self.ui.parsed_args)
        self.assertEqual(self.ui.parsed_args.select, {})
        self.ui.parse_args("some.csv -select name=bob".split())
        self.assertEqual(self.ui.parsed_args.select, {"name": "bob"})
        # Multiple use
        self.ui.parse_args("some.csv -select name=bob -select age=33".split())
        self.assertEqual(self.ui.parsed_args.select, {"name": "bob", "age": "33"})
        self.ui.parse_args("some.csv -select name=bob age=33".split())
        self.assertEqual(self.ui.parsed_args.select, {"name": "bob", "age": "33"})

    def test_select(self):
        def block():
            self.ui.main("data/cars.csv -select Make=GMC".split())
        lines = self.capture_block_output(block)
        expected = dedent("""\
        |Make|Model |Year|
        |----|------|----|
        |GMC |Safari|2002|""")
        self.assertEqual(expected, "\n".join(lines))

    def test_lookup_arguments(self):
        self.ui.parse_args(["some.csv"])
        self.assertIn("lookup", self.ui.parsed_args)
        self.assertEqual(self.ui.parsed_args.lookup, [])
        self.ui.parse_args("some.csv -lookup age name=bob".split())
        self.assertIn("lookup_spec", self.ui.parsed_args)
        self.assertEqual(self.ui.parsed_args.lookup, ["age"])
        self.assertEqual(self.ui.parsed_args.lookup_spec, {"name": "bob"})
        # Multiple use
        self.ui.make_arg_parser()
        self.ui.parse_args("some.csv -lookup age name=bob age=33 -lookup w=5 h=20".split())
        self.assertEqual(self.ui.parsed_args.lookup, ["age"])
        self.assertEqual(self.ui.parsed_args.lookup_spec, {"name": "bob", "age": "33", "w": "5", "h": "20"})
        # First argument is a key value but should be a field list
        self.ui.make_arg_parser()
        took_exception = False
        try:
            self.ui.parse_args("some.csv -lookup name=bob age=33 -lookup w=5 h=20".split())
        except argparse.ArgumentTypeError as e:
            self.assertIn("should be a field list", e.args[0])
            took_exception = True
        self.assertTrue(took_exception)

    def test_lookup(self):
        def block():
            self.ui.main("data/cars.csv -lookup Make,Year Make=Ford Year=1996 Model=Windstar".split())
        output = self.capture_block_output(block)
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], "Ford, 1996")

    def test_lookup_not_found(self):
        def block():
            self.ui.main("data/cars.csv -lookup Make Make=Ford Year=1966".split())
        exception_taken = False
        try:
            output = self.capture_block_output(block)
        except CSVShowError as e:
            self.assertIn("Lookup failed", e.args[0])
            # print(e.args[0])
            exception_taken = True
        self.assertTrue(exception_taken)

    def test_can_get_max_width_from_user(self):
        self.ui.parse_args("cars.csv -max_width 5".split())
        self.assertIn("max_width", self.ui.parsed_args)
        self.ui.parsed_args = None
        self.ui.parse_args("cars.csv -max 5".split())
        self.assertIn("max_width", self.ui.parsed_args)
        self.assertEqual(5, self.ui.parsed_args.max_width)

    def test_user_set_max_width(self):
        def block():
            self.ui.main("data/cars.csv -max_width 5".split())
        lines = self.capture_block_output(block)
        expected_output = [
            "|Make |Model|Year|",
            '|-----|-----|----|',
            "|Ford |Expe*|2016|",
            "|Honda|Acco*|2007|",
            "|Ford |Expl*|2003|",
            "|Ford |Wind*|1996|",
            "|GMC  |Safa*|2002|",
            "|Tesla|Mode*|2015|"
        ]
        self.assertEqual(expected_output, lines)

    def test_columns_arguments(self):
        self.ui.parse_args(["some.csv"])
        self.assertIn("columns", self.ui.parsed_args)
        self.assertIn("nocolumns", self.ui.parsed_args)
        self.assertEqual(self.ui.parsed_args.columns, None)
        self.assertEqual(self.ui.parsed_args.nocolumns, None)
        self.ui.parse_args("some.csv -columns red,green,blue".split())
        self.assertEqual(["red", "green", "blue"], self.ui.parsed_args.columns)
        self.ui.parse_args("some.csv -nocolumns red,green,blue".split())
        self.assertEqual(["red", "green", "blue"], self.ui.parsed_args.nocolumns)

    def test_see_help_output(self):
        self.ui.make_arg_parser()
        #print(self.ui.parser.format_help())

    def test_see_final_output(self):
        def block():
            self.ui.main((self.dir + "/data/cars.csv -sort").split())
        output = self.capture_block_output(block)
        #print("\n".join(output))

if __name__ == '__main__':
    unittest.main()
