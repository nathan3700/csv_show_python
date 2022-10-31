#!/bin/env python
import re

from csv_show_format import CsvPrintFormatter
from csv_show_db import CSVShowDB
from csv_show_shared import *
import argparse
import csv
import sys
import os
import subprocess


class CsvShow:
    def __init__(self):
        self.db = CSVShowDB()
        self.formatter = CsvPrintFormatter()
        self.has_header = True
        self.parser = None
        self.parsed_args = argparse.Namespace()
        self.dialect = csv.excel
        self.regex_flags = re.IGNORECASE
        self.removed_columns = set()

        self.tty_columns = CsvShow.get_tty_columns()
        self.tty_lines = CsvShow.get_tty_lines()

    def main(self, args):
        self.make_arg_parser()
        self.parse_args(args)
        self.read_db(self.parsed_args.csv_file)
        self.match_column_args_to_column_names()

        # Do sort before lookup since sorting can affect first-lookup found
        if self.parsed_args.sort is not None:
            self.db.sort(self.parsed_args.sort, self.parsed_args.reverse)

        self.db.regex_flags = self.regex_flags
        if len(self.parsed_args.lookup) > 0:
            values = self.get_lookup()
            print(", ".join(values))
        else:
            if len(self.parsed_args.select) > 0:
                self.db = self.db.select(self.parsed_args.select)
            self.apply_column_changes()
            if self.parsed_args.grep:
                self.db = self.db.grep(self.parsed_args.grep, self.regex_flags)
            self.formatter.set_db(self.db)
            if self.parsed_args.max_width[None] is not None:
                for column_name in self.db.column_names:
                    self.formatter.max_width_by_name[column_name] = self.parsed_args.max_width[None]
            for max_width_column in self.parsed_args.max_width:
                if max_width_column in self.db.column_names:
                    self.formatter.max_width_by_name[max_width_column] = self.parsed_args.max_width[max_width_column]

            if self.parsed_args.csv:
                output = self.formatter.format_output_as_csv()
            else:
                output = self.formatter.format_output_as_lines()

            self.print_formatted_db(output)

    @staticmethod
    def get_tty_columns():
        default = 120
        if 'COLUMNS' in os.environ:
            return string_to_number(os.environ['COLUMNS']) or default
        else:
            return default

    @staticmethod
    def get_tty_lines():
        default = 30
        if 'LINES' in os.environ:
            return string_to_number(os.environ['LINES']) or default
        else:
            return default

    def make_arg_parser(self):
        # noinspection PyPep8Naming
        explain_FIELD_LIST = "FIELD_LIST is comma separated with /regex/ allowed"
        self.parser = argparse.ArgumentParser(add_help=False)
        self.parser.add_argument("-help", "-h", action="help", default=argparse.SUPPRESS,
                                 help='Show this help message and exit.')
        self.parser.add_argument("csv_file", help="CSV file to be viewed.  Use \"-\" to indicate STDIN")
        self.parser.add_argument("-sep", default=",", help="Separator used for input data. "
                                                           "Popular values: ',' (Default), '\\t', ' ', and 'guess'")
        self.parser.add_argument("-noheader", action="store_true", default=False,
                                 help="Indicates that the first row does not have column header names")
        self.parser.add_argument("-sort", action=ParseCommaSeparatedArgs, metavar="FIELD_LIST",
                                 help="Sort on these fields. " + explain_FIELD_LIST)
        self.parser.add_argument("-reverse", default=False, action="store_true",
                                 help="Reverse the direction of -sort")
        self.parser.add_argument("-select", action=ParseMatchSpec, metavar="KEY<op>VALUE",
                                 help="Select matching rows. Supported <op>: " +
                                      ParseMatchSpec.supported_relational_ops +
                                      " Note: = and == both mean equality.  "
                                      "=~ and !~ mean VALUE is a regular expression"
                                 )
        self.parser.add_argument("-lookup", action=ParseLookupSpec, metavar=("FIELD_LIST", "KEY<op>VALUE"),
                                 help="Lookup fields of first matching record. " + explain_FIELD_LIST +
                                      ". See -select for <op> explanation")
        self.parser.add_argument("-pre_grep", metavar="REGEX",
                                 help="Grep rows using space-separated data before any database modifications")
        self.parser.add_argument("-grep", metavar="REGEX",
                                 help="Grep rows after database modifications such as column reordering")
        self.parser.add_argument("-match_case", default=False, action="store_true",
                                 help="Regular expressions match on case (Default is IGNORECASE)")
        self.parser.add_argument("-max_width", action=ParseMaxWidthSpec, metavar=("[MAX_WIDTH]", "COLUMN_NAME=WIDTH"),
                                 help="Set the maximum column width globally, or on a per column basis. ")
        self.parser.add_argument("-columns", action=ParseCommaSeparatedArgs,
                                 help="Show only these columns in this order. " + explain_FIELD_LIST, metavar="FIELD_LIST")
        self.parser.add_argument("-nocolumns", action=ParseCommaSeparatedArgs,
                                 help="Omit these columns. " + explain_FIELD_LIST, metavar="FIELD_LIST")
        self.parser.add_argument("-csv", default=False, action="store_true", help="Format output as CSV")
        self.parser.add_argument("-less", default=False, action="store_true", help="Pipe to less")
        self.parser.add_argument("-noless", default=False, action="store_true", help="Disable pipe to less")

    def parse_args(self, args):
        self.parsed_args = self.parser.parse_args(args)
        self.apply_sep_to_dialect()
        self.apply_regex_flags()

    def apply_sep_to_dialect(self):
        if self.parsed_args.sep in ["\\t", "\t"]:
            self.dialect = csv.excel_tab
        elif self.parsed_args.sep == " ":
            self.dialect.delimiter = self.parsed_args.sep
            self.dialect.skipinitialspace = True
        elif self.parsed_args.sep == "guess":
            with open(self.parsed_args.csv_file, newline='') as csvfile:
                self.dialect = csv.Sniffer().sniff(csvfile.read(1024))
                csvfile.close()
        else:
            self.dialect.delimiter = self.parsed_args.sep

        if self.parsed_args.noheader:
            self.has_header = False

    def apply_regex_flags(self):
        if self.parsed_args.match_case:
            self.regex_flags = 0

    def read_db(self, file):
        self.db.clear()
        if file == "-":
            file_handle = sys.stdin
        else:
            file_handle = open(file)
        reader = csv.reader(file_handle, dialect=self.dialect)
        if self.has_header:
            column_names = reader.__next__()
            self.db.set_column_names(column_names)
        if self.parsed_args.pre_grep:
            remaining_rows = []
            for row in reader:
                if re.search(self.parsed_args.pre_grep, " ".join(row), self.regex_flags):
                    remaining_rows.append(row)
        else:
            remaining_rows = [row for row in reader]
        self.db.add_rows(remaining_rows)
        file_handle.close()

    def match_column_args_to_column_names(self):
        if self.parsed_args.columns:
            self.parsed_args.columns = self.get_matching_columns(self.parsed_args.columns)
        if self.parsed_args.nocolumns:
            self.parsed_args.nocolumns = self.get_matching_columns(self.parsed_args.nocolumns)
        if self.parsed_args.sort:
            self.parsed_args.sort = self.get_matching_columns(self.parsed_args.sort)
        if self.parsed_args.lookup:
            self.parsed_args.lookup = self.get_matching_columns(self.parsed_args.lookup)

    def get_lookup(self):
        lookup_row = self.db.lookup_row(self.parsed_args.lookup_spec)
        if lookup_row is None:
            raise CSVShowError("Lookup failed. Lookup spec: " + str(self.parsed_args.lookup_spec))
        rec = self.db.row_to_record(lookup_row)
        values = []
        for field in self.parsed_args.lookup:
            values.append(rec[field])
        return values

    def apply_column_changes(self):
        if self.parsed_args.columns is not None or self.parsed_args.nocolumns is not None:
            nocolumns = self.parsed_args.nocolumns or []
            selected_columns = self.parsed_args.columns or self.db.column_names
            selected_columns = [column for column in selected_columns if column not in nocolumns]
            orig = set(self.db.column_names)
            sel = set(selected_columns)
            self.removed_columns = orig - sel

            try:
                self.db = self.db.select_columns(selected_columns)
            except KeyError:
                raise CSVShowError(f"Invalid column name")

    def get_matching_columns(self, column_expressions):
        matched_set = set()
        matched = []
        for expr in column_expressions:
            regex = get_regex(expr)
            expr_did_match = False
            for col in self.db.column_names:
                is_selected = False
                if regex and re.search(regex, col, self.regex_flags):
                    is_selected = True
                if not regex and col == expr:
                    is_selected = True
                if is_selected:
                    expr_did_match = True
                    if col not in matched_set:
                        matched_set.add(col)
                        matched.append(col)
            if not expr_did_match:
                raise CSVShowError(f"Expression \"{expr}\" did not match a column name")
        return matched

    def print_formatted_db(self, output):
        is_tty = sys.stdout.isatty()
        has_less = CsvShow.get_has_less()
        fits_in_tty_window = ((len(self.db) + 2 <= self.tty_lines)
                              and (len(output) == 0 or (len(output[0]) <= self.tty_columns))
                              )
        if (self.parsed_args.less or
                (not self.parsed_args.noless and is_tty and has_less and not fits_in_tty_window)):
            proc = subprocess.run("less -S", input="\n".join(output), text=True, shell=True)
        else:
            self.print_all_lines(output)

    @staticmethod
    def print_all_lines(output):
        try:
            last_index = len(output) - 1
            for line_num in range(len(output)):
                line = output[line_num]
                if line_num != last_index:
                    print(line, )
                else:
                    print(line, end="")
        except BrokenPipeError as e:
            pass  # Okay: The user piped to another program which didn't consume all the output

    @staticmethod
    def get_has_less():
        result = subprocess.run("less --version", shell=True, capture_output=True)
        has_less = result.returncode == 0
        return has_less


