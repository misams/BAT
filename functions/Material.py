"""
Materials class for clamped parts and bolts
"""
class Material:
    def __init__(self, row):
        self.name = ""
        # material properties
        self.E = 0.0
        self.sig_y = 0.0
        self.sig_u = 0.0
        self.alpha = 0.0 # CTE
        self.tau_y = 0.0
        self.tau_u = 0.0
        # fill entries in Material-class
        self.__csv_line_to_material(row)

    # process csv-line out of material database file
    def __csv_line_to_material(self, row):
        self.name = row[0].lstrip().rstrip()
        # material properties
        self.E = float(row[1])
        self.sig_y = float(row[3])
        self.sig_u = float(row[2])
        self.alpha = float(row[4]) # CTE
        self.tau_y = self.sig_y*0.577
        self.tau_u = self.sig_u*0.577

    # string output for print()
    def __str__(self):
        return "{0:^}, {1:.1f}, {2:.1f}, {3:.1f}, {4:.3e}, {5:.1f}, {6:.1f}".format(\
            self.name, self.E, self.sig_y, self.sig_u, self.alpha, self.tau_y, self.tau_u)