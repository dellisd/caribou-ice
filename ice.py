# noinspection PyUnresolvedReferences
import patch_env
import argparse
import logging
import os
import csv
from qgis.PyQt.QtXml import QDomDocument
from qgis.core import *
from skimage.graph import route_through_array
from osgeo import gdal
from osgeo import osr
import numpy as np
import geopandas as gpd


def config_qgis():
    """
    Initialize an instance of QGIS

    :return: Reference to the QGIS instance, to be closed later
    :author: Derek Ellis
    """
    qgs = QgsApplication([], False)

    logging.info("Initializing QGIS")
    qgs.initQgis()
    return qgs


def qgis_load_layout(path):
    """
    Loads a QgsPrintLayout from a template file.

    :param path: Path to a .qpt file to load
    :return: A QgsPrintLayout instance loaded from the file
    :author: Derek Ellis
    """
    document = QDomDocument()
    with open(path) as f:
        document.setContent(f.read())

    layout = QgsPrintLayout(QgsProject.instance())
    layout.loadFromTemplate(document, QgsReadWriteContext())

    return layout


def export_map_test(title, data_path, output_path):
    """
    Exports a map based on the test layout template

    :param title: Title to be displayed in the exported map
    :param data_path: Path to the data to be loaded into the map
    :param output_path: Path to save the exported map to
    :author: Derek Ellis
    """
    v_layer = QgsVectorLayer(data_path, "ROI", "ogr")
    if not v_layer.isValid():
        logging.error("Layer failed to load!")
    else:
        logging.info("Loaded Vector Layer")
        QgsProject.instance().addMapLayer(v_layer)

    layout = qgis_load_layout("test/test.qpt")

    # Update title and map extent
    layout_title = layout.itemById("title")
    layout_title.setText(title)

    layout_map = layout.itemById("Map 1")
    layout_map.setExtent(v_layer.extent())

    # Export layout to PDF
    exporter = QgsLayoutExporter(layout)
    exporter.exportToPdf(output_path, QgsLayoutExporter.PdfExportSettings())
    logging.info(f"Exported to {output_path}")


def export_csv(icepath_output, filename):
    """ 
    Exports ice path data to a comma-seperated values (csv) file
    
    author: @oliviadale

    Parameters
    ----------
    icepath_output : attribute data from vector linestring

    Returns
    -------
    None.

    """
    with open(filename, 'w') as file:
        header = ['chart_name', 'date', 'path_viability', 'length']
        writer = csv.writer(file)
        writer.writerows([header] + icepath_output)
    logging.info("The file has been exported")


"""
Function(s): Calculating Least Cost Path and returning a vector line

Purpose: This function will take inputs of a cost raster based on
Canadian ice charts and  will (if possible) output a least-cost path line shapefile that can be accessed and used in 
a QGIS map layout. 

You can delete my docstring if you want Derek E!

Created on Thu Mar 10 17:46:39 2022

@author: Matthew

"""


# This sub function uses gdal's raster functionality to create an array, taking in an InputRaster as a parameter
def rasterToArray(InputRaster):
    # Local variable 'raster' is defined as an opened input raster
    raster = gdal.Open(InputRaster)
    # Variable 'band' created by querying raster for its band
    band = raster.GetRasterBand(1)
    # Variable 'array' defined as the raster band values read as an array
    array = band.ReadAsArray()
    # Sub function returns array
    return array


# This subfunction will convert an x/y coordinate using geotransforms to a raster X/Y offset for use in creating least-cost paths
def coordinateToPixelOffset(InputRaster, x, y):
    raster = gdal.Open(InputRaster)
    geotransform = raster.GetGeoTransform()

    originX = geotransform[0]
    originY = geotransform[3]

    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]

    # The xOffset variable is an integer (int()) transformation of the (x-originX)/(pixelWidth) (gives you the raster index of your x coordinate)
    xOffset = int((x - originX) / pixelWidth)
    # The yOffset variable is an integer (int()) transformation of the (y-originY)/(pixelWidth) (gives you the raster index of your y coordinate)
    yOffset = int((y - originY) / pixelHeight)
    return xOffset, yOffset


def pixelOffsetToCoordinate(InputRaster, xOffset, yOffset):
    # Declare a local raster variable by gdal reading the input raster
    raster = gdal.Open(InputRaster)
    # The geotransform variable is retrieved from the raster's information as a gdal object
    geotransform = raster.GetGeoTransform()
    # originX variable declared from 0th element on geotransform 
    originX = geotransform[0]
    # originY variable declared from the 3rd element from the geotransform 
    originY = geotransform[3]
    # The pixel width is declared using 1st geotransform element
    pixelWidth = geotransform[1]
    # Pixel height is declared using 5th geotransform element
    pixelHeight = geotransform[5]
    coordX = originX + pixelWidth * xOffset
    coordY = originY + pixelHeight * yOffset
    return coordX, coordY


