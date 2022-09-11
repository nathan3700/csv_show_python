class CSVShowDB:
    def __init__(self):
        self.column_names = []
        self.rows = []

    def set_column_names(self, names):
        if len(names) >= len(self.column_names):
            self.column_names = names
        else:
            self.column_names[0:len(names)] = names

    def set_column_name(self, position, name):
        if position >= len(self.column_names):
            self.generate_names_for_unnamed_columns([None] * (position + 1))
        self.column_names[position] = name

    def add_rows(self, rows):
        for row in rows:
            self.rows.append(row)

    def add_row(self, row):
        self.rows.append(row)
        self.generate_names_for_unnamed_columns(row)

    def generate_names_for_unnamed_columns(self, row):
        while len(self.column_names) < len(row):
            self.column_names.append(f"Col{len(self.column_names)}")

    def get_length(self):
        return len(self.rows)

    def get_width(self):
        return len(self.column_names)

    def lookup_item(self, item_name, criteria):
        row = self.lookup_row(criteria)
        col_num = self.get_col_number(item_name)
        return row[col_num]

    def lookup_row(self, criteria):
        # Unpack the criteria from a dictionary to these lists
        col_names = []
        col_numbers = []

        for col_name in criteria.keys():
            col_names.append(col_name)
            col_numbers.append(self.get_col_number(col_name))

        # Find the row where all match values are found
        for row_data in self.rows:
            matches_found = 0
            for x in range(len(col_names)):
                col_name = col_names[x]
                if row_data[x] == criteria[col_name]:
                    matches_found += 1
            if matches_found == len(col_names):
                return row_data
        return None

    def get_col_number(self, name):
        for i in range(len(self.column_names)):
            if self.column_names[i] == name:
                return i
        return None





