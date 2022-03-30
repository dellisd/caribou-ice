# noinspection PyUnresolvedReferences
import patch_env
import pandas as pd
import shapely.geometry
import argparse
import logging
import os
import csv
from qgis.PyQt.QtXml import QDomDocument
from qgis.core import *
from skimage.graph import route_through_array
from osgeo import gdal, osr, ogr
import numpy as np
import geopandas as gpd
from glob import glob


def config_qgis() -> QgsApplication:
    """
    Initialize an instance of QGIS

    :return: Reference to the QGIS instance, to be closed later
    :author: Derek Ellis
    """
    qgs = QgsApplication([], False)

    logging.info("Initializing QGIS")
    qgs.initQgis()
    return qgs


def qgis_load_layout(path: str) -> QgsPrintLayout:
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


def apply_layer_style(layer: QgsMapLayer, style_file: str | None) -> None:
    """
    Helper function to apply a style from a qml file.
    Applies the style if the file can be loaded, or logs a warning if it can not

    :param layer: The QgsMapLayer to apply the style to.
    :param style_file: Path to the qml style file
    :return: None
    :author: Derek Ellis
    """
    if style_file is not None:
        if not os.path.isfile(style_file):
            logging.warning(f"Style file {style_file} does not exist")
        else:
            # noinspection PyArgumentList
            layer.loadNamedStyle(style_file)


def load_vector_layer(path: str, name: str, style_file: str = None) -> QgsVectorLayer:
    """
    Helper function to load a vector layer for QGIS

    :param path: Path to the vector data file to load
    :param name: The name of the layer in the QGIS project (shown on the legend)
    :param style_file: An optional path to a style file to apply to the layer
    :return: The loaded QgsVectorLayer.
    :author: Derek Ellis
    """
    v_layer = QgsVectorLayer(path, name, "ogr")
    if not v_layer.isValid():
        logging.error(f"Layer for {path} failed to load!")
    else:
        logging.info(f"Loaded Vector Layer {name}")
    apply_layer_style(v_layer, style_file)
    return v_layer


def load_raster_layer(path: str, name: str, style_file: str = None) -> QgsRasterLayer:
    """
    Helper function to load a raster layer for QGIS.

    :param path: Path to the raster data file to load
    :param name: The name of the layer in the QGIS project (shown on the legend)
    :param style_file: An optional path to a style file to apply to the layer
    :return: The loaded QgsRasterLayer.
    :author: Derek Ellis
    """
    r_layer = QgsRasterLayer(path, name, "gdal")
    if not r_layer.isValid():
        logging.error(f"Layer for {path} failed to load!")
    else:
        logging.info(f"Loaded Raster Layer {name}")
    apply_layer_style(r_layer, style_file)
    return r_layer


def bbox_vector_layer(geom: gpd.GeoDataFrame | gpd.GeoSeries, name: str, style_file: str = None) -> QgsVectorLayer:
    """
    Takes a geopandas dataframe or series and creates a QgsVectorLayer from its bounds
    Used for creating the "background" water layer in the map.

    :param geom: The geopandas dataframe or series
    :param name: Name of the layer
    :param style_file: Path to a style file for the layer
    :return: The QgsVectorLayer
    """
    layer = QgsVectorLayer(f"polygon?crs={geom.crs.to_wkt()}", name, "memory")
    # noinspection PyArgumentList
    geometry = QgsGeometry.fromWkt(shapely.geometry.box(*geom.total_bounds).wkt)

    feature = QgsFeature()
    feature.setGeometry(geometry)
    layer.dataProvider().addFeatures([feature])

    apply_layer_style(layer, style_file)
    return layer


