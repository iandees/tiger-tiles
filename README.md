# Building TIGER 2021 Road Tiles

US Census Bureau's TIGER dataset is one of the primary nationwide geographic datasets. Roughly 15 years ago, it was imported into OpenStreetMap and huge swaths of it haven't been touched since, even though the TIGER dataset is updated yearly. Based on earlier work that OpenStreetMap US did, [Erica Fischer's TIGER2015 layer](https://github.com/e-n-f/tiger-delta) provides an overlay that helps mappers identify roads that are missing from OpenStreetMap and gives a way to find street names for roads that might not have names in OpenStreetMap.

These instructions replicate this layer with the more recent TIGER 2021 release. The TIGER dataset includes a `ROADS` and `FEATNAMES` dataset. The `ROADS` dataset includes geometries and a `linearid` that can be joined with the `linearid` in the `FEATNAMES` dataset. In `FEATNAMES` the road names are broken into several pieces, which we expand (unabbreviate) and concatenate to form a display label. Finally, the resulting joined data is built into a mbtiles file with [tippecanoe](https://github.com/mapbox/tippecanoe) and uploaded to MapBox Studio for styling.

## Running

The steps below assume you're running on an Amazon EC2 using Amazon Linux, but the concept is general enough to run wherever (including on your desktop/laptop if you have ~100GB free disk space).

### Set up instance

1. Start an EC2 instance with multiple vCPUs. I used an `m6g.2xlarge`. Use Ubuntu 20.04 and set up the security group so you can SSH to the instance.

1. Increase the main partition of the instance to 500GB.

1. SSH to the instance so we can continue configuring dependencies on it.

1. Update the instance:

   ```
   sudo apt-get update && sudo apt-get upgrade -y
   ```

1. Create a space for work:

   ```
   sudo mkdir -p /mnt
   sudo chown ubuntu /mnt
   ```

### Install GDAL

1. Install build and compile dependencies:

   ```
   sudo apt-get -y install build-essential
   ```

1. Download, compile, and install the gdal source:

   ```
   cd /tmp
   curl -L http://download.osgeo.org/gdal/2.4.2/gdal-2.4.2.tar.gz | tar zxf -
   cd gdal-2.4.2/
   ./configure --prefix=/usr/local --without-python
   make -j$(nproc)
   sudo make install
   ```

### Install libgeos

1. Install build dependencies:

   ```
   sudo apt-get -y install cmake
   ```

1. Download, compile, and install the libgeos sources:

   ```
   cd /tmp
   curl -L https://github.com/libgeos/geos/archive/3.6.1.tar.gz | tar zxf -
   cd geos-3.6.1/
   mkdir build && cd build && cmake -DCMAKE_BUILD_TYPE=Release ..
   make -j$(nproc)
   sudo make install
   ```

### Install Tippecanoe

1. Install compile dependencies:

   ```
   sudo apt-get install -y libsqlite3-dev zlib1g-dev
   ```

1. Download, compile, and install the Tippecanoe source:

   ```
   cd /tmp
   curl -L https://github.com/mapbox/tippecanoe/archive/1.34.3.tar.gz | tar zxf -
   cd tippecanoe-1.34.3/
   make -j$(nproc)
   sudo make install
   ```

### Download and expand the TIGER dataset

1. Download TIGER data. `ROADS` for the geometries, `FEATNAMES` for the split-apart road names.

   ```bash
   mkdir -p /mnt/tiger/featnames
   curl -s https://www2.census.gov/geo/tiger/TIGER2021/FEATNAMES/ | \
      grep -o '<a href=['"'"'"][^"'"'"']*['"'"'"]' | \
      grep featnames | \
      sed -e 's/^<a href=["'"'"']/https:\/\/www2.census.gov\/geo\/tiger\/TIGER2021\/FEATNAMES\//' -e 's/["'"'"']$//' | \
      xargs -I {} -P 24 -n 1 sh -c 'export f={}; curl -s -o /mnt/tiger/featnames/$(basename $f) $f; echo $f'

   mkdir -p /mnt/tiger/roads
   curl -s https://www2.census.gov/geo/tiger/TIGER2021/ROADS/ | \
      grep -o '<a href=['"'"'"][^"'"'"']*['"'"'"]' | \
      grep roads | \
      sed -e 's/^<a href=["'"'"']/https:\/\/www2.census.gov\/geo\/tiger\/TIGER2021\/ROADS\//' -e 's/["'"'"']$//' | \
      xargs -I {} -P 24 -n 1 sh -c 'export f={}; curl -s -o /mnt/tiger/roads/$(basename $f) $f; echo $f'
   ```

1. Unzip the TIGER data into per-county directories.

   ```bash
   mkdir -p /mnt/tiger/expanded
   sudo apt-get install -y unzip
   find /mnt/tiger/featnames -name '*.zip' -print | \
      xargs -t -L1 -P 24 -I {} /bin/sh -c 'export f={}; unzip -q $f -d /mnt/tiger/expanded/$(basename $f _featnames.zip)'
   find /mnt/tiger/roads -name '*.zip' -print | \
      xargs -t -L1 -P 24 -I {} /bin/sh -c 'export f={}; unzip -q $f -d /mnt/tiger/expanded/$(basename $f _roads.zip)'
   ```

1. Convert the `ROADS` Shapefiles and `FEATNAMES` DBF files into CSVs.

   ```bash
   find /mnt/tiger/expanded -name '*_featnames.dbf' -print0 | \
      xargs -t -0 -P 24 -Ifile ogr2ogr -f CSV file.csv file
   find /mnt/tiger/expanded -name '*_roads.shp' -print0 | \
      xargs -t -0 -P 24 -Ifile ogr2ogr -lco GEOMETRY=AS_WKT -f CSV file.csv file
   ```

1. Use the included Python script to join the `ROADS` and `FEATNAMES` data sets and expand the abbreviated road names. The resulting data will be written as newline-separated GeoJSON features.

   ```bash
   cd /tmp
   curl -L https://github.com/iandees/tiger-tiles/archive/master.tar.gz | tar zxf -
   cd tiger-tiles-master/
   sudo apt-get install -y python3-pip
   pip3 install -r requirements.txt

   find /mnt/tiger/expanded -name '*_roads.shp' -print | \
      xargs -t -L1 -P 24 -Ifile /bin/sh -c 'f=file; d=$(dirname $f); b=$(basename $f _roads.shp) && \
      python3 merge_tiger_roads.py $d/${b}_roads.shp.csv $d/${b}_featnames.dbf.csv $d/$b.expanded.json'
   ```

1. Run the resulting CSV through tippecanoe to generate an mbtiles file.

   ```bash
   mkdir -p /mnt/tiger/tmp
   (find /mnt/tiger/expanded -type f -name '*.expanded.json' -exec cat {} \;) | \
     tippecanoe \
       --no-line-simplification \
       --buffer=0 \
       --read-parallel \
       --temporary-directory=/mnt/tiger/tmp \
       --base-zoom=12 \
       --maximum-zoom=12 \
       --minimum-zoom=12 \
       -o /mnt/tiger/tiger_roads.mbtiles
   ```

1. Save the mbtiles file to S3 so you don't have to do this again.

   ```bash
   aws s3 cp \
      --acl=public-read \
      /mnt/tiger/tiger_roads.mbtiles \
      s3://data.openstreetmap.us/tiger2021_expanded_roads.mbtiles
   ```

Once this is complete, you'll probably want to follow the instructions for [`tiger-battlegrid`](https://github.com/iandees/tiger-battlegrid).
