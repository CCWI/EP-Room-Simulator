from flask import render_template, Blueprint, request, redirect
import os
from pathlib import Path
import logging
import fileHandler

import editParameters
import OccupancyUpload

home_Blueprint = Blueprint('home', __name__, template_folder='templates')


@home_Blueprint.route('/', methods=['GET'])
def home_GET():
    """
    Basic GET function --> Checks if a simulation was created and not started
    :return: template
    """
    discoverSimulation()
    simStatus = getSimStatus()
    return render_template('home.html', status=simStatus)


@home_Blueprint.route('/', methods=['POST'])
def home_POST():
    """
    Basic POST function --> checks which button has been pressed
    :return: redirect or template
    """
    try:
        if 'return_Sim' in request.form:
            return resumeSimulation()
        else:
            setCurrentStep(1)
            Cleaner()
            setSimStatus(True)

            editParameters.resetParameter()

            return redirect('/InputFile')
    except Exception:
        return render_template('home.html')


def Cleaner():
    """
    Main file cleaner. Used to clear all file based caches
    """
    EmptyIDFCache()
    EmptyOcpCache()
    Empty64Cache()
    EmptyEPW()
    EmptyEsoOutput()
    EmptyMeta()


def EmptyIDFCache():
    """
    Searches and deletes all idf files within the designated cache directory
    """
    try:
        root = os.getcwd() + '/idf_cache'
        for path in Path(root).rglob('*.idf'):
            os.remove(path)
        fileHandler.fileDetails.currentFileName = None
        logging.info("[Cleaner]: idf-file cache cleaned.")
    except FileNotFoundError:
        logging.info("[EmptyCache]: Directory already cleared]")
    except Exception as e:
        logging.error("[EmptyCache]: An unspecified error occurred. Log:" + str(e))


def EmptyOcpCache():
    """
     Searches and deletes all csv files within the designated cache directory
     """
    try:
        root = os.getcwd() + '/occupancy_cache'
        for path in Path(root).rglob('*.csv'):
            os.remove(path)
        fileHandler.fileDetails.currentFileName = None
        logging.info("[Cleaner]: csv-file cache cleaned.")
    except FileNotFoundError:
        logging.info("[EmptyCache]: Directory already cleared]")
    except Exception as e:
        logging.error("[EmptyCache]: An unspecified error occurred. Log:" + str(e))


def Empty64Cache():
    """
     Searches and deletes all dat files within the designated cache directory
     """
    try:
        root = os.getcwd() + '/64_cache'
        for path in Path(root).rglob('*.dat'):
            os.remove(path)
        fileHandler.fileDetails.currentFileName = None
        logging.info("[Cleaner]: B64-file cache cleaned.")
    except FileNotFoundError:
        logging.info("[EmptyCache]: Directory already cleared]")
    except Exception as e:
        logging.error("[EmptyCache]: An unspecified error occurred. Log:" + str(e))


def EmptyEsoOutput():
    """
     Searches and deletes all eso files within the designated cache directory
     """
    try:
        root = os.getcwd() + '/output_data'
        for path in Path(root).rglob('*.eso'):
            os.remove(path)
        fileHandler.fileDetails.currentFileName = None
        logging.info("[Cleaner]: ESO-file cache cleaned.")
    except FileNotFoundError:
        logging.info("[EmptyCache]: Directory already cleared]")
    except Exception as e:
        logging.error("[EmptyCache]: An unspecified error occurred. Log:" + str(e))


def EmptyEPW():
    """
     Searches and deletes all epw files within the designated cache directory
     """
    try:
        root = os.getcwd() + '/epw_cache'
        for path in Path(root).rglob('*.epw'):
            os.remove(path)
        fileHandler.fileDetails.currentFileName = None
        logging.info("[Cleaner]: EPW-file cache cleaned.")
    except FileNotFoundError:
        logging.info("[EmptyCache]: Directory already cleared]")
    except Exception as e:
        logging.error("[EmptyCache]: An unspecified error occurred. Log:" + str(e))


def EmptyMeta():
    """
     Searches and deletes all json files within the designated cache directory
     """
    try:
        root = os.getcwd() + '/meta_data'
        for path in Path(root).rglob('*.json'):
            os.remove(path)
        fileHandler.fileDetails.currentFileName = None
        logging.info("[Cleaner]: Meta-Data-file cache cleaned.")
    except FileNotFoundError:
        logging.info("[EmptyCache]: Directory already cleared]")
    except Exception as e:
        logging.error("[EmptyCache]: An unspecified error occurred. Log:" + str(e))


def resumeSimulation():
    """
    If a simulation was started --> this function helps the user to return to his previous step
    :return: redirect to step
    """
    sim_step = HomeHelper.current_sim_step
    if sim_step == 1:
        return redirect('/InputFile')
    elif sim_step == 2:
        return redirect('/ocpUpload')
    elif sim_step == 3:
        return redirect('/editParameters')
    elif sim_step == 4:
        OccupancyUpload.checkOccupancyCache()
        if OccupancyUpload.fileDetails.ocpfilename is not None:
            return redirect('/StartSim')
        else:
            return redirect('/startSimOnlyIdf')
    else:
        HomeHelper.simulation_status = False
        return redirect('/')


def discoverSimulation():
    """
    Checks if a filecache is already filled in order to determine the current simulation status
    """

    try:
        # First check the idf_cache
        root_idf = os.getcwd() + '/idf_cache'
        for path in Path(root_idf).rglob('*.idf'):
            setSimStatus(True)
            setCurrentStep(1)

        # Second check occupancy
        root = os.getcwd() + '/occupancy_cache'
        for path in Path(root).rglob('*.csv'):
            setSimStatus(True)
            setCurrentStep(3)

        # check for b64 files
        root = os.getcwd() + '/64_cache'
        for path in Path(root).rglob('*.dat'):
            setSimStatus(True)
            setCurrentStep(4)

    except Exception as e:
        logging.error("[Home]: Failed to retrieve previous simulation data. Error-Log: " + str(e))


def setCurrentStep(step):
    HomeHelper.current_sim_step = step


def getSimStatus():
    return HomeHelper.simulation_status


def setSimStatus(status):
    HomeHelper.simulation_status = status


class HomeHelper:
    simulation_status = False
    current_sim_step = 0
