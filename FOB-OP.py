import arcpy
import os
from arcpy.sa import *
from arcpy.ia import *
from arcpy.management import *
arcpy.env.addOutputsToMap = False
arcpy.env.overwriteOutput = True
import numpy as np
from tkinter import Tk
from tkinter.filedialog import askdirectory

workspace = askdirectory(title='Select Folder')
arcpy.env.workspace = workspace
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(2958)

def rescale_value(x, min_value, max_value):
    return 10 * ( (x-min_value)/(max_value-min_value))

def rescale_value_inv(x, min_value, max_value):
    return 10 - 10 * ((x - min_value) / (max_value - min_value))

def canopy_reclass(ras,weight):
    ras = Con(ras < 0, 0, ras) # Renove Negative Values
    ras = FocalStatistics(
                        in_raster=ras,
                        neighborhood="Rectangle 5 5 CELL",
                        statistics_type="PERCENTILE",
                        ignore_nodata="DATA",
                        percentile_value=10)
        #Min vertical height is the first variable atm its 5m tall, the values plateau at 15m
    GrowthFunc = TfLogisticGrowth(minimum = 5, maximum = 15, lowerThreshold =5, valueBelowThreshold =0, upperThreshold = 20,  valueAboveThreshold = 10)
    ras = RescaleByFunction(ras, GrowthFunc, 1, 10)
    ras.save("reclass_canopy.tif")
    ras_weighted = ras * weight
    return ras_weighted

def slope_reclass(ras,weight):
    SmallFunction = TfSmall(5, 5, 0, 0, 9, 0)
    ras = RescaleByFunction(ras, SmallFunction, 1, 10)
    ras.save("reclass_slope.tif")
    ras_weighted = ras * weight
    return ras_weighted

def roads_reclass(ras,weight):
    ras = Con(Raster(ras) == 1, 1, None)
    ras = DistanceAccumulation(ras, in_surface_raster = "Meaford_DSM_5m_5.tif")
    #Tflinear, Near or logistic decay would be useful for roads since we want a certain point I'll useNear
    NearFunction = TfNear(300, 0.000006, 50, 1, 600, 0)
    ras = RescaleByFunction(ras, NearFunction, 1, 10) 
    ras.save("reclass_roads.tif")
    ras_weighted = ras * weight
    return ras_weighted

def viewshed_reclass(ras,weight):
    GrowthFunc = TfLogisticGrowth(minimum = 0, maximum = 200, lowerThreshold = 0, valueBelowThreshold = 0, upperThreshold = 200,  valueAboveThreshold = 1)
    ras = RescaleByFunction(ras, GrowthFunc, 10, 1)
    ras.save("reclass_viewshed.tif")
    ras_weighted = ras * weight
    return ras_weighted

def DSM_reclass(ras,weight):
    arcpy.management.CalculateStatistics(ras)
    # Perform normalization and weighting using RescaleByFunction
    ras = rescale_value(ras, ras.minimum, ras.maximum)
    ras.save("reclass_DSM.tif")
    ras_weighted = ras * weight
    return ras_weighted

def EnemyDist_reclass(ras,weight):
    arcpy.management.CalculateStatistics(ras)
    # Perform normalization and weighting using RescaleByFunction
    ras = rescale_value(ras, ras.minimum, ras.maximum)
    ras.save("reclass_EnemyDistance.tif")
    ras_weighted = ras * weight
    return ras_weighted

def EnemyDist_inv_reclass(ras,weight):
    arcpy.management.CalculateStatistics(ras)
    # Perform normalization and weighting using RescaleByFunction
    ras = rescale_value_inv(ras, ras.minimum, ras.maximum)
    ras.save("reclass_EnemyDistance.tif")
    ras_weighted = ras * weight
    return ras_weighted

def visibility_reclass(ras,weight):
    arcpy.management.CalculateStatistics(ras)
    # Perform normalization and weighting using RescaleByFunction
    ras = rescale_value(ras, ras.minimum, ras.maximum)
    ras.save("reclass_visibility.tif")
    ras_weighted = ras * weight
    return ras_weighted

def create_mask():
    mask_raster = arcpy.Raster("Reclass_MEAF1.tif")
    mask_raster = Con(mask_raster == 1, 1, None)
    mask_raster.save("mask.tif")
    return mask_raster

def locate_points(suitability,outputName):
    print("Running Locating...")
    with arcpy.EnvManager(cellSizeProjectionMethod="CONVERT_UNITS", cellSize=suitability):
        out_raster = arcpy.sa.LocateRegions(
            in_raster=suitability,
            total_area=2000,
            area_units="SQUARE_METERS",
            number_of_regions=1,
            region_shape="CIRCLE",
            region_orientation=0,
            shape_tradeoff=80,
            evaluation_method="HIGHEST_AVERAGE_VALUE",
            minimum_area=1000,
            maximum_area=2000,
            minimum_distance=4,
            maximum_distance=None,
            distance_units="KILOMETERS",
            in_existing_regions=None,
            number_of_neighbors="EIGHT",
            no_islands="NO_ISLANDS",
            region_seeds="SMALL",
            region_resolution="LOW",
            selection_method="COMBINATORIAL"
        )
        out_raster.save(outputName)

