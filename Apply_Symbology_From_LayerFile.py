# Run this in python windows to update symbology for 404 symbols

import arcpy

project = arcpy.mp.ArcGISProject("CURRENT")
map = project.listMaps()[0]

#layer files
Points_File = r"N:\gis\LSD_GIS_Templates\Symbology\404_Points.lyrx"
Lines_File = r"N:\gis\LSD_GIS_Templates\Symbology\404_Lines.lyrx"
Polygons_File = r"N:\gis\LSD_GIS_Templates\Symbology\404_Polygons.lyrx"
Project_Area_File = r"N:\gis\LSD_GIS_Templates\Symbology\Project_Area.lyrx"

#Set workspace for 404 data and add to map
arcpy.env.workspace = r"N:\gis\LSD_GIS_Templates\Template_Data\Survey_Map_Data\404_Collection_Geodatabase\404_Collection_Features.gdb"
arcpy.env.addOutputsToMap = True

for fc in arcpy.ListFeatureClasses():
    layer_name = arcpy.Describe(fc).baseName
    layers = arcpy.management.MakeFeatureLayer(fc, layer_name)

#Set workspace for project area polygon and add to map
arcpy.env.workspace = r"N:\gis\LSD_GIS_Templates\Template_Data\APS_Template_Master_Data.gdb"
arcpy.env.addOutputsToMap = True


for fc in arcpy.ListFeatureClasses():
    if arcpy.Describe(fc).baseName == "Project_Area":
        arcpy.management.MakeFeatureLayer(fc, fc)

#Apply symbology to layers
arcpy.management.ApplySymbologyFromLayer('Points', rf"{Points_File}")
arcpy.management.ApplySymbologyFromLayer('Lines', rf"{Lines_File}")
arcpy.management.ApplySymbologyFromLayer('Polygons', rf"{Polygons_File}")
arcpy.management.ApplySymbologyFromLayer('Project_Area', rf"{Project_Area_File}")