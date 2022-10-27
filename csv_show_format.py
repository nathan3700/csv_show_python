import collections
import re

from csv_show_db import CSVShowDB


class CsvPrintFormatter:
    def __init__(self):
        self.width_histograms = {}  # Dict of Dict  h[col_name][width]=count
        self.max_width_by_name = collections.OrderedDict()
        self.db = CSVShowDB()
        self.has_header = True
        self.column_numbers_by_name = collections.OrderedDict()

    def set_db(self, db: CSVShowDB):
        self.db = db

    def format_output(self):
        output = ''
        longest = self.find_longest_column_widths()

        if self.has_header:
            output += self.format_row(self.db.column_names, longest)
            output += "\n"
            output += self.format_row(["-" * x for x in longest], longest)
            if len(self.db.rows) > 0:
                output += "\n"

        last_index = len(self.db.rows) - 1
        for row_index in range(len(self.db.rows)):
            row = self.db.rows[row_index]
            formatted_row = self.format_row(row, longest)
            output += formatted_row
            if row_index != last_index:
                output += "\n"

        return output

    def format_output_as_csv(self):
        output = ''
        if self.has_header:
            output += ",".join(self.db.column_names)
            if len(self.db.rows) > 0:
                output += "\n"
        last_index = len(self.db.rows) - 1
        for row_index in range(len(self.db.rows)):
            row = self.db.rows[row_index]
            output += ",".join(row)
            if row_index != last_index:
                output += "\n"
        return output

    @classmethod
    def format_row(cls, row, col_widths):
        row_str = ""
        for col_num in range(len(row)):
            if col_num == 0:
                row_str += "|"
            width = col_widths[col_num]
            data = row[col_num]
            if len(data) > width:  # Remove a character to make room for truncation indicator
                width -= 1
            fmt = "{item:" + f"{width}" + "." + f"{width}" "}"
            row_str += fmt.format(item=data)
            if len(data) > width:  # Indicate truncation to the user with a "*"
                row_str += "*"
            row_str += "|"
        return row_str

    def find_longest_column_widths(self):
        longest = []
        rows_including_header = [self.db.column_names] + self.db.rows
        for row in rows_including_header:
            for col_num in range(len(row)):
                col_width = len(row[col_num])
                self.update_longest_by_col_num(longest, col_width, col_num)
                self.update_width_histograms(col_num, col_width)

        self.apply_width_caps(longest)
        return longest

    @staticmethod
    def update_longest_by_col_num(longest, col_width, col_num):
        if len(longest) <= col_num:
            longest.append(0)
        if col_width > longest[col_num]:
            longest[col_num] = col_width

    def update_width_histograms(self, col_num, col_width):
        col_name = self.db.column_names[col_num]
        if col_name not in self.width_histograms:
            self.width_histograms[col_name] = {}
        if col_width not in self.width_histograms[col_name]:
            self.width_histograms[col_name][col_width] = 0
        self.width_histograms[col_name][col_width] += 1

    def apply_width_caps(self, longest):
        for col_name in self.max_width_by_name.keys():
            col_num = self.db.get_col_number(col_name)
            if longest[col_num] > self.max_width_by_name[col_name]:
                longest[col_num] = self.max_width_by_name[col_name]

