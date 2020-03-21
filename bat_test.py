import functions.InputFileParser as fp
import functions.MaterialManager as mat
import functions.BoltManager as bm
import functions.EsaPss as esapss
import os

def main():
    #TODO: Linux vs. Windows file path mess?!
    os.chdir("./BAT")
    # read and process input file
    inp_file = fp.InputFileParser("./template_input_file.inp")
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
    ana_esapss.print_results()

if __name__ == '__main__':
    main()
