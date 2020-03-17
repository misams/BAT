"""
Washer class
"""
class Washer:
    def __init__(self, splitted_row):
        self.name = ""
        # geometrical properties
        self.dmin = 0.0
        self.pmaj = 0.0
        self.h = 0.0
        # process splitted *.wshr row
        self.__csv_line_to_washer(splitted_row)

    # process csv-line out of washer database file
    def __csv_line_to_washer(self, row):
        self.name = row[0].lstrip().rstrip()
        # geometrical properties
        self.dmin = float(row[1])
        self.dmaj = float(row[2])
        self.h = float(row[3])

    # string output for print()
    def __str__(self):
        return "{0:^} dmin={1:.1f}, dmaj={2:.2f}, h={3:.3f}".format(\
            self.name, self.dmin, self.dmaj, self.h)