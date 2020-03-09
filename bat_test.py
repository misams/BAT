import functions.Material as ma
import functions.Input_File_Parser as fp

def main():
    inp_file = fp.Input_File_Parser("./template_input_file.inp")
    inp_file.print()

if __name__ == '__main__':
    main()
