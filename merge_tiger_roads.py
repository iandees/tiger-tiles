import unicodecsv
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('roadfile', type=argparse.FileType('r'))
parser.add_argument('featnamefile', type=argparse.FileType('r'))
parser.add_argument('outfile', type=argparse.FileType('w'), nargs='?', default=sys.stdout)
args = parser.parse_args()

with open('2016_feature_name_directionals.csv', 'r') as f:
    directionals = dict(
        (row['Direction Code'], row['Expanded Full Text'])
        for row in unicodecsv.DictReader(f)
    )

with open('2016_feature_name_qualifiers.csv', 'r') as f:
    qualifiers = dict(
        (row['Qualifier Code'], row['Expanded Full Text'])
        for row in unicodecsv.DictReader(f)
    )

with open('2016_feature_name_types.csv', 'r') as f:
    types = dict(
        (row['Type Code'], row['Expanded Full Text'])
        for row in unicodecsv.DictReader(f)
    )

featnames = dict()
for featname in unicodecsv.DictReader(args.featnamefile):
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

outcsv = unicodecsv.DictWriter(args.outfile, ['LINEARID', 'MTFCC', 'NAME_EXPANDED', 'WKT'])
for road in unicodecsv.DictReader(args.roadfile):
    linearid = road['LINEARID']
    featname = featnames.get(linearid)
    out = {
        'LINEARID': linearid,
        'WKT': road['WKT'],
    }
    if featname:
        out.update(featname)
    outcsv.writerow(out)
