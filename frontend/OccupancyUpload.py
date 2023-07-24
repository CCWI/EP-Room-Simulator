import logging
import os
import OccupancyCustom
from werkzeug.utils import secure_filename
import json
import home
import csv
from pathlib import Path
from flask import render_template, Blueprint, request, current_app, redirect
import glob

ocpUpload_Blueprint = Blueprint('ocpUpload', __name__, template_folder='templates')
upload_error = None


@ocpUpload_Blueprint.route('/ocpUpload', methods=['GET'])
def ocpUploadGET():
    """Basic GET-function. Identical functionality as described in fileHandler.py."""
    home.setCurrentStep(2)
    try:
        checkOccupancyCache()
        if fileDetails.ocpfilename is not None:
            ocpTitle = fileDetails.ocpfilename
            with open("./meta_data/date.json", 'r') as file:
                data = json.load(file)
                timeframe = str(data['start_date']) + " (START) - (END) " + str(data['end_date'])
            return render_template('ocpUpload.html', timeframe=timeframe, occupancyTitle=ocpTitle)
        if os.path.exists("./meta_data/date.json"):
            with open("./meta_data/date.json", 'r') as file:
                data = json.load(file)
                timeframe = str(data['start_date']) + " (START) - (END) " + str(data['end_date'])
                file = request.files['file']
                ocpTitle = str(file.filename)
        csv_files = glob.glob('./occupancy_cache/*.csv')
        if len(csv_files) > 0:
            with open("./occupancy_cache/*.csv", 'r') as file:
                ocpTitle=str(file.filename)
        return render_template('ocpUpload.html', timeframe=timeframe, occupancyTitle=ocpTitle)
    except Exception as e:
        logging.error("[ocpUpload]: Failed to properly execute GET-method. Error-Log: " + str(e))
        return render_template('ocpUpload.html')


@ocpUpload_Blueprint.route('/ocpUpload', methods=['POST'])
def ocpUploadPost():
    """Basic POST-function. Identical functionality as described in fileHandler.py """
    error = None
    checkOccupancyCache()
    if fileDetails.ocpfilename is not None:
        ocpTitle = fileDetails.ocpfilename
    else:
        ocpTitle = None
    try:
        if 'custom_occupancy_upload' in request.form:
            success, upload_error = uploadCustomFile(request)
            if success:
                timeframe = getTimeframe()
                file = request.files['file']
                ocpTitle = str(file.filename)
                return render_template('ocpUpload.html', success="True", timeframe=timeframe, occupancyTitle=ocpTitle)
            else:
                timeframe = getTimeframe()
                return render_template('ocpUpload.html', error="Error: " + str(upload_error), timeframe=timeframe)
        elif 'start_date' in request.form:
            if os.path.exists("./meta_data/timeframe_error.json"):
                os.remove("./meta_data/timeframe_error.json")
            result = OccupancyCustom.verifyDate(request)
            if result is None:
                with open("./meta_data/timeframe_error.json", 'r') as file:
                    data = json.load(file)
                    error = str(data['Error'])
                return render_template('ocpUpload.html', timeframe_error=error, success=UploadHelp.file_uploaded)
            else:
                timeframe = getTimeframe()
                return render_template('ocpUpload.html', timeframe=timeframe,success=UploadHelp.file_uploaded)
        elif 'delete_selected_timeframe' in request.form:
            os.remove('meta_data/date.json')
            return render_template('ocpUpload.html')
        else:
            csv_files = glob.glob('./occupancy_cache/*.csv')
            if len(csv_files) > 0:
                return redirect('/editParameters')
            else:
                timeframe = getTimeframe()
                return render_template('ocpUpload.html',
                                   error="Error: Please upload or create a occupancy before you proceed",
                                   timeframe=timeframe)
    except Exception as e:
        logging.error("[ocpUpload]: Failed to properly execute POST-method. Error-Log: " + str(e))
        return render_template('ocpUpload.html')


def getTimeframe():
    """Simple function retrieve data from a json dictionary"""
    try:
        if os.path.exists("./meta_data/date.json"):
            with open("./meta_data/date.json", 'r') as file:
                data = json.load(file)
                timeframe = str(data['start_date']) + " (START) - (END) " + str(data['end_date'])
                return timeframe
        return None

    except Exception as e:
        logging.error("[ocpUpload]: Failed to get the timeframe. Error-Log: " + str(e))
        return None


def uploadCustomFile(webRequest):
    """Identical to the functions described in fileHandler.py"""
    path = './occupancy_cache'
    error_case = None
    try:
        uploaded_file = webRequest.files['file']
        home.EmptyOcpCache()
        filename = secure_filename(uploaded_file.filename)
        if filename is not None:
            point_count = filename.count(".")
            if point_count > 1:
                upload_error = "Please remove all '.' from the filename!"
                return False, upload_error
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in current_app.config['UPLOAD_EXTENSIONS']:
                upload_error = "The selected file is not allowed. Please provide a valid .csv file!"
                return False, upload_error
            uploaded_file.save(os.path.join(path, filename))
            file_path = path + "/" + filename
            with open(file_path, 'r') as file:
                csv_reader = csv.reader(file)
                headers = next(csv_reader)
                if headers != ["day|time|occupants|win1"]:
                    upload_error = "The selected file does not have the correct format. Please " \
                                   "provide a file with the header day, time, occupants, win1. The header " \
                                   "should be in the following format: day|time|occupants|win1 Here is an " \
                                   "example of the data format: 0|00:00:00|0|0"
                    return False, upload_error
            UploadHelp.file_uploaded = "True"
            fileDetails.ocpfilename = filename
            upload_error = None
            return True, upload_error
    except Exception as e:
        logging.error("[uploadCustomFile]: Unspecified error occurred during file upload. Log: " + str(e))
        return str(e)

def checkOccupancyCache():
    """Identical to checkFileCache"""
    try:
        root = os.getcwd() + '/occupancy_cache'

        if os.path.exists(root + '/Simulation_OCP.csv'):
            fileDetails.ocpfilename = "Simulation_OCP.csv"
            return None
        else:
            for path in Path(root).rglob('*.csv'):
                fileDetails.ocpfilename = path.name
                return None
        fileDetails.ocpfilename = None
    except Exception as e:
        logging.error("[CheckOccupancyCache]: Unspecified error o"
                      "ccurred during Occupancy file check. Log: " + str(e))


class UploadHelp:
    file_uploaded = None


class fileDetails:
    ocpfilename = None
