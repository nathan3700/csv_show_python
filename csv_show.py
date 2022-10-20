#!/bin/env python
import re

from csv_show_format import CsvPrintFormatter
from csv_show_db import CSVShowDB
from csv_show_shared import *
import argparse
import csv
import sys
import os


class CsvShow:
    def __init__(self):
        self.db = CSVShowDB()
        self.formatter = CsvPrintFormatter()
        self.has_header = True
        self.parser = None
        self.parsed_args = argparse.Namespace()
        self.dialect = csv.excel
        self.regex_flags = re.IGNORECASE

    def main(self, args):
        self.fix_screen_width()
        self.make_arg_parser()
        self.parse_args(args)
        self.read_db(self.parsed_args.csv_file)

        # Do sort before lookup since sorting can affect first-lookup found
        if self.parsed_args.sort is not None:
            self.db.sort(self.parsed_args.sort)

        if len(self.parsed_args.lookup) > 0:
            values = self.get_lookup()
            print(", ".join(values))
        else:
            if len(self.parsed_args.select) > 0:
                self.db = self.db.select(self.parsed_args.select, self.regex_flags)
            self.apply_column_changes()
            if self.parsed_args.grep:
                self.db = self.db.grep(self.parsed_args.grep, self.regex_flags)
            self.formatter.set_db(self.db)
            if self.parsed_args.max_width is not None:
                for column_name in self.db.column_names:
                    self.formatter.max_width_by_name[column_name] = self.parsed_args.max_width
            if self.parsed_args.csv:
                output = self.formatter.format_output_as_csv()
                print(output, end="")
            else:
                output = self.formatter.format_output()
                print(output)

    @staticmethod
    def fix_screen_width():
        if 'COLUMNS' not in os.environ:
            os.environ['COLUMNS'] = "120"

    def make_arg_parser(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("csv_file", help="CSV file to be viewed")
        self.parser.add_argument("-sep", default=",", help="Separator used for input data. "
                                                           "Popular values: ',' (Default), '\\t', ' ', and 'guess'")
        self.parser.add_argument("-noheader", action="store_true", default=False,
                                 help="Indicates that the first row does not have column header names")
        self.parser.add_argument("-sort", action=ParseCommaSeparatedArgs, metavar="FIELD_LIST",
                                 help="Sort on these fields (FIELD_LIST is comma separated)")
        self.parser.add_argument("-select", action=ParseKVPairs, metavar="KEY=VALUE",
                                 help="Select matching rows. (/regex/ allowed in VALUES)")
        self.parser.add_argument("-lookup", action=ParseLookupSpec, metavar=("FIELD_LIST", "KEY=VALUE"),
                                 help="Lookup fields of first matching record (FIELD_LIST is comma separated) "
                                      "(/regex/ allowed in VALUES)")
        self.parser.add_argument("-pre_grep", metavar="REGEX",
                                 help="Grep rows using space-separated data before any database modifications")
        self.parser.add_argument("-grep", metavar="REGEX",
                                 help="Grep rows after database modifications such as column reordering")
        self.parser.add_argument("-max_width", type=int, help="Set the maximum column width")
        self.parser.add_argument("-columns", action=ParseCommaSeparatedArgs,
                                 help="Show only these columns in this order (FIELD_LIST is comma separated)", metavar="FIELD_LIST")
        self.parser.add_argument("-nocolumns", action=ParseCommaSeparatedArgs,
                                 help="Omit these columns (FIELD_LIST is comma separated)", metavar="FIELD_LIST")
        self.parser.add_argument("-csv", default=False, action="store_true", help="Format output as CSV")
        self.parser.add_argument("-match_case", default=False, action="store_true",
                                 help="Regular expressions match on case (Default is IGNORECASE)")

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
            try:
                self.db = self.db.select_columns(selected_columns)
            except KeyError:
                raise CSVShowError(f"Invalid column name")


class ParseCommaSeparatedArgs(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None or ("default" in kwargs and ["default"] is not None):
            raise ValueError("nargs and default cannot be changed.  Will always use ? and None respectively")
        nargs = "?"
        kwargs["default"] = None
        super(ParseCommaSeparatedArgs, self).__init__(option_strings, dest, nargs, **kwargs)

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


class ParseKVPairs(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None or ("default" in kwargs and ["default"] is not None):
            raise ValueError("nargs and default cannot be changed.  Will always use \"+\" and {} respectively")
        nargs = "+"
        kwargs["default"] = {}
        super(ParseKVPairs, self).__init__(option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, new_values, option_string=None):
        kv_pairs = getattr(namespace, self.dest)
        self.add_new_pairs(kv_pairs, new_values)

    def add_new_pairs(self, kv_pairs, new_values):
        for pair_string in new_values:
            kv = pair_string.split("=")
            if len(kv) != 2:
                raise argparse.ArgumentError(self, f"This argument must be of the form key=value: \"{pair_string}\"")
            kv_pairs[kv[0]] = kv[1]


class ParseLookupSpec(ParseKVPairs):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None or ("default" in kwargs and ["default"] is not None):
            raise ValueError("nargs and default cannot be changed.  Will always use \"+\" and [] respectively")
        nargs = "+"
        kwargs["default"] = []
        super(ParseKVPairs, self).__init__(option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, new_values, option_string=None):
        fields = getattr(namespace, self.dest)
        if not hasattr(namespace, "lookup_spec"):
            setattr(namespace, "lookup_spec", {})
        kv_pairs = getattr(namespace, "lookup_spec")
        if len(fields) == 0:  # The first value is a comma separated lis of chosen fields
            if "=" in new_values[0]:
                raise(argparse.ArgumentTypeError(
                    "The first value for this argument should be a field list, not be a key=value pair"))
            fields += new_values[0].split(",")
            new_values.pop(0)
        self.add_new_pairs(kv_pairs, new_values)


if __name__ == "__main__":
    show = CsvShow()
    show.main(sys.argv[1:])