def export_map_test(title: str, layers: [QgsMapLayer], output_path: str) -> None:
    """
    Exports a map based on the test layout template

    :param title: Title to be displayed in the exported map
    :param layers: A list of QgsMapLayer objects to be shown on the map
    :param output_path: Path to save the exported map to
    :author: Derek Ellis
    """
    # noinspection PyArgumentList
    project = QgsProject.instance()
    project.clear()
    layout = qgis_load_layout("test/test.qpt")

    extent = None
    for layer in layers:
        if layer is None:
            continue

        if extent is None:
            extent = layer.extent()
        else:
            extent.combineExtentWith(layer.extent())
        project.addMapLayer(layer)

    # Update title and map extent
    layout_title = layout.itemById("title")
    layout_title.setText(title)

    layout_map = layout.itemById("Map 1")
    layout_map.zoomToExtent(extent)

    # Set the layout picture path because it somehow loses it
    north_arrow = layout.itemById("North Arrow")
    north_arrow.setPicturePath(f"{os.environ['CONDA_PREFIX']}/Library/svg/arrows/NorthArrow_02.svg")

    # Export layout to PDF
    exporter = QgsLayoutExporter(layout)
    exporter.exportToPdf(output_path, QgsLayoutExporter.PdfExportSettings())
    logging.info(f"Exported to {output_path}")


def build_vector_line_layer(line: [(float, float)], crs: str) -> QgsVectorLayer:
    layer = QgsVectorLayer(f"linestring?crs={crs}", "Path", "memory")
    # noinspection PyArgumentList
    geometry = QgsGeometry.fromPolyline(map(lambda p: QgsPoint(p[0], p[1]), line))

    feature = QgsFeature()
    feature.setGeometry(geometry)
    layer.dataProvider().addFeatures([feature])

    return layer


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


# df['path_viability'] = df.apply(lambda row: "Yes" if row["CT"] >= 90 else "No", axis=1)


def export_file_to_csv(path_df, filename):
    """
    Exports ice path data to CSV file

    :param path_df: Data to write to the CSV file 
    :param filename: The file to write the CSV data to 
    :return: None 
    :author: Olivia Dale
    """
    header = ['chart_name', 'path_viability']
    path_df.to_csv(filename, index=False, header=header)


"""
Function(s): Calculating Least Cost Path and returning a vector line

Purpose: This function will take inputs of a cost raster based on
Canadian ice charts and  will (if possible) output a least-cost path line shapefile that can be accessed and used in 
a QGIS map layout. 

You can delete my docstring if you want Derek E!

Created on Thu Mar 10 17:46:39 2022

@author: Matthew

"""


def raster_to_array(input_raster: gdal.Dataset) -> np.ndarray:
    """
    Opens the given raster file using GDAL and converts it to an array.

    :param input_raster: the loaded raster
    :return: The raster as a numpy array
    :author: Matthew
    """
    band = input_raster.GetRasterBand(1)

    array = band.ReadAsArray()
    return array


def coordinate_to_pixel_offset(input_raster: gdal.Dataset, x: float, y: float) -> (int, int):
    """
    Takes a coordinate and transforms it to a pixel offset within the given input raster.

    :param input_raster: the input raster
    :param x: The x coordinate, in the raster's CRS
    :param y: The y coordinate, in the raster's CRS
    :return: The pixel offset, as a tuple (x, y)
    :author: Matthew
    """
    geotransform = input_raster.GetGeoTransform()

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


def pixel_offset_to_coordinate(input_raster: gdal.Dataset, x_offset: int, y_offset: int) -> (float, float):
    """
    Convert a raster pixel location to a geotransformed coordinate

    :param input_raster: the input raster
    :param x_offset: x pixel offset
    :param y_offset: y pixel offset
    :return: The transformed coordinate in the raster's CRS as a tuple (x, y)
    :author: Matthew
    """
    geotransform = input_raster.GetGeoTransform()

    # Get the raster's origin from the geotransform elements
    origin_x = geotransform[0]
    origin_y = geotransform[3]

    # Get pixel size from the raster's geotransform
    pixel_width = geotransform[1]
    pixel_height = geotransform[5]

    coord_x = origin_x + pixel_width * x_offset
    coord_y = origin_y + pixel_height * y_offset
    return coord_x, coord_y


