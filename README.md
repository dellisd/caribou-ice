# caribou-ice (GEOM 4009)

Determine whether there exists a potential path for caribou to cross sea ice.

# Running the Program

A conda environment is provided in `environment.yml`. To install the environment, run the following commands in
a `conda` shell.

```shell
conda env create -f environment.yml
conda activate caribou-ice
```

Once in the conda environment, the script can be run using the following command:

```shell
usage: ice.py [-h] [--start START] [--end END] [--cellsize CELLSIZE] [--out OUT] [--debug] roi charts [charts ...]

Compute possible least-cost paths for caribou across a set of sea ice chart data

positional arguments:
  roi                  A vector shapefile containing a polygon of the region of interest
  charts               One or more shapefiles containing sea ice chart data

options:
  -h, --help           show this help message and exit
  --start START        Coordinate to start the path at, as an "X,Y" string. Defaults to (162100.17, 3162874.07), coordinates of Gjoa Haven
  --end END            Coordinate to end the path at, as an "X,Y" string. Defaults to (245651.55, 3268528.81), coordinates of Taloyoak
  --cellsize CELLSIZE  Raster cellsize to use in the lowest cost path computation. Default is 900.
  --out OUT, -o OUT    Path to the directory to write all output files. Defaults to ./out
  --debug              Enable debug log details
```

## Examples

```shell
python ice.py test/GH_CIS.shp test/*_CEXPRWA.shp

# Will output the following files:
#   out/06092021_CEXPRWA.pdf
#   out/12092021_CEXPRWA.pdf
#   out/report.csv
```

# User Guide

## Supported Platforms

This script should work across all platforms that are supported by the dependencies listed in
the [conda environment](environment.yml) (e.g. QGIS). All the most common platforms (Windows, Linux, macOS) are
supported.

### Dependencies

The main packages used by this script are QGIS, scikit-image, numpy, gdal, and geopandas. See [environment.yml](environmeny.yml) for more detail.

## Inputs

All paths passed to the script can either be absolute or relative paths.

Multiple ice chart shapefiles can be listed when running the script, or glob syntax can be used.

```shell
# Listed separately
python ice.py region.shp 01012022_CEXPRWA.shp 01022022_CEXPRWA.shp

# Glob syntax
python ice.py region.shp *_CEXPRWA.shp
```

### Region of Interest

The script requires a region of interest defined by a shapefile. The shapefile's extent is used to clip the sea ice
chart data to the region where the LCP computation will be done. The full extent is used for clipping to ensure that all
land, ice, and water data is taken into account when determining if a path is possible.

### Ice Charts

Ice charts are read from shapefiles in the [SIGRID-3 format](https://library.wmo.int/doc_num.php?explnum_id=9270). When
analyzing potential paths across the ice, the script uses the `N_CT` field as the ice concentration measure. Currently,
areas representing sea ice (i.e. `POLY_TYPE='I'`)
with a `N_CT` value of 0.9 or higher are considered to be traversable in the LCP computation in addition to
land (`POLY_TYPE='L'`).

For the purposes of the LCP computation, all areas with `N_CT < 9.0` are made impassable and will not be considered in
the computation. The remaining ice concentrations are mapped to a cost with the following
formula: `cost = 100 - round(N_CT * 10) + 1`, i.e. a linear scaling from 1-11. All land areas are assigned an arbitrary
cost of 255 so that ice is preferred in the LCP.

The vector data is rasterized for the purposes of computing the LCP. The pixel size of the raster used for this
computation can be set using the `--cellsize` option. The default pixel size is 900. The unit of the pixel size is
dependent on the projection of the ice chart shapefile and the units that it uses.

### Start and End Coordinates

To evaluate if there is a potential path across sea ice, the script requires a start and end location to try and find a
path between. By default, the script uses the coordinates of Gjao Haven and Taloyaok as the start and end points,
respectively.

These coordinates can also be supplied to the script using the `--start` and `--end` options. These coordinates should
be provided in the `"X,Y"` format. The unit of these coordinates depends on the projection of the ice chart shapefiles.

## Outputs

The script generates a table of results based on whether a path is feasible for a given ice chart, and a separate map
for each of the provided charts. By default, these files are written to the `out/` folder in the current working
directory, however this can be overridden by specifying the `--out` or `-o` option with a path to another folder.

When the script completes, it prints the path where all files were written, and then lists each of the files that was
produced during the script's execution.

### report.csv

This output from the script is a CSV file that has two columns: `chart_name` and `path_viability`.

Each row in the table simply indicates whether a path is viable for a given chart. The `chart_name` value corresponds to
the ice chart shapefile's filename, and the `path_viability` value is either `Yes` or `No`.

### Maps

The script also outputs a set of PDF maps that show the estimated path (if one exists). The name of the chart shapefile
is included in the subtitle of the map, and if a path is infeasible the subtitle will also include "(No Path)".

The maps show the ice coverage for the region of interest. The ice is given a graduated symbology to show the
concentration of ice. The estimated path is drawn on top of the ice as a pink line.

#### Layout

The maps are exported by QGIS and the layout is defined by a QGIS layout template (`.qpt`) file. This layout can be
customized by modifying the existing layout or creating a new print layout file.

Requirements:

1. The "subtitle" text, i.e. the chart name, is displayed in a text layout item with an item ID of `date`.
2. The map is displayed in a map layout item with an item ID of `map`.
3. The layout file is located in [`resources/maplayout.qpt`](resources/maplayout.qpt).

### Logs

In addition to logging all output to the console, a `run.log` file is also created every time the script is run. By
default, all messages with a severity of `INFO` or higher (including warnings and errors) are logged. Debug logging can
be enabled by adding the `--debug` option when running the script.

## Project Structure

```
resources/       -- QGIS template and style files
test/            -- Sample Region of Interest and CIS chart shapefiles

environment.yml  -- Conda environment
ice.py           -- Main script
patch_env.py     -- Helper script
```

# FAQ

* **Where can I find sea ice chart data?**  
  Ice chart data can be obtained from
  the [Canadian Ice Service's archive](https://iceweb1.cis.ec.gc.ca/Archive/page1.xhtml) (Weekly Regional Ice Data - E00
  / ZIP).
* **What file formats are accepted for input data?**  
  This script has only been tested with Shapefiles (`.shp`), however other geospatial formats that are supported
  by [fiona](https://fiona.readthedocs.io/en/latest/) _may_ work. The ice chart data attributes _must_ follow the
  SIGRID-3 standard.
* **Is the older E00 format of ice charts supported?**  
  No, since the `AVCE00` driver is not supported by fiona.
* **Do I need to know how to code to use this script?**  
  A basic understanding of the command line can be helpful, however no coding is required to run
  the script.

# Contact

* Derek Ellis (derekellis@cmail.carleton.ca)
* Olivia Dale (oliviadale@cmail.carleton.ca)
* Matthew Wierdsma (matthewwierdsma@cmail.carleton.ca)
* Sadaf Nahyaan (sadafnahyaan@cmail.carleton.ca)

# License

```
MIT License

Copyright (c) 2022 Derek Ellis, Olivia Dale, Matthew Wierdsma, Sadaf Nahyaan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
