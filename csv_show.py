import collections
class CsvShow:
    def __init__(self):
        self.width_histograms = {}  # Dict of Dict  h[col_name][width]=count
        self.max_width_by_name = collections.OrderedDict()
        self.db = []
        self.has_header = True
        self.column_names = []
        self.column_numbers_by_name = collections.OrderedDict()

    def set_db(self, db):
        self.db = db
        self.set_column_names()

    def set_column_names(self):
        for row_num in range(len(self.db)):
            if row_num == 0:
                if self.has_header:
                    self.column_names = self.db[0]
                else:
                    self.column_names = [f"Col{x}" for x in range(len(self.db[0]))]
            else:
                # Handle surprise extra data (rows with more columns than expected)
                # Since we definitely don't know a header name, use "Col{x}" format.
                while len(self.column_names) < len(self.db[row_num]):
                    self.column_names.append(f"Col{len(self.column_names)}")
        for col_num in range(len(self.column_names)):
            self.column_numbers_by_name[self.column_names[col_num]] = col_num

    def format_output(self):
        output = ''
        longest = self.find_longest_column_widths()

        row_num = 0
        for row in self.db:
            if row_num > 0:
                output += "\n"
            output += self.format_row(row, longest)
            if self.has_header and row_num == 0:
                output += "\n"
                output += self.format_row(["-" * x for x in longest], longest)
            row_num += 1

        return output

    @classmethod
    def format_row(cls, row, longest):
        row_str = ""
        for col_num in range(len(row)):
            if col_num == 0:
                row_str += "|"
            width = longest[col_num]
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
        for row in self.db:
            for col_num in range(len(row)):
                col_name = self.column_names[col_num]
                col_width = len(row[col_num])
                self.update_width_histograms(col_name, col_width)

                if len(longest) <= col_num:
                    longest.append(0)
                if col_width > longest[col_num]:
                    longest[col_num] = col_width
        self.apply_width_caps(longest)
        return longest

    def update_width_histograms(self, col_name, col_width):
        if col_name not in self.width_histograms:
            self.width_histograms[col_name] = {}
        if col_width not in self.width_histograms[col_name]:
            self.width_histograms[col_name][col_width] = 0
        self.width_histograms[col_name][col_width] += 1

    def apply_width_caps(self, longest):
        for col_name in self.max_width_by_name.keys():
            col_num = self.name2column_num(col_name)
            if longest[col_num] > self.max_width_by_name[col_name]:
                longest[col_num] = self.max_width_by_name[col_name]

    def name2column_num(self, col_name):
        return self.column_numbers_by_name[col_name]


if __name__ == "__main__":
    print("Main")


