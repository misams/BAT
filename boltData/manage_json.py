import json
import csv

def write_json_file():
    material_data = {}

    material_data['clamp'] = []
    material_data['clamp'].append({
        'name' : 'Titan',
        'rmk' : 'Ti6Al4V',
        'E' : 110000
    })

    with open('data.txt', 'w') as outfile:
        json.dump(material_data, outfile, indent=4)

def read_material_csv():
    print("Read CSV file:\n")
    with open('BAT/boltData/clamp_materials.csv') as csvfile:
        readCSV = csv.reader(csvfile, delimiter=';')
        for row in readCSV:
            print(row[0])