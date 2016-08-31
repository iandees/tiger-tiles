Building TIGER 2016 Road Tiles
==============================

US Census Bureau's TIGER dataset is one of the primary nationwide geographic datasets. Roughly 10 years ago, it was imported into OpenStreetMap and huge swaths of it haven't been touched since, even though the TIGER dataset is updated yearly. Based on earlier work that OpenStreetMap US did, [Eric Fischer's TIGER2015 layer](https://github.com/ericfischer/tiger-delta) provides an overlay that helps mappers identify roads that are missing from OpenStreetMap and gives a way to find street names for roads that might not have names in OpenStreetMap.

These instructions replicate this layer with the more recent TIGER 2016 release. The TIGER dataset includes a `ROADS` and `FEATNAMES` dataset. The `ROADS` dataset includes geometries and a `linearid` that can be joined with the `linearid` in the `FEATNAMES` dataset. In `FEATNAMES` the road names are broken into several pieces, which we expand (unabbreviate) and concatenate to form a display label. Finally, the resulting joined data is built into a mbtiles file with [tippecanoe]() and uploaded to MapBox Studio for styling.

1. Download TIGER data. `ROADS` for the geometries, `FEATNAMES` for the split-apart road names.

   ```bash
   wget -e robots=off --quiet --mirror --no-parent --continue http://www2.census.gov/geo/tiger/TIGER2016/FEATNAMES/
   wget -e robots=off --quiet --mirror --no-parent --continue http://www2.census.gov/geo/tiger/TIGER2016/ROADS/
   ```

2. Unzip the TIGER data 

   ```bash
   find www2.census.gov/geo/tiger/TIGER2016/ROADS/ -name '*.zip' -print | xargs -L1 -P4 unzip -q
   find www2.census.gov/geo/tiger/TIGER2016/FEATNAMES/ -name '*.zip' -print | xargs -L1 -P4 unzip -q
   ```

3. Convert the `ROADS` Shapefiles and `FEATNAMES` DBF files into CSVs.
4. Use the included Python script to join the `ROADS` and `FEATNAMES` data sets and expand the abbreviated road names. The geometries from the `ROADS` table will be encoded in Well-Known-Text format in a column of the CSV.
5. Run the resulting CSV through tippecanoe to generate an mbtiles file.
6. Send the mbtiles file to MapBox for rendering.