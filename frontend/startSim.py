import json
import logging
import os.path
import time
import requests
import pandas as pd
from flask import render_template, Blueprint, request
import fileEncode
import fileHandler
import endpoint_connector
import viewResult
import OccupancyUpload
from io import BytesIO
import base64
import home
from datetime import date

startSim_Blueprint = Blueprint('startSim', __name__, template_folder='templates')


@startSim_Blueprint.route('/StartSim', methods=['GET'])
def startSimGet():
    """GET-Function which retrieves all necessary values for display"""
    SimHelper.simulationStatus = True
    home.setCurrentStep(4)
    try:
        reopenSim()
    except ValueError:
        logging.error("[startSim]: Simulation could not be reopened")

    fileHandler.checkEPWCache()
    fileHandler.checkFileCache()
    OccupancyUpload.checkOccupancyCache()
    epwTitle = fileHandler.fileDetails.epwFile
    docTitle = fileHandler.fileDetails.currentFileName
    ocpTitle = OccupancyUpload.fileDetails.ocpfilename
    param = getParamFrame()
    date = getTimeFrame()
    try:
        df = getOCP()
        if df is not None:
            df.rename(columns={'day': 'Day', 'startTime': 'Start (HH:MM)', 'endTime': 'End (HH:MM)',
                               'amountPeople': '# People', 'window': 'Window'}, inplace=True)

        return render_template('startSim.html', documentTitle=docTitle, sim_status=SimHelper.sim_id, sim_progress=None,
                               tables=[df.to_html(classes='table')], occupancyTitle=ocpTitle,
                               titles=['Day', 'Start (HH:MM)', 'End (HH:MM)', '# People', 'Window'], epwTitle=epwTitle,
                               width=param['Width'], length=param['Length'], height=param['Height'],
                               orientation=param['Orientation'], infiltrationRate=param['Infiltration'],
                               start_date=date['start_date'], end_date=date['end_date'])
    except Exception as e:
        logging.error(str(e))
        return render_template('startSim.html', documentTitle=docTitle, sim_status=SimHelper.sim_id, epwTitle=epwTitle,
                               width=param['Width'], length=param['Length'], height=param['Height'],
                               orientation=param['Orientation'], infiltrationRate=param['Infiltration'],
                               occupancyTitle=ocpTitle, sim_progress=None, start_date=date['start_date'],
                               end_date=date['end_date'])


@startSim_Blueprint.route('/Simulation_Start')
def startSimPost():
    """
    Post-Method for the startSim page.
    """
    try:
        return render_template("startSim.html")
    except Exception as e:
        error = str(e)
        logging.error("[startSim]: An unspecified error occurred during the POST-Handling. Log:" + str(e))
        return render_template("startSim.html", error=error)


@startSim_Blueprint.route('/Simulation_Start/CreateID')
def startSim_CreateID():
    """
    Internal endpoint for creating the simulation id
    The function is called by js from the template --> connects to the given endpoint and returns the id as json dump
    If no id is returned by the backend, the whole simulation gets canceled
    :return: json
    """
    try:
        status = endpoint_connector.check_status()
        for key in status:
            if (key == 'errors') and not status['errors']['success']:
                raise ConnectionError(str(status['errors']['message']))
        SimHelper.sim_id = endpoint_connector.init_simulation()
        SimHelper.sim_id_show = SimHelper.sim_id
        SimHelper.SIM_Complete = False
        viewResult.ResultHelper.simID = SimHelper.sim_id
        SimHelper.simulationStatus = True
        value = {"id": SimHelper.sim_id}
        return json.dumps(value)
    except requests.exceptions.ConnectionError as e:
        logging.error("[startSim]: " + str(e))
        value = {"id": "Backend unavailable!"}
        SimHelper.sim_id = None
        return json.dumps(value)
    except TimeoutError as e:
        logging.error("[startSim]: Timeout-Error, " + str(e))
        value = {"id": "Timeout_Error"}
        SimHelper.sim_id = None
        return json.dumps(value)
    except ConnectionError as e:
        logging.error("[startSim]: " + str(e))
        value = {"id": "Docker unavailable!"}
        SimHelper.sim_id = None
        return json.dumps(value)
    except Exception as e:
        logging.error("[startSim]: An unspecified error occurred during the creation of sim id. Log: " + str(e))
        SimHelper.simulationStatus = False
        value = {
            "id": str(e)
        }
        SimHelper.sim_id = None
        return json.dumps(value)


