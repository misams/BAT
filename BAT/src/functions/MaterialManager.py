import csv
import src.functions.Material as mat
from pathlib import Path
import logging
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
        logging.info("Read material database file:  {0:^}".format(str(self._mat_file.absolute())))
        # read materal db-file
        tmp_dict = {}
        try:
            with open(self._mat_file) as csvfile:
                readCSV = csv.reader(csvfile, delimiter=';')
                for row in readCSV:
                    if row[0].strip()[0] != '#': # ignore comments
                        tmp_mat = mat.Material(row)
                        tmp_dict.update({tmp_mat.name : tmp_mat})
        # exception handling
        except ValueError as val_error:
            logging.error("Material database file ({0:^}) read error --> check correct syntax!\n{1:^}"\
                .format(str(self._mat_file.absolute()), str(val_error)), exc_info=True)
            raise
        except FileNotFoundError as fnf_error:
            logging.error(fnf_error, exc_info=True)
            raise
        # return tmp_dict
        return tmp_dict

    # print both material dicts
    # DEBUGGING function
    def print(self):
        print("Materials DICT:")
        print(str(self.materials))

    # get mat-file path
    @property
    def mat_file(self):
        return self._mat_file