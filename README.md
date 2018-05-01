# Building TIGER 2017 Road Tiles

US Census Bureau's TIGER dataset is one of the primary nationwide geographic datasets. Roughly 10 years ago, it was imported into OpenStreetMap and huge swaths of it haven't been touched since, even though the TIGER dataset is updated yearly. Based on earlier work that OpenStreetMap US did, [Eric Fischer's TIGER2015 layer](https://github.com/ericfischer/tiger-delta) provides an overlay that helps mappers identify roads that are missing from OpenStreetMap and gives a way to find street names for roads that might not have names in OpenStreetMap.

These instructions replicate this layer with the more recent TIGER 2017 release. The TIGER dataset includes a `ROADS` and `FEATNAMES` dataset. The `ROADS` dataset includes geometries and a `linearid` that can be joined with the `linearid` in the `FEATNAMES` dataset. In `FEATNAMES` the road names are broken into several pieces, which we expand (unabbreviate) and concatenate to form a display label. Finally, the resulting joined data is built into a mbtiles file with [tippecanoe](https://github.com/mapbox/tippecanoe) and uploaded to MapBox Studio for styling.

## Running

The steps below assume you're running on an Amazon EC2 using Amazon Linux, but the concept is general enough to run wherever (including on your desktop/laptop if you have ~100GB free disk space).

### Set up instance

1. Start an EC2 instance with multiple vCPUs. I used an `m5.2xlarge`. Use Amazon Linux and set up the security group so you can SSH to the instance.

1. Attach an EBS volume. I used a 500GB size with general purpose IO and attached it to the instance that was created above.

1. SSH to the instance so we can continue configuring dependencies on it.

1. Update the instance and install the XFS tools:

   ```
   sudo yum update -y
   sudo yum install xfsprogs -y
   ```

1. Create a filesystem on the EBS volume and mount it at `/mnt`:

   ```
   sudo mkdir -p /mnt
   sudo mkfs.xfs /dev/nvme1n1
   sudo mount /dev/nvme1n1 /mnt
   sudo chown ec2-user /mnt
   ```

### Install GDAL

(Based on [this gist](https://gist.github.com/mojodna/2f596ca2fca48f08438e))

1. Update `yum` and add a 3rd party repository:

   ```
   sudo yum-config-manager --enable epel
   sudo yum -y update
   ```

1. Install build and compile dependencies:

   ```
   sudo yum -y install make automake gcc gcc-c++ libcurl-devel proj-devel geos-devel
   ```

1. Download, compile, and install the gdal source:

   ```
   cd /tmp
   curl -L http://download.osgeo.org/gdal/2.0.0/gdal-2.0.0.tar.gz | tar zxf -
   cd gdal-2.0.0/
   ./configure --prefix=/usr/local --without-python
   make -j8
   sudo make install
   ```

### Install Tippecanoe

1. Install compile dependencies:

   ```
   sudo yum install -y sqlite-devel zlib-devel
   ```
   
1. Download, compile, and install the Tippecanoe source:

   ```
   cd /tmp
   curl -L https://github.com/mapbox/tippecanoe/archive/1.27.14.tar.gz | tar zxf -
   cd tippecanoe-1.27.14/
   make -j8
   sudo make install
   ```

### Download and expand the TIGER dataset

1. Download TIGER data. `ROADS` for the geometries, `FEATNAMES` for the split-apart road names.

   ```bash
   mkdir -p /mnt/tiger/featnames
   curl -s https://www2.census.gov/geo/tiger/TIGER2017/FEATNAMES/ | \
      grep -o '<a href=['"'"'"][^"'"'"']*['"'"'"]' | \
      grep featnames | \
      sed -e 's/^<a href=["'"'"']/https:\/\/www2.census.gov\/geo\/tiger\/TIGER2017\/FEATNAMES\//' -e 's/["'"'"']$//' | \
      xargs -I {} -P 24 -n 1 sh -c 'export f={}; curl -s -o /mnt/tiger/featnames/$(basename $f) $f; echo $f'
   
   mkdir -p /mnt/tiger/roads
   curl -s https://www2.census.gov/geo/tiger/TIGER2017/ROADS/ | \
      grep -o '<a href=['"'"'"][^"'"'"']*['"'"'"]' | \
      grep roads | \
      sed -e 's/^<a href=["'"'"']/https:\/\/www2.census.gov\/geo\/tiger\/TIGER2017\/ROADS\//' -e 's/["'"'"']$//' | \
      xargs -I {} -P 24 -n 1 sh -c 'export f={}; curl -s -o /mnt/tiger/roads/$(basename $f) $f; echo $f'
   ```

2. Unzip the TIGER data into per-county directories.

   ```bash
   mkdir -p /mnt/tiger/expanded
   find /mnt/tiger/featnames -name '*.zip' -print | \
      xargs -t -L1 -P 24 -I {} /bin/sh -c 'export f={}; unzip -q $f -d /mnt/tiger/expanded/$(basename $f _featnames.zip)'
   find /mnt/tiger/roads -name '*.zip' -print | \
      xargs -t -L1 -P 24 -I {} /bin/sh -c 'export f={}; unzip -q $f -d /mnt/tiger/expanded/$(basename $f _roads.zip)'
   ```

3. Convert the `ROADS` Shapefiles and `FEATNAMES` DBF files into CSVs.

   ```bash
   find /mnt/tiger/expanded -name '*_featnames.dbf' -print0 | \
      xargs -t -0 -P 24 -Ifile ogr2ogr -f CSV file.csv file
   find /mnt/tiger/expanded -name '*_roads.shp' -print0 | \
      xargs -t -0 -P 24 -Ifile ogr2ogr -lco GEOMETRY=AS_WKT -f CSV file.csv file
   ```

4. Use the included Python script to join the `ROADS` and `FEATNAMES` data sets and expand the abbreviated road names. The resulting data will be written as newline-separated GeoJSON features.

   ```bash
   find /mnt/tiger/expanded -name '*_roads.shp' -print | \
      xargs -t -L1 -P 24 -Ifile /bin/sh -c 'f=file; d=$(dirname $f); b=$(basename $f _roads.shp) && \
      python merge_tiger_roads.py $d/${b}_roads.shp.csv $d/${b}_featnames.dbf.csv $d/$b.expanded.json'
   ```

5. Run the resulting CSV through tippecanoe to generate an mbtiles file.

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

6. Send the mbtiles file to MapBox for rendering.