def locate_points_OP(suitability,outputName):
    print("Running Locating...")
    with arcpy.EnvManager(cellSizeProjectionMethod="CONVERT_UNITS", cellSize=suitability):
        out_raster = arcpy.sa.LocateRegions(
            in_raster=suitability,
            total_area=500,
            area_units="SQUARE_METERS",
            number_of_regions=5,
            region_shape="CIRCLE",
            region_orientation=0,
            shape_tradeoff=80,
            evaluation_method="HIGHEST_AVERAGE_VALUE",
            minimum_area=50,
            maximum_area=100,
            minimum_distance=750,
            maximum_distance=None,
            distance_units="METERS",
            in_existing_regions=None,
            number_of_neighbors="EIGHT",
            no_islands="NO_ISLANDS",
            region_seeds="SMALL",
            region_resolution="LOW",
            selection_method="COMBINATORIAL"
        )
        out_raster.save(outputName)

def create_OP_mask(FOBlocs,res):
    mask = create_mask()
    inputFile = arcpy.sa.Con(FOBlocs != 0, FOBlocs, None)
    inputFile.save("filtered_locs.tif")
    
    arcpy.conversion.RasterToPolygon(inputFile, "FOBPolys_"+res+".shp", "SIMPLIFY", "VALUE")
    arcpy.analysis.Buffer("FOBPolys_"+res+".shp","FOBBuffer_"+res+".shp","3000 meters","FULL","ROUND","NONE")
    arcpy.conversion.PolygonToRaster("FOBBuffer_"+res+".shp","FID","FOBBuffers_"+res+".tif")
    
    FOBBuffer = arcpy.Raster("FOBBuffers_"+res+".tif")
    FOBBuffer = Con(FOBBuffer >= 0, 1, 1)
    output_mask = mask*FOBBuffer
    output_mask = Con(output_mask == 1, 1, None)
    output_mask.save("OP_mask.tif")
    return output_mask

def create_FOB_OP_points(FOBlocs,OPlocs,res):
    OPlocs = arcpy.sa.Con(OPlocs != 0, OPlocs, None)
    arcpy.conversion.RasterToPolygon(OPlocs, "OPPolys_"+res+".shp", "SIMPLIFY", "VALUE")
    arcpy.management.FeatureToPoint("OPPolys_"+res+".shp","OPPoints_"+res+".shp","INSIDE")

    FOBlocs = arcpy.sa.Con(FOBlocs != 0, FOBlocs, None)
    arcpy.conversion.RasterToPolygon(FOBlocs, "FOBPolys_"+res+".shp", "SIMPLIFY", "VALUE")
    arcpy.management.FeatureToPoint("FOBPolys_"+res+".shp","FOBPoints_"+res+".shp","INSIDE")

def locate_FOB():
    # 5m
    print("Creating 5 Meter FOB Suitability...")
    arcpy.env.cellSize = 5
    canopy = arcpy.Raster("Meaford_Canopy_5m.tif")
    slope = arcpy.Raster("DTM_Slope_5m.tif")
    roads = arcpy.Raster("Roads.tif")
    viewshed = arcpy.Raster("Viewshed V2 - 2m(Obs) - 3m(FOBheight) - 3000m(viewdist).tif")
    DSM = arcpy.Raster("Meaford_DSM_5m_5.tif")
    enemydist = arcpy.Raster("Distanc_CAF_5m.tif")

    ras_sums = canopy_reclass(canopy,21.50) + slope_reclass(slope,10.13) + roads_reclass(roads,18.4)+ viewshed_reclass(viewshed,26.52) + DSM_reclass(DSM,6.47) + EnemyDist_reclass(enemydist,16.67)
    mask = create_mask()

    
    suitability = mask*ras_sums
    suitability.save(workspace+"\\Output\\suitability_map_5m.tif")
    locate_points(suitability,workspace+"\\Output\\located_points_5m.tif")

    # 15m
    print("Creating 15 Meter FOB Suitability...")
    arcpy.env.cellSize = 15
    canopy = arcpy.Raster("Meaford_CHM_15m.tif")
    slope = arcpy.Raster("Meaford_Slope_15m.tif")
    roads = arcpy.Raster("Roads.tif")
    viewshed = arcpy.Raster("Viewshed_15m.tif")
    DSM = arcpy.Raster("Meaford_DSM_15m.tif")
    enemydist = arcpy.Raster("Distanc_CAF_5m.tif")


    ras_sums = canopy_reclass(canopy,21.50) + slope_reclass(slope,10.13) + roads_reclass(roads,18.4)+ viewshed_reclass(viewshed,26.52) + DSM_reclass(DSM,6.47) + EnemyDist_reclass(enemydist,16.67)
    mask = create_mask()

    suitability = mask*ras_sums
    suitability.save(workspace+"\\Output\\suitability_map_15m.tif")
    locate_points(suitability,workspace+"\\Output\\located_points_15m.tif")

    # 30m
    print("Creating 30 Meter FOB Suitability...")
    arcpy.env.cellSize = 30
    canopy = arcpy.Raster("Meaford_CHM_30m.tif")
    slope = arcpy.Raster("Meaford_Slope_30m.tif")
    roads = arcpy.Raster("Roads.tif")
    viewshed = arcpy.Raster("Viewshed_30m.tif")
    DSM = arcpy.Raster("Meaford_DSM_30m.tif")
    enemydist = arcpy.Raster("Distanc_CAF_5m.tif")


    ras_sums = canopy_reclass(canopy,21.50) + slope_reclass(slope,10.13) + roads_reclass(roads,18.4)+ viewshed_reclass(viewshed,26.52) + DSM_reclass(DSM,6.47) + EnemyDist_reclass(enemydist,16.67)
    mask = create_mask()

    suitability = mask*ras_sums
    suitability.save(workspace+"\\Output\\suitability_map_30m.tif")
    locate_points(suitability,workspace+"\\Output\\located_points_30m.tif")

