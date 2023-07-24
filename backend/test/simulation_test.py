import sys
import unittest
import requests
import json
import logging
import time

sys.path.append("..")
from backend import endpoint_request
from backend import utils
sys.path.append("tmp")


import sys
sys.path.append("..")

from backend import utils
from backend import endpoint_request
from backend import db_controller



# this unittest class tests calls to the class simulation.py. Wrong values should raise exceptions which
# should be properly handled by simulation.py (and app.py for that matter) to ensure that the simulation_worker
# thread still runs after a known error occurs. The Tests in this class test exactly that. Corrupted csv and epw
# files or invalid metadata is used to check if the correct string is written into the MongoDb simulation_result
# collection. Unittests are failed if the wrong or no status is inserted into the result collection for a given
# sim_id

# start a simulation via endpoint with wrong values for infiltration_rate

def start_simulation_invalid_infiltration_rate(sim_id):
    """Start simulation """
    url = "http://localhost:5000/simulation/control"
    payload = json.dumps({
        "id": sim_id,
        "height": 8.88,
        "length": 7.77,
        "width": 6.66,
        "orientation": 30,
        "start_day": 30,
        "start_month": 12,
        "start_year": 2022,
        "end_day": 31,
        "end_month": 12,
        "end_year": 2022,
        "infiltration_rate": -1
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


# start a simulation via endpoint with unlogical values for start end end Run Period e.g. start date after end date

def start_simulation_unlogical_run_period(sim_id):
    """Start simulation """
    url = "http://localhost:5000/simulation/control"
    payload = json.dumps({
        "id": sim_id,
        "height": 8.88,
        "length": 7.77,
        "width": 6.66,
        "orientation": 30,
        "start_day": 30,
        "start_month": 12,
        "start_year": 2022,
        "end_day": 31,
        "end_month": 11,
        "end_year": 2022,
        "infiltration_rate": 0.0019
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


# start a simulation via endpoint with wrong values for room values (here: length)

def start_simulation_invalid_room_size(sim_id):
    """Start simulation """
    url = "http://localhost:5000/simulation/control"
    payload = json.dumps({
        "id": sim_id,
        "height": 8.88,
        "length": -5,
        "width": 6.66,
        "orientation": 30,
        "start_day": 30,
        "start_month": 12,
        "start_year": 2022,
        "end_day": 31,
        "end_month": 12,
        "end_year": 2022,
        "infiltration_rate": 0.0019
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


# start a simulation via endpoint with wrong values for run period (here: start_day = 0)

def start_simulation_invalid_run_period(sim_id):
    """Start simulation """
    url = "http://localhost:5000/simulation/control"
    payload = json.dumps({
        "id": sim_id,
        "height": 8.88,
        "length": 7.77,
        "width": 6.66,
        "orientation": 30,
        "start_day": 0,
        "start_month": 12,
        "start_year": 2022,
        "end_day": 31,
        "end_month": 12,
        "end_year": 2022,
        "infiltration_rate": 0.0019
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


class SimulationTestcase(unittest.TestCase):

    # takes a corrupted csv file in backend/test/tmp and runs a simulation with otherwise valid data
    # e.g. valid epw, valid metadata
    # Asserts that the correct string is written in the result DB. If so, that means exception was handled in
    # simulation.py and simulation worker is still running.

    def test_corrupted_csv(self):
        sim_id = endpoint_request.init_simulation()
        endpoint_request.edit_idf_file(sim_id, utils.encode_file_to_base64("room.idf"))
        endpoint_request.edit_csv_file(sim_id, utils.encode_file_to_base64("corruptedCSV.csv"))
        endpoint_request.edit_epw_file(sim_id, utils.encode_file_to_base64("SanFranciscoWeather.epw"))
        endpoint_request.start_simulation(sim_id)
        logged = False
        while endpoint_request.check_simulation(sim_id)['status'] == 'in Progress':
            if not logged:
                logging.info("simulation status: " + str(endpoint_request.check_simulation(sim_id)))
                logged = True
                time.sleep(5.0)
        response = endpoint_request.check_simulation(sim_id)
        self.assertEqual("corrupted CSV-file", response['status'])

    # takes a corrupted epw file in backend/test/tmp and runs a simulation with otherwise valid data
    # e.g. valid csv, valid metadata
    # Asserts that the correct string is written in the result DB. If so, that means exception was handled in
    # simulation.py and simulation worker is still running.

    def test_corrupted_epw(self):
        sim_id = endpoint_request.init_simulation()
        endpoint_request.edit_idf_file(sim_id, utils.encode_file_to_base64("room.idf"))
        endpoint_request.edit_csv_file(sim_id, utils.encode_file_to_base64("functional_occupancy.csv"))
        endpoint_request.edit_epw_file(sim_id, utils.encode_file_to_base64("corruptedEPW.epw"))
        endpoint_request.start_simulation(sim_id)
        logged = False
        while endpoint_request.check_simulation(sim_id)['status'] == 'in Progress':
            if not logged:
                logging.info("simulation status: " + str(endpoint_request.check_simulation(sim_id)))
                logged = True
                time.sleep(5.0)
        response = endpoint_request.check_simulation(sim_id)
        self.assertEqual("EnergyPlus Error - check the error-file (...\\backend\\eppy_output\\eplusout.err)",
                         response["status"])

    # runs a simulation with invalid room size values (height, length, width) in metadata. Otherwise, valid
    # files are used e.g. valid csv, valid epw
    # Asserts that the correct string is written in the result DB. If so, that means exception was handled in
    # simulation.py and simulation worker is still running.

    def test_invalid_room_size(self):
        sim_id = endpoint_request.init_simulation()
        endpoint_request.edit_idf_file(sim_id, utils.encode_file_to_base64("room.idf"))
        endpoint_request.edit_csv_file(sim_id, utils.encode_file_to_base64("functional_occupancy.csv"))
        endpoint_request.edit_epw_file(sim_id, utils.encode_file_to_base64("SanFranciscoWeather.epw"))
        start_simulation_invalid_room_size(sim_id)
        logged = False
        while endpoint_request.check_simulation(sim_id)['status'] == 'in Progress':
            if not logged:
                logging.info("simulation status: " + str(endpoint_request.check_simulation(sim_id)))
                logged = True
                time.sleep(5.0)
        response = endpoint_request.check_simulation(sim_id)
        self.assertEqual("room size invalid", response["status"])

    # runs a simulation with invalid run period  values (start/end_day, start/end_month, start/end_year)
    # in metadata. Otherwise, valid files are used e.g. valid csv, valid epw
    # Asserts that the correct string is written in the result DB. If so, that means exception was handled in
    # simulation.py and simulation worker is still running.

    def test_invalid_run_period(self):
        sim_id = endpoint_request.init_simulation()
        endpoint_request.edit_idf_file(sim_id, utils.encode_file_to_base64("room.idf"))
        endpoint_request.edit_csv_file(sim_id, utils.encode_file_to_base64("functional_occupancy.csv"))
        endpoint_request.edit_epw_file(sim_id, utils.encode_file_to_base64("SanFranciscoWeather.epw"))
        start_simulation_invalid_run_period(sim_id)
        logged = False
        while endpoint_request.check_simulation(sim_id)['status'] == 'in Progress':
            if not logged:
                logging.info("simulation status: " + str(endpoint_request.check_simulation(sim_id)))
                logged = True
                time.sleep(5.0)
        response = endpoint_request.check_simulation(sim_id)
        self.assertEqual("run period invalid", response["status"])

    # runs a simulation with unlogical run period values (start/end_day, start/end_month, start/end_year)
    # in metadata. The start date is after the end date which makes no sense.
    # Otherwise, valid files are used e.g. valid csv, valid epw
    # Asserts that the correct string is written in the result DB. If so, that means exception was handled in
    # simulation.py and simulation worker is still running.

    def test_unlogical_run_period(self):
        sim_id = endpoint_request.init_simulation()
        endpoint_request.edit_idf_file(sim_id, utils.encode_file_to_base64("room.idf"))
        endpoint_request.edit_csv_file(sim_id, utils.encode_file_to_base64("functional_occupancy.csv"))
        endpoint_request.edit_epw_file(sim_id, utils.encode_file_to_base64("SanFranciscoWeather.epw"))
        start_simulation_unlogical_run_period(sim_id)
        logged = False
        while endpoint_request.check_simulation(sim_id)['status'] == 'in Progress':
            if not logged:
                logging.info("simulation status: " + str(endpoint_request.check_simulation(sim_id)))
                logged = True
                time.sleep(5.0)
        response = endpoint_request.check_simulation(sim_id)
        self.assertEqual("day is out of range for month", response["status"])

    # runs a simulation with invalid infiltration_rate value in metadata.
    # Otherwise, valid files are used e.g. valid csv, valid epw
    # Asserts that the correct string is written in the result DB. If so, that means exception was handled in
    # simulation.py and simulation worker is still running.

    def test_invalid_infiltration_rate(self):
        sim_id = endpoint_request.init_simulation()
        endpoint_request.edit_idf_file(sim_id, utils.encode_file_to_base64("room.idf"))
        endpoint_request.edit_csv_file(sim_id, utils.encode_file_to_base64("functional_occupancy.csv"))
        endpoint_request.edit_epw_file(sim_id, utils.encode_file_to_base64("SanFranciscoWeather.epw"))
        start_simulation_invalid_infiltration_rate(sim_id)
        logged = False
        while endpoint_request.check_simulation(sim_id)['status'] == 'in Progress':
            if not logged:
                logging.info("simulation status: " + str(endpoint_request.check_simulation(sim_id)))
                logged = True
                time.sleep(5.0)
        response = endpoint_request.check_simulation(sim_id)
        self.assertEqual("infiltration rate invalid", response["status"])

    # takes a csv file which is valid but has not enough rows (row count not equal to 10081) in backend/test/tmp and
    # runs a simulation with otherwise valid data e.g. valid epw, valid metadata
    # Asserts that the correct string is written in the result DB. If so, that means exception was handled in
    # simulation.py and simulation worker is still running.

    def test_to_short_csv_file(self):
        sim_id = endpoint_request.init_simulation()
        endpoint_request.edit_idf_file(sim_id, utils.encode_file_to_base64("room.idf"))
        endpoint_request.edit_csv_file(sim_id, utils.encode_file_to_base64("occupancyToShort.csv"))
        endpoint_request.edit_epw_file(sim_id, utils.encode_file_to_base64("SanFranciscoWeather.epw"))
        endpoint_request.start_simulation(sim_id)
        logged = False
        while endpoint_request.check_simulation(sim_id)['status'] == 'in Progress':
            if not logged:
                logging.info("simulation status: " + str(endpoint_request.check_simulation(sim_id)))
                logged = True
                time.sleep(5.0)
        response = endpoint_request.check_simulation(sim_id)
        self.assertIn("cannot reshape array of size", response["status"])

    # Final teardown after all tests are completed. Runs a "normal" simulation to overwrite maybe overwritten csv,
    # epw, eso or idf files. Resets everything back to normal.

    @classmethod
    def tearDownClass(cls):
        sim_id = endpoint_request.init_simulation()
        endpoint_request.edit_idf_file(sim_id, utils.encode_file_to_base64("room.idf"))
        endpoint_request.edit_csv_file(sim_id, utils.encode_file_to_base64("functional_occupancy.csv"))
        endpoint_request.edit_epw_file(sim_id, utils.encode_file_to_base64("SanFranciscoWeather.epw"))
        endpoint_request.start_simulation(sim_id)


if __name__ == '__main__':
    unittest.main()
