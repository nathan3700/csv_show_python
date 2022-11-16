from csv_show_shared import *
import re


class CSVShowDB:
    def __init__(self, new_db=None, column_names=[]):
        self.num_named_columns = 0
        self.__curr_row = 0
        self.rows_as_records = False
        self.column_names = []
        self.column_number_by_name = {}
        self.rows = []
        self.set_column_names(column_names)
        if new_db is not None:
            self.add_rows(new_db)
        self.regex_flags = 0

    def __iter__(self):
        self.__curr_row = 0
        return self

    def __next__(self):
        if self.__curr_row >= len(self.rows):
            raise StopIteration
        row = self.get_row(self.__curr_row)
        self.__curr_row += 1
        return row

    def __eq__(self, other):
        return isinstance(other, CSVShowDB) and other.rows == self.rows and other.column_names == self.column_names

    def __repr__(self):
        return f"Header: {self.column_names}\nData: {self.rows}"

    def __len__(self):
        return len(self.rows)

    def clear(self):
        self.column_names.clear()
        self.rows.clear()

    def get_row(self, row_num):
        if self.rows_as_records:
            return self.row_to_record(self.rows[row_num])
        else:
            return self.rows[row_num]

    def get_row_field(self, row, field_name: str):
        col = self.get_col_number(field_name)
        return row[col]

    def set_row_field(self, row, field_name: str, value: str):
        col = self.get_col_number(field_name)
        while len(row) < col + 1:
            row.append("")
        row[col] = value

    def row_to_record(self, row):
        return {key: val for key, val in zip(self.column_names, row)}

    def set_column_names(self, names):
        self.num_named_columns = len(names)
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
        while len(row) < self.num_named_columns:
            row.append("")
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
        results_rows = []
        results_row_numbers = []

        # Find the rows where all match values are found
        row_num = 0
        for row_data in self.rows:
            matches_found = 0
            for relation in criteria:
                # Relations are of the form [name, operator, value]
                col_name = relation[0]
                col_num = self.get_col_number(col_name)
                op = relation[1]
                if op == "=":  # Be flexible and let user use = instead of ==
                    op = "=="
                value = relation[2]
                data = row_data[col_num]

                if op == "=~":
                    if re.search(value, data, flags=self.regex_flags):
                        matches_found += 1
                elif op == "!~":
                    if not re.search(value, data, flags=self.regex_flags):
                        matches_found += 1
                else:
                    if string_is_number(value) and string_is_number(data):
                        value = string_to_number(value)
                        data = string_to_number(data)
                    if eval(f"data {op} value"):
                        matches_found += 1
            if matches_found == len(criteria):
                results_rows.append(row_data)
                results_row_numbers.append(row_num)
            row_num += 1
        return results_rows, results_row_numbers

    def get_col_number(self, name: str):
        if name not in self.column_names:
            raise CSVShowError(f"Column name not found: {name}")
        return self.column_number_by_name[name]

    #  regex input can be a string,  a tuple of the form (regex, positive_match_boolean), or a list of those tuples
    #  use False in the positive_match_boolean part of the tuple to invert the match similar to grep -v
    def grep(self, regex_list, regex_flags=None):
        if regex_flags is None:
            regex_flags = self.regex_flags

        new_rows = grep_rows(self.rows, regex_list, regex_flags)
        new_db = CSVShowDB(new_rows, self.column_names)
        return new_db

    def sort(self, sort_col_names, reverse=False):
        if len(sort_col_names) == 0:
            sort_col_names = self.column_names
        sort_col_nums = [self.get_col_number(name) for name in sort_col_names]

        def key_func(row):
            return RowComparable(row, sort_col_nums)
        self.rows = sorted(self.rows, reverse=reverse, key=key_func)

    def select_columns(self, selected_columns):
        selected_column_numbers = [self.column_number_by_name[column] for column in selected_columns]
        new_rows = [self.get_row_with_columns_by_number(row, selected_column_numbers) for row in self.rows]
        return CSVShowDB(new_rows, selected_columns)

    @staticmethod
    def get_row_with_columns_by_number(row, selected_column_numbers):
        new_row = []
        for column_number in selected_column_numbers:
            new_row.append(row[column_number])
        return new_row

