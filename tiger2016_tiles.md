Based on [Eric Fischer's TIGER2015 work](https://github.com/ericfischer/tiger-delta).

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

3. 