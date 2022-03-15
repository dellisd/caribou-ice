import os
import sys

# QGIS modules are saved under CONDA_PREFIX/Library/python
# Add this path to sys.path so that the qgis module can be loaded
sys.path.append(f"{os.environ['CONDA_PREFIX']}/Library/python")
