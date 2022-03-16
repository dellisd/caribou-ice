# noinspection PyUnresolvedReferences
import patch_env
import argparse
import logging
from qgis.PyQt.QtXml import QDomDocument
from qgis.core import *


def config_qgis():
    """
    Initialize an instance of QGIS

    :return: Reference to the QGIS instance, to be closed later
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


def main():
    parser = argparse.ArgumentParser(
        description="Compute possible least-cost paths for caribou across a set of sea ice chart data")

    parser.add_argument("roi", type=str, help="A vector shapefile containing a polygon of the region of interest")
    parser.add_argument("charts", nargs="+", type=str, help="One or more shapefiles containing sea ice chart data")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.FileHandler("run.log"), logging.StreamHandler()])

    logging.debug("Hello World!")

    qgs = config_qgis()
    export_map_test("Hello World!", "test/GH_CIS.shp", "test/output.pdf")
    qgs.exitQgis()


if __name__ == "__main__":
    main()
