import geopandas as gpd
import pandas as pd
import shutil 
import os 
from qgis.core import *
from qgis.gui import *
from PyQt5.QtGui import *

###########USER INPUT REQUIRED############
State = 'California'
CityState = 'RidgecrestCA'
Project_Number = '50511'
coordinate_system = '102645'
S_Drive_Path = r'S:\IMS Data\California\Ridgecrest\50511 Ridgecrest, CA (2022)'
path_to_GPSData = rf'O:\{State}\{CityState}_{Project_Number}\Raw\NOMAD\20220604_NOMAD\SurveyData'  # Need to change date here
###########USER INPUT REQUIRED############

###########MAY NEED USER INPUT############
Survey_Year = '2022'
path_to_Centerline = rf'O:\{State}\{CityState}_{Project_Number}\GIS\Final Inventory\NormalMap'
path_to_Europa = rf'{S_Drive_Path}\Condition Data\Processed\Working\Europa'
path_to_Processed = rf'O:\{State}\{CityState}_{Project_Number}\Processed'
###########MAY NEED USER INPUT############


# Transfer the Geopackage and QGS file
print("Transferring geopackage and QGIS Project File...")
Project_Name = CityState + Survey_Year
Server_Geopackage = r'O:\_IMS Data\_Pavemetrics\Empty Geopackage Template\empty.gpkg'
Server_QGS = r'O:\_IMS Data\_Pavemetrics\Blank QGIS FIle Template\empty.qgz'

try:
    shutil.copy(Server_Geopackage, os.path.join(path_to_Processed, 'empty.gpkg'))
    shutil.copy(Server_QGS, os.path.join(path_to_Processed, 'empty.qgz'))
except FileExistsError:
    print("The files already exist in the processed folder")
    pass

# Rename the files
os.chdir(path_to_Processed)
for file in os.listdir(path_to_Processed):
    os.rename(os.path.join(path_to_Processed, file), file.replace('empty', rf'{Project_Name}' + '_StreetPhotos'))

gpkg = os.path.join(path_to_Processed, rf'{Project_Name}' + '_StreetPhotos.gpkg')
QGZ = os.path.join(path_to_Processed, rf'{Project_Name}' + '_StreetPhotos.qgz')

print('Geopackage and QGZ transferred and renamed')


# Read and format Format Dataframes
print("Importing dataframes...")

# Survey Notes and Distress
Survey_Distress = gpd.read_file(path_to_GPSData + '\SurveyDistress.shp')
Survey_Notes = gpd.read_file(path_to_GPSData + '\SurveyNote.shp')

# Norpix_europa and Flagger_europa
Norpix_europa = pd.read_csv(path_to_Europa + r'\Norpix_europa.csv')
Flagger_europa = pd.read_csv(path_to_Europa + r'\Flagger_europa.csv')
Norpix_europa = Norpix_europa[['filename', 'latitude', 'longitude', 'dttm', 'ims_sec', 'gisid', 'trace', 'dw_path', 'lf_path', 'lr_path', 'rf_path', 'Street', 'Frombk', 'Tobk', 'Bearing']]
Flagger_europa = Flagger_europa[['longitude', 'latitude', 'crk_img']]
QCImage_df = Flagger_europa.replace({'PNGs':'QC', '.png':'.jpg'}, regex=True)

Norpix_gdf = gpd.GeoDataFrame(Norpix_europa, geometry=gpd.points_from_xy(Norpix_europa.longitude, Norpix_europa.latitude), crs='ESRI:104145')
QCImage_gdf = gpd.GeoDataFrame(QCImage_df, geometry=gpd.points_from_xy(QCImage_df.longitude, QCImage_df.latitude), crs='ESRI:104145')


# Nodes, routes, and limits
Routes_gdf = gpd.read_file(rf'{path_to_Centerline}\{Project_Name}_Inventory.shp')
Routes_gdf = Routes_gdf.set_crs(crs='ESRI:' + coordinate_system, allow_override=True)
Limits_gdf = gpd.read_file(rf'{path_to_Centerline}\{Project_Name}_Limits.shp')
Limits_gdf = Limits_gdf.set_crs(crs='ESRI:' + coordinate_system, allow_override=True)
Nodes_gdf = gpd.read_file(rf'{path_to_Centerline}\{Project_Name}_Nodes.shp')
Nodes_gdf = Nodes_gdf.set_crs(crs='ESRI:' + coordinate_system, allow_override=True)

