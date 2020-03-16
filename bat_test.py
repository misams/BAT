import functions.Input_File_Parser as fp
import functions.MaterialManager as mat
import functions.BoltManager as bm

def main():
    # read and process input file
    inp_file = fp.Input_File_Parser("./template_input_file.inp")
    #inp_file.print() # debug

    # read and process material-database files
    materials = mat.MaterialManager("./db/materials_clamp.mat", "./db/materials_bolt.mat")
    #materials.print() # debug
    #bolt_mat = inp_file.bolt_material
    #print(materials.bolt_mat[bolt_mat])

    # handle bolt db files
    bolts = bm.BoltManager("./db")
    # TODO: BoltManager rework --> do not read all files everytime; select file to read!?

if __name__ == '__main__':
    main()
