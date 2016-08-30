Based on [Eric Fischer's TIGER2015 work](https://github.com/ericfischer/tiger-delta).

1. Download TIGER data. `ROADS` for the geometries, `FEATNAMES` for the split-apart road names.

   ```bash
   wget -e robots=off --mirror --no-parent --continue http://www2.census.gov/geo/tiger/TIGER2016/FEATNAMES/
   wget -e robots=off --mirror --no-parent --continue http://www2.census.gov/geo/tiger/TIGER2016/ROADS/
   ```

2. Unzip the TIGER data 

   ```bash
   find www2.census.gov/geo/tiger/TIGER2016/ROADS/ -name '*.zip' -print | xargs -L1 -P8 unzip -q
   find www2.census.gov/geo/tiger/TIGER2016/FEATNAMES/ -name '*.zip' -print | xargs -L1 -P8 unzip -q
   ```

3. Import data into a PostGIS database

   ```bash
   createuser -E tiger
   createdb -E utf8 -O tiger tiger
   psql -d tiger -c "CREATE EXTENSION postgis;"
   shp2pgsql -n -p tl_2016_55079_featnames.dbf featnames | psql -q -d tiger -U tiger
   for fn in *_featnames.dbf; do echo $fn; shp2pgsql -n -a $fn featnames | psql -q -d tiger -U tiger; done
   shp2pgsql -p tl_2016_55079_roads.dbf roads | psql -q -d tiger -U tiger
   for fn in *_roads.shp; do echo $fn; shp2pgsql -a $fn roads | psql -q -d tiger -U tiger; done
   ```

4. 
