import json
import csv

with open('lists/bounty.json') as file:
    bounty_json = json.loads(file.read())
with open('bountycsv.csv', mode='w', newline='') as bounties:
    bounty_writer = csv.writer(bounties, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for item in bounty_json:
        name = item['name']
        hints = '\n'.join([hint.strip() for hint in item['hints']])
        '''for n in range(3):
            try:
                temp = hints[n]
            except IndexError:
                hints.append('')'''
        locations = '\n'.join([location for location in item["locations"]])
       # print(locations)
       #input()
        row = [item['name']]
        row.append(hints)
        row.append(locations)
        bounty_writer.writerow(row)
        #print(locations)
        #print('Current Line Being Written: ')
        #print([item["name"].strip(), hints.strip(), locations.strip()])
        #print('==================End Of Line===================')
        # input()