@startSim_Blueprint.route('/Simulation_Start/TIDF')
def startSim_TransferIDF():
    """
    Internal endpoint for the transfer of the idf file (called by js)
    The function checks if an id exists, if that is true it checks the file cache for an idf file
    The file gets encoded as byte64 with the utf-8 codec and send to the backend
    The function will always be successful if the id could be generated
    :return: json dump with status "done" (json because of the internal endpoint)
    """
    try:
        if SimHelper.sim_id is None:
            raise Exception("No SIM-ID")
        if not SimHelper.simulationStatus:
            raise Exception("Simulation unsuccessful!")
        fileHandler.checkFileCache()
        filename = fileHandler.fileDetails.currentFileName
        docTitle = filename.split(".")[0]
        fileEncode.encodeFile(docTitle, 'idf')
        idf_b64String_utf = fileEncode.extractString(docTitle, 'idf')
        idf_b64String = idf_b64String_utf.decode('utf-8')
        idf_endpoint = endpoint_connector.edit_idf_file(SimHelper.sim_id, idf_b64String)
        print(idf_endpoint)
        SimHelper.IDF_Transfer = True
        value = {
            "status": "Done"
        }
        return json.dumps(value)
    except Exception as e:
        logging.error("[startSim]: An error occurred during the idf encoding and transfer. Log: " + str(e))
        SimHelper.simulationStatus = False
        value = {
            "status": str(e)
        }
        return json.dumps(value)


@startSim_Blueprint.route('/Simulation_Start/TCSV')
def startSim_TransferCSV():
    """
    Identical to idf transfer --> this time the occupancy gets encoded and transferred
    :return: json dump with status "done"
    """
    try:
        docTitle = None
        if SimHelper.sim_id is None:
            raise Exception("No SIM-ID")
        if not SimHelper.simulationStatus:
            raise Exception("Simulation unsuccessful!")
        if os.path.exists('./occupancy_cache/Simulation_OCP.csv'):
            docTitle = "Simulation"
        if os.path.exists('./occupancy_cache/occupancy_file_reopen_sim.csv'):
            docTitle = "Simulation"
        else:
            docTitle = "Upload"
        OccupancyUpload.checkOccupancyCache()
        filename = OccupancyUpload.fileDetails.ocpfilename
        docTitle = filename.split(".")[0]
        fileEncode.encodeFile(docTitle, 'csv')
        csv_b64String_utf = fileEncode.extractString(docTitle, 'csv')
        csv_b64String = csv_b64String_utf.decode('utf-8')
        csv_endpoint = endpoint_connector.edit_csv_file(SimHelper.sim_id, csv_b64String)
        SimHelper.CSV_Transfer = True
        print(csv_endpoint)
        value = {
            "status": "Done"
        }
        return json.dumps(value)
    except Exception as e:
        logging.error("[startSim]: An error occurred during the csv encoding and transfer. Log: " + str(e))
        SimHelper.simulationStatus = False
        value = {
            "status": str(e)
        }
        return json.dumps(value)


@startSim_Blueprint.route('/Simulation_Start/TEPW')
def startSim_TransferEPW():
    """
    Identical to idf transfer --> this time the weather data gets encoded and transferred
    :return: json dump with status "done"
    """
    try:
        if SimHelper.sim_id is None:
            raise Exception("No SIM-ID")
        if not SimHelper.simulationStatus:
            raise Exception("Simulation unsuccessful!")
        fileHandler.checkEPWCache()
        filename = fileHandler.fileDetails.epwFile
        docTitle = filename.split(".")[0]
        fileEncode.encodeFile(docTitle, 'epw')
        epw_b64String_utf = fileEncode.extractString(docTitle, 'epw')
        epw_b64String = epw_b64String_utf.decode('utf-8')
        epw_endpoint = endpoint_connector.edit_epw_file(SimHelper.sim_id, epw_b64String)
        SimHelper.EPW_Transfer = True
        print(epw_endpoint)
        value = {
            "status": "Done"
        }
        return json.dumps(value)
    except Exception as e:
        logging.error("[startSim]: An unspecified error occurred during the epw encoding and transfer. Log: " + str(e))
        SimHelper.simulationStatus = False
        value = {
            "status": str(e)
        }
        return json.dumps(value)


