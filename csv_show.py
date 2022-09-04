
class CsvShow:
    def __init__(self):
        self.db = []
        self.has_header = True

    def set_db(self, db):
        self.db = db

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
                output += "|" + "|".join(["------", "------"]) + "|"
            row_num += 1

        return output

    def find_longest_column_widths(self):
        longest = []
        for row in self.db:
            for col_num in range(len(row)):
                if len(longest) <= col_num:
                    longest.append(0)
                if len(row[col_num]) > longest[col_num]:
                    longest[col_num] = len(row[col_num])
        return longest

    @classmethod
    def format_row(cls, row, longest):
        row_str = ""
        for col_num in range(len(row)):
            if col_num == 0:
                row_str += "|"
            fmt = "{item:" + f"{longest[col_num]}" + "}"
            row_str += fmt.format(item=row[col_num])
            row_str += "|"
        return row_str

if __name__ == "__main__":
    print("Main")