print('dataframes imported successfully')

# Export to gpkg
print('Exporting data to geopackage...')
# Survey_Distress, Survey_Notes, Routes_gdf, Limits_gdf, QCImage_gdf, Norpix_gdf, Nodes_gdf

Database = open(gpkg)

QCImage_gdf.to_file(gpkg, layer='QC Images', driver='GPKG')
Norpix_gdf.to_file(gpkg, layer='StreetPhotos', driver='GPKG')

Survey_Distress.to_file(gpkg, layer='Surveydistress', driver='GPKG')
Survey_Notes.to_file(gpkg, layer='Surveynotes', driver='GPKG')

Routes_gdf.to_file(gpkg, layer='Routes', driver='GPKG')
Limits_gdf.to_file(gpkg, layer='Limits', driver='GPKG')
Nodes_gdf.to_file(gpkg, layer='Nodes', driver='GPKG')

print('data exported to geopackage successfully')


# Configure Map
# Survey_Distress, Survey_Notes, Routes_gdf, Limits_gdf, QCImage_gdf, Norpix_gdf, Nodes_gdf

# define a qgis project
QgsApplication.setPrefixPath(r"C:\OSGeo4W\bin")
qgs = QgsApplication([], False)
qgs.initQgis()

project = QgsProject.instance()
project.read(QGZ)
project = QgsProject.instance()
print(project.fileName())

canvas = QgsMapCanvas()
canvas.enableAntiAliasing(True)
bridge = QgsLayerTreeMapCanvasBridge(project.layerTreeRoot(), canvas)

print("adding and symbolizing map layers...")
# Add layers
Limits_layer = gpkg + "|layername=Limits"
Vector_Limitslayer = QgsVectorLayer(Limits_layer, 'Limits', 'ogr')
project.addMapLayer(Vector_Limitslayer)

Routes_layer = gpkg + "|layername=Routes"
Vector_Routeslayer = QgsVectorLayer(Routes_layer, 'Routes', 'ogr')
project.addMapLayer(Vector_Routeslayer)

Norpix_layer = gpkg + "|layername=StreetPhotos"
Vector_Norpixlayer = QgsVectorLayer(Norpix_layer, 'StreetPhotos', 'ogr')
project.addMapLayer(Vector_Norpixlayer)

QCImage_layer = gpkg + "|layername=QC Images"
Vector_QCImagelayer = QgsVectorLayer(QCImage_layer, 'QC Images', 'ogr')
project.addMapLayer(Vector_QCImagelayer)

Nodes_layer = gpkg + "|layername=Nodes"
Vector_Nodeslayer = QgsVectorLayer(Nodes_layer, 'Nodes', 'ogr')
project.addMapLayer(Vector_Nodeslayer)

Distress_layer = gpkg + "|layername=SurveyDistress"
Vector_Distresslayer = QgsVectorLayer(Distress_layer, 'SurveyDistress', 'ogr')
project.addMapLayer(Vector_Distresslayer)

Notes_layer = gpkg + "|layername=SurveyNotes"
Vector_Noteslayer = QgsVectorLayer(Notes_layer, 'SurveyNotes', 'ogr')
project.addMapLayer(Vector_Noteslayer)

project.write()

# Symbolize Layers

#Limits layer repaint
Limits_symbol = QgsFillSymbol.createSimple({'color': '0,0,0,0', 'outline_color': 'red', 'outline_width': '1.25'})
Vector_Limitslayer.renderer().setSymbol(Limits_symbol)
Vector_Limitslayer.triggerRepaint()

#Routes layer repaint
Routes_symbol = QgsLineSymbol.createSimple({'color':'#868686', 'width': '0.75'}) 
Vector_Routeslayer.renderer().setSymbol(Routes_symbol)
Vector_Routeslayer.triggerRepaint()

#Nodes layer repaint
Nodes_symbol = QgsMarkerSymbol.createSimple({'name':'pentagon', 'color': 'orange', 'size': '2.5', 'outline_color': '0,0,0,0'})
Vector_Nodeslayer.renderer().setSymbol(Nodes_symbol)
Vector_Nodeslayer.triggerRepaint()

