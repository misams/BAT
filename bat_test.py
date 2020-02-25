#import boltData.manage_json as bd
from boltData.manage_json import write_json_file
import functions.material as ma

def main():
    mat = ma.Material()
    mat.select_material_db("Titan")
    print(mat)

if __name__ == '__main__':
    main()