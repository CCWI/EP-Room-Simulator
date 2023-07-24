import json
from flask import render_template, Blueprint, request, current_app, redirect, Request
import os
import logging
import shutil
import home
import fileEncode
from IDFUpdater import IDFUpdater
from pathlib import Path
from werkzeug.utils import secure_filename
import editParameters

fileHandler_Blueprint = Blueprint('fileHandler', __name__, template_folder='templates')

idd_file = "resources/Energy+.idd"
meta_data_path = "meta_data"
param_file_name = "param.json"

param_dict = {'Width': 4.1,
              'Height': 3,
              'Length': 6,
              'Infiltration': 0.0019,
              'Orientation': 0,
              'zone_name': ''}


@fileHandler_Blueprint.route('/InputFile', methods=['GET'])
def fileHandlerGet():
    """
    Basic GET-Function --> checks if files already exist (normally there shouldn't be any)
    :return: template with determined args
    """
    home.setCurrentStep(1)
    checkFileCache()
    checkEPWCache()
    if fileDetails.currentFileName is not None:
        docTitle = fileDetails.currentFileName
    else:
        docTitle = None
    if fileDetails.epwFile is not None:
        epwTitle = fileDetails.epwFile
    else:
        epwTitle = None
    return render_template('fileUpload.html', documentTitle=docTitle, epwTitle=epwTitle)


@fileHandler_Blueprint.route('/InputFile', methods=['Post'])
def fileHandlerPost():
    """
    POST-function: determines action based on the id value in the given request
    Every given id has its own sub function and must return a template based on the executed actions
    Every branch basically does something and checks if the action was executed properly and renders the template
    Every branch needs to check if other branches were already executed and need that information
    --> For a rework: remove branches and rewrite everything with javascript (e.g. startSim or ocpCustom)
    :return: template based on the given id
    """
    if request.method == 'POST':
        if 'submit_base_file' in request.form:
            check = createBasicFile(request)
            if not check:
                return render_template('fileUpload.html', error=fileDetails.GlobalError, documentTitle=None,
                                       epwTitle=str(fileDetails.epwFile),
                                       idfopen="",
                                       epwopen="",
                                       idfbaseopen="open",
                                       epwbaseopen="")
            else:
                return render_template('fileUpload.html', documentTitle=str(fileDetails.currentFileName),
                                       idfopen="",
                                       epwopen="",
                                       idfbaseopen="open",
                                       epwbaseopen="",
                                       epwTitle=str(fileDetails.epwFile))
        elif 'custom_file_upload' in request.form:
            check = uploadCustomFile(request)
            if not check:
                error = "The uploaded file does not comply to the required data type. Provide a suitable .idf-file!"
                return render_template('fileUpload.html', idferror=fileDetails.GlobalIDFError, documentTitle=None,
                                       idfopen="open",
                                       epwopen="",
                                       idfbaseopen="",
                                       epwbaseopen="",
                                       epwTitle=str(fileDetails.epwFile))
            else:
                return render_template('fileUpload.html', documentTitle=str(fileDetails.currentFileName),
                                       idfopen="open",
                                       epwopen="",
                                       idfbaseopen="",
                                       epwbaseopen="",
                                       epwTitle=str(fileDetails.epwFile))
        elif 'use_base_epw_file' in request.form:
            check = createBasicEPWfile()
            if not check:
                return render_template('fileUpload.html', error=fileDetails.GlobalError, documentTitle=None,
                                       epwTitle=str(fileDetails.epwFile),
                                       idfopen="",
                                       epwopen="",
                                       idfbaseopen="",
                                       epwbaseopen="open")
            else:
                return render_template('fileUpload.html', documentTitle=str(fileDetails.currentFileName),
                                       idfopen="",
                                       epwopen="",
                                       idfbaseopen="",
                                       epwbaseopen="open",
                                       epwTitle=str(fileDetails.epwFile))
        elif 'epw_file_upload' in request.form:
            check = uploadEPWFile(request)
            if not check:
                error = "The uploaded file does not comply to the required data type. Provide a suitable .epw-File!"
                return render_template('fileUpload.html', epwerror=fileDetails.GlobalEPWError,
                                       documentTitle=str(fileDetails.currentFileName),
                                       idfopen="",
                                       epwopen="open",
                                       idfbaseopen="",
                                       epwbaseopen="",
                                       epwTitle=None)
            else:
                return render_template('fileUpload.html', documentTitle=str(fileDetails.currentFileName),
                                       idfopen="",
                                       epwopen="open",
                                       idfbaseopen="",
                                       epwbaseopen="",
                                       epwTitle=str(fileDetails.epwFile))
        elif 'InputFile_proceed' in request.form:
            checkFileCache()
            if fileDetails.currentFileName is not None:
                if fileDetails.epwFile is not None:
                    # to write the zone name (from idf file) in param.json
                    update_zone_name_param_json()
                    return redirect('/ocpUpload')
                else:
                    error = 'Please use the example or upload an idf and epw file before you continue!'
                    return render_template('fileUpload.html', error=error,
                                           documentTitle=None, epwTitle=None)
        elif 'start_simulation_with_idf' in request.form:
            checkFileCache()
            if fileDetails.currentFileName is not None:
                if fileDetails.epwFile is not None:
                     #write zone name (from idf file) in param.json
                    update_zone_name_param_json()
                    return redirect('/startSimOnlyIdf')
                else:
                    error = 'Please use the example or upload an idf and epw file before you continue!'
                    return render_template('fileUpload.html', error=error,
                                               documentTitle=None, epwTitle=None)
            else:
                error = 'Please use the example or upload an idf and epw file before you continue!'
                return render_template('fileUpload.html', error=error, documentTitle=None,
                                       epwTitle=None)

    return render_template('fileUpload.html', documentTitle=str(fileDetails.currentFileName),
                           epwTitle=str(fileDetails.epwFile))


