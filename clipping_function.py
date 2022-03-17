# -*- coding: utf-8 -*-
"""
Created on Sun Mar 13 20:22:16 2022

@author: sadaf
"""
#%%
#set working directories and making all necessary imports
import os
import geopandas as gpd
import pandas as pd
import fnmatch      
#%%
#This clip function will take in the parameters of the names of the study area shapefile and the icechart shapefile
def clip(area_file,icechart_file):
    wrkdir=input("enter your working directory path to the study area shapefile") #the working directories to your shapefiles will be different so just enter them as they are
    wrkdir2=input('enter your working directory path to the icechart shapefile')
    os.chdir(wrkdir)
    for area_file in os.listdir(wrkdir):
        if fnmatch.fnmatch(area_file, 'GH_CIS.shp'):
            region=gpd.read_file(area_file)
            os.chdir(wrkdir2)
    for icechart_file in os.listdir(wrkdir2):
        if icechart_file.endswith('shp'):
            icechart_gdf=gpd.read_file(icechart_file)
            clipped=gpd.clip(icechart_gdf, region)
            return clipped.to_file('clipped2') 
#the resulting clipped layer should be added to your working directory

clip('GH_CIS.shp','06092021_CEXPRWA.shp') #to call the function just enter the names of the shapefiles in quotations as parameters











