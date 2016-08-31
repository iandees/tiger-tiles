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

4. Add the feature name feature code tables.

   ```bash
   ## Directionals
   wget https://gist.github.com/iandees/5ec04ace6a9eb47b1ef8f7aeaa5f5bd2/raw/6d6025b73f4a670ef476515865d504c552b11742/2016_feature_name_directionals.csv
   psql -d tiger -U tiger -c "create table feature_name_directionals (direction_code varchar, expanded_full varchar, display_abbr varchar, spanish varchar, translation varchar)"
   psql -d tiger -U tiger -c "\copy feature_name_directionals FROM '2016_feature_name_directionals.csv' delimiter ',' header csv"
   psql -d tiger -U tiger -c "create index on feature_name_directionals (direction_code);"
   
   ## Qualifiers
   wget https://gist.github.com/iandees/5ec04ace6a9eb47b1ef8f7aeaa5f5bd2/raw/6d6025b73f4a670ef476515865d504c552b11742/2016_feature_name_qualifiers.csv
   psql -d tiger -U tiger -c "CREATE TABLE feature_name_qualifiers (qualifier_code varchar, expanded_full varchar, display_abbr varchar, prefix_qual varchar, suffix_qual varchar)"
   psql -d tiger -U tiger -c "\copy feature_name_qualifiers FROM '2016_feature_name_qualifiers.csv' delimiter ',' header csv"
   psql -d tiger -U tiger -c "create index on feature_name_qualifiers (qualifier_code);"
   
   ## Types
   wget https://gist.github.com/iandees/5ec04ace6a9eb47b1ef8f7aeaa5f5bd2/raw/6d6025b73f4a670ef476515865d504c552b11742/2016_feature_name_types.csv
   psql -d tiger -U tiger -c "CREATE TABLE feature_name_types (type_code varchar, expanded_full varchar, display_abbr varchar, spanish varchar, translation varchar, prefix_type varchar, suffix_type varchar)"
   psql -d tiger -U tiger -c "\copy feature_name_types FROM '2016_feature_name_types.csv' delimiter ',' header csv"
   psql -d tiger -U tiger -c "create index on feature_name_types (type_code);"
   ```

5. 
