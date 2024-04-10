import arcpy, time, math
from pathlib import Path
from arcpy import Raster, sa, intelligence, FeatureSet
from tkinter.filedialog import askdirectory

workspace = askdirectory(title='Select Folder')
arcpy.env.workspace = workspace

# Setup Environment
tempdir = workspace
outdir = workspace + "\\Output\\"
arcpy.CheckOutExtension("Spatial")
print("Make sure the current path is the path you are executing the script from in console")
print("Current Path: " + str(Path.cwd()))
print("Make sure the python exe you are excuting with is from arcgis")
print(r"E.g. \"c:/Program Files/ArcGIS/Pro/bin/Python/envs/arcgispro-py3/python.exe\" smugglers-path.py" + "\n")
arcpy.env.overwriteOutput = True

def create_smugglers_path(outputFilename, 
                          VISfilename, #Must be Visibility To
                          SLOPEfilename, #Must be a raster with values between 0-100 (slope %)
                          LAKEfilename, #Must be a binary raster
                          WETLANDfilename, #Must be a binary raster
                          RIVERfilename,  #Must be a binary raster
                          STARTfilename, #Must be a shapefile with point features
                          ENDfilename,  #Must be a shapefile with point features
                          FORESTfilename, #Must be a raster with values between 0-100 (forest cover %)
                          clean=True, 
                          saveTempFiles = True):

    start_t = time.time()
    print("[X] Starting Smuggler's Path Calculation")
    print("[*] Removing NULL values from rasters")
    VISr = sa.Con(sa.IsNull(VISfilename),1,VISfilename)
    SLOPEr = sa.Con(sa.IsNull(SLOPEfilename),0,SLOPEfilename)
    LAKEr = sa.Con(sa.IsNull(LAKEfilename),0,LAKEfilename)
    WETLANDr = sa.Con(sa.IsNull(WETLANDfilename),0,WETLANDfilename)
    RIVERr = sa.Con(sa.IsNull(RIVERfilename),0,RIVERfilename)
    FORESTr = sa.Con(sa.IsNull(FORESTfilename),0,FORESTfilename)
    STARTv = FeatureSet(STARTfilename)
    ENDv = FeatureSet(ENDfilename)
                                        
    # Rescale VIS exponentially (Lower Visibility >> Higher Visibility)
    vis_rescale = ((0.2*math.e ** (4 * VISr))-0.2)
    print("[*] Rescaled Visibility Raster")
    cost_raster_i = ((SLOPEr / 200) + # Add Slope (10% Slope -> 0.05)
        sa.Con(FORESTr > 10, vis_rescale/FORESTr,vis_rescale) + # Add Rescaled Visibility, if Covered by >10% forest then visibility is divided by forest density
        sa.Con((WETLANDr + RIVERr) >= 1, 0.16, 0) + LAKEr) # If wetland or lake add 0.16 (allows for crossing of these areas but avoids going directly along)
    cost_raster = sa.Con(cost_raster_i > 1, 1, cost_raster_i) # Rescale all values between 0 and 1
    print("[*] Created Cost Raster")
    if(saveTempFiles):
        cost_raster.save(tempdir+"cost-raster.tif")
        print("[S] Saved Cost Raster")

    # Create Barrier Raster for LCP
    # Slope > 30% or Lakes are Barriers
    barrier_raster_i = sa.Con(sa.Con(SLOPEr > 30, 1, 0) + LAKEr >= 1, 0, -1)
    barrier_raster = sa.SetNull(barrier_raster_i,barrier_raster_i,"VALUE < 0")
    print("[*] Created Barrier Raster")
    if(saveTempFiles):
        barrier_raster.save(tempdir+"barrier-raster.tif")
        print("[S] Saved Barrier Raster")


    # Create Distance Accumulation and Back Cost Rasters
    distance_raster = sa.DistanceAccumulation(STARTv, barrier_raster,
                            in_cost_raster=cost_raster,
                            out_back_direction_raster=tempdir+"back-dir-raster.tif")
    print("[*] Distance Accumulation Raster Created")
    print("[*] Back Direction Raster Created")
    print("[S] Saved Back Direction Raster")
    if(saveTempFiles):
        distance_raster.save(tempdir+"dist-raster.tif")
        print("[S] Saved Distance Accumulation Raster")

    #Create LCPs
    sa.OptimalPathAsLine(ENDv,distance_raster,tempdir+"back-dir-raster.tif",outdir+outputFilename,path_type="EACH_CELL")
    print("[*] Least Cost Pathways Created")
    print(f"[*] Created Smuggler's Path in {time.time()-start_t}s")



arcpy.CheckInExtension("Spatial")