def uploadCustomFile(webRequest):
    """
    Check a given file if it adheres to the naming convention and to the allowed file types
    Saves the file if everything is correct in the given path or returns an error if not
    :param webRequest: flask-request
    :return: boolean
    """
    try:
        uploaded_file = webRequest.files['file']
        filename = secure_filename(uploaded_file.filename)
        if filename is not None:
            point_count = filename.count(".")
            if point_count > 1:
                fileDetails.GlobalError = "Please remove all '.' from the filename"
                return False
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in current_app.config['UPLOAD_EXTENSIONS'][0]:
                fileDetails.GlobalIDFError = "The uploaded file does not comply to the required data type. Please provide a suitable .idf - File!"
                return False
            uploaded_file.save(os.path.join(current_app.config['UPLOAD_PATH'], filename))
            fileDetails.currentFileName = filename
            return True
    except Exception as e:
        logging.error("[uploadCustomFile]: Unspecified error occurred during file upload. Log: " + str(e))
        return False


def uploadEPWFile(webRequest):
    """Identical to uploadCustomFile"""
    path = './epw_cache'
    try:
        uploaded_file = webRequest.files['epw_file']

        filename = secure_filename(uploaded_file.filename)

        if filename is not None:
            point_count = filename.count(".")
            if point_count > 1:
                fileDetails.GlobalError = "Please remove all '.' from the filename"
                return False
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in current_app.config['UPLOAD_EXTENSIONS'][2]:
                fileDetails.GlobalEPWError = "The uploaded file does not comply to the required data type. Please provide a suitable .epw - File!"
                return False

            fileDetails.epwFile = filename
            uploaded_file.save(os.path.join(path, filename))
            return True
    except Exception as e:
        logging.error("[uploadEPWFile]: Unspecified error occurred during file upload. Log: " + str(e))
        return False