def create_path(cost_surface_raster: gdal.Dataset,
                start_coord: (float, float), stop_coord: (float, float)) -> [(float, float)]:
    """
    Computes the least cost path over the given raster surface from a given start to stop coordinate

    :param cost_surface_raster: GDAL-loaded raster
    :param start_coord: The start coordinate in the raster's CRS
    :param stop_coord: The stop coordinate in the raster's CRS
    :return: A list of X,Y tuples for the computed path, in the raster's original CRS, or None if the path is impossible
    :author: Matthew
    """
    # Load raster as an array
    cost_surface_array = raster_to_array(cost_surface_raster)
    # Exclude / Change values of our threshold (CT Below 90) to untraversable (-1)
    cost_surface_array[cost_surface_array < 90] = -1
    # Convert CT to costs (Inverse of CT = Cost, High Concentration = Lower Cost)
    cost_surface_array[cost_surface_array == 90] = 10
    cost_surface_array[cost_surface_array == 91] = 9
    cost_surface_array[cost_surface_array == 92] = 8
    cost_surface_array[cost_surface_array == 93] = 7
    cost_surface_array[cost_surface_array == 94] = 6
    cost_surface_array[cost_surface_array == 95] = 5
    cost_surface_array[cost_surface_array == 96] = 4
    cost_surface_array[cost_surface_array == 97] = 3
    cost_surface_array[cost_surface_array == 98] = 2
    cost_surface_array[cost_surface_array == 99] = 1
    cost_surface_array[cost_surface_array == 100] = 0
    start_x, start_y = start_coord
    start_index_x, start_index_y = coordinate_to_pixel_offset(cost_surface_raster, start_x, start_y)

    stop_x, stop_y = stop_coord
    stop_index_x, stop_index_y = coordinate_to_pixel_offset(cost_surface_raster, stop_x, stop_y)

    # A path is created using the route_through_array function from skimage using the cost array, start and stop
    # indices as inputs. Variables indices, and weight are declared from the returns from the route_through_array
    # function
    try:
        indices, weight = route_through_array(cost_surface_array, (start_index_y, start_index_x),
                                              (stop_index_y, stop_index_x), geometric=True, fully_connected=True)
    except ValueError:
        return None
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
    return coordinate_list


def array_to_raster(output_path: str, original_raster: gdal.Dataset, array) -> None:
    """
    Writes an array to the output path as a raster, using the same geo transform as the original raster

    :param output_path: Path to write the output raster
    :param original_raster: Path to the original raster
    :param array: Array to write to the output, as a raster
    :return: None
    :author: Matthew
    """
    geotransform = original_raster.GetGeoTransform()

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
    out_raster_srs.ImportFromWkt(original_raster.GetProjectionRef())
    out_raster.SetProjection(out_raster_srs.ExportToWkt())
    outband.FlushCache()


def lcp(surface_raster: str, start_coordinate: (float, float),
        stop_coordinate: (float, float)) -> QgsVectorLayer | None:
    """
    Helper function to run the LCP computation

    :param surface_raster: Path to the surface cost raster
    :param start_coordinate: Start coordinate in the cost raster's CRS
    :param stop_coordinate:  Stop coordinate in the cost raster's CRS
    :return: None
    :author: Matthew
    """
    raster = gdal.Open(surface_raster)
    path_array = create_path(raster, start_coordinate, stop_coordinate)
    if path_array is None:
        return None

    return build_vector_line_layer(path_array, raster.GetProjectionRef())


def clip(area_file, icechart_file):
    """
    Clips an ice chart shapefile given a shapefile for the region of interest.
    The chart file will be clipped to the bounding box of the area file.

    :param area_file: Shapefile of the region of interest
    :param icechart_file: Shapefile of the ice chart data
    :return: The clipped geometry
    :author: Sadaf
    """
    region = gpd.read_file(area_file)
    bbox = shapely.geometry.box(*region.total_bounds)

    icechart_gdf = gpd.read_file(icechart_file)
    clipped = gpd.clip(icechart_gdf, gpd.GeoSeries([bbox]))
    return clipped


