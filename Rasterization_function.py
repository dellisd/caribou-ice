# -*- coding: utf-8 -*-
"""
Created on Sun Mar 27 15:45:40 2022

@author: sadaf
"""

'''
Rasterization:
Function to convert the clipped geodataframe we get from running clip() into a raster .tiff file. Calling the function should first ask for your working directory and then output a geotiff file of of your geodataframe and also display the raster statistics as well.
Enter Parameters as follows
1.param input_gdf: resulting geodataframe from clip(). 
2.param output_tiff: name of the output geotiff file you want as a string. (be sure to include the .tiff extension at the end!)
3.param cellSize: whatever pixel size you want
'''

#%%
#making all necessary imports:
import os     
from osgeo import gdal
from osgeo import ogr
#%%
def rasterize(input_gdf, output_tiff, cellSize):
    wrkdir= input("enter you working directory") #this is where output .tiff file will be stored
    os.chdir(wrkdir)
    # Define pixel_size and NoData value of new raster
    pixel_size = cellSize
    NoData_value = 0
    
    #input_gdf to shapefile conversion:
    input_gdf.to_file('clipped.shp')
    #now there is a shapefile name of clipped.shp in the wrkdir
    #filename of raster tiff that will be created
    output_shp= output_tiff
    
    #open the data source/input and read in the extent
    source_ds=ogr.Open('clipped.shp')
    lyr=source_ds.GetLayer(0)
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
    #Extents
    x_min, x_max, y_min, y_max = lyr.GetExtent(0)
    print(x_min, x_max, y_min, y_max)
    x_res = int((x_max - x_min) / pixel_size)
    y_res = int((y_max - y_min) / pixel_size)
    
    #create the destination data source
    output_driver = gdal.GetDriverByName('GTiff')
    if os.path.exists(output_shp):
        output_driver.Delete(output_shp)
    output_ds=output_driver.Create(output_shp, x_res, y_res, 1, gdal.GDT_Int16)
    #output_source = out_driver.Create(output_tiff, x_res, y_res, 0, gdal.GDT_Int16)
    output_ds.SetGeoTransform((x_min, pixel_size, 0, y_max, 0, -pixel_size))
    output_ds.SetProjection(inp_srs.ExportToWkt())
    output_lyr=output_ds.GetRasterBand(1)
    output_lyr.SetNoDataValue(NoData_value)
    #Rasterization
    gdal.RasterizeLayer(output_ds, [1], lyr, options=["ATTRIBUTE=CT"]) 
    #Viewing Band Statistics
    print("Raster band count:", output_ds.RasterCount)
    for band in range(output_ds.RasterCount):
        band+=1
        print("Getting band:", band)
        output_ds_band=output_ds.GetRasterBand(band)
        if output_ds_band is None:
            continue
        stats=output_ds_band.GetStatistics(True, True)
        if stats is None:
            continue
        print("[ STATS ] =  Minimum=, Maximum=, Mean=, StdDev=", stats[0], stats[1], stats[2], stats[3] )
        
    
    # Save and/or close the data sources
    source_ds = None
    output_ds = None
    
    if os.path.exists(output_shp) == False:
        print('Failed to create raster: %s' % output_shp)
    # Return
    return gdal.Open(output_shp)
#%%

#Example call:
#rasterize(clipped, "tiff_file.tif" , 900)