import json
import csv

def write_json_file( ):
    # generate json material file
    material_data = {}
    material_data['clamp'] = {}

    with open('BAT/boltData/clamp_materials.csv') as csvfile:
        readCSV = csv.reader(csvfile, delimiter=';')
        next(readCSV)
        for m in readCSV:
            material_data['clamp'].update({ m[0] : {
                'rmk' : m[1]+';'+m[2],
                'E' : float(m[3]),
                'sig_u' : float(m[4]),
                'sig_y' : float(m[5]),
                'alpha' : float(m[6])
            }})

    with open('BAT/boltData/material_data.txt', 'w') as outfile:
        json.dump(material_data, outfile, indent=4)

def read_material_csv():
    print("Read CSV file:\n")
    with open('BAT/boltData/clamp_materials.csv') as csvfile:
        readCSV = csv.reader(csvfile, delimiter=';')
        for row in readCSV:
            print(row)

def read_json():
    with open('BAT/boltData/material_data.txt') as json_file:
        data = json.load(json_file)
        for p in data['clamp']:
            print(str(p))