@startSim_Blueprint.route('/Simulation_Start/EngageSim')
def startSim_EngageSim():
    """
    Internal endpoint for metadata-transfer and the start of the simulation
    Checks if the required metadata files exist and triggers the start of the simulation
    (Triggers the loading effect on the template)
    :return: json dump with status
    """
    try:
        if SimHelper.sim_id is None:
            raise Exception("No SIM-ID")
        if not SimHelper.simulationStatus:
            raise Exception("Simulation unsuccessful!")
        param_dict = getParamFrame()
        if param_dict is None:
            raise Exception("Missing room parameters!")
        date_dict = getTimeFrame()
        if date_dict is None:
            raise Exception("Missing timeframe!")
        start = endpoint_connector.start_simulation(SimHelper.sim_id, date_dict, param_dict)
        print(start)
        SimHelper.simulationStarted = True
        value = {
            "status": "Simulation in progress."
        }
        return json.dumps(value)

    except Exception as e:
        logging.error("[startSim]: An unspecified error occurred during the simulation startup. Log: " + str(e))
        SimHelper.simulationStatus = False
        value = {
            "status": str(e)
        }
        return json.dumps(value)


@startSim_Blueprint.route('/Simulation_Start/MonitorProgress')
def MonitorProgress():
    """
    Internal endpoint for evaluating if the simulation is finished
    Sleep prevents the function from flooding the backend with requests (decreases performance)
    The function only returns an error state or a notification if the simulation is finished
    :return:
    """
    try:
        if not SimHelper.simulationStatus:
            SimHelper.SIM_Complete = True
            raise Exception("Simulation unsuccessful!")
        while not SimHelper.SIM_Complete:
            time.sleep(3)
            response = endpoint_connector.check_simulation(SimHelper.sim_id)
            result = response.get('status')
            if str(result) == "None":
                raise "No Simulation is currently running."
            elif str(result) == "done":
                value = {"status": "Simulation finished"}
                SimHelper.SIM_Complete = True
                cleanup()
                return json.dumps(value)
            elif str(result) == "in Progress":
                SimHelper.simulationStarted = True
                continue
            else:
                raise Exception(str(result))
        raise Exception("Simulation already completed")
    except Exception as e:
        value = {
            "status": str(e)
        }
        return json.dumps(value)


@startSim_Blueprint.route('/Simulation_Start/printSimID')
def printSimID():
    """Simple function to get the current simID"""
    data = {"id": str(SimHelper.sim_id_show)}
    return json.dumps(data)


@startSim_Blueprint.route('/Simulation_Start/printIDF')
def printIDF():
    """Simple function to get the current IDF file"""
    data = {"idf": str(SimHelper.IDF_Transfer)}
    return json.dumps(data)


@startSim_Blueprint.route('/Simulation_Start/printCSV')
def printCSV():
    """Simple function to get the current CSV file"""
    data = {"csv": str(SimHelper.CSV_Transfer)}
    return json.dumps(data)


@startSim_Blueprint.route('/Simulation_Start/printEPW')
def printEPW():
    """Simple function to get the current EPW file"""
    data = {"epw": str(SimHelper.EPW_Transfer)}
    return json.dumps(data)


@startSim_Blueprint.route('/Simulation_Start/printStarted')
def printStarted():
    """Simple function to get the current simulation"""
    data = {"start": str(SimHelper.simulationStarted)}
    return json.dumps(data)


def getOCP():
    """Simple function to get the dataframe"""
    path = './occupancy_cache/Modify_OCP.csv'
    if os.path.exists(path):
        dataframe = pd.read_csv(path)
        return dataframe
    else:
        return None


def getTimeFrame():
    """Simple function to get the timeframe"""
    path = './meta_data/date.json'
    if os.path.exists(path):
        with open('./meta_data/date.json') as json_file:
            date_dict = json.load(json_file)
            return date_dict
    else:
        return None


def getParamFrame():
    """Simple function to get the room parameters"""
    path = './meta_data/param.json'
    if os.path.exists(path):
        with open('./meta_data/param.json') as json_file:
            param_dict = json.load(json_file)
            return param_dict
    else:
        return None


