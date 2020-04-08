import functions.InputFileParser as fp
import functions.MaterialManager as mat
import functions.BoltManager as bm
import functions.EsaPss as esapss
import functions.exceptions as ex
import os
import argparse
import logging

__version__ = "0.2(beta)"
"""
Change Log:

v0.1(beta) - April 2020
- first revision of beta software status
v0.2(beta) - 08.04.2020
- VDI 2230 thermal method added (takes Young's Modulus temperature dependance into account)
"""

def main():
    #TODO: Linux vs. Windows file path mess?!
    os.chdir("./BAT")

    # define logging config (overwrite log file 'w')
    # DEBUG, INFO, WARNING, ERROR, and CRITICAL
    logging.basicConfig(filename="./bat.log", filemode='w',
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
        default="./input_test_1.inp",
        help="define input file (default: ./input_test_1.inp)")
    arg_parser.add_argument("-o",
        "--Output",
        type=str,
        default="./output_test.out",
        help="define output result file (default: ./output_test.out)")
    arg_parser.add_argument("--version", 
        action="version",
        version="BAT Version: %(prog)s "+__version__)
    # parse command line arguments
    args = arg_parser.parse_args()

    # print header
    print("#\n# Bolt Analysis Tool (BAT: {0:^})\n#".format(__version__))

    # run BAT analysis
    try:
        # read and process input file
        inp_file = fp.InputFileParser(args.Input)
        #inp_file.print() # debug

        # read and process material-database files
        materials = mat.MaterialManager("./db/materials.mat")

        # handle bolt db files - read all available bolts and washers
        bolts = bm.BoltManager("./db")

        # calc ESA-PSS
        ana_esapss = esapss.EsaPss(inp_file, materials, bolts)
        ana_esapss.print_results(args.Output)

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
