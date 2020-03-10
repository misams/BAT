import csv
import functions.Material as mat
"""
Manage all materials: bolts and clamped-parts
"""
class MaterialManager:
    def __init__(self, cp_mat, bolt_mat):
        # clamped-parts and bolts material dict for all materials
        self.cp_mat = self.__import_mat_db(cp_mat)
        self.bolt_mat = self.__import_mat_db(bolt_mat)

    # import mat-files and return material-dict
    def __import_mat_db(self, db_file):
        print("Read material database file: {0:^}".format(db_file))
        tmp_dict = {}
        with open(db_file) as csvfile:
            readCSV = csv.reader(csvfile, delimiter=';')
            for row in readCSV:
                if row[0].strip()[0] != '#': # ignore comments
                    tmp_mat = mat.Material(row)
                    tmp_dict.update({tmp_mat.name : tmp_mat})
        return tmp_dict

    # print both material dicts
    # DEBUGGING function
    def print(self):
        print("Clamped-Parts materials DICT:")
        print(str(self.cp_mat))
        print("Bolt materials DICT:")
        print(str(self.bolt_mat))