def locate_OPs():
    # 5m
    print("Creating 5 Meter OP Suitability...")
    arcpy.env.cellSize = 5
    canopy = arcpy.Raster("Meaford_Canopy_5m.tif")
    slope = arcpy.Raster("DTM_Slope_5m.tif")
    roads = arcpy.Raster("Roads.tif")
    visibility = arcpy.Raster("Visibility Index - Visibility From.tif")
    enemydist = arcpy.Raster("Distanc_CAF_5m.tif")
    FOB_locations = arcpy.Raster(workspace+"\\Output\\located_points_5m.tif")

    ras_sums = canopy_reclass(canopy,16.11) + slope_reclass(slope,7.20) + roads_reclass(roads,14.22)+ visibility_reclass(visibility,22.56) + EnemyDist_inv_reclass(enemydist,20.47)
    OPmask = create_OP_mask(FOB_locations,"5m")

    suitability = OPmask*ras_sums
    suitability.save(workspace+"\\Output\\suitability_map_OPs_5m.tif")
    locate_points_OP(suitability,workspace+"\\Output\\located_points_OPs_5m.tif")
    OP_locations = arcpy.Raster(workspace+"\\Output\\located_points_OPs_5m.tif")
    create_FOB_OP_points(FOB_locations,OP_locations,"5m")

    # 15m
    print("Creating 15 Meter OP Suitability...")
    arcpy.env.cellSize = 15
    canopy = arcpy.Raster("Meaford_CHM_15m.tif")
    slope = arcpy.Raster("Meaford_Slope_15m.tif")
    roads = arcpy.Raster("Roads.tif")
    visibility = arcpy.Raster("Visibility_15m.tif")
    enemydist = arcpy.Raster("Distanc_CAF_5m.tif")
    FOB_locations = arcpy.Raster(workspace+"\\Output\\located_points_15m.tif")

    ras_sums = canopy_reclass(canopy,16.11) + slope_reclass(slope,7.20) + roads_reclass(roads,14.22)+ visibility_reclass(visibility,22.56) + EnemyDist_inv_reclass(enemydist,20.47)
    OPmask = create_OP_mask(FOB_locations,"15m")

    suitability = OPmask*ras_sums
    suitability.save(workspace+"\\Output\\suitability_map_OPs_15m.tif")
    locate_points_OP(suitability,workspace+"\\Output\\located_points_OPs_15m.tif")
    OP_locations = arcpy.Raster(workspace+"\\Output\\located_points_OPs_15m.tif")
    create_FOB_OP_points(FOB_locations,OP_locations,"15m")

    # 30m
    print("Creating 30 Meter OP Suitability...")
    arcpy.env.cellSize = 30
    canopy = arcpy.Raster("Meaford_CHM_30m.tif")
    slope = arcpy.Raster("Meaford_Slope_30m.tif")
    roads = arcpy.Raster("Roads.tif")
    visibility = arcpy.Raster("Visibility_30m.tif")
    enemydist = arcpy.Raster("Distanc_CAF_5m.tif")
    FOB_locations = arcpy.Raster(workspace+"\\Output\\located_points_30m.tif")

    ras_sums = canopy_reclass(canopy,16.11) + slope_reclass(slope,7.20) + roads_reclass(roads,14.22)+ visibility_reclass(visibility,22.56) + EnemyDist_inv_reclass(enemydist,20.47)
    OPmask = create_OP_mask(FOB_locations,"30m")

    suitability = OPmask*ras_sums
    suitability.save(workspace+"\\Output\\suitability_map_OPs_30m.tif")
    locate_points_OP(suitability,workspace+"\\Output\\located_points_OPs_30m.tif")
    OP_locations = arcpy.Raster(workspace+"\\Output\\located_points_OPs_30m.tif")
    create_FOB_OP_points(FOB_locations,OP_locations,"30m")

   