def reopenSim():
    """Reopens an old simulation, uploads all provided files in the cache in frontend und goes back to the file input page
    that the user can click through the simulation"""
    try:
        # Update Sim data to reopen simulation
        simulation_id = request.args.get('simulation_id')

        if simulation_id is not None:
            metadata = endpoint_connector.get_metadata(simulation_id)
            for key, value in metadata.items():
                if key == 'zone_name':
                    exec(key + ' = "' + value + '"')
                else:
                    exec(key + ' = ' + str(value))
            height = metadata.get('height')
            infiltration_rate = metadata['infiltration_rate']
            length = metadata['length']
            width = metadata['width']
            orientation = metadata['orientation']
            start_day = metadata['start_day']
            start_month = metadata['start_month']
            start_year = metadata['start_year']
            end_day = metadata['end_day']
            end_month = metadata['end_month']
            end_year = metadata['end_year']

            start_date_variable = date(start_year, start_month, start_day)
            end_date_variable = date(end_year, end_month, end_day)

            start_date = start_date_variable.strftime('%Y-%m-%d')
            end_date = end_date_variable.strftime('%Y-%m-%d')

            room_parameters = dict(Height=height, Width=width, Length=length, Orientation=orientation)
            infiltration_rate = dict(infiltration_rate=infiltration_rate)

            idf_file = endpoint_connector.get_idf_file(simulation_id)
            idf_bytes = idf_file.encode('utf-8')
            base64_idf = base64.b64encode(idf_bytes)
            base64_idf_file = base64_idf.decode('utf-8')
            epw_file = endpoint_connector.get_epw_file(simulation_id)
            epw_bytes = epw_file.encode('utf-8')
            base64_epw = base64.b64encode(epw_bytes)
            base64_epw_file = base64_epw.decode('utf-8')
            csv_file = endpoint_connector.get_csv_file(simulation_id)
            csv_bytes = csv_file.encode('utf-8')

            home.EmptyIDFCache()
            filename_idf = "idf_file_reopen_sim.idf"  #
            # Create a BytesIO object with the content
            file_content_idf = BytesIO(idf_bytes)
            path = './idf_cache'
            # Save the content to the desired location
            with open(os.path.join(path, filename_idf), 'wb') as f:
                f.write(file_content_idf.getvalue())

            home.EmptyEPW()
            filename_epw = "epw_file_reopen_sim.epw"  #
            # Create a BytesIO object with the content
            file_content_epw = BytesIO(epw_bytes)
            path_epw = './epw_cache'
            # Save the content to the desired location
            with open(os.path.join(path_epw, filename_epw), 'wb') as f:
                f.write(file_content_epw.getvalue())

            home.EmptyOcpCache()
            filename_csv = "occupancy_file_reopen_sim.csv"  #
            # Create a BytesIO object with the content
            file_content_csv = BytesIO(csv_bytes)
            path_csv = './occupancy_cache'
            # Save the content to the desired location
            with open(os.path.join(path_csv, filename_csv), 'wb') as f:
                f.write(file_content_csv.getvalue())

            home.EmptyMeta()
            param_dict = {'Width': metadata['width'], 'Height': metadata['height'], 'Length': metadata['length'],
                          'Infiltration': metadata['infiltration_rate'], 'Orientation': metadata['orientation'],
                          'zone_name': metadata['zone_name']}

            json_object = json.dumps(param_dict, indent=8)
            with open("./meta_data/param.json", "w") as file:
                file.write(json_object)

            json_dict = {'start_date': str(start_date), 'start_day': int(start_day), 'start_month': int(start_month),
                         'start_year': int(start_year),
                         'end_day': int(end_day), 'end_month': int(end_month), 'end_year': int(end_year),
                         'end_date': str(end_date)}
            json_object = json.dumps(json_dict, indent=8)
            with open("./meta_data/date.json", "w") as file:
                file.write(json_object)

        else:
            logging.info("No Sim Id for reopen Simulation. New Simulation is created")
    except Exception as e:
        logging.error("[startSim]: Failed to reopen Simulation. Log:" + str(e))
        return False


def cleanup():
    SimHelper.simulationStarted = False
    SimHelper.simulationStatus = True
    SimHelper.sim_id_show = None
    SimHelper.IDF_Transfer = False
    SimHelper.CSV_Transfer = False
    SimHelper.EPW_Transfer = False
    SimHelper.Counter = 0
    SimHelper.SIM_Complete = False
    SimHelper.Backup_date = None


class SimHelper:
    simulationStarted = False
    simulationStatus = True
    sim_id = None
    sim_id_show = None
    IDF_Transfer = False
    CSV_Transfer = False
    EPW_Transfer = False
    Counter = 0
    SIM_Complete = False
    Backup_date = None
