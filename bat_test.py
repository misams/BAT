import functions.InputFileParser as fp
import functions.MaterialManager as mat
import functions.BoltManager as bm
import functions.EsaPss as esapss

def main():
    #TODO: linux files does not work!!!
    # read and process input file
    inp_file = fp.InputFileParser("./template_input_file.inp")
    #inp_file.print() # debug

    # read and process material-database files
    materials = mat.MaterialManager("./db/materials_clamp.mat", "./db/materials_bolt.mat")
    #bolt_mat = inp_file.bolt_material
    #print(materials.bolt_mat[bolt_mat])

    # handle bolt db files - read all available bolts and washers
    bolts = bm.BoltManager("./db")
    #print(bolts.bolts["M2"])

    # calc ESA-PSS
    ana_esapss = esapss.EsaPss(inp_file, materials, bolts)

if __name__ == '__main__':
    main()
