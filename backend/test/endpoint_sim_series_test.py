import sys
import unittest
import logging
import time
import json

sys.path.append("..")

from backend import utils
from backend import endpoint_request
from backend import db_controller

sys.path.append("tmp")

logging.basicConfig(level=logging.INFO)


class TestEndpoints(unittest.TestCase):
    sim_id = ''

    def setUp(self):
        logging.info("Initializing Simulation...")
        try:
            logging.info("Create Simulation Series ...")
            params = json.dumps({
                "height": 8,
                "height_max": 8,
                "height_iter": 0,
                "length": 11,
                "length_max": 12,
                "length_iter": 1,
                "width": 6,
                "width_max": 6,
                "width_iter": 0,
                "orientation": 0,
                "orientation_max": 0,
                "orientation_iter": 0,
                "start_day": 17,
                "start_month": 5,
                "start_year": 2023,
                "end_day": 17,
                "end_month": 5,
                "end_year": 2023,
                "infiltration_rate": 0.0019,
                "infiltration_rate_max": 0.0019,
                "infiltration_rate_iter": 0
            })
            self.sim_id = endpoint_request.post_start_sim_series(params)
            if type(self.sim_id) == dict:
                sys.exit("Initializing failed! " + self.sim_id['message'])
            logging.info("Simulation " + self.sim_id + " initialized")
        except Exception as e:
            logging.error("An unspecified error occurred during the file encoding. Log: " + str(e))

    def tearDown(self):
        logging.info("Checking if simulation is running.")
        logged = False
        while endpoint_request.get_simulation_series_control(self.sim_id)['status'] == 'in Progress':
            if not logged:
                logging.info("simulation status: " + str(endpoint_request.get_simulation_series_control(self.sim_id)))
                logged = True
                time.sleep(5.0)
        logging.info("Deleting Simulation...")
        endpoint_request.delete_simulation(self.sim_id)
        logging.info("Simulation deleted")


    def test_series_occupancy(self):
        logging.info("Series Occupancy ...")
        response = endpoint_request.edit_simulation_series_occupancy(self.sim_id,
                                                                     utils.encode_file_to_base64("occupancy.csv"))
        logging.info("Done!")
        self.assertTrue(response['success'])


    def test_series_results(self):

        logging.info("Series Results ...")

        logging.info("Start Simulation Series ...")

        logging.info("Simulation Series files: idf")
        logging.info(endpoint_request.post_sim_series_room(self.sim_id, utils.encode_file_to_base64(
            "room.idf")))
        logging.info("Simulation Series files: epw")
        logging.info(
            endpoint_request.post_sim_series_epw(self.sim_id, utils.encode_file_to_base64(
                "SanFranciscoWeather.epw")))
        logging.info("Simulation Series files: csv")
        logging.info(endpoint_request.edit_simulation_series_occupancy(self.sim_id, utils.encode_file_to_base64(
            "occupancy.csv")))

        logging.info("start Simulation Series: " + str(endpoint_request.start_series_simulation(self.sim_id)))

        logged = False
        while endpoint_request.get_simulation_series_control(self.sim_id)['status'] == 'in Progress':
            if not logged:
                logging.info("Simulation series simulation status: " + str(endpoint_request.get_simulation_series_control(self.sim_id)))            #.check_simulation(self.sim_id)))
                logged = True
                time.sleep(5.0)
        logging.info("Simulation series simulation finished with " + str(endpoint_request.get_simulation_series_control(self.sim_id)))
        logging.info("Getting result csv ...")
        try:
            result_csv = (endpoint_request.get_simulation_series_List(self.sim_id))
        except Exception:
            self.fail("Simulation Series result csv is not available")


    def test_post_sim_series_room(self):
        logging.info("Post room data for simulation series...")
        seriesID = db_controller.create_Simulation_Series()
        response = endpoint_request.post_sim_series_room(seriesID, utils.encode_file_to_base64("room.idf"))
        logging.info("Done!")
        self.assertTrue(response['success'])

    def test_post_start_sim_series(self):
        logging.info("Post start for simulation series...")
        payload = json.dumps({
            "height": 8.5,
            "height_max": 9,
            "height_iter": 0.5,
            "length": 5.1,
            "length_max": 5.2,
            "length_iter": 0.1,
            "width": 4.5,
            "width_max": 5,
            "width_iter": 0.5,
            "orientation": 10,
            "orientation_max": 20,
            "orientation_iter": 10,
            "start_day": 17,
            "start_month": 5,
            "start_year": 2023,
            "end_day": 18,
            "end_month": 5,
            "end_year": 2023,
            "infiltration_rate": 0.0019,
            "infiltration_rate_max": 0.0020,
            "infiltration_rate_iter": 0.0001
        })
        response = endpoint_request.post_start_sim_series(payload)
        logging.info("Done!")
        self.assertIsNotNone(response)

    def test_post_sim_series_epw(self):
        logging.info("Edit EPW Data...")
        response = endpoint_request.post_sim_series_epw(self.sim_id, utils.encode_file_to_base64("SanFranciscoWeather"
                                                                                                 ".epw"))
        logging.info("Done!")
        self.assertTrue(response['success'])

    def test_start_series_simulation(self):
        logging.info("Uploading files")
        logging.info(endpoint_request.post_sim_series_room(self.sim_id, utils.encode_file_to_base64("room.idf")))
        logging.info(endpoint_request.post_sim_series_epw(self.sim_id, utils.encode_file_to_base64("SanFranciscoWeather.epw")))
        logging.info(endpoint_request.edit_simulation_series_occupancy(self.sim_id, utils.encode_file_to_base64("occupancy.csv")))
        logging.info("Start Series Simulation...")
        response = endpoint_request.start_series_simulation(self.sim_id)
        logging.info("Done!")
        self.assertTrue(response['success'])


    def test_check_sim_status(self):
        logging.info("Check Simulation Status...")
        response = endpoint_request.get_simulation_series_control(self.sim_id)
        logging.info("Done!")
        self.assertEqual(response['status'], 'No Status found for ' + str(self.sim_id))


