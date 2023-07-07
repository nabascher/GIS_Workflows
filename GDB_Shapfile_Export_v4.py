import arcpy
import os
import zipfile

arcpy.overwriteOutput = True

# Delete feature classes variable
Remove_FC = False

# Create path variables
Path_To_Project_Area_GDB = r"C:\Users\nbasch\Desktop\Temp\Script_Working"
Output_Folder_Name = 'Test'

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
def zip_shapes(Output_Folder, Remove_SHP):
    """
     Creates a zip file containing the input shapefile
     inputs -
     inShp: Full path to shapefile to be zipped
     Delete: Set to True to delete shapefile files after zip
     """
    #List of shapefile fiile extensions
    extensions = [".shp",
                  ".shx",
                  ".dbf",
                  ".sbn",
                  ".sbx",
                  ".fbn",
                  ".fbx",
                  ".ain",
                  ".aih",
                  ".atx",
                  ".ixs",
                  ".mxs",
                  ".prj",
                  ".xml",
                  ".cpg"]

    shapefile = rf"{Output_Folder}\Project_Area.shp"

    #Describe shapefile directory
    inLocation = arcpy.Describe(shapefile).path
    print(inLocation)

    # Base name of shapefile
    inName = arcpy.Describe(shapefile).baseName
    print(inName)

    #Create zipfile name
    zip_path = os.path.join(inLocation, 'Project_Area.zip')

    # Create zipfile object
    zip = zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED)

    for file in os.listdir(inLocation):
        for extension in extensions:
            if file == inName + extension:
                inFile = os.path.join(inLocation, file)
                zip.write(inFile, file)
    
    if Remove_SHP:
        arcpy.Delete_management('Project_Area.shp')

    zip.close()

    return zip_path


try:
    zip_shapes(Output_Folder, True)

except RuntimeError:
    for zip_file in os.listdir(Output_Folder):
        if os.path.exists(zip_file):
            os.unlink(zip_file)
    zip_shapes(Output_Folder, False)

# Copy project geodatabase
arcpy.Copy_management(Project_Area_GDB, rf"{Output_Folder}\Project_Area.gdb")

# Remove unnecessary feature classes
if Remove_FC:
    arcpy.env.workspace = rf"{Output_Folder}\Project_Area.gdb"
    for fc in arcpy.ListFeatureClasses():
        if fc != 'Project_Area' or fc != 'Project_Centerline':
            arcpy.Delete_management(fc)

print("Project area file geodatabase and shapefile exported successfully")
