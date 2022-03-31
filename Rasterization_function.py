# -*- coding: utf-8 -*-
"""
Created on Sun Mar 27 15:45:40 2022

@author: sadaf
"""

#%%
#making all necessary imports:
import os     
from osgeo import gdal
from osgeo import ogr
import tempfile
import shutil

#%%
'''
Rasterization:
Function to convert the clipped geodataframe we get from running clip() into a raster .tiff file. 
Calling the function should first ask for your working directory and then output a geotiff file of of your geodataframe and also display the raster statistics as well.
Enter Parameters as follows:
1.param input_gdf: resulting geodataframe from clip(). 
2.param output_tiff: name of the output geotiff file you want as a string. (be sure to include the .tiff extension at the end!)
3.param cellSize: whatever pixel size you want
'''
def rasterize(input_gdf, output_tiff, cellSize):
    
    #Create a temporary file to store intermediate shapefiles, geotiffs. Documentatation taken from: https://docs.python.org/3/library/tempfile.html
    #temp_file = tempfile.mkdtemp('w+b')
    
    # Define pixel_size and NoData value of new raster
    pixel_size = cellSize
    NoData_value = 0
    
    #manipulating gdf data:
    # Array with distinct values of field 'POLY_TYPE' (Classes)
    '''
    Create a new column, and set it to equivalent as CT. 
    Replacing all land concentration values to 255 to give land the highest cost.
    Code Source: https://stackoverflow.com/questions/49161120/pandas-python-set-value-of-one-column-based-on-value-in-another-column
'''
    input_gdf.loc[input_gdf['POLY_TYPE'] == 'L', 'CT'] = '255'
    
    
    #input_gdf to shapefile conversion:
    input_gdf.to_file('clipped.shp')
    #temp_file.write(shp)
    #now there is a shapefile name of clipped.shp in the temporary file
    #filename of raster tiff that will be created
    output_shp= output_tiff
    
    #open the data source/input and read in the extent
    source_ds=ogr.Open('clipped.shp')
    
    lyr=source_ds.GetLayer(0)
    inp_srs = lyr.GetSpatialRef()
    
    #Checking if shapefile was loaded properly
    if source_ds:
        lyr=source_ds.GetLayer(0)
        inp_srs = lyr.GetSpatialRef()
        print("shapefile loaded")
        print(lyr)
        print(inp_srs)
    else:
        print("couldn't load shapefile")

    
    '''
    Defining Extents
    x nd y resolutions are made based on the vector layer extents and pixel size. This is because the X,Y resolution are the spatial extent of the raster.
    idea taken from: https://howtoinqgis.wordpress.com/2017/05/13/quick-coding-tip-how-to-get-the-extent-from-a-vector-or-raster-layer-in-qgis-using-python/
'''
    
    x_min, x_max, y_min, y_max = lyr.GetExtent(0)
    print(x_min, x_max, y_min, y_max)
    x_res = int((x_max - x_min) / pixel_size)
    y_res = int((y_max - y_min) / pixel_size)
                
    '''
    #create the destination data source: output_tiff that is passed through is created first initially as an "output_ds".
    Projection, Geotiff file creation, Raster band is modified and viewed through the output_ds.
    Sources: https://gdal.org/tutorials/raster_api_tut.html
             
'''
    output_driver = gdal.GetDriverByName('GTiff') # taken from https://gdal.org/tutorials/raster_api_tut.html
    if os.path.exists(output_shp):
        output_driver.Delete(output_shp) #this will delete any existing output_shp in the directory 
    output_ds=output_driver.Create(output_shp, x_res, y_res, 1, gdal.GDT_Int16) # taken from https://gdal.org/programs/gdal_create.html.
    #output_source = out_driver.Create(output_tiff, x_res, y_res, 0, gdal.GDT_Int16)
    output_ds.SetGeoTransform((x_min, pixel_size, 0, y_max, 0, -pixel_size))
    output_ds.SetProjection(inp_srs.ExportToWkt())
    output_lyr=output_ds.GetRasterBand(1) 
    output_lyr.SetNoDataValue(NoData_value)
       
    '''Rasterization:
        passing through the template raster dataset, the raster band, vector layer and Attribute column into gdal.RasterizeLayer().
        Documentation Sources: https://gdal.org/programs/gdal_rasterize.html
                               https://www.programcreek.com/python/example/101827/gdal.RasterizeLayer
'''
    gdal.RasterizeLayer(output_ds, [1], lyr, options=["ATTRIBUTE=CT"]) 
    
    
    '''
    Viewing band statistics: 
        Majorly used for testing and comparing with the rasterized geotiff file created on ArcGIS Pro(From Progress Report 2).
        Sources: https://gis.stackexchange.com/questions/29064/how-to-get-gdal-to-create-statistics-for-gtiff-in-python
'''
    print("Raster band count:", output_ds.RasterCount)
    for band in range(output_ds.RasterCount):
        band+=1
        print("Getting band:", band) #Only one band should be returned 
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
     
    ''' Function to create a temporary directory to store files and then deletes.
    Link to source: https://stackoverflow.com/questions/13379742/right-way-to-clean-up-a-temporary-folder-in-python-class
'''
    def make_temp_directory(): #defining a function to make temporary directory
        temp_dir=tempfile.mkdtemp() #make directory
        try: 
         yield temp_dir
        finally:
            shutil.rmtree(temp_dir) #recursively deletes the directory
        
        with make_temp_directory() as tmpdirname:
           print('created temporary directory', tmpdirname)
           

    return output_shp