class TestEndpointsWithInvalidID(unittest.TestCase):
    sim_id = 'InvalidSimIDInvalidSimID'
    error_string = "'InvalidSimIDInvalidSimID' is not a valid ObjectId, it must be a 12-byte input or a 24-character hex string"


    def test_series_occupancy(self):
        logging.info("Series Occupancy ...")
        response = endpoint_request.edit_simulation_series_occupancy(self.sim_id,
                                                                     utils.encode_file_to_base64("occupancy.csv"))
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], self.error_string)

    def test_series_results(self):
        logging.info("Series Results ...")
        response = endpoint_request.get_simulation_series_List(self.sim_id)
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], self.error_string)


    def test_post_sim_series_room(self):
        logging.info("Post room data for simulation series...")
        response = endpoint_request.post_sim_series_room(self.sim_id, utils.encode_file_to_base64("room.idf"))
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], self.error_string)

    def test_post_start_sim_series(self):
        logging.info("Post start for simulation series...")
        error_string = "The Height cannot be 0 or negativ!"
        payload = json.dumps({
            "height": 0,
            "height_max": 9,
            "height_iter": 0.5,
            "length": 5.1,
            "length_max": 5.2,
            "length_iter": 0.1,
            "width": 4.5,
            "width_max": 5,
            "width_iter": 0.5,
            "orientation": 10,
            "orientation_max": 20,
            "orientation_iter": 10,
            "start_day": 17,
            "start_month": 5,
            "start_year": 2023,
            "end_day": 18,
            "end_month": 5,
            "end_year": 2023,
            "infiltration_rate": 0.0019,
            "infiltration_rate_max": 0.0020,
            "infiltration_rate_iter": 0.0001
        })
        response = endpoint_request.post_start_sim_series(payload)
        logging.info("Done!")
        print(response)
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], error_string)

    def test_post_sim_series_epw(self):
       logging.info("Edit EPW Data...")
       response = endpoint_request.post_sim_series_epw(self.sim_id, utils.encode_file_to_base64("SanFranciscoWeather"
                                                                                                ".epw"))
       logging.info("Done!")
       self.assertFalse(response['errors']['success'])
       self.assertEqual(response['errors']['message'], self.error_string)

    def test_start_series_simulation(self):
        logging.info("Uploading files")
        logging.info(endpoint_request.post_sim_series_room(self.sim_id, utils.encode_file_to_base64("room.idf")))
        logging.info(endpoint_request.post_sim_series_epw(self.sim_id, utils.encode_file_to_base64("SanFranciscoWeather.epw")))
        logging.info(endpoint_request.edit_simulation_series_occupancy(self.sim_id, utils.encode_file_to_base64("occupancy.csv")))
        logging.info("Start Series Simulation...")
        response = endpoint_request.start_series_simulation(self.sim_id)
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], self.error_string)

    def test_check_sim_status(self):
        logging.info("Check Simulation Status...")
        response = endpoint_request.get_simulation_series_control(self.sim_id)
        logging.info("Done!")
        self.assertEqual(response['status'], 'No Status found for ' + str(self.sim_id))

