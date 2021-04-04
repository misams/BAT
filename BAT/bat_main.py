import os
import sys
import argparse
import logging
import configparser
from PyQt5 import QtWidgets
import src.functions.InputFileParser as fp
import src.functions.MaterialManager as mat
import src.functions.BoltManager as bm
import src.EsaPss as esapss
import src.Ecss as ecss
import src.TorqueTable as torque_table
import src.ThreadPullOut as thread_pull_out
import src.functions.exceptions as ex
import src.bat_qt_gui as bat_qt_gui

__version__ = "0.7.5-ALPHA"
"""
Change Log:
v0.7.5 - xx.xx.2021
- start work on Flange-GUI
v0.7.4 - 04.04.2021
- bolt and material info button and windows added to GUI
- Tools/Bolted Flange disabled (under development)
v0.7.3 - 30.01.2021
- MIN / MAX prevailing torque M_p added
v0.7.2 - 02.01.2021
- ECSS / ESA-PSS some bugs corrected (Mp implementation)
- ECSS: 5% embedding added
- fitting factor added (applied to loads)
- Flange-GUI-window added (dummy status)
- tests.py added (ECSS worked example 7.14 added)
- BAT User-Manual (LaTex) created
v0.7.1 - 13.09.2020
- Torque table py added
v0.7 - 08.09.2020
- Base-Class for analysis methods
- ESA-PSS converted to base-class
- ECSS-E-HB-32-23A method included (GUI updated)
v0.6 - 01.09.2020
- Save-methods finished
v0.5 - 26.07.2020
- FQ bug corrected
- Save-as method implemented
v0.4 - 10.06.2020
- pyQT5 GUI initial release
- config file: bat.ini added
v0.3.1 - 18.04.2020
- GUI development started (--gui option added to launch BAT GUI)
v0.3 - 13.04.2020
- BAT input printed to output
- error corrected if *USE_SHIM = no
v0.2 - 08.04.2020
- VDI 2230 thermal method added (takes Young's modulus temperature dependance into account)
v0.1 - April 2020
- first revision of beta software status
"""

def main():
    # get file path of bat_main.py - initial home-directory
    work_dir = os.path.dirname(os.path.realpath(__file__))
    print("BAT home directory: " + work_dir)

    # define logging config (overwrite log file 'w')
    # DEBUG, INFO, WARNING, ERROR, and CRITICAL
    log_file = work_dir+"/bat.log"
    logging.basicConfig(filename=log_file, filemode='w',
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S")
    log_header_str = "BAT run started\n#\n# Bolt Analysis Tool (BAT) Log-File\n"\
        "#\n# BAT-Version: {0:^}\n#".format(__version__)
    logging.info(log_header_str)

    # define command line argument handling
    arg_parser = argparse.ArgumentParser(description="Bolt Analysis Tool (BAT)")
    arg_parser.add_argument("-i",
        "--Input",
        type=str,
        default=work_dir+"/input_test_1.inp",
        help="define input file (default: ./input_test_1.inp)")
    arg_parser.add_argument("-o",
        "--Output",
        type=str,
        help="define output result file")
    arg_parser.add_argument("--config",
        type=str,
        default= work_dir + "/config/bat.ini",
        help="define config file (default: ./config/bat.ini)")
    arg_parser.add_argument("--gui",
        action="store_true",
        help="use BAT GUI")
    arg_parser.add_argument("--torque_table",
        action="store_true",
        help="generate torque table")
    arg_parser.add_argument("--thread_pull_out",
        action="store_true",
        help="calculate thread pull-out")
    arg_parser.add_argument("--version", 
        action="version",
        version="BAT Version: %(prog)s "+__version__)
    # parse command line arguments
    args = arg_parser.parse_args()
    # set output file default
    if args.Output:
        output_file = args.Output
    else:
        output_file = args.Input.split('.')[0]+".out"

    # EXCECUTE BAT
    try:
        #
        # read config file: bat.ini
        #
        config = configparser.ConfigParser()
        config.read_file(open(args.config, 'r'))
        print("BAT config file   : " + args.config)
        logging.info("BAT config file   : " + args.config)
        # database directory
        db_dir = config["PATHS"]["db_dir"]
        if db_dir != "DEFAULT":
            db_dir = os.path.abspath(db_dir)
        else:
            db_dir = work_dir+"/db"
        print("BAT DB directory  : " + db_dir)
        logging.info("BAT DB directory  : " + db_dir)
        # location of bat_gui.ui
        ui_file = config["PATHS"]["ui_file"]
        if ui_file != "DEFAULT":
            ui_file = os.path.abspath(ui_file)
        else:
            ui_file = work_dir+"/src/gui/bat_gui.ui"
        print("BAT GUI ui-file   : " + ui_file)
        logging.info("BAT GUI ui-file   : " + ui_file)
        # default input-file directory
        inp_dir = config["PATHS"]["inp_dir"]
        if inp_dir != "DEFAULT":
            inp_dir = os.path.abspath(inp_dir)
        else:
            inp_dir = work_dir
        print("BAT input-file directory  : " + inp_dir)
        logging.info("BAT input-file directory  : " + inp_dir)
        #
        # run BAT analysis
        #
        # print header
        print("#\n# Bolt Analysis Tool (BAT: {0:^})\n#".format(__version__))

        # read and process material-database files
        materials = mat.MaterialManager(db_dir+"/materials.mat")

        # handle bolt db files - read all available bolts and washers
        bolts = bm.BoltManager(db_dir)

        # use GUI or command-line
        if args.gui is True:
            print("BAT GUI initialized...rock it!")
            app = QtWidgets.QApplication(sys.argv)
            window = bat_qt_gui.Ui(ui_file, materials, bolts, inp_dir, __version__)
            window.show()
            sys.exit(app.exec_())
        elif args.torque_table is True:
            tb = torque_table.TorqueTable(materials, bolts)
        elif args.thread_pull_out is True:
            tpo = thread_pull_out.ThreadPullOut(materials, bolts)
        else:
            # read and process input file
            inp_file = fp.InputFileParser(args.Input, bolts)
            #inp_file.print() # debug
            #
            if inp_file.method == "ESAPSS":
                # calc ESA PSS-03-208
                ana_esapss = esapss.EsaPss(inp_file, materials, bolts, __version__)
                ana_esapss.print_results(output_file)
            elif inp_file.method == "ECSS":
                # calc ECSS-E-HB-32-23A
                ana_ecss = ecss.Ecss(inp_file, materials, bolts, __version__)
                ana_ecss.print_results(output_file)
            else:
                print("#\n# ERROR: analysis method not implemented.")
                logging.error("ERROR: analysis method not implemented.")

    # handle exceptions
    except (ex.Error, ValueError, IndexError, FileNotFoundError, KeyError) as e:
        # print successful end of BAT analysis
        print("#\n# ERROR --> go to \"bat.log\" file\n# BAT analysis terminated: " + str(e))
        logging.error("BAT run terminated due to fatal error: " + str(e))
    finally:
        # print successful end of BAT analysis
        print("#\n# END of BAT analysis")
        logging.info("BAT run successfully finished")

if __name__ == '__main__':
    main()