# This function creates the cost surface path, taking in the cost surface raster, array, and start and stop coordinates as inputs
def createPath(costSurfaceRaster, costSurfaceArray, startCoordinate, stopCoordinate):
    # X coordinate is the 0th element of startCoordinate array (x, y)
    startCoordinateX = startCoordinate[0]
    # Y coordinate is the 1st element of startCoordinate array (x, y)
    startCoordinateY = startCoordinate[1]
    # The raster index of your start X and start Y variable (startIndexX, startIndexY) are declared together as the returned elements from coordinateToPixelOffset function
    startIndexX, startIndexY = coordinateToPixelOffset(costSurfaceRaster, startCoordinateX, startCoordinateY)
    # X coordinate is the 0th element of stopCoordinate array (x, y)
    stopCoordinateX = stopCoordinate[0]
    # Y coordinate is the 1st element of stopCoordinate array (x, y)
    stopCoordinateY = stopCoordinate[1]
    # The raster index of your start X and start Y variable (stopIndexX, stopIndexY) are declared together as the returned elements from coordinateToPixelOffset function
    stopIndexX, stopIndexY = coordinateToPixelOffset(costSurfaceRaster, stopCoordinateX, stopCoordinateY)
    # A path is created using the route_through_array function from skimage using the cost array, start and stop indices as inputs.
    # Variables indices, and weight are declared from the returns from the route_through_array function
    indices, weight = route_through_array(costSurfaceArray, (startIndexY, startIndexX), (stopIndexY, stopIndexX),
                                          geometric=True, fully_connected=True)
    # indices variable converted to a numpy array
    indices = np.array(indices).T
    # The below section is being used for testing creation of a coordinate list to be coverted to WKT/shapefile
    # When complete. Work in progress for now. List creation works. 
    coordinateList = []
    for offsets in indices:
        xOffset = offsets[0]
        yOffset = offsets[1]
        coordinateList.append(pixelOffsetToCoordinate(costSurfaceRaster, xOffset, yOffset))
        # Path is created as array using numpy
    path = np.zeros_like(costSurfaceArray)
    # Values along the path that are our LCP are declared as 255 values
    path[indices[0], indices[1]] = 255
    # Path array returned
    return path


# Definition of the arrayToRaster function, which intakes the new raster, the original cost raster (or any raster), and the path array
def arrayToRaster(newInputRaster, InputRaster, array):
    # Declares the raster variable by opening in gdal
    raster = gdal.Open(InputRaster)
    # Geotransform variable gathered again
    geotransform = raster.GetGeoTransform()
    # OriginX gathered from 0th element of geotransform again
    originX = geotransform[0]
    # OriginY gathered from 3rd element again
    originY = geotransform[3]
    # pixelWidth gathered from 1st element again
    pixelWidth = geotransform[1]
    # pixelHeght gathered from 5th element again
    pixelHeight = geotransform[5]
    # Columns declared as first element of array
    cols = array.shape[1]
    # Rows declared as 0th element of array
    rows = array.shape[0]
    # Driver variable declared as gdal's GTiff driver
    driver = gdal.GetDriverByName('GTiff')
    # Outraster variable is created from driver.Create, using new raster, columns, rows, from GDAL
    outRaster = driver.Create(newInputRaster, cols, rows, gdal.GDT_Byte)
    # OutRaster geotransform is set using paramaters 
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    # Outband is equal to the raster band of the outRaster
    outband = outRaster.GetRasterBand(1)
    # Create an array from the outraster band
    outband.WriteArray(array)
    # Outraster spatial reference retrieved using OSR
    outRasterSRS = osr.SpatialReference()
    # Outraster spatial reference imported using Well-Known Text
    outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
    # Outraster projection set as the SRS gathered above
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    # Flush cache to clean up drive
    outband.FlushCache()


def leastCostPathCalculation(costSurfaceRaster, outputRaster, startCoordinate, stopCoordinate):
    # Cost surface array gathered using raster to array function on our cost raster
    costSurfaceArray = rasterToArray(costSurfaceRaster)  # creates array from cost surface raster
    # Path array created using createPath
    pathArray = createPath(costSurfaceRaster, costSurfaceArray, startCoordinate, stopCoordinate)  # creates path array
    # Array to raster used on outputpath (where the output raster will go) and cost raster, path array
    arrayToRaster(outputRaster, costSurfaceRaster, pathArray)  # converts path array to raster


def clip(area_file, icechart_file, out_file):
    """
    Clipds an ice chart shapefile given a shapefile for the region of interest
    :author: Sadaf

    :param area_file: Shapefile of the region of interest
    :param icechart_file: Shapefile of the ice chart data
    :return:
    """
    region = gpd.read_file(area_file)
    icechart_gdf = gpd.read_file(icechart_file)
    clipped = gpd.clip(icechart_gdf, region)
    return clipped.to_file(out_file)


def main():
    parser = argparse.ArgumentParser(
        description="Compute possible least-cost paths for caribou across a set of sea ice chart data")

    parser.add_argument("roi", type=str, help="A vector shapefile containing a polygon of the region of interest")
    parser.add_argument("charts", nargs="+", type=str, help="One or more shapefiles containing sea ice chart data")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.FileHandler("run.log"), logging.StreamHandler()])

    logging.debug("Hello World!")

    # Test QGIS PDF export
    logging.info("Testing QGIS PDF export")
    qgs = config_qgis()
    export_map_test("Hello World!", "test/GH_CIS.shp", "test/output.pdf")
    qgs.exitQgis()

    # Test CSV export
    logging.info("Testing CSV export")
    export_csv([["06092021_CEXPRWA.shp", False], ["06122021_CEXPRWA.shp", True]], "test/output.csv")

    # Test clipping
    logging.info("Testing ROI clipping")
    output = clip("test/GH_CIS.shp", "test/06092021_CEXPRWA.shp", "test/clipped2")
    print(output)

    # Test LCP computation
    gdal.GetDriverByName("GTiff")
    logging.info("Testing LCP computation")
    start_coordinate = (162100.17, 3162874.07)
    stop_coordinate = (245651.55, 3268528.81)
    cost_raster = os.path.abspath("test/ShouldWork.tif")
    output_raster = "test/LeastPath.tif"

    cost_surface_array = rasterToArray(cost_raster)
    path_array = createPath(cost_raster, cost_surface_array, start_coordinate, stop_coordinate)
    arrayToRaster(output_raster, cost_raster, path_array)


if __name__ == "__main__":
    main()
