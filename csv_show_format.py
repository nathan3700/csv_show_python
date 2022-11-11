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
        self.longest_by_col = []

    def set_db(self, db: CSVShowDB):
        self.db = db

    def format_output_as_string(self):
        return "\n".join(self.format_output_as_lines())

    def format_output_as_lines(self):
        output = []
        self.find_longest_column_widths()

        if self.has_header:
            output.append(self.format_row(self.db.column_names, self.longest_by_col))
            output.append(self.format_row(["-" * x for x in self.longest_by_col], self.longest_by_col))

        for row in self.db.rows:
            output.append(self.format_row(row, self.longest_by_col))
        return output

    def format_output_as_csv(self):
        output = []
        if self.has_header:
            output.append(",".join(self.db.column_names))
        for row in self.db.rows:
            output.append(",".join(row))
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
            if width > 0:
                row_str += fmt.format(item=data)
            if len(data) > width:  # Indicate truncation to the user with a "*"
                row_str += "*"
            row_str += "|"
        return row_str

    def find_longest_column_widths(self):
        self.longest_by_col = []
        rows_including_header = [self.db.column_names] + self.db.rows
        for row in rows_including_header:
            for col_num in range(len(row)):
                col_width = len(row[col_num])
                self.update_width_histograms(col_num, col_width)
                self.update_longest_by_col_num(col_num, col_width)
        self.apply_width_caps()

    def update_width_histograms(self, col_num, col_width):
        col_name = self.db.column_names[col_num]
        if col_name not in self.width_histograms:
            self.width_histograms[col_name] = {}
        if col_width not in self.width_histograms[col_name]:
            self.width_histograms[col_name][col_width] = 0
        self.width_histograms[col_name][col_width] += 1

    def update_longest_by_col_num(self, col_num, col_width):
        if len(self.longest_by_col) <= col_num:
            self.longest_by_col.append(0)
        if col_width > self.longest_by_col[col_num]:
            self.longest_by_col[col_num] = col_width

    def apply_width_caps(self):
        for col_name in self.max_width_by_name.keys():
            col_num = self.db.get_col_number(col_name)
            if self.longest_by_col[col_num] > self.max_width_by_name[col_name]:
                self.longest_by_col[col_num] = self.max_width_by_name[col_name]

