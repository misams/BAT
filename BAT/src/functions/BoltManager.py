import csv
import os
import src.functions.Bolt as bolt
import src.functions.Washer as washer
from pathlib import Path
import logging

class BoltManager:
    def __init__(self, db_path):
        # bolt-dict and washer-dict for all bolts in db-files available
        self.bolts = {}
        self.washers = {}
        # process files in db-dir
        self._read_db_files(db_path)

    # read all *.bolt and *.wshr files in db_path and add to dict
    def _read_db_files(self, db_path):
        # db-directory
        db_dir = Path(db_path)
        print("Process database-files in  : {0:^}".format(str(db_dir.absolute())))
        # process only *.bolt files
        for f in db_dir.rglob('*.bolt'):
            logging.info("Process and add bolt db-file: {0:^}".format(str(f)))
            # read csv 
            try:
                with open(f) as fid:
                    line = fid.readline() # first line in file
                    while line:
                        if line[0:7]=="BOLT_ID":
                            logging.info(" -> " + line.split('=')[1].lstrip().rstrip())
                        elif line[0]=='#':
                            pass # ignore comment lines --> more elegant version of while/if??
                        else:
                            csv_row = line.strip().split(';')
                            # read all bolts of file and save it to dict
                            self.bolts.update( { csv_row[0] : bolt.Bolt(csv_row)} )
                        line = fid.readline()
            # exception handling
            except (ValueError, IndexError) as e:
                logging.error("Bolt database file ({0:^}) read error --> check correct syntax!\n{1:^}"\
                    .format(str(f), str(e)), exc_info=True)
                raise
            except FileNotFoundError as fnf_error:
                logging.error(fnf_error, exc_info=True)
                raise

        # process only *.wshr files
        for f in db_dir.rglob('*.wshr'):
            logging.info("Process and add washer db-file: {0:^}".format(str(f)))
            # read csv 
            try:
                with open(f) as fid:
                    line = fid.readline() # first line in file
                    while line:
                        if line[0:9]=="WASHER_ID":
                            logging.info(" -> " + line.split('=')[1].lstrip().rstrip())
                        elif line[0]=='#':
                            pass # ignore comment lines --> more elegant version of while/if??
                        else:
                            csv_row = line.strip().split(';')
                            # read all bolts of file and save it to dict
                            self.washers.update( { csv_row[0] : washer.Washer(csv_row)} )
                        line = fid.readline()
            # exception handling
            except (ValueError, IndexError) as e:
                logging.error("Washer database file ({0:^}) read error --> check correct syntax!\n{1:^}"\
                    .format(str(f), str(e)), exc_info=True)
                raise
            except FileNotFoundError as fnf_error:
                logging.error(fnf_error, exc_info=True)
                raise

    # print bolts and washers dicts
    # DEBUGGING function
    def print(self):
        for key in self.bolts:
            print(key, '->', self.bolts[key])
        for key in self.washers:
            print(key, '->', self.washers[key])