import argparse
import csv
import sys
import ujson as json
from shapely import wkt
from shapely.geometry import mapping
import shapely.speedups

csv.field_size_limit(sys.maxsize)

parser = argparse.ArgumentParser()
parser.add_argument('roadfile', type=argparse.FileType('r'))
parser.add_argument('featnamefile', type=argparse.FileType('r'))
parser.add_argument('outfile', type=argparse.FileType('w'), nargs='?', default=sys.stdout)
args = parser.parse_args()

with open('expansions/directionals.csv', 'r') as f:
    directionals = dict(
        (row['Direction Code'], row['Expanded Full Text'])
        for row in csv.DictReader(f)
    )

with open('expansions/qualifiers.csv', 'r') as f:
    qualifiers = dict(
        (row['Qualifier Code'], row['Expanded Full Text'])
        for row in csv.DictReader(f)
    )

with open('expansions/types.csv', 'r') as f:
    types = dict(
        (row['Type Code'], row['Expanded Full Text'])
        for row in csv.DictReader(f)
    )

featnames = dict()
for featname in csv.DictReader(args.featnamefile):
    linearid = featname['LINEARID']
    if linearid not in featnames:
        featnames[linearid] = {
            'MTFCC': featname.get('MTFCC'),
            'NAME_EXPANDED': ' '.join(filter(None, [
                qualifiers.get(featname.get('PREQUAL')),
                directionals.get(featname.get('PREDIR')),
                types.get(featname.get('PRETYP')),
                featname.get('NAME'),
                types.get(featname.get('SUFTYP')),
                directionals.get(featname.get('SUFDIR')),
                qualifiers.get(featname.get('SUFQUAL')),
            ]))
        }

for road in csv.DictReader(args.roadfile):
    linearid = road['LINEARID']
    featname = featnames.get(linearid)
    parsed_shape = wkt.loads(road['WKT'])
    out = {
        'type': 'Feature',
        'geometry': mapping(parsed_shape),
        'properties': {
            'LINEARID': linearid,
        }
    }
    if featname:
        out['properties'].update(featname)
    args.outfile.write(json.dumps(out) + '\n')
