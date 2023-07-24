import json
import logging
import os.path
import time
import OccupancyData
import threading
import home
import OccupancyCreator
import OccupancyModifier
from flask import render_template, Blueprint, request, redirect, send_file

ocpCustom_Blueprint = Blueprint('ocpCustom', __name__, template_folder='templates')


@ocpCustom_Blueprint.route('/ocpCustom', methods=['GET'])
def ocpCustomGET():
    """Basic GET-function. Identical functionality as described in fileHandler.py."""
    home.setCurrentStep(2)
    try:
        if os.path.exists("./meta_data/date.json"):
            with open("./meta_data/date.json", 'r') as file:
                data = json.load(file)
                timeframe = str(data['start_date']) + " (START) - (END) " + str(data['end_date'])
                home.EmptyOcpCache()
                # create Base_CSV
                start_date = data['start_date']
                end_date = data['end_date']
                createBaseCsv(start_date, end_date)
            return render_template('ocpCustom.html', timeframe=timeframe)
        else:
            return render_template('ocpCustom.html')
    except Exception as e:
        logging.error("[ocpCustom]: Failed to properly execute GET-method. Error-Log: " + str(e))
        return render_template('ocpCustom.html')


@ocpCustom_Blueprint.route('/ocpCustom', methods=['POST'])
def ocpCustomPost():
    """Basic POST-function. Identical functionality as described in fileHandler.py """
    try:
        if 'start_date' in request.form:
            if os.path.exists("./meta_data/timeframe_error.json"):
                os.remove("./meta_data/timeframe_error.json")
            result = verifyDate(request)
            if result is None:
                with open("./meta_data/timeframe_error.json", 'r') as file:
                    data = json.load(file)
                    error = str(data['Error'])
                return render_template('ocpCustom.html', timeframe_error=error)
            else:
                with open("./meta_data/date.json", 'r') as file:
                    data = json.load(file)
                    timeframe = str(data['start_date']) + " (START) - (END) " + str(data['end_date'])
                return render_template('ocpCustom.html', timeframe=timeframe)
        elif 'delete_selected_timeframe' in request.form:
            os.remove('meta_data/date.json')
            return render_template('ocpCustom.html')
        elif 'OcpCustom_proceed' in request.form:
            home.setCurrentStep(3)
            return redirect('/editParameters')
    except Exception as e:
        logging.error("[ocpCustom]: Failed to properly execute POST-method. Error-Log: " + str(e))
        return render_template('ocpCustom.html')


@ocpCustom_Blueprint.route('/ocpCustom/Verify', methods=['POST'])
def ocpCustomVerifyData():
    """
    Serves as endpoint for the ajax post request started on the template
    Determines if an error file exists and removes it before sending the request data to the  verification function
    The function serves only as connector
    :return: basic template
    """
    try:
        if os.path.exists("./meta_data/ocp_error.json"):
            os.remove("./meta_data/ocp_error.json")
        OccupancyData.verifyOccupancyData(request)
        return render_template('ocpCustom.html')
    except Exception as e:
        return str(e)


@ocpCustom_Blueprint.route('/ocpCustom/Verify', methods=['GET'])
def ocpCustomReturnVerify():
    """
    Serves as endpoint for the ajax get request started on the template
    Function checks if an error-file exists --> if it does, the content gets returned as dictionary
    :return: json dictionary containing no or the identified error
    """
    value = {"Error": "No"}
    time.sleep(1)  # Should stop ajax from messing with the verification
    if os.path.exists("./meta_data/ocp_error.json"):
        with open("./meta_data/ocp_error.json", 'r') as file:
            value = json.load(file)
    return json.dumps(value)


@ocpCustom_Blueprint.route('/ocpCustom/Create', methods=['Post'])
def ocpCustomCreateOCP():
    """
    Serves as endpoint for an ajax post request
    Starts the occupancy creation
    :return: standard template
    """
    try:
        OccupancyModifier.modifyCSV_Main()
        return render_template('ocpCustom.html')
    except Exception as e:
        logging.error("[ocpCustom]: The modification of the base ocp failed. Error-Log: " + str(e))


@ocpCustom_Blueprint.route('/ocpCustom/Download')
def downloadCreatedOccupancy():
    """
    Serves as endpoint for an ajax or url request
    :return: generated occupancy csv as download file
    """
    try:
        root = os.getcwd() + './occupancy_cache/Simulation_OCP.csv'
        if os.path.exists(root):
            return send_file(root, as_attachment=True)
    except Exception as e:
        logging.error("[ocpCustom]: Failed to generate file download. Log: " + str(e))
        return str(e)


def verifyDate(webRequest):
    """
    Function extracts the selected date from the request and makes sure, that the entered date is realistic
    After verification, the correct date is saved within a json metadata file
    The function also starts the creation of a basic occupancy file, based on the given date
    :param webRequest: flask-request
    :return: Boolean or None
    """
    try:
        # Retrieve data from request
        start_date = webRequest.values['start_date']
        if start_date is None:
            raise Exception("The start date was not submitted properly to the form")
        start_day = start_date.split("-")[2]
        start_month = start_date.split("-")[1]
        start_year = start_date.split("-")[0]
        end_date = webRequest.values['end_date']
        if end_date is None:
            raise Exception("The end date was not submitted properly to the form")
        end_day = end_date.split("-")[2]
        end_month = end_date.split("-")[1]
        end_year = end_date.split("-")[0]

        # Verify years
        if end_year < start_year:
            raise Exception(
                "Timeframe-Error: The selected time frame is illogical: start year > end year is NOT allowed!")
        elif end_year == start_year:
            if end_month < start_month:
                raise Exception(
                    "Timeframe-Error: The selected time frame is illogical: start month > end month is NOT allowed!")
            elif end_month == start_month:
                if end_day < start_day:
                    raise Exception(
                        "Timeframe-Error: The selected time frame is illogical: start day > end day is NOT allowed!")
        elif end_year != start_year:
            if end_year > start_year:
                raise Exception(
                    "Timeframe-Error: The selected time frame is longer than a year or between two years! Those Timeframes can currently not be simulated!")

        json_dict = {'start_date': str(start_date), 'start_day': int(start_day), 'start_month': int(start_month),
                     'start_year': int(start_year),
                     'end_day': int(end_day), 'end_month': int(end_month), 'end_year': int(end_year),
                     'end_date': str(end_date)}
        json_object = json.dumps(json_dict, indent=8)
        with open("./meta_data/date.json", "w") as file:
            file.write(json_object)

        if request.path == '/ocpUpload':
            return True
        if request.path == '/ocpCustom':
            csv_thread = threading.Thread(target=OccupancyCreator.createCSV, args=(start_date, end_date))
            csv_thread.setDaemon(True)
            csv_thread.start()

        return True
    except Exception as e:
        global_error = {'Error': str(e)}
        global_json = json.dumps(global_error, indent=1)
        with open("./meta_data/timeframe_error.json", "w") as file:
            file.write(global_json)
        logging.error("[OCPCustom]: Failed to verify the given date. Log: " + str(e))
        return None


def createBaseCsv(start_date, end_date):
    csv_thread = threading.Thread(target=OccupancyCreator.createCSV, args=(start_date, end_date))
    csv_thread.setDaemon(True)
    csv_thread.start()
