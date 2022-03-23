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

    # noinspection PyArgumentList
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
        # noinspection PyArgumentList
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
    Exports ice path data to a CSV file

    :param icepath_output: Data to write to the CSV file
    :param filename: The file to write the CSV data to
    :return: None
    :author: Olivia Dale
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


def raster_to_array(input_raster):
    """
    Opens the given raster file using GDAL and converts it to an array.

    :param input_raster: Path to the raster file
    :return: The raster as an array
    :author: Matthew
    """
    raster = gdal.Open(input_raster)
    band = raster.GetRasterBand(1)

    array = band.ReadAsArray()
    return array


def coordinate_to_pixel_offset(input_raster: str, x: float, y: float) -> (int, int):
    """
    Takes a coordinate and transforms it to a pixel offset within the given input raster.

    :param input_raster: The path to the raster
    :param x: The x coordinate, in the raster's CRS
    :param y: The y coordinate, in the raster's CRS
    :return: The pixel offset, as a tuple (x, y)
    :author: Matthew
    """
    raster = gdal.Open(input_raster)
    geotransform = raster.GetGeoTransform()

    origin_x = geotransform[0]
    origin_y = geotransform[3]

    pixel_width = geotransform[1]
    pixel_height = geotransform[5]

    # The xOffset variable is an integer (int()) transformation of the (x-originX)/(pixelWidth) (gives you the raster
    # index of your x coordinate)
    x_offset = int((x - origin_x) / pixel_width)
    # The yOffset variable is an integer (int()) transformation of the (y-originY)/(pixelWidth) (gives you the raster
    # index of your y coordinate)
    y_offset = int((y - origin_y) / pixel_height)
    return x_offset, y_offset


def pixel_offset_to_coordinate(input_raster: str, x_offset: int, y_offset: int) -> (float, float):
    """
    Convert a raster pixel location to a geotransformed coordinate

    :param input_raster: Path to the input raster
    :param x_offset: x pixel offset
    :param y_offset: y pixel offset
    :return: The transformed coordinate in the raster's CRS as a tuple (x, y)
    :author: Matthew
    """
    raster = gdal.Open(input_raster)
    geotransform = raster.GetGeoTransform()

    # Get the raster's origin from the geotransform elements
    origin_x = geotransform[0]
    origin_y = geotransform[3]

    # Get pixel size from the raster's geotransform
    pixel_width = geotransform[1]
    pixel_height = geotransform[5]

    coord_x = origin_x + pixel_width * x_offset
    coord_y = origin_y + pixel_height * y_offset
    return coord_x, coord_y


def create_path(cost_surface_raster: str, start_coord: (float, float), stop_coord: (float, float)):
    """
    Computes the least cost path over the given raster surface from a given start to stop coordinate

    :param cost_surface_raster: Path to the raster
    :param start_coord: The start coordinate in the raster's CRS
    :param stop_coord: The stop coordinate in the raster's CRS
    :return: A raster array showing the path
    :author: Matthew
    """
    # Load raster as an array
    cost_surface_array = raster_to_array(cost_surface_raster)

    start_x, start_y = start_coord
    start_index_x, start_index_y = coordinate_to_pixel_offset(cost_surface_raster, start_x, start_y)

    stop_x, stop_y = stop_coord
    stop_index_x, stop_index_y = coordinate_to_pixel_offset(cost_surface_raster, stop_x, stop_y)

    # A path is created using the route_through_array function from skimage using the cost array, start and stop
    # indices as inputs. Variables indices, and weight are declared from the returns from the route_through_array
    # function
    indices, weight = route_through_array(cost_surface_array, (start_index_y, start_index_x),
                                          (stop_index_y, stop_index_x), geometric=True, fully_connected=True)
    indices = np.array(indices).T

    # The below section is being used for testing creation of a coordinate list to be converted to WKT/shapefile
    # When complete. Work in progress for now. List creation works. 
    coordinate_list = []
    for offsets in indices:
        x_offset = offsets[0]
        y_offset = offsets[1]
        coordinate_list.append(pixel_offset_to_coordinate(cost_surface_raster, x_offset, y_offset))

    path = np.zeros_like(cost_surface_array)
    # Values along the path that are our LCP are declared as 255 values
    path[indices[0], indices[1]] = 255
    return path


def array_to_raster(output_path: str, original_raster: str, array) -> None:
    """
    Writes an array to the output path as a raster, using the same geo transform as the original raster

    :param output_path: Path to write the output raster
    :param original_raster: Path to the original raster
    :param array: Array to write to the output, as a raster
    :return: None
    :author: Matthew
    """
    raster = gdal.Open(original_raster)
    geotransform = raster.GetGeoTransform()

    # Get the raster's origin from the geotransform elements
    origin_x = geotransform[0]
    origin_y = geotransform[3]

    # Get pixel size from the raster's geotransform
    pixel_width = geotransform[1]
    pixel_height = geotransform[5]

    cols = array.shape[1]
    rows = array.shape[0]

    driver = gdal.GetDriverByName('GTiff')
    # Out raster created from GTiff driver, using new raster's columns, rows
    out_raster = driver.Create(output_path, cols, rows, gdal.GDT_Byte)

    out_raster.SetGeoTransform((origin_x, pixel_width, 0, origin_y, 0, pixel_height))
    outband = out_raster.GetRasterBand(1)
    outband.WriteArray(array)

    # Set the out raster's srs to be the same as the original raster's srs
    out_raster_srs = osr.SpatialReference()
    out_raster_srs.ImportFromWkt(raster.GetProjectionRef())
    out_raster.SetProjection(out_raster_srs.ExportToWkt())
    outband.FlushCache()


def lcp(surface_raster: str,
        output_raster: str, start_coordinate: (float, float), stop_coordinate: (float, float)) -> None:
    """
    Helper function to run the LCP computation

    :param surface_raster: Path to the surface cost raster
    :param output_raster:  Path to write the output path raster
    :param start_coordinate: Start coordinate in the cost raster's CRS
    :param stop_coordinate:  Stop coordinate in the cost raster's CRS
    :return: None
    :author: Matthew
    """
    cost_surface_array = raster_to_array(surface_raster)
    path_array = create_path(cost_surface_array, start_coordinate, stop_coordinate)
    array_to_raster(output_raster, surface_raster, path_array)


def clip(area_file, icechart_file, out_file):
    """
    Clips an ice chart shapefile given a shapefile for the region of interest

    :param area_file: Shapefile of the region of interest
    :param icechart_file: Shapefile of the ice chart data
    :param out_file: Path to write the clipped file to
    :return: TODO: ???
    :author: Sadaf
    """
    region = gpd.read_file(area_file)
    icechart_gdf = gpd.read_file(icechart_file)
    clipped = gpd.clip(icechart_gdf, region)
    return clipped.to_file(out_file)


def main():
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.FileHandler("run.log"), logging.StreamHandler()])

    parser = argparse.ArgumentParser(
        description="Compute possible least-cost paths for caribou across a set of sea ice chart data")

    parser.add_argument("roi", type=str, help="A vector shapefile containing a polygon of the region of interest")
    parser.add_argument("charts", nargs="+", type=str, help="One or more shapefiles containing sea ice chart data")
    args = parser.parse_args()

    # Check that all files exist before proceeding
    for chart in [args.roi] + args.charts:
        if not os.path.isfile(chart):
            logging.error(f"Shapefile \"{chart}\" does not exist, exiting.")
            exit(-1)

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

    path_array = create_path(cost_raster, start_coordinate, stop_coordinate)
    array_to_raster(output_raster, cost_raster, path_array)


if __name__ == "__main__":
    main()
