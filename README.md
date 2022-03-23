# caribou-ice (GEOM 4009)

Determine whether there exists a potential path for caribou to cross sea ice.

## Running the Program

A conda environment is provided in `environment.yml`.
To install the environment, run the following commands in a `conda` shell.

```shell
conda env create -f environment.yml
conda activate caribou-ice
```

Once in the conda environment, the script can be run using the following command:

```shell
python ice.py [roi] [charts...]
```

### Examples
```shell
python ice.py test/GH_CIS.shp test/*_CEXPRWA.shp

# Will output the following files:
#   test/06092021_CEXPRWA.shp.pdf
#   test/12092021_CEXPRWA.shp.pdf
```

## Contact
* Derek Ellis (derekellis@cmail.carleton.ca)
* Olivia Dale (oliviadale@cmail.carleton.ca)
* Matthew Wierdsma (matthewwierdsma@cmail.carleton.ca)
* Sadaf Nahyaan (sadafnahyaan@cmail.carleton.ca)