class TestEndpointsWithIdNone(unittest.TestCase):
    sim_id = None

    def test_series_occupancy(self):
        logging.info("Series Occupancy ...")
        response = endpoint_request.edit_simulation_series_occupancy(self.sim_id, utils.encode_file_to_base64("occupancy.csv"))
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], {'id': ['Field may not be null.']})

    def test_series_results(self):
        logging.info("Series Results ...")
        response = endpoint_request.get_simulation_series_List(self.sim_id)
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], {'id': ['Field may not be null.']})

    def test_post_sim_series_room(self):
        logging.info("Post room data for simulation series...")
        response = endpoint_request.post_sim_series_room(self.sim_id, utils.encode_file_to_base64("room.idf"))
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], {'id': ['Field may not be null.']})

    def test_post_start_sim_series(self):
        logging.info("Post start for simulation series...")
        payload = json.dumps({
            "height": 0,
            "height_max": 9,
            "height_iter": 0.5,
            "length": 5.1,
            "length_max": 5.2,
            "length_iter": 0.1,
            "width": 4.5,
            "width_max": 5,
            "width_iter": 0.5,
            "orientation": 10,
            "orientation_max": 20,
            "orientation_iter": 10,
            "start_day": 17,
            "start_month": 5,
            "start_year": 2023,
            "end_day": 18,
            "end_month": 5,
            "end_year": 2023,
            "infiltration_rate": 0.0019,
            "infiltration_rate_max": 0.0020,
            "infiltration_rate_iter": 0.0001
        })
        response = endpoint_request.post_start_sim_series(payload)
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], "The Height cannot be 0 or negativ!")

    def test_post_sim_series_epw(self):
        logging.info("Edit EPW Data...")
        response = endpoint_request.post_sim_series_epw(self.sim_id, utils.encode_file_to_base64("SanFranciscoWeather"
                                                                                                 ".epw"))
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], {'id': ['Field may not be null.']})


    def test_start_series_simulation(self):
        logging.info("Uploading files")
        logging.info(endpoint_request.post_sim_series_room(self.sim_id, utils.encode_file_to_base64("room.idf")))
        logging.info(
            endpoint_request.post_sim_series_epw(self.sim_id, utils.encode_file_to_base64("SanFranciscoWeather.epw")))
        logging.info(endpoint_request.edit_simulation_series_occupancy(self.sim_id, utils.encode_file_to_base64("occupancy.csv")))
        logging.info("Start Series Simulation...")
        response = endpoint_request.start_series_simulation(self.sim_id)
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], {'id': ['Field may not be null.']})

    def test_check_sim_status(self):
        logging.info("Check Simulation Status...")
        response = endpoint_request.get_simulation_series_control(self.sim_id)
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], {'id': ['Field may not be null.']})


if __name__ == '__main__':
    unittest.main()
