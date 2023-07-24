import os
from flask import render_template, Blueprint, request, send_file
import fileHandler
from IDFUpdater import IDFUpdater
import fileEncode
import home
import json
from pathlib import Path
import logging
import zipfile

editParameters_Blueprint = Blueprint('editParameters', __name__, template_folder='templates')

"""
Creates Python Dictionary for room parameters and sets default values.
"""

param_dict = {}

idd_file = "resources/Energy+.idd"


@editParameters_Blueprint.route('/editParameters', methods=['GET'])
def editParametersGet():
    """
    GET function, that sets the current step in the navbar, checks if IDF-file already exists
    and writes the param_dict Dictionary into the param.json file. Through writing the JSON file both in the
    GET and POST method, we can ensure that there is always a param.json file being created even if the user
    decides not to make any changes to the parameters or submit the pre-set values.
    :return: template with determined room parameters
    """
    loadParameters()
    home.setCurrentStep(3)
    fileHandler.checkFileCache()
    docTitle = fileHandler.fileDetails.currentFileName

    if checkParameterCache() is True:
        metadata = get_Parameter_chache()
        width = metadata['Width']
        height = metadata['Height']
        length = metadata['Length']
        infiltrationrate = metadata['Infiltration']
        orientation = metadata['Orientation']
        param_dict['Height'] = height
        param_dict['Width'] = width
        param_dict['Length'] = length
        param_dict['Infiltration'] = infiltrationrate
        param_dict['Orientation'] = orientation

    if checkParameterCache() is False:
        metadata = get_Parameter_chache()
        zone = metadata['zone_name']
        param_dict['zone_name'] = zone
        json_object = json.dumps(param_dict, indent=8)
        with open("./meta_data/param.json", "w") as file:
            file.write(json_object)

    return render_template('editParameters.html', documentTitle=docTitle,
                           width=param_dict['Width'], length=param_dict['Length'], height=param_dict['Height'],
                           orientation=param_dict['Orientation'], infiltrationRate=param_dict['Infiltration'],
                           visibility="hidden")


@editParameters_Blueprint.route('/downloadIDF', methods=['GET'])
def download_idf():
    """
    Downloads idf file for visualization in Step Room
    """
    fileHandler.checkFileCache()
    idf_file_for_visualization_string = fileHandler.fileDetails.currentFileName
    idf_file_for_visualization_name = idf_file_for_visualization_string.split(".")[0]
    idf_file_for_visualization_file = fileEncode.getIDFFile(idf_file_for_visualization_name)
    return send_file(idf_file_for_visualization_file, as_attachment=True)


@editParameters_Blueprint.route('/downloadIDF.zip', methods=['GET'])
def download_idf_zip():
    """
    Downloads idf as zip file
    """
    fileHandler.checkFileCache()
    idf_file_for_visualization_string = fileHandler.fileDetails.currentFileName
    idf_file_for_visualization_name = idf_file_for_visualization_string.split(".")[0]
    idf_file_for_visualization_file = fileEncode.getIDFFile(idf_file_for_visualization_name)

    # Make zip-Folder with idf File as input
    zip_filename = f"{idf_file_for_visualization_name}.zip"
    with zipfile.ZipFile(zip_filename, "w") as zip_file:
        zip_file.write(idf_file_for_visualization_file, arcname=f"{idf_file_for_visualization_name}.idf")

    # return .zip-File as Download
    return send_file(zip_filename, as_attachment=True)


def update_idf_for_visualization(width, length, height, orientation):
    """
    Uploads an idf after new Parameters were set for visualization
    """
    fileHandler.checkFileCache()
    idf_file_for_visualization_string = fileHandler.fileDetails.currentFileName
    idf_file_for_visualization_name = idf_file_for_visualization_string.split(".")[0]
    idf_file_for_visualization_file = fileEncode.getIDFFile(idf_file_for_visualization_name)
    epw_file_string = fileHandler.fileDetails.epwFile
    epw_file_name = epw_file_string.split(".")[0]
    epw_file = fileEncode.getEPWFile(epw_file_name)
    idfupdate = IDFUpdater(idf_file_for_visualization_file, epw_file, idd_file)
    idfupdate.updateRoomSize(width, length, height)
    idfupdate.updateOrientation(orientation % 360)


