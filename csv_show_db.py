from csv_show_shared import *
import re


class CSVShowDB:
    def __init__(self, new_db=None, column_names=[]):
        self.__curr_row = 0
        self.rows_as_records = False
        self.column_names = []
        self.column_number_by_name = {}
        self.rows = []
        self.set_column_names(column_names)
        if new_db is not None:
            self.add_rows(new_db)

    def __iter__(self):
        self.__curr_row = 0
        return self

    def __next__(self):
        if self.__curr_row >= len(self.rows):
            raise StopIteration
        row = self.get_row(self.__curr_row)
        self.__curr_row += 1
        return row

    def get_row(self, row_num):
        if self.rows_as_records:
            return self.row_to_record(self.rows[row_num])
        else:
            return self.rows[row_num]

    def set_column_names(self, names):
        for i in range(len(names)):
            self.set_column_name(i, names[i])

    def set_column_name(self, position, name):
        if position + 1 > len(self.column_names):
            self.add_unnamed_column_names(position + 1)
        self.column_names[position] = name
        self.column_number_by_name[name] = position

    def add_rows(self, rows):
        for row in rows:
            self.add_row(row.copy())

    def add_row(self, row):
        self.rows.append(row)
        if len(row) > len(self.column_names):
            self.add_unnamed_column_names(len(row))

    def add_unnamed_column_names(self, new_width):
        while len(self.column_names) < new_width:
            position = len(self.column_names)
            self.column_names.append(None)  # Placeholder to resize list.
            self.set_column_name(position, f"Col{position}")

    def insert_column(self, new_column_name, position):
        self.column_names.insert(position, None)  # Just open a gap, then set below
        self.set_column_name(position, new_column_name)
        for row in self.rows:
            row.insert(position, "")

    def insert_row(self, position, row):
        self.rows.insert(position, row)

    def update_data(self, name, value, criteria):
        col_num = self.get_col_number(name)
        rows, row_numbers = self.select_rows_and_row_numbers(criteria)
        for row_number in row_numbers:
            self.update_data_at_col_row(col_num, row_number, value)

    def update_data_at_col_row(self, col, row, value):
        self.rows[row][col] = value

    def update_data_at_row(self, name, row, value):
        col_num = self.get_col_number(name)
        self.update_data_at_col_row(col_num, row, value)

    def get_length(self):
        return len(self.rows)

    def get_width(self):
        return len(self.column_names)

    def lookup_item(self, item_name, criteria, fail_if_not_found=False):
        row = self.lookup_row(criteria)
        col_num = self.get_col_number(item_name)
        if row is None:
            if fail_if_not_found:
                raise CSVShowError("Look up criteria did not yield a match.")
            return ""
        else:
            return row[col_num]

    def lookup_row(self, criteria):
        rows, row_numbers = self.select_rows_and_row_numbers(criteria)
        if len(row_numbers) == 0:
            return None
        else:
            return self.get_row(row_numbers[0])

    def select(self, criteria):
        rows, row_numbers = self.select_rows_and_row_numbers(criteria)
        new_db = CSVShowDB(rows, self.column_names)
        return new_db

    def select_rows_and_row_numbers(self, criteria):
        # Unpack the criteria from a dictionary to these lists
        criteria_column_names = []
        criteria_col_numbers = []
        results_rows = []
        results_row_numbers = []

        for col_name in criteria.keys():
            criteria_column_names.append(col_name)
            criteria_col_numbers.append(self.get_col_number(col_name))

        # Find the row where all match values are found
        row_num = 0
        for row_data in self.rows:
            matches_found = 0
            for x in range(len(criteria_column_names)):
                col_name = criteria_column_names[x]
                regex = self.get_regex(criteria[col_name])
                if regex and re.match(regex, row_data[criteria_col_numbers[x]]):
                    matches_found += 1
                elif row_data[criteria_col_numbers[x]] == criteria[col_name]:
                    matches_found += 1
            if matches_found == len(criteria_column_names):
                results_rows.append(row_data)
                results_row_numbers.append(row_num)
            row_num += 1
        return results_rows, results_row_numbers

    @staticmethod
    def get_regex(string_input):
        for regex_delimiter in ["/", "|"]:
            if string_input[0] == regex_delimiter and string_input[len(string_input)-1] == regex_delimiter:
                return string_input[1:len(string_input)-1]
        return None

    def get_col_number(self, name):
        if name not in self.column_names:
            raise CSVShowError(f"Column name not found: {name}")
        return self.column_number_by_name[name]

    def row_to_record(self, row):
        return {key: val for key, val in zip(self.column_names, row)}

    def sort(self, sort_col_names, reverse=False):
        sort_col_nums = [self.get_col_number(name) for name in sort_col_names]

        def key_func(row):
            return RowComparable(row, sort_col_nums)
        self.rows = sorted(self.rows, reverse=reverse, key=key_func)

