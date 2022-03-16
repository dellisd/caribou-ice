# -*- coding: utf-8 -*-
"""
Created on Wed Mar 16 19:51:32 2022

@author: sadaf
"""

#%%
import os
wrkdir= input("enter your working directory")
from osgeo import gdal
from osgeo import ogr
os.chdir(wrkdir)


#For now Thus part not in function. I'll make it into a function later
fn_ras = input("enter your path to the raster file")  #path to the raster file. 
fn_vec = input("Enter your path to the CLIPPED Vector shapefile") #path to the vector file
 
ras_ds = gdal.Open(fn_ras)

vec_ds = ogr.Open(fn_vec) #this is the vector dataset opened

lyr = vec_ds.GetLayer() 
inGridSize=float(2/110575) #converting to 2 meters gridsize since its in GCS coordinates (vector layer)
#type(inGridSize)) #type returns a float

#destination source file:
xMin, xMax, yMin, yMax = lyr.GetExtent()
xRes= int((xMax - xMin) / inGridSize)
yRes = int((yMax - yMin) / inGridSize) #all this works upto here.

#%% This creates template raster using the bounding box of the vector shapefile.
rasterDS = gdal.GetDriverByName('GTiff').Create(fn_ras, ras_ds .RasterXSize, ras_ds .RasterYSize, 1, gdal.GDT_Float32) 

#transforming to the vector coordinate system
geot=rasterDS.GetGeoTransform()
rasterDS=rasterDS.SetGeoTransform(geot)

#%%
#Over here dealing with empty values and setting them to 0
rBand = rasterDS.GetRasterBand(1)
rBand=rBand.SetNoDataValue(0.0)
rBand=rBand.Fill(0.0)

#define spatial reference
#rasterDS.SetProjection(lyr.GetSpatialRef().ExportToWkt())

#%%
rasterized_data=gdal.RasterizeLayer(rasterDS, [1], lyr, options=['ATTRIBUTE=CT']) #This is the main function where we pass the template raster, vector layer to burn, band number and column which we are rasterizing. 
rasterized_data=rasterDS.GetRasterBand(1).SetNoDataValue(0.0)
rasterDs= None