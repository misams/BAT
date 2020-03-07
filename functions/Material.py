import csv

"""
Materials class for clamped parts and bolts
"""
class Material:
    def __init__(self):
        self.name = ""
        # material properties
        self.E = 0.0
        self.sig_y = 0.0
        self.sig_u = 0.0
        self.alpha = 0.0 # CTE
        self.tau_y = 0.0
        self.tau_u = 0.0

    # read CSV DB file and select material
    def select_material_db(self, mat_sel):
        print("Read CSV file:\n")
        with open('BAT/boltData/clamp_materials.csv') as csvfile:
            readCSV = csv.reader(csvfile, delimiter=';')
            for row in readCSV:
                if row[0]==mat_sel:
                    # set material class with selected data out of db
                    self.csv_line_to_material(row)
                    break

    def csv_line_to_material(self, row):
        self.name = row[0]
        # material properties
        self.E = float(row[3])
        self.sig_y = float(row[5])
        self.sig_u = float(row[4])
        self.alpha = float(row[6]) # CTE
        self.tau_y = self.sig_y*0.577
        self.tau_u = self.sig_u*0.577
        print(str(self.name))

    def __str__(self):
        return "{0:^}: {1:.1f}".format(self.name, self.E)