def createBasicFile(webRequest):
    """
    Duplicates a file from the resources folder and gives it the provided name (if it adheres to the naming conventions)
    :param webRequest: flask request
    :return: boolean
    """
    try:
        filename = webRequest.form['base_file_name']

        point_count = filename.count(".")

        if filename == "":
            fileDetails.GlobalError = 'Please enter a valid title for your file before you continue! (Emtpy name)'
            return False
        if len(filename) > 200:
            fileDetails.GlobalError = 'Please enter a valid title for your file before you continue! (Length exceeded)'
            return False
        if point_count > 1:
            fileDetails.GlobalError = "Please remove all '.' from the filename"
            return False
        source = os.getcwd() + '/resources/base.idf'
        target = os.getcwd() + '/idf_cache/' + str(filename) + '.idf'
        shutil.copy(source, target)
        fileDetails.currentFileName = str(filename) + '.idf'
        return True
    except Exception as e:
        logging.error(
            "[createBasicFile]: An unspecified error occurred during the creation of a basic file. Log: " + str(e))


def createBasicEPWfile():
    """
    Provides a base EPW file (San Francisco Weather file), doesn't have an own EPW weather file or
    doesn't want to provide one.
    """
    try:
        source = os.getcwd() + '/resources/base.epw'
        target = os.getcwd() + '/epw_cache/base.epw'
        shutil.copy(source, target)

        filename = 'base.epw'
        fileDetails.epwFile = filename

        return True
    except Exception as e:
        logging.error(
            "[createBasicFile]: An unspecified error occurred during the creation of a basic file. Log: " + str(e))


def checkFileCache():
    """
    Checks if a directory contains a certain file and saves the name in an instantiated class
    --> can be refactored into a utility file
    :return None if not file can be found
    """
    try:
        root = os.getcwd() + '/idf_cache'
        for path in Path(root).rglob('*.idf'):
            fileDetails.currentFileName = path.name
            return None
        fileDetails.currentFileName = None
    except Exception as e:
        logging.error("[CheckFileCache]: Unspecified error o"
                      "ccurred during file check. Log: " + str(e))


def checkEPWCache():
    """Identical to checkFileCache"""
    try:
        root = os.getcwd() + '/epw_cache'

        for path in Path(root).rglob('*.epw'):
            fileDetails.epwFile = path.name
            return None
        fileDetails.epwFile = None
    except Exception as e:
        logging.error("[CheckFileCache]: Unspecified error o"
                      "ccurred during epwfile check. Log: " + str(e))


def update_zone_name_param_json():
    """
    update param.json file with zone name
    """
    checkFileCache()
    checkEPWCache()
    idf_file_for_visualization_string = fileDetails.currentFileName
    idf_file_for_visualization_name = idf_file_for_visualization_string.split(".")[0]
    idf_file_for_visualization_file = fileEncode.getIDFFile(idf_file_for_visualization_name)
    epw_file_string = fileDetails.epwFile
    epw_file_name = epw_file_string.split(".")[0]
    epw_file = fileEncode.getEPWFile(epw_file_name)
    idfupdate = IDFUpdater(idf_file_for_visualization_file, epw_file, idd_file)

    zone = idfupdate.IDF.idfobjects['Zone'][0]
    if editParameters.checkParameterCache() is True:
        metadata = editParameters.get_Parameter_chache()
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
        param_dict['zone_name'] = zone.Name

        json_object = json.dumps(param_dict, indent=8)
        with open("./meta_data/param.json", "w") as file:
            file.write(json_object)

    if editParameters.checkParameterCache() is False:
        param_dict['zone_name'] = zone.Name
        json_object = json.dumps(param_dict, indent=8)
        with open("./meta_data/param.json", "w") as file:
            file.write(json_object)


class fileDetails:
    currentFileName = None
    epwFile = None
    GlobalError = None
    GlobalEPWError = None
    GlobalIDFError = None