class ParseCommaSeparatedArgs(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None or ("default" in kwargs and ["default"] is not None):
            raise ValueError("nargs and default cannot be changed.  Will always use ? and None respectively")
        nargs = "?"
        kwargs["default"] = None
        super().__init__(option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, new_values, option_string=None):
        if new_values is None:
            new_values = []
        else:
            prev_values = getattr(namespace, self.dest)
            if not prev_values:
                prev_values = []
            if "," in new_values:
                new_values = prev_values + new_values.split(",")
            else:
                new_values = prev_values + [new_values]
        setattr(namespace, self.dest, new_values)


class ParseActionBase(argparse.Action):
    supported_relational_ops = '(=|==|!=|>|>=|<|<=|=~|!~)'
    supported_relational_ops_re = r'(==|!=|>=|<=|=~|!~|=|>|<)'  # Single char ops need to be last to work

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, nargs, **kwargs)
        self.value_type = str

    def add_new_pairs(self, kv_pairs, new_values):
        for pair_string in new_values:
            kv = pair_string.split("=")
            if len(kv) != 2:
                raise argparse.ArgumentError(self, f"This argument must be of the form key=value: \"{pair_string}\"")
            kv_pairs[kv[0]] = self.value_type(kv[1])

    def add_new_relations(self, relations, new_relations):
        for relation_str in new_relations:
            relation = re.split(self.supported_relational_ops_re, relation_str, 1)
            if len(relation) != 3:
                raise argparse.ArgumentError(self, f"This argument must be of the form key<operator>value: \"{relation_str}\"")
            relations.append(relation)


