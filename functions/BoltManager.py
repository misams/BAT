import csv
import os
import functions.Bolt as bolt
from pathlib import Path

class BoltManager:
    def __init__(self, db_path):
        # list of bolt-dict and washer-dict for all db-files available
        self.bolts = []
        self.washers = []
        # process files in db-dir
        self.__read_db_files(db_path)

    def __read_db_files(self, db_path):
        # db-directory
        db_dir = Path(db_path)
        # process only *.bolt files
        for f in db_dir.rglob('*.bolt'):
            print("Process bolt db-file: {0:^}".format(str(f)))
            bolt_id = ""
            bolts_per_file = {}
            # read csv 
            with open(f) as fid:
                line = fid.readline() # first line in file
                while line:
                    if line[0:7]=="BOLT_ID":
                        bolt_id = line.split('=')[1].lstrip().rstrip()
                        print("-> "+bolt_id)
                    elif line[0]=='#':
                        pass # ignore comment lines
                    else:
                        csv_row = line.strip().split(';')
                        # read all bolts of file and save it to dict
                        bolts_per_file.update( { csv_row[0] : bolt.Bolt(csv_row)} )
                    line = fid.readline()
            # save dict to list of bolt files
            self.bolts.append(bolts_per_file)