def rasterize(input_gdf: gpd.GeoDataFrame, output_tiff: str, cell_size: int) -> gdal.Dataset:
    """
    Rasterizes a given vector GeoDataFrame and writes the output to a TIFF file.
    TODO: Write files to temporary location during processing

    :param input_gdf: The GeoDataFrame to be rasterized
    :param output_tiff: The path to write the output to
    :param cell_size: The cell size of the output raster
    :return: A gdal Dataset of the output raster
    :author: Sadaf
    """
    # Define NoData value of new raster
    no_data_value = 0

    # input_gdf to shapefile conversion:
    input_gdf.to_file('clipped.shp')
    # now there is a shapefile name of clipped.shp in the wrkdir
    # filename of raster tiff that will be created
    output_shp = output_tiff

    # open the data source/input and read in the extent
    source_ds = ogr.Open('clipped.shp')
    lyr = source_ds.GetLayer(0)
    inp_srs = lyr.GetSpatialRef()
    '''
    Checking if shapefile was loaded properly
    if source_ds:
        lyr=source_ds.GetLayer(0)
        inp_srs = lyr.GetSpatialRef()
        print("shapefile loaded")
        print(lyr)
        print(inp_srs)
    else:
        print("couldn't load shapefile")
'''
    # Extents
    x_min, x_max, y_min, y_max = lyr.GetExtent(0)
    logging.debug("Extent:", x_min, x_max, y_min, y_max)
    x_res = int((x_max - x_min) / cell_size)
    y_res = int((y_max - y_min) / cell_size)

    # create the destination data source
    output_driver = gdal.GetDriverByName('GTiff')
    if os.path.exists(output_shp):
        output_driver.Delete(output_shp)
    output_ds = output_driver.Create(output_shp, x_res, y_res, 1, gdal.GDT_Int16)
    output_ds.SetGeoTransform((x_min, cell_size, 0, y_max, 0, -cell_size))
    output_ds.SetProjection(inp_srs.ExportToWkt())
    output_lyr = output_ds.GetRasterBand(1)
    output_lyr.SetNoDataValue(no_data_value)
    # Rasterization
    gdal.RasterizeLayer(output_ds, [1], lyr, options=["ATTRIBUTE=CT"])
    # Viewing Band Statistics
    logging.debug("Raster band count:", output_ds.RasterCount)
    for band in range(output_ds.RasterCount):
        band += 1
        logging.debug("Getting band:", band)
        output_ds_band = output_ds.GetRasterBand(band)
        if output_ds_band is None:
            continue
        stats = output_ds_band.GetStatistics(True, True)
        if stats is None:
            continue
        logging.debug("[ STATS ] =  Minimum=, Maximum=, Mean=, StdDev=", stats[0], stats[1], stats[2], stats[3])

    if not os.path.exists(output_shp):
        logging.error('Failed to create raster: %s' % output_shp)
    # Return
    return gdal.Open(output_shp)


