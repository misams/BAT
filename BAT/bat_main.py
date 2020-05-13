import os
import sys
import argparse
import logging
from PyQt5 import QtWidgets
import src.functions.InputFileParser as fp
import src.functions.MaterialManager as mat
import src.functions.BoltManager as bm
import src.EsaPss as esapss
import src.functions.exceptions as ex
import src.bat_qt_gui as bat_qt_gui

__version__ = "0.3(beta)"
"""
Change Log:

v0.3.1(beta) - 18.04.2020
- GUI development started (--gui option added to launch BAT GUI)
v0.3(beta) - 13.04.2020
- BAT input printed to output
- error corrected if *USE_SHIM = no
v0.2(beta) - 08.04.2020
- VDI 2230 thermal method added (takes Young's modulus temperature dependance into account)
v0.1(beta) - April 2020
- first revision of beta software status
"""

def main():
    # get file path of bat_main.py --> start here with relative file path
    work_dir = os.path.dirname(os.path.realpath(__file__))
    print("Working directory: " + work_dir)

    # define logging config (overwrite log file 'w')
    # DEBUG, INFO, WARNING, ERROR, and CRITICAL
    logging.basicConfig(filename=work_dir+"/bat.log", filemode='w',
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.DEBUG,
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
        help="define output result file (default: ./output_test.out)")
    arg_parser.add_argument("--gui",
        action="store_true",
        help="use BAT GUI")
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

    # print header
    print("#\n# Bolt Analysis Tool (BAT: {0:^})\n#".format(__version__))

    # run BAT analysis
    try:
        # read and process material-database files
        materials = mat.MaterialManager(work_dir+"/db/materials.mat")

        # handle bolt db files - read all available bolts and washers
        bolts = bm.BoltManager(work_dir+"/db")

        # use GUI or command-line
        if args.gui is True:
            print("BAT GUI initialized...rock it!")
            app = QtWidgets.QApplication(sys.argv)
            window = bat_qt_gui.Ui(materials, bolts)
            window.show()
            sys.exit(app.exec_())
        else:
            # read and process input file
            inp_file = fp.InputFileParser(args.Input)
            #inp_file.print() # debug
            #
            # calc ESA-PSS
            ana_esapss = esapss.EsaPss(inp_file, materials, bolts)
            ana_esapss.print_results(output_file)

    # handle exceptions
    except (ex.Error, ValueError, IndexError, FileNotFoundError) as e:
        # print successful end of BAT analysis
        print("#\n# ERROR --> go to \"bat.log\" file\n# BAT analysis terminated: " + str(e))
        logging.error("BAT run terminated due to fatal error: " + str(e))
    else:
        # print successful end of BAT analysis
        print("#\n# END of BAT analysis")
        logging.info("BAT run successfully finished")

if __name__ == '__main__':
    main()
