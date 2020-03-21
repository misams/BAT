import csv
import functions.Material as mat
from pathlib import Path
"""
Manage all materials: bolts and clamped-parts
"""
class MaterialManager:
    def __init__(self, materials_file):
        self._mat_file = Path(materials_file)
        # clamped-parts and bolts material dict for all materials
        self.materials = self._import_mat_db()

    # import mat-file and return material-dict
    def _import_mat_db(self):
        print("Read material database file:  {0:^}".format(str(self._mat_file.absolute())))
        tmp_dict = {}
        with open(self._mat_file) as csvfile:
            readCSV = csv.reader(csvfile, delimiter=';')
            for row in readCSV:
                if row[0].strip()[0] != '#': # ignore comments
                    tmp_mat = mat.Material(row)
                    tmp_dict.update({tmp_mat.name : tmp_mat})
        return tmp_dict

    # print both material dicts
    # DEBUGGING function
    def print(self):
        print("Materials DICT:")
        print(str(self.materials))