import functions.InputFileParser as fp
import functions.MaterialManager as mat
import functions.BoltManager as bm
import functions.EsaPss as esapss
import os
import argparse
import logging

__version__ = "0.1(beta)"

def main():
    #TODO: Linux vs. Windows file path mess?!
    os.chdir("./BAT")

    # define logging config (overwrite log file 'w')
    # DEBUG, INFO, WARNING, ERROR, and CRITICAL
    logging.basicConfig(filename="./bat.log", filemode='w',
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S")
    logging.info("first log info message")
    logging.debug("first debug message")
    logging.critical("bla")

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

    # read and process input file
    inp_file = fp.InputFileParser(args.Input)
    #inp_file.print() # debug

    # read and process material-database files
    materials = mat.MaterialManager("./db/materials.mat")
    #bolt_mat = inp_file.bolt_material
    #print(materials.bolt_mat[bolt_mat])

    # handle bolt db files - read all available bolts and washers
    bolts = bm.BoltManager("./db")
    #print(bolts.bolts["M2"])

    # calc ESA-PSS
    ana_esapss = esapss.EsaPss(inp_file, materials, bolts)
    #ana_esapss.print_results(args.Output)

if __name__ == '__main__':
    main()
