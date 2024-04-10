import fob2, smugglers_path as smpath

fob2.locate_FOB()
fob2.locate_OPs()
smpath.create_smugglers_path("paths_5m","\\in\\visibility.tif","\\in\\DTM_Slope_5m.tif","\\in\\lakes.tif","\\in\\wetlands.tif","\\in\\rivers.tif", "FOBPoints_5m.shp", "OPPoints_5m.shp","\\in\\forest.tif")
smpath.create_smugglers_path("paths_15m","\\in\\visibility.tif","\\in\\DTM_Slope_5m.tif","\\in\\lakes.tif","\\in\\wetlands.tif","\\in\\rivers.tif", "\\FOBPoints_15m.shp", "\\OPPoints_15m.shp","\\in\\forest.tif")
smpath.create_smugglers_path("paths_30m","\\in\\visibility.tif","\\in\\DTM_Slope_5m.tif","\\in\\lakes.tif","\\in\\wetlands.tif","\\in\\rivers.tif", "\\FOBPoints_30m.shp", "\\OPPoints_30m.shp","\\in\\forest.tif")