@editParameters_Blueprint.route('/editParameters', methods=['POST', 'GET'])
def editParametersPost():
    """
    POST function, that sets the current step in the navbar, checks if IDF-file already exists
    and stores the parameter input in the parameter dictionary. Identically to the GET method
    this dictionary then gets written into the param.json file.
    :return: template with determined room paramaters
    """
    loadParameters()
    home.setCurrentStep(3)
    fileHandler.checkFileCache()
    docTitle = fileHandler.fileDetails.currentFileName

    if 'width' in request.form:
        if request.form['height'] == "" or request.form['width'] == "" or request.form['length'] == "" or request.form[
            'orientation'] == "":
            error = 'Please give a value to each single parameter'
            return render_template('editParameters.html', errorRoom=error, width=request.form['width'],
                                   length=request.form['length'], height=request.form['height'],
                                   orientation=request.form['orientation'], infiltrationRate=param_dict['Infiltration'])
        param_dict['Height'] = float(request.form['height'])
        param_dict['Width'] = float(request.form['width'])
        param_dict['Length'] = float(request.form['length'])
        param_dict['Orientation'] = float(request.form['orientation'])
        editParamaterHelper.area = param_dict['Width'] * param_dict['Length']

        json_object = json.dumps(param_dict, indent=8)
        with open("./meta_data/param.json", "w") as file:
            file.write(json_object)

        update_idf_for_visualization(param_dict['Width'], param_dict['Length'], param_dict['Height'],
                                     param_dict['Orientation'])

        return render_template('editParameters.html', documentTitle=docTitle, AdjRoomDimenOpen="open",
                               AdjInfiltRateOpen="", area=round(editParamaterHelper.area, 2),
                               width=param_dict['Width'], length=param_dict['Length'], height=param_dict['Height'],
                               orientation=param_dict['Orientation'], infiltrationRate=param_dict['Infiltration'],
                               visibility="visible")

    else:
        editParamaterHelper.area = param_dict['Width'] * param_dict['Length']
        if request.form['infiltrationRate'] == "":
            error = 'Please give a value to this single parameter'
            return render_template('editParameters.html', error=error, width=param_dict['Width'],
                                   length=param_dict['Length'], height=param_dict['Height'],
                                   orientation=param_dict['Orientation'],
                                   infiltrationRate=request.form['infiltrationRate'])
        param_dict['Infiltration'] = float(request.form['infiltrationRate'])

        json_object = json.dumps(param_dict, indent=8)
        with open("./meta_data/param.json", "w") as file:
            file.write(json_object)

        return render_template('editParameters.html', documentTitle=docTitle, AdjRoomDimenOpen="",
                               AdjInfiltRateOpen="open", area=round(editParamaterHelper.area, 2),
                               width=param_dict['Width'], length=param_dict['Length'], height=param_dict['Height'],
                               orientation=param_dict['Orientation'], infiltrationRate=param_dict['Infiltration'],
                               visibility="hidden")


def checkParameterCache():
    """Identical to checkFileCache"""
    try:
        root = os.getcwd() + '/meta_data'
        for path in Path(root).rglob('param.json'):
            return True
        return False
    except Exception as e:
        logging.error("[CheckOccupancyCache]: Unspecified error o"
                      "ccurred during Occupancy file check. Log: " + str(e))


def get_Parameter_chache():
    """
     return values from json files within the designated cache directory
     """
    try:
        root = os.getcwd() + '/meta_data'
        for path in Path(root).rglob('param.json'):
            with open(path, 'r') as file:
                file_content = json.load(file)
            return file_content
        return None
    except Exception as e:
        logging.error("[Parameter_cache_get]: An unspecified error occurred. Log:" + str(e))


def resetParameter():
    """
    method to reset the room paramters to their default value at the start of a new simulation
    """
    param_dict['Height'] = 3
    param_dict['Width'] = 4.1
    param_dict['Length'] = 6
    param_dict['Infiltration'] = 0.0019
    param_dict['Orientation'] = 0
    param_dict['zone_name'] = ""


def loadParameters():
    """
    method to load the parameters and to make param_dict global
    """
    with open("./meta_data/param.json", "r") as param_file:
        global param_dict
        param_dict = json.load(param_file)
        param_file.close()


class editParamaterHelper:
    """
    helper class used for the area, which is only being shown to the user but now used anywhere else in the code
    """
    area = None
