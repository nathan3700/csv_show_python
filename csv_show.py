#!/bin/env python
from csv_show_format import *
import argparse
import csv
import sys

class CsvShow:
    def __init__(self):
        self.db = CSVShowDB()
        self.formatter = CsvPrintFormatter()
        self.has_header = True
        self.parsed_args = argparse.Namespace()

    def main(self, args):
        self.parse_args(args)
        self.read_db(self.parsed_args.csv_file)
        self.formatter.set_db(self.db)
        print(self.formatter.format_output())

    def read_db(self, file):
        file_handle = open(file)
        reader = csv.reader(file_handle)
        if self.has_header:
            column_names = reader.__next__()
            self.db.set_column_names(column_names)
        remaining_rows = [row for row in reader]
        self.db.add_rows(remaining_rows)
        file_handle.close()


    def parse_args(self, args):
        parser = argparse.ArgumentParser()
        parser.add_argument("--help2", action="store_true", default=False, help="Print this message")
        parser.add_argument("csv_file", help="CSV file to be viewed")
        self.parsed_args = parser.parse_args(args)


if __name__ == "__main__":
    show = CsvShow()
    show.main(sys.argv[1:])


