"""
The functionality of this file is currently not in use.
It could be used to quick start a simulation only with a provided idf and epw file.
There is an invisible button for this in fileUpload.html
"""

import json
import logging
import time
import requests
from flask import render_template, Blueprint, request, redirect
import fileEncode
import fileHandler
import endpoint_connector
import home
import viewResult

startSimOnlyIdf_Blueprint = Blueprint('startSimOnlyIdf', __name__, template_folder='templates')


@startSimOnlyIdf_Blueprint.route('/startSimOnlyIdf', methods=['GET'])
def startSimOnlyIdfGet():
    """GET-Function which retrieves all necessary values for display"""
    SimHelper.simulationStatus = True
    home.setCurrentStep(4)
    fileHandler.checkFileCache()
    fileHandler.checkEPWCache()
    epwTitle = fileHandler.fileDetails.epwFile
    docTitle = fileHandler.fileDetails.currentFileName

    try:
        return render_template('startSimOnlyIdf.html', documentTitle=docTitle, sim_status=SimHelper.sim_id,
                               sim_progress=None, epwTitle=epwTitle)
    except Exception as e:
        logging.error(str(e))
        return render_template('startSim.html', documentTitle=docTitle, sim_status=SimHelper.sim_id, epwTitle=epwTitle,
                               sim_progress=None)


@startSimOnlyIdf_Blueprint.route('/startSimOnlyIdf')
def startSimPost():
    """
    Post-Method for the startSimOnlyIdf page.
    """
    try:
        if request.method == 'POST':
            if 'start_simulation_with_idf' in request.form:
                fileHandler.checkFileCache()
                if fileHandler.fileDetails.currentFileName is not None:
                    if fileHandler.fileDetails.epwFile is not None:
                        return redirect('/startSimOnlyIdf')
                    else:
                        error = 'Please use the example or upload an idf and epw file before you continue!'
                        return render_template('fileUPload.html', error=error,
                                           documentTitle=None, epwTitle=None)
                else:
                    error = 'Please use the example or upload an idf and epw file before you continue!'
                    return render_template('fileUpload.html', error=error, documentTitle=None,
                                       epwTitle=None)

        return render_template("fileUpload.html")
    except Exception as e:
        error = str(e)
        logging.error("[startSim]: An unspecified error occurred during the POST-Handling. Log:" + str(e))
        return render_template("startSimOnlyIdf.html", error=error)


@startSimOnlyIdf_Blueprint.route('/startSimOnlyIdf/CreateID')
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


@startSimOnlyIdf_Blueprint.route('/startSimOnlyIdf/TIDF')
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


@startSimOnlyIdf_Blueprint.route('/startSimOnlyIdf/TEPW')
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


@startSimOnlyIdf_Blueprint.route('/startSimOnlyIdf/EngageSim')
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
        start = endpoint_connector.start_simulation_only_idf(SimHelper.sim_id)
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


@startSimOnlyIdf_Blueprint.route('/startSimOnlyIdf/MonitorProgress')
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


@startSimOnlyIdf_Blueprint.route('/startSimOnlyIdf/printSimID')
def printSimID():
    """Simple function to get the current simID"""
    data = {"id": str(SimHelper.sim_id_show)}
    return json.dumps(data)


@startSimOnlyIdf_Blueprint.route('/startSimOnlyIdf/printIDF')
def printIDF():
    """Simple function to get the current IDF file"""
    data = {"idf": str(SimHelper.IDF_Transfer)}
    return json.dumps(data)


@startSimOnlyIdf_Blueprint.route('/startSimOnlyIdf/printEPW')
def printEPW():
    """Simple function to get the current EPW file"""
    data = {"epw": str(SimHelper.EPW_Transfer)}
    return json.dumps(data)


def cleanup():
    SimHelper.simulationStarted = False
    SimHelper.simulationStatus = True
    SimHelper.sim_id_show = None
    SimHelper.IDF_Transfer = False
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
