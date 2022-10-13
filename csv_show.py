#!/bin/env python
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

    def main(self, args):
        self.fix_screen_width()
        self.make_arg_parser()
        self.parse_args(args)
        self.read_db(self.parsed_args.csv_file)
        if self.parsed_args.sort is not None:
            self.db.sort(self.parsed_args.sort)
        if len(self.parsed_args.lookup) > 0:
            values = self.get_lookup()
            print(", ".join(values))
        else:
            if len(self.parsed_args.select) > 0:
                self.db = self.db.select(self.parsed_args.select)
            self.formatter.set_db(self.db)
            if self.parsed_args.max_width is not None:
                for column_name in self.db.column_names:
                    self.formatter.max_width_by_name[column_name] = self.parsed_args.max_width
            print(self.formatter.format_output())

    def get_lookup(self):
        lookup_row = self.db.lookup_row(self.parsed_args.lookup_spec)
        if lookup_row is None:
            raise CSVShowError("Lookup failed. Lookup spec: " + str(self.parsed_args.lookup_spec))
        rec = self.db.row_to_record(lookup_row)
        values = []
        for field in self.parsed_args.lookup:
            values.append(rec[field])
        return values

    def read_db(self, file):
        self.db.clear()
        file_handle = open(file)
        reader = csv.reader(file_handle)
        if self.has_header:
            column_names = reader.__next__()
            self.db.set_column_names(column_names)
        remaining_rows = [row for row in reader]
        self.db.add_rows(remaining_rows)
        file_handle.close()

    @staticmethod
    def fix_screen_width():
        if 'COLUMNS' not in os.environ:
            os.environ['COLUMNS'] = "100"

    def parse_args(self, args):
        self.parsed_args = self.parser.parse_args(args)

    def make_arg_parser(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("csv_file", help="CSV file to be viewed")
        self.parser.add_argument("-sort", action=ParseCommaSeparatedArgs,
                                 help="Sort on these fields: Field1,Field2,...")
        self.parser.add_argument("-select", action=ParseKVPairs, metavar="Key=Value",
                                 help="Select rows with Key1=Value1,Key2=Value2,... "
                                      "(/regex/ allowed for value)")
        self.parser.add_argument("-lookup", action=ParseLookupSpec, metavar=("Fields", "Key=Value"),
                                 help="Lookup fields (comma separated) with Key1=Value1,Key2=Value2,... "
                                      "(/regex/ allowed for value)")
        self.parser.add_argument("-max_width", type=int, help="Set the maximum column width")


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


