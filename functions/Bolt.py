import math
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
        # calculated values
        self.Ap = 0.0 # pitch cross section
        self.A1 = 0.0 # nominal cross section
        self.A3 = 0.0 # minor thread cross section
        self.slope = 0.0 # slope, phi
        # process splitted *.bolt row
        self._csv_line_to_bolt(splitted_row)

    # process csv-line out of bolt database file
    def _csv_line_to_bolt(self, row):
        try:
            self.name = row[0].lstrip().rstrip()
            # geometrical properties
            self.d = float(row[1])
            self.p = float(row[2])
            self.d2 = float(row[3])
            self.d3 = float(row[4])
            self.As = float(row[5])
            self.dh = float(row[6])
            # calculated values
            self.A1 = math.pow(self.d, 2.0)*math.pi/4.0
            self.Ap = math.pow(self.d2, 2.0)*math.pi/4.0
            self.A3 = math.pow(self.d3, 2.0)*math.pi/4.0
            self.slope = math.atan(self.p/(self.d2*math.pi)) # phi
            self.ds = math.sqrt(4*self.As/math.pi) # stress diameter
        # excepton handling - catch ValueError --> incorrect syntax in bolt db-file
        except ValueError:
            raise

    # string output for print()
    def __str__(self):
        return "{0:^} d={1:.1f}, p={2:.2f}, d2={3:.3f}, d3={4:.3f}, As={5:.2f}, dh={6:.2f}".format(\
            self.name, self.d, self.p, self.d2, self.d3, self.As, self.dh)