class ParseMatchSpec(ParseActionBase):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None or ("default" in kwargs and ["default"] is not None):
            raise ValueError("nargs and default cannot be changed.  Will always use \"+\" and [] respectively")
        nargs = "+"
        kwargs["default"] = []
        super().__init__(option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, new_values, option_string=None):
        relations = getattr(namespace, self.dest)
        self.add_new_relations(relations, new_values)


class ParseLookupSpec(ParseActionBase):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None or ("default" in kwargs and ["default"] is not None):
            raise ValueError("nargs and default cannot be changed.  Will always use \"+\" and [] respectively")
        nargs = "+"
        kwargs["default"] = []
        super().__init__(option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, new_values, option_string=None):
        fields = getattr(namespace, self.dest)
        if not hasattr(namespace, f"{self.dest}_spec"):
            setattr(namespace, f"{self.dest}_spec", [])
        relations = getattr(namespace, f"{self.dest}_spec")
        if len(fields) == 0:  # The first value is a comma separated list of chosen fields
            for op in self.supported_relational_ops:
                if op in new_values[0]:
                    raise(argparse.ArgumentTypeError(
                        "The first value for this argument should be a field list, not be a key<operator>value pair"))
            fields += new_values[0].split(",")
            new_values.pop(0)
            self.add_new_relations(relations, new_values)
        else:
            raise(argparse.ArgumentTypeError(f"Please use {self.option_strings} only once"))


class ParseMaxWidthSpec(ParseActionBase):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None or ("default" in kwargs and ["default"] is not None):
            raise ValueError("nargs and default cannot be changed.  Will always use \"+\" and {None: None} respectively")
        nargs = "+"
        kwargs["default"] = {None: None}
        super().__init__(option_strings, dest, nargs, **kwargs)
        self.value_type = int

    def __call__(self, parser, namespace, new_values, option_string=None):
        kv_pairs = getattr(namespace, self.dest)
        new_kv_strings = [value for value in new_values if "=" in value]
        new_single_values = [int(value) for value in new_values if "=" not in value]
        if len(new_single_values) == 1:
            kv_pairs[None] = new_single_values[0]
        if len(new_single_values) > 1:
            raise(argparse.ArgumentTypeError(
                "Please specify only one default value (values that are not of the form key=value)"))
        self.add_new_pairs(kv_pairs, new_kv_strings)
        for key in kv_pairs:
            if kv_pairs[key] is not None and kv_pairs[key] <= 1:
                raise(argparse.ArgumentTypeError(
                    "-max_width: "
                    "Please choose values that are larger than 1. "
                    "To eliminate a column use -columns/-nocolumns "
                ))


if __name__ == "__main__":
    show = CsvShow()
    show.main(sys.argv[1:])


