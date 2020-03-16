"""
Bolt class
"""
class Bolt:
    def __init__(self, splitted_row):
        self.name = ""
        # geometrical properties
        self.d = 0.0 # nominal diameter
        self.p = 0.0 # pitch
        self.d2 = 0.0 # pitch diameter
        self.d3 = 0.0 # minor diameter
        self.As = 0.0 # stress cross section
        self.dh = 0.0 # min dia. under head or head diameter
        # process splitted *.bolt row
        self.__csv_line_to_bolt(splitted_row)

    # process csv-line out of bolt database file
    def __csv_line_to_bolt(self, row):
        self.name = row[0].lstrip().rstrip()
        # geometrical properties
        self.d = float(row[1])
        self.p = float(row[2])
        self.d2 = float(row[3])
        self.d3 = float(row[4])
        self.As = float(row[5])
        self.dh = float(row[6])

    # string output for print()
    def __str__(self):
        return "{0:^} d={1:.1f}, p={2:.2f}, d2={3:.3f}, d3={4:.3f}, As={5:.2f}, dh={6:.2f}".format(\
            self.name, self.d, self.p, self.d2, self.d3, self.As, self.dh)