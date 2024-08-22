"""

This code objetive is to import the QGIS environment into python 3.9 PYCharm
Step 1:
Set the QGIS environment into Pycharm
source: https://gis.stackexchange.com/questions/362874/using-pyqgis-in-pycharm/428577#428577

Test task for all functions:

    1. Read geopackage
    2. Check information of vector layer
        2.1     check current projection
        2.1.1   get information from vector layer
        2.2     fix geometries
        2.3     reproject layer to 3044 EPSG

Documentation PYQGIS:
https://docs.qgis.org/3.28/en/docs/pyqgis_developer_cookbook/cheat_sheet.html
See https://gis.stackexchange.com/a/155852/4972 for details about the prefix

"""

# importing general libraries
import os
import sys
import time
from datetime import date
import pandas as pd

# --------------------------------------------------------------------------------------------------------------------
# Setting environment and modules form QGIS in PyCharm
# --------------------------------------------------------------------------------------------------------------------
# importing QGIS modules
from qgis.core import (
    QgsApplication,
    QgsProcessingFeedback,
    QgsVectorLayer
)

QgsApplication.setPrefixPath('/usr', True)
qgs = QgsApplication([], False)
qgs.initQgis()

# add the path folder where the QGIS is installed in the local machine
sys.path.append(r'C:\Program Files\QGIS 3.28.11\apps\qgis-ltr\python\plugins')
import processing
from processing.core.Processing import Processing

Processing.initialize()


# --------------------------------------------------------------------------------------------------------------------
# step 1. reading geopackage
def read_geodataframe_pygis(path_geodata) -> str:
    """
    :type path_geodata: full path to geodata
    """
    print('------------------------------------------------------------------')
    print('Starting Geo-preprocessing...')
    print('------------------------------------------------------------------')
    start_function = time.time()
    print('Reading geo-dataframe...')
    print('------------------------------------------------------------------')

    vlayer = QgsVectorLayer(path_geodata, "geodata", "ogr")
    if not vlayer.isValid():
        raise Exception("Failed to load vector layer")
    print(' - Geodata frame imported...')
    # getting current CRS
    lyrCRS = vlayer.crs().authid()
    print(f'- Current CRS: {lyrCRS}')
    end = time.time()
    print(' - Geodata red in minutes:', ((end - start_function) / 60))
    # printing  info from vector layer
    print('Attribute in geodataframe ------------------------------>')
    for field in vlayer.fields():
        print(field.name(), field.typeName())
    print('Attribute in geodataframe ------------------------------>')
    return vlayer


# --------------------------------------------------------------------------------------------------------------------
# printing algorithm available
# for alg in QgsApplication.processingRegistry().algorithms():
#         print(alg.id(), "->", alg.displayName())

def get_available_algorithms():
    # Get a list of algorithm names and display names
    algorithm_info = []

    # Iterate through processing algorithms
    for alg in QgsApplication.processingRegistry().algorithms():
        algorithm_info.append({'name': alg.id(), 'display_name': alg.displayName()})

    # Convert the list to a DataFrame
    algorithm_df = pd.DataFrame(algorithm_info)
    # Print the DataFrame
    print("DataFrame of algorithm information:")
    print(algorithm_df)
    # algorithm_df.to_excel('algorithm_information.xlsx', index=False)


# --------------------------------------------------------------------------------------------------------------------
# step 2. fixing geometry from vector layer
# processing.algorithmHelp("native:fixgeometries")

def fix_geometries_pyqgis(vlayer: object) -> QgsVectorLayer:
    if not vlayer.isValid():
        print('Layer not valid, check the path...')
    else:
        print('Fixing geometries...')
        # Create feedback objects
        feedback = QgsProcessingFeedback()
        # Set up parameters for the fix geometries algorithm
        params = {
            'INPUT': vlayer,
            'OUTPUT': 'memory:'
        }
        # Run the fix geometries algorithm
        result = processing.run("native:fixgeometries", params, feedback=feedback)
        # Get the fixed layer from the result
        fixed_layer = result['OUTPUT']
        # Update the original layer with the fixed geometries
        vlayer.dataProvider().deleteFeatures(vlayer.allFeatureIds())
        vlayer.dataProvider().addFeatures(fixed_layer.getFeatures())
        # Commit the changes and stop editing
        vlayer.commitChanges()
        print('Geometry fixed successfully...')
        return vlayer


# --------------------------------------------------------------------------------------------------------------------
# step 3. Re-projecting vector layer
# processing.algorithmHelp("native:reprojectlayer")

def reproject_layer_pyqgis(vlayer, target_projection='EPSG:3044'):
    print('------------------------------------------------------------------')
    print('Re-projecting layer...')
    print('------------------------------------------------------------------')

    feedback = QgsProcessingFeedback()
    # Set up parameters for the fix geometries algorithm
    params = {
        'INPUT': vlayer,
        'TARGET_CRS': target_projection,
        'OUTPUT': 'memory:Reprojected'
    }
    # Run the fix geometries algorithm
    result = processing.run("native:reprojectlayer", params, feedback=feedback)
    # Get the fixed layer from the result
    reprojected_layer = result['OUTPUT']
    print('Reprojected successfully to EPSG:3044...')
    return reprojected_layer


# --------------------------------------------------------------------------------------------------------------------
# step 3. Detect changes between 2 vector layer
# processing.algorithmHelp("native:detectvectorchanges")

def detect_vector_changes_pygis(vlayer_previous, vlayer_newest, output_folder):
    if vlayer_previous.crs().authid() == vlayer_newest.crs().authid():
        print('------------------------------------------------------------------')
        print('Both data sets have same CRS...')
        print('Detecting vector changes...')
        print('------------------------------------------------------------------')

        # context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        # adding full name output
        today_date = date.today().strftime('%d-%m-%Y')
        filename_add = 'vector_added_(' + today_date + ').gpkg'
        filename_del = 'vector_deleted_(' + today_date + ').gpkg'
        full_path_add = os.path.join(output_folder, filename_add)
        full_path_del = os.path.join(output_folder, filename_del)
        # Set up parameters
        params = {
            'ORIGINAL': vlayer_previous,
            'REVISED': vlayer_newest,
            'COMPARE_ATTRIBUTES': '',
            'MATCH_TYPE': 1,
            'ADDED': full_path_add
            # 'DELETED': full_path_del
        }
        # Run detect changes algorithm
        result = processing.run("native:detectvectorchanges", params, feedback=feedback, is_child_algorithm=True)
        added_layer = result['ADDED']
        print('Changes detected successfully...')
        print(f'Output saved in: {output_folder}')
    else:
        print("CRS does not macht...")
        print('Warning: result layer ADDED is a string...')
    return added_layer


def get_newest_file(directory):
    """
    This funtion get the newest file in a folder
    :param directory: String path of the data to find e.g 'C:\path\to\data'
    :return: the newest file name in a folder e.g Newest_file.gpgk
    """
    print('Getting previous file..')
    # Get a list of all files in the specified directory
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    # Check if there are any files
    if not files:
        print("No files found.")
        return None
    # Sort the files by modification time (newest first)
    files.sort(key=lambda f: os.path.getmtime(os.path.join(directory, f)), reverse=True)
    # Get the newest file
    # newest_file = os.path.join(directory, files[0])
    latest_file = files[0]
    print(f'Previous geodata report: {latest_file}...')
    return latest_file


# --------------------------------------------------------------------------------------------------------------------
# get newest data, loop over folders TAB data

def get_newest_folder_files(directory):
    """
    This function get the newest folder name and file name
    :param directory: String path of the data to find e.g 'C:\path\to\data'
    :return: a string the newest folder and file name in a folder
    """

    print('Getting newest TAB geodata within folders... ')
    # Get a list of all folders in the specified directory
    folders = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
    # Sort the folders by creation time (newest first)
    folders.sort(key=lambda f: os.path.getctime(os.path.join(directory, f)), reverse=True)
    # Check if there are any folders
    if not folders:
        print("No folders found.")
        return None
    # Get the newest folder
    newest_folder = os.path.join(directory, folders[0])
    # print(f'Newest data folder {newest_folder}...')
    # Get a list of all files in the newest folder
    files = [f for f in os.listdir(newest_folder) if os.path.isfile(os.path.join(newest_folder, f))]
    print(f'Newest SpeerIT data: {files[3]}')
    full_path_newest_data = os.path.join(newest_folder, files[3])
    return full_path_newest_data


# updated version
def createSpatialIndex_pyqgis(vlayer):
    print('------------------------------------------------------------------')
    print('Checking for existing spatial index...')
    print('------------------------------------------------------------------')

    # Check if the layer already has a spatial index
    if vlayer.hasSpatialIndex():
        print('Spatial index already exists. Returning the same layer...')
        return vlayer

    print('Creating spatial index from points...')

    feedback = QgsProcessingFeedback()

    # Set up parameters for the fix geometries algorithm
    params = {
        'INPUT': vlayer,
        'OUTPUT': 'memory:SpatialIndex'
    }

    # Run the fix geometries algorithm
    result = processing.run("native:createspatialindex", params, feedback=feedback)

    # Get the fixed layer from the result
    spatial_index_layer = result['OUTPUT']

    print('Spatial index successfully added...')
    return spatial_index_layer


# --------------------------------------------------------------------------------------------------------------------
# getting distance from points
# processing.algorithmHelp("native:joinbynearest")

def joinAttributesbyNearest(vlayer_points, vlayer_piplines, output_folder, OMPorGFC):
    """
    :param vlayer_points:
    :param vlayer_piplines:
    :param output_folder:
    :param OMPorGFC: string input GFC or OMP data name
    :return:
    """
    print('------------------------------------------------------------------')
    print('Starting algorithm, getting distance...')
    print('------------------------------------------------------------------')
    if vlayer_points.crs().authid() == vlayer_piplines.crs().authid():
        print('Both data sets have same CRS...')
        print('Joining distance column...')
        # context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        # adding full name output
        today_date = date.today().strftime('%d-%m-%Y')
        filename_joined = OMPorGFC.upper() + '_distance_calculated(' + today_date + ').gpkg'
        full_path_joined = os.path.join(output_folder, filename_joined)

        # Set up parameters
        params = {
            'INPUT': vlayer_points,
            'INPUT_2': vlayer_piplines,
            'MAX_DISTANCE': None,
            'NEIGHBORS': 1,
            'OUTPUT': full_path_joined
        }
        # Run detect changes algorithm
        result = processing.run("native:joinbynearest", params, feedback=feedback)
        joined_layer = result['OUTPUT']
        print('Distance successfully calculated...')
        print(f'Output saved in: {output_folder}')
    else:
        print("CRS does not macht...")
    print('Successfully joined distance metrics...')

    return joined_layer


# --------------------------------------------------------------------------------------------------------------------
#                                       Main function
# --------------------------------------------------------------------------------------------------------------------

# usage
if __name__ == "__main__":
    """
    :param
    dataPath_folder: folder where the geo-packages files are located
    outputPath_folder: folder where you want to save the data changes results ADDED und DELETED
    fileName_newest: change this name with the newest report
    fileName_previous: change this name with the latest report
    
    """

    print('Starting application...')
    start_function = time.time()
    cwd = os.getcwd()
    # input data newest geo-packages
    pathTab_folder = os.path.join(cwd, 'Geodata_TAB')
    dataPath_folder_prev = os.path.join(cwd, 'Geodata_ChangeDetection')

    # getting automatic newest folder and geodata path
    fileName_newest = get_newest_folder_files(pathTab_folder)[3]
    fullPath_newest = os.path.join(pathTab_folder, fileName_newest)

    # getting automatic newest previous report
    fileName_previous = get_newest_folder_files(dataPath_folder_prev)
    fullPath_previous = os.path.join(dataPath_folder_prev, fileName_previous)

    # output folder data changes results
    outputPath_folder = r'C:\Users\output\folder'
    # 1. Importing vector layers
    vector_newest = read_geodataframe_pygis(fullPath_newest)
    vector_previous = read_geodataframe_pygis(fullPath_previous)

    # 2. Fixing geometries
    vector_newest = fix_geometries_pyqgis(vector_newest)

    # 3. Re-projecting vector
    vector_newest = reproject_layer_pyqgis(vector_newest)
    vectorAdded_changes = detect_vector_changes_pygis(vector_previous, vector_newest, outputPath_folder)
    end = time.time()
    print('Entire process finished in (min):', ((end - start_function) / 60))