def parse_arg_coord(arg: str) -> (float, float):
    """
    Parsers a coordinate given in the program arguments and returns them as a tuple of floats
    e.g. "-75.2,123", or "-54, 234". Spaces are stripped out.

    :param arg: The argument in the coordinate format
    :return: The coordinate as a float tuple.
    :author: Derek Ellis
    """
    parts = arg.split(",")
    if len(parts) != 2:
        raise SyntaxError(f"Two coordinate values expected, {len(parts)} were provided.")

    return float(parts[0].strip()), float(parts[1].strip())


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.FileHandler("run.log"), logging.StreamHandler()])

    parser = argparse.ArgumentParser(
        description="Compute possible least-cost paths for caribou across a set of sea ice chart data")

    parser.add_argument("roi", type=str, help="A vector shapefile containing a polygon of the region of interest")
    parser.add_argument("charts", nargs="+", type=str, help="One or more shapefiles containing sea ice chart data")
    parser.add_argument("--start", type=str, help="Coordinate to start the path at, as an \"X,Y\" string")
    parser.add_argument("--end", type=str, help="Coordinate to end the path at, as an \"X,Y\" string")
    parser.add_argument("--cellsize", type=str, help="Cellsize to use in the lowest cost path computation")
    args = parser.parse_args()

    if args.start is not None:
        try:
            start = parse_arg_coord(args.start)
        except ValueError:
            logging.error("Invalid start coordinate value provided")
            exit(-1)
        except SyntaxError:
            logging.error("Invalid start coordinate string provided")

    if args.end is not None:
        try:
            end = parse_arg_coord(args.start)
        except ValueError:
            logging.error("Invalid start coordinate value provided")
            exit(-1)
        except SyntaxError:
            logging.error("Invalid start coordinate string provided")

    charts = args.charts
    # Handle globbing in case the user's shell doesn't do this for them
    if len(charts) == 1 and "*" in charts[0]:
        charts = glob(charts[0])

    # Check that all files exist before proceeding
    for chart in [args.roi] + charts:
        if not os.path.isfile(chart):
            logging.error(f"Shapefile \"{chart}\" does not exist, exiting.")
            exit(-1)

    # Load QGIS
    qgs = config_qgis()
    logging.debug("QGIS started successfully")

    df = pd.DataFrame({"chart_name": [], "path_viability": []})

    for chart in charts:
        # 1. Clip chart to region of interest
        clipped = clip(args.roi, chart)
        # 2. Rasterize clipped
        chart_tiff = rasterize(clipped, f"{chart}.tiff", args.cellsize if args.cellsize else 900)
        # 3. Compute LCP, using clipped raster
        start_coordinate = (162100.17, 3162874.07)
        stop_coordinate = (245651.55, 3268528.81)
        vector = lcp(f"{chart}.tiff", start_coordinate, stop_coordinate)

        df = df.append({"chart_name": chart, "path_viability": "No" if vector is None else "Yes"}, ignore_index=True)

        # 4. Generate map
        clipped.to_file("map_tmp.shp")
        land_layer = load_vector_layer("map_tmp.shp", "Land", "test/land.qml")
        land_layer.setSubsetString("POLY_TYPE = 'L'")

        background_layer = bbox_vector_layer(clipped, "Water", "test/water.qml")

        export_map_test(chart,
                        [background_layer, load_raster_layer(f"{chart}.tiff", chart, "test/raster.qml"), land_layer,
                         vector], f"{chart}.pdf")
        # export_map_test(chart, [land_layer, vector], f"{chart}.pdf")
        # 5. Add path status (yes/no) to pandas table
        pass
    # 6. Write pandas table to csv
    export_file_to_csv(df, "report.csv")
    # 7. Print

    logging.debug("Hello World!")

    # # Test QGIS PDF export
    # logging.info("Testing QGIS PDF export")
    # qgs = config_qgis()
    # export_map_test("Hello World!", "test/GH_CIS.shp", "test/output.pdf")
    # qgs.exitQgis()
    #
    # # Test CSV export
    # logging.info("Testing CSV export")
    # export_csv([["06092021_CEXPRWA.shp", False], ["06122021_CEXPRWA.shp", True]], "test/output.csv")
    #
    # # Test clipping
    logging.info("Testing ROI clipping")
    output = clip("test/GH_CIS.shp", "test/06092021_CEXPRWA.shp")
    output.to_file("test/clipped2")
    print(output)
    #
    # # Test LCP computation
    gdal.GetDriverByName("GTiff")
    logging.info("Testing LCP computation")
    start_coordinate = (162100.17, 3162874.07)
    stop_coordinate = (245651.55, 3268528.81)
    cost_raster = os.path.abspath("test/ShouldWork.tif")

    layer = lcp(cost_raster, start_coordinate, stop_coordinate)
    export_map_test("Path!", [load_vector_layer("test/GH_CIS.shp", "ROI"), layer], "test/path.pdf")

    logging.debug("Killing QGIS")
    qgs.exitQgis()


if __name__ == "__main__":
    main()
