# caribou-ice (GEOM 4009)

Determine whether there exists a potential path for caribou to cross sea ice.

## Running the Program

A conda environment is provided in `environment.yml`. To install the environment, run the following commands in
a `conda` shell.

```shell
conda env create -f environment.yml
conda activate caribou-ice
```

Once in the conda environment, the script can be run using the following command:

```shell
usage: ice.py [-h] [--start START] [--end END] [--cellsize CELLSIZE]
              [--out OUT] [--debug]
              roi charts [charts ...]

Compute possible least-cost paths for caribou across a set of sea ice chart
data

positional arguments:
  roi                  A vector shapefile containing a polygon of the region
                       of interest
  charts               One or more shapefiles containing sea ice chart data

options:
  -h, --help           show this help message and exit
  --start START        Coordinate to start the path at, as an "X,Y" string
  --end END            Coordinate to end the path at, as an "X,Y" string
  --cellsize CELLSIZE  Raster cellsize to use in the lowest cost path
                       computation
  --out OUT, -o OUT    Path to the directory to write all output files
  --debug              Enable debug log details
```

### Examples

```shell
python ice.py test/GH_CIS.shp test/*_CEXPRWA.shp

# Will output the following files:
#   out/06092021_CEXPRWA.pdf
#   out/12092021_CEXPRWA.pdf
#   out/report.csv
```

## Contact

* Derek Ellis (derekellis@cmail.carleton.ca)
* Olivia Dale (oliviadale@cmail.carleton.ca)
* Matthew Wierdsma (matthewwierdsma@cmail.carleton.ca)
* Sadaf Nahyaan (sadafnahyaan@cmail.carleton.ca)
