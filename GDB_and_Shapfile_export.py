import arcpy
import os
import zipfile

arcpy.overwriteOutput = True

# Create path variables
Path_To_Project_Area_GDB = r"\\logansimpson.com\corporate\ndrive\projects\2022\225008 APS Environmental Project Assistance (1.ENV)\23_Delano 10 WE012293\Environmental\Graphics-GIS\gis"
Output_Folder_Name = 'To_LYoung_221111'

# Join Folder names
Path_To_Source_Dir = rf"{Path_To_Project_Area_GDB}\source"
Project_Area_GDB = rf"{Path_To_Project_Area_GDB}\Project_Area.gdb"

# Create Output Folder
try:
    os.mkdir(rf"{Path_To_Source_Dir}\{Output_Folder_Name}")
except FileExistsError:
    print("Output folder already exists")
    pass

# Copy Shapefile
Output_Folder = rf"{Path_To_Source_Dir}\{Output_Folder_Name}"
arcpy.env.workspace = Project_Area_GDB
arcpy.FeatureClassToShapefile_conversion('Project_Area', rf"{Output_Folder}")

# Zip up shapefile
arcpy.env.workspace = Output_Folder
shapes = arcpy.ListFeatureClasses()
for shape in shapes:
    name = os.path.splitext(shape)[0]
    print(name)
    zip_path = os.path.join(Output_Folder, name + '.zip')
    zip = zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED)
    zip.write(os.path.join(Output_Folder, shape), shape)
    for file in arcpy.ListFiles('%s*' % name):
        if not file.endswith('.shp'):
            zip.write(os.path.join(Output_Folder, file), file)
    print("All files written to %s" % zip_path)
    zip.close()
arcpy.Delete_management('Project_Area.shp')

# Copy project geodatabase
arcpy.Copy_management(Project_Area_GDB, rf"{Output_Folder}\Project_Area.gdb")

# Remove unnecessary feature classes
arcpy.env.workspace = rf"{Output_Folder}\Project_Area.gdb"
for fc in arcpy.ListFeatureClasses():
    if fc != 'Project_Area':
        arcpy.Delete_management(fc)

print("Project area file geodatabase and shapefile exported successfully")
