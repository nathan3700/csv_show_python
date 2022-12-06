import argparse
import io
import unittest
import sys
import os
from csv_show import *
from textwrap import dedent
import argparse


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
        self.ui.parse_args([self.dir + "/data/cars.csv"])
        self.ui.read_db(self.ui.parsed_args.csv_file)
        self.assertIn("Make", self.ui.db.column_names)
        self.assertEqual(self.ui.db.rows[0][0], "Ford")

    def test_can_get_csv_name_from_user(self):
        self.ui.parse_args(["cars.csv"])
        self.assertIn("csv_file", self.ui.parsed_args)

    def test_can_run_program(self):
        def block():
            self.ui.show([self.dir + "/data/cars.csv"])
        lines = self.capture_block_output(block)
        expected_output = [
            "|Make |Model     |Year|",
            '|-----|----------|----|',
            "|Ford |Expedition|2016|",
            "|Honda|Accord    |2007|",
            "|Ford |Explorer  |2003|",
            "|Ford |Windstar  |1996|",
            "|GMC  |Safari    |2002|",
            "|Tesla|Model S   |2015|",
            "|Roman|Chariot   |300 |"
        ]
        self.assertEqual(expected_output, lines)

    def test_can_run_with_empty_file(self):
        sav_stdin = sys.stdin
        class FakeEmptyStdIn:
            def __iter__(self):
                return self
            def __next__(self):
                    raise StopIteration

            def close(self):
                pass
        sys.stdin = FakeEmptyStdIn()

        def block():
            self.ui.show("- -csv".split())
        lines = self.capture_block_output(block)
        self.assertEqual(lines, [""])
        sys.stdin = sav_stdin

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
        self.assertEqual(self.ui.parsed_args.select, [])
        self.ui.parse_args("some.csv -select name=bob".split())
        self.assertEqual(self.ui.parsed_args.select, [["name", "=", "bob"]])
        # Multiple use
        self.ui.make_arg_parser()
        self.ui.parse_args("some.csv -select name=bob -select age=33".split())
        self.assertEqual(self.ui.parsed_args.select, [["name", "=", "bob"], ["age", "=", "33"]])
        self.ui.make_arg_parser()
        self.ui.parse_args("some.csv -select name=bob age=33".split())
        self.assertEqual(self.ui.parsed_args.select, [["name", "=", "bob"], ["age", "=", "33"]])

    def test_select(self):
        def block():
            self.ui.show((self.dir + "/data/cars.csv -select Make=GMC").split())
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
        self.assertEqual(self.ui.parsed_args.lookup_spec, [["name", "=", "bob"]])
        # Multiple use
        self.ui.make_arg_parser()
        self.ui.parse_args("some.csv -lookup age name=bob age=33 w=5 h=20".split())
        self.assertEqual(self.ui.parsed_args.lookup, ["age"])
        self.assertEqual(self.ui.parsed_args.lookup_spec,
                         [["name", "=", "bob"], ["age", "=", "33"], ["w", "=", "5"], ["h", "=", "20"]])
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
            self.ui.show((self.dir + "/data/cars.csv -lookup Make,Year Make=Ford Year=1996 Model=Windstar").split())
        output = self.capture_block_output(block)
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], "Ford, 1996")

    def test_lookup_not_found(self):
        def block():
            self.ui.show((self.dir + "/data/cars.csv -lookup Make Make=Ford Year=1966").split())
        exception_taken = False
        try:
            output = self.capture_block_output(block)
        except CSVShowError as e:
            self.assertIn("Lookup failed", e.args[0])
            # print(e.args[0])
            exception_taken = True
        self.assertTrue(exception_taken)

    def test_grep_arguments(self):
        self.ui.parse_args("some.csv -pregrep Ford -grep 2.*".split())
        self.assertIn("pregrep", self.ui.parsed_args)
        self.assertIn("grep", self.ui.parsed_args)

    def test_pregrep(self):
        def block():
            self.ui.show((self.dir + "/data/cars.csv -pregrep ford.*2.*").split())

        lines = self.capture_block_output(block)
        self.assertEqual(
            [
                "|Make|Model     |Year|",
                "|----|----------|----|",
                "|Ford|Expedition|2016|",
                "|Ford|Explorer  |2003|"
            ], lines
        )

        def block():
            self.ui.show((self.dir + "/data/cars.csv -pregrep! Ford -csv").split())

        lines = self.capture_block_output(block)
        self.assertEqual(
            [
                "Ford,Expedition,2016",
                "Ford,Explorer,2003",
                "Ford,Windstar,1996"
            ], lines
        )

    def test_post_grep(self):
        def block():
            self.ui.show((self.dir + "/data/cars.csv -columns Year,Make -grep 2.*ford").split())

        lines = self.capture_block_output(block)
        self.assertEqual(
            [
                "|Year|Make|",
                "|----|----|",
                "|2016|Ford|",
                "|2003|Ford|"
            ], lines
        )

    def test_can_get_max_width_from_user(self):
        self.ui.parse_args("cars.csv".split())
        self.assertIn("max_width", self.ui.parsed_args)
        self.assertEqual({None: None}, self.ui.parsed_args.max_width)
        self.ui.parsed_args = None
        self.ui.parse_args("cars.csv -max 5".split())
        self.assertIn("max_width", self.ui.parsed_args)
        self.assertEqual({None: 5}, self.ui.parsed_args.max_width)

    def test_per_column_max_width(self):
        self.ui.parse_args("some.csv -max_width Model=3".split())
        self.assertEqual(self.ui.parsed_args.max_width, {None: None, "Model": 3})
        self.ui.make_arg_parser()
        self.ui.parse_args("some.csv -max_width 20 Model=3".split())
        self.assertEqual(self.ui.parsed_args.max_width, {None: 20, "Model": 3})
        self.ui.make_arg_parser()
        self.ui.parse_args("some.csv -max_width Model=3 Make=4".split())
        self.assertEqual(self.ui.parsed_args.max_width, {None: None, "Model": 3, "Make": 4})
        self.ui.make_arg_parser()
        self.ui.parse_args("some.csv -max_width 25 -max_width Model=3".split())
        self.assertEqual(self.ui.parsed_args.max_width, {None: 25, "Model": 3})
        self.ui.make_arg_parser()
        saw_exception = False
        try:
            self.ui.parse_args("some.csv -max_width 1".split())
        except argparse.ArgumentTypeError as e:
            saw_exception = True
        self.assertTrue(saw_exception)
        try:
            self.ui.parse_args("some.csv -max_width Model=0".split())
        except argparse.ArgumentTypeError as e:
            saw_exception = True
        self.assertTrue(saw_exception)

    def test_user_set_max_width(self):
        def block():
            self.ui.show((self.dir + "/data/cars.csv -max_width 5 Year=3").split())
        lines = self.capture_block_output(block)
        expected_output = [
            "|Make |Model|Ye*|",
            '|-----|-----|---|',
            "|Ford |Expe*|20*|",
            "|Honda|Acco*|20*|",
            "|Ford |Expl*|20*|",
            "|Ford |Wind*|19*|",
            "|GMC  |Safa*|20*|",
            "|Tesla|Mode*|20*|",
            "|Roman|Char*|300|"
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

    def test_regex_column_matching(self):
        self.ui.db.column_names = ["Model", "Make", "Measurement"]
        self.ui.parse_args("some.csv -columns /M.*/".split())
        result_list = self.ui.get_matching_columns(["/M.*/"])
        self.assertEqual(["Model", "Make", "Measurement"], result_list)
        result_list = self.ui.get_matching_columns(["/Mo.*/"])
        self.assertEqual(["Model"], result_list)
        result_list = self.ui.get_matching_columns(["/^.*ment$/", "/.*ke/", "Model"])
        self.assertEqual(["Measurement", "Make", "Model"], result_list)
        error_seen = False
        try:
            result_list = self.ui.get_matching_columns(["NoMatch"])
        except CSVShowError as e:
            error_seen = True
        self.assertTrue(error_seen)

    def test_format_output_as_csv(self):
        def block():
            self.ui.show((self.dir + "/data/cars.csv -csv").split())
        output = "\n".join(self.capture_block_output(block))

        fh = open(self.dir + "/data/cars.csv")
        expected = "".join(fh.readlines())
        fh.close()
        self.assertEqual(expected, output)

    def test_match_case(self):
        self.ui.parse_args("some.csv".split())
        self.assertEqual(self.ui.regex_flags, re.IGNORECASE)
        self.ui.parse_args("some.csv -match_case".split())
        self.assertEqual(self.ui.regex_flags, 0)

    def test_see_help_output(self):
        self.ui.make_arg_parser()
        #print(self.ui.parser.format_help())

    def test_see_final_output(self):
        def block():
            self.ui.show((self.dir + "/data/cars.csv -sort").split())
        output = self.capture_block_output(block)
        #print("\n".join(output))

    def test_less_argument(self):
        self.ui.parse_args("some.csv".split())
        self.assertEqual(self.ui.parsed_args.less, None)
        self.ui.parse_args("some.csv -less".split())
        self.assertEqual(self.ui.parsed_args.less, True)
        self.ui.parse_args("some.csv -noless".split())
        self.assertEqual(self.ui.parsed_args.less, False)

    def test_can_parse_other_db_types(self):
        self.ui.parse_args("some.csv".split())
        self.assertEqual(self.ui.parsed_args.sep, ",")
        self.ui.parse_args("some.csv -sep MYSEP".split())
        self.assertEqual(self.ui.parsed_args.sep, "MYSEP")

        self.ui.parse_args((self.dir + "/data/cars.tsv -sep \\t").split())
        self.ui.read_db(self.ui.parsed_args.csv_file)
        self.ui.parse_args([self.dir + "/data/cars.txt", "-sep", " "])
        self.ui.read_db(self.ui.parsed_args.csv_file)
        self.ui.parse_args((self.dir + "/data/cars.tsv -sep guess").split())
        self.ui.read_db(self.ui.parsed_args.csv_file)

    def test_user_can_modify_db(self):
        class UserShow(CsvShow):
            def user_add_args(self):
                self.parser.add_argument("-hex", default=False, action="store_true", help="Show numbers as hexadecimal")
                self.parser.add_argument("-add_Model_prefix", default=False, action="store_true",
                                         help="Prepend model with the prefix \"model:\"")

            def user_modify_db(self):
                year_col_num = self.db.column_number_by_name["Year"]
                for row in self.db.rows:
                    row[year_col_num] = hex(string_to_number(row[year_col_num]))

            def user_modify_db_post_select(self):
                model_col_num = self.db.column_number_by_name["Model"]
                for row in self.db.rows:
                    row[model_col_num] = "model:" + row[model_col_num]

        user_shower = UserShow()
        def block():
            user_shower.show((self.dir + "/data/cars.csv -hex").split())

        output = self.capture_block_output(block)
        #print("\n".join(output))


if __name__ == '__main__':
    unittest.main()