#SurveyNotes layer repaint
SurveyNotes_symbol = QgsMarkerSymbol.createSimple({'name': 'triangle', 'color':'#dbcc1e', 'outline_color': 'red', 'size': '4'})
Vector_Noteslayer.renderer().setSymbol(SurveyNotes_symbol)
Vector_Noteslayer.triggerRepaint()

#SurveyDistress layer repaint
SurveyDistress_symbol =  QgsMarkerSymbol.createSimple({'name': 'diamond', 'color': 'green', 'outline_color': 'black', 'size': '3.5'})
Vector_Distresslayer.renderer().setSymbol(SurveyDistress_symbol)
Vector_Distresslayer.triggerRepaint()

#StreetPhotos
StreetPhotos_symbol = QgsMarkerSymbol.createSimple({'name': 'arrow', 'color': 'black', 'size': '3.5'})
StreetPhotos_symbol.setDataDefinedAngle(QgsProperty().fromField("Bearing"))
Vector_Norpixlayer.renderer().setSymbol(StreetPhotos_symbol)
Vector_Norpixlayer.triggerRepaint()

#QC Images
QCImages_symbol = QgsMarkerSymbol.createSimple({'name': 'star', 'color': 'pink', 'size': '3.5'})
Vector_QCImagelayer.renderer().setSymbol(QCImages_symbol)
Vector_QCImagelayer.triggerRepaint()

project.write()
print("layers added and symbolized")

 # Add layer actions for QC Images and StreetPhotos

# QC Images
QCImage_acManager = Vector_QCImagelayer.actions()
QCImage_Action = QgsAction(5, 'QC Image', '[%crk_img%]', capture=False)
QCImage_acManager.addAction(QCImage_Action)

# StreetPhotos
StreetPhotos_acManager = Vector_Norpixlayer.actions()
StreetPhotos_Action_LF = QgsAction(5, 'View_LF', '[%lf_path%]', capture=False)
StreetPhotos_Action_DW = QgsAction(5, 'View_DW', '[%dw_path%]', capture=False)
StreetPhotos_acManager.addAction(StreetPhotos_Action_LF)
StreetPhotos_acManager.addAction(StreetPhotos_Action_DW)

project.write()

# Label Notes and distress Layers

# SurveyNote Labels
Notes_label_settings = QgsPalLayerSettings()
Notes_text_format = QgsTextFormat()

Notes_text_format.setFont(QFont("Gill Sans MT", 10))
Notes_text_format.setSize(10)

Notes_buffer_settings = QgsTextBufferSettings()
Notes_buffer_settings.setEnabled(True)
Notes_buffer_settings.setSize(2)
Notes_buffer_settings.setColor(QColor("#fdbf6f"))

Notes_text_format.setBuffer(Notes_buffer_settings)
Notes_label_settings.setFormat(Notes_text_format)

Notes_label_settings.fieldName = "SurveyNote"

Notes_label_settings.enabled = True

Notes_label_settings = QgsVectorLayerSimpleLabeling(Notes_label_settings)
Vector_Noteslayer.setLabelsEnabled(True)
Vector_Noteslayer.setLabeling(Notes_label_settings)

Vector_Noteslayer.triggerRepaint()
project.write()

# SurveyDistress Labels
Distress_label_settings = QgsPalLayerSettings()
Distress_text_format = QgsTextFormat()

Distress_text_format.setFont(QFont("Gill Sans MT", 10))
Distress_text_format.setSize(10)

Distress_buffer_settings = QgsTextBufferSettings()
Distress_buffer_settings.setEnabled(True)
Distress_buffer_settings.setSize(2)
Distress_buffer_settings.setColor(QColor("#fdbf6f"))

Distress_text_format.setBuffer(Distress_buffer_settings)
Distress_label_settings.setFormat(Distress_text_format)

Distress_label_settings.fieldName = "P_DIST"

Distress_label_settings.enabled = True

Distress_label_settings = QgsVectorLayerSimpleLabeling(Distress_label_settings)
Vector_Distresslayer.setLabelsEnabled(True)
Vector_Distresslayer.setLabeling(Distress_label_settings)

Vector_Distresslayer.triggerRepaint()
print("Labeling for Surveynotes and Surveydistress configured")
project.write()

qgs.exitQgis()
Database.close()

print("End of map configuration")




