import os
import pandas as pd
import shutil
import warnings
from tkinter import messagebox
try:
    import arcpy
    print("arcpy has been loaded")

except:
    print("the system does not have arcpy installed")

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
pd.options.mode.chained_assignment = None

########### NEED USER INPUT FOR THESE LINES ########################
Processed_Folder = r'T:\Texas\MansfieldTX_50310\Processed'  # This is the folder where the 'SreetPhotos Map' and database are located
path_to_Inventory = r'T:\Texas\MansfieldTX_50310\GIS\Final Inventory'   #Directory to project Nomad files
CRS = r'S:\IMS Data\Texas\Mansfield\50310 Mansfield TX NCTCOG\Condition Data\Processed\MansfieldTX2021_byGISID_ClientReview_Rev1.xlsx' #Project CRS file
ProjectName = 'MansfieldTX2021'         #EX) SmithtownNY2021
########### NEED USER INPUT FOR THESE LINES ########################

# Add the superseg folder
Project_Folder = 'SuperSegs'
path = os.path.join(Processed_Folder, Project_Folder)
try:
    os.mkdir(path)
    print("Directory '% s' created" % Project_Folder)
except FileExistsError:
    print("The directory already exists")
    pass

#  Copy and paste files into new folder
files = os.listdir(Processed_Folder)
print('copying files to SuperSegs folder...')
for file in files:
    if file.endswith('s.mdb') or file.endswith('s.mxd'):
        shutil.copy(os.path.join(Processed_Folder, file), path)
        print('successfully copied',  file, 'to SuperSegs folder')

#Rename the Supersegs mxd
mxd = os.listdir(path)[1]
mdb = os.listdir(path)[0]
Streetphotos_mdb = mdb[-16:]
Streetphotos_mxd = mxd[-16:]
os.chdir(path)
try:
    os.rename(os.path.join(path, mxd), mxd.replace(Streetphotos_mxd, 'SuperSegs.mxd'))
    os.rename(os.path.join(path, mdb), mdb.replace(Streetphotos_mdb, 'SuperSegs.mdb'))
    print('Succesfully renamed the mxd and mdb')
except FileExistsError:
    print('The files have already been renamed')
    pass

#Navigate to CRS
xlsx = pd.ExcelFile(CRS)
#
#Configure ACP data
ACP = pd.read_excel(xlsx, 'ACP')
new_header_ACP = ACP.iloc[5]
ACP = ACP[7:]
ACP.columns = new_header_ACP
ACP.rename(columns={'Agency Functional Class': 'FunCl', 'Pavement Type': 'PaveType', 'Pavement Condition Index (PCI)': 'PCI'}, inplace=True)
ACP_Final = ACP[['GISID', 'FunCl', 'PaveType', 'PCI']]
ACP_Final['PCI'] = ACP_Final['PCI'].astype(int).round()
print(ACP_Final.head())

# Configure PCC data
PCC = pd.read_excel(xlsx, 'PCC')
for i in PCC:                               # This loop checks to see if there is a value in the first GISID cell
    if pd.isnull(PCC.iloc[7, 0]) == True:
        break
    elif pd.isnull(PCC.iloc[7, 0]) == False:
        new_header_PCC = PCC.iloc[5]
        PCC = PCC[7:]
        PCC.columns = new_header_PCC
        PCC.rename(columns={'Agency Functional Class': 'FunCl', 'Pavement Type': 'PaveType', 'Pavement Condition Index (PCI)': 'PCI'}, inplace=True)
        break

# Append the two data frames together and export to the SuperSeg folder
try:
    PCC_Final = PCC[['GISID', 'FunCl', 'PaveType', 'PCI']]
    PCC_Final['PCI'] = PCC_Final['PCI'].astype(int).round()
    print(PCC_Final.head())
    Combined_data = ACP_Final.append(PCC_Final)
    print('Exporting PCI_Update...')
    PCI_Update = str(ProjectName) + '_PCI_Update.csv'
    Combined_data.to_csv(os.path.join(path, PCI_Update))
    print("PCI_Update has been exported")

except KeyError:
    print('There is no PCC data for this project')
    print('Exporting PCI_Update...')
    PCI_Update = str(ProjectName) + '_PCI_Update.csv'
    ACP_Final.to_csv(os.path.join(path, PCI_Update))
    print("PCI_Update has been exported")
    pass

# Shapefile configurations below

#Create ArcGisPro File Geodatabase and add Nomad
print('Creating the SuperSegs File Geodatabase...')
result = arcpy.CreateFileGDB_management(path, ProjectName + 'SuperSegs.gdb')
Project_Geodatabase = result.getOutput(0)
arcpy.env.workspace = path_to_Inventory
arcpy.env.overwriteOutput = True
fclist = arcpy.ListFeatureClasses()
print(fclist)
for shapefile in fclist:
    if shapefile.endswith('ES.shp') or shapefile.endswith('ES.shp'):
        print('Importing NOMAD Feature Classes to geodatabase...')
        outFeatureClass = os.path.join(Project_Geodatabase, shapefile.strip(".shp"))
        arcpy.CopyFeatures_management(shapefile, outFeatureClass)

print('NODES and ROUTES added to Geodatabase successfully')

#Add CSV file to Geodatabase
arcpy.env.workspace = path
arcpy.env.overwriteOutput = True
for csv in os.listdir(path):
    if csv.endswith('.csv'):
        PCI_Update = ProjectName + '.dbf'
        arcpy.TableToTable_conversion(csv, Project_Geodatabase, PCI_Update)

print('PCI_Update imported to geodatabase')

# Do the Join and add the fields to routes layer
arcpy.env.workspace = Project_Geodatabase
arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False
inputfeatures = "ROUTES"

SuperSegLayer = arcpy.MakeFeatureLayer_management(inputfeatures, "ROUTES_lyr")   # You can't do a join to a feature class only to a layer or table
joinField = "GISID"
joined_table = arcpy.AddJoin_management(SuperSegLayer, joinField, PCI_Update, joinField, "KEEP_ALL")
arcpy.CopyFeatures_management(joined_table, "ProjectID_Rev1")

inputfeatures = "ProjectID_Rev1"
fields = [
    ("ProjectID_Rev1", "LONG", "", "", "", "", "NULLABLE", "REQUIRED", ""),
    ("SegCheck", "SHORT", "", "", "", "", "NULLABLE", "REQUIRED", "")
]

for field in fields:
    arcpy.AddField_management(*(inputfeatures,) + field)

arcpy.CalculateField_management(inputfeatures, "SegCheck", "0", "", "", "", "")

print("SuperSegs Layer configured with Condition data")

#Make Copies of the ProjectID Layer
arcpy.CopyFeatures_management(inputfeatures, "Base")
arcpy.CopyFeatures_management(inputfeatures, "PCI")
print("Superseg layer copies successfully created")

messagebox.showinfo("Sergeant Superseg", "Woohoo! Now you can group supersegs! ^-^ ")