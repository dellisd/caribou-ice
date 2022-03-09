from qgis.PyQt.QtXml import QDomDocument
from qgis.core import *


def config_qgis() -> QgsApplication:
    """
    Initialize an instance of QGIS

    :return: Reference to the QGIS instance, to be closed later
    """
    qgs = QgsApplication([], False)

    print("Initializing QGIS")
    qgs.initQgis()
    return qgs


def qgis_load_layout(path: str) -> QgsPrintLayout:
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


def export_map_test(title: str, data_path: str, output_path: str) -> None:
    """
    Exports a map based on the test layout template

    :param title: Title to be displayed in the exported map
    :param data_path: Path to the data to be loaded into the map
    :param output_path: Path to save the exported map to
    """
    v_layer = QgsVectorLayer(data_path, "ROI", "ogr")
    if not v_layer.isValid():
        print("Layer failed to load!")
    else:
        print("Loaded Vector Layer")
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
    print(f"Exported to {output_path}")


def main():
    print("Hello World!")

    qgs = config_qgis()
    export_map_test("Hello World!", "test/GH_CIS.shp", "test/output.pdf")
    qgs.exitQgis()


if __name__ == "__main__":
    main()
