import sys
import unittest
import logging
import time

sys.path.append("..")

from backend import utils
from backend import endpoint_request

sys.path.append("tmp")

logging.basicConfig(level=logging.INFO)


class TestEndpoints(unittest.TestCase):
    sim_id = ''

    def setUp(self):
        logging.info("Initializing Simulation...")
        try:
            self.sim_id = endpoint_request.init_simulation()
            if type(self.sim_id) == dict:
                sys.exit("Initializing failed! " + self.sim_id['message'])
            logging.info("Simulation " + self.sim_id + " initialized")
        except Exception as e:
            logging.error("An unspecified error occurred during the file encoding. Log: " + str(e))

    def tearDown(self):
        logging.info("Checking if simulation is running.")
        logged = False
        while endpoint_request.check_simulation(self.sim_id)['status'] == 'in Progress':
            if not logged:
                logging.info("simulation status: " + str(endpoint_request.check_simulation(self.sim_id)))
                logged = True
                time.sleep(5.0)
        logging.info("Deleting Simulation...")
        endpoint_request.delete_simulation(self.sim_id)
        logging.info("Simulation deleted")

    def test_get_sim_info(self):
        logging.info("Getting Simulation Info...")
        response = endpoint_request.get_simulation(self.sim_id)
        logging.info("Done!")
        self.assertIsNotNone(response)

    def test_edit_idf_file(self):
        logging.info("Edit IDF Data...")
        response = endpoint_request.edit_idf_file(self.sim_id, utils.encode_file_to_base64("room.idf"))
        logging.info("Done!")
        self.assertTrue(response['success'])

    def test_edit_epw_file(self):
        logging.info("Edit EPW Data...")
        response = endpoint_request.edit_epw_file(self.sim_id, utils.encode_file_to_base64("SanFranciscoWeather"
                                                                                           ".epw"))
        logging.info("Done!")
        self.assertTrue(response['success'])

    def test_edit_csv_file(self):
        logging.info("Edit CSV Data...")
        response = endpoint_request.edit_csv_file(self.sim_id, utils.encode_file_to_base64("occupancy.csv"))
        logging.info("Done!")
        self.assertTrue(response['success'])

    def test_check_sim_status(self):
        logging.info("Check Simulation Status...")
        response = endpoint_request.check_simulation(self.sim_id)
        logging.info("Done!")
        self.assertEqual(response['status'], 'No Status found for ' + str(self.sim_id))

    def test_start_sim(self):
        logging.info("Uploading files")
        logging.info(endpoint_request.edit_idf_file(self.sim_id, utils.encode_file_to_base64("room.idf")))
        logging.info(
            endpoint_request.edit_epw_file(self.sim_id, utils.encode_file_to_base64("SanFranciscoWeather.epw")))
        logging.info(endpoint_request.edit_csv_file(self.sim_id, utils.encode_file_to_base64("occupancy.csv")))
        logging.info("Start Simulation...")
        response = endpoint_request.start_simulation(self.sim_id)
        logging.info("Done!")
        self.assertTrue(response['success'])

    def test_check_result(self):
        logging.info("check simulation result")
        logging.info(endpoint_request.edit_idf_file(self.sim_id, utils.encode_file_to_base64("room.idf")))
        logging.info(
            endpoint_request.edit_epw_file(self.sim_id, utils.encode_file_to_base64("SanFranciscoWeather.epw")))
        logging.info(endpoint_request.edit_csv_file(self.sim_id, utils.encode_file_to_base64("occupancy.csv")))
        logging.info(endpoint_request.get_simulation(self.sim_id)['idf_filename'])
        """ start Simulation """
        logging.info("start Simulation: " + str(endpoint_request.start_simulation(self.sim_id)))
        """ check simulation status """
        logged = False
        while endpoint_request.check_simulation(self.sim_id)['status'] == 'in Progress':
            if not logged:
                logging.info("simulation status: " + str(endpoint_request.check_simulation(self.sim_id)))
                logged = True
                time.sleep(5.0)
        logging.info("simulation finished with " + str(endpoint_request.check_simulation(self.sim_id)))
        """ get result overview """
        result = (endpoint_request.get_result(self.sim_id))
        self.assertEqual(result['sim_id'], self.sim_id)

    def test_check_result_csv(self):
        logging.info("check simulation result csv")
        logging.info(endpoint_request.edit_idf_file(self.sim_id, utils.encode_file_to_base64("room.idf")))
        logging.info(
            endpoint_request.edit_epw_file(self.sim_id, utils.encode_file_to_base64("SanFranciscoWeather.epw")))
        logging.info(endpoint_request.edit_csv_file(self.sim_id, utils.encode_file_to_base64("occupancy.csv")))
        logging.info(endpoint_request.get_simulation(self.sim_id)['idf_filename'])
        """ start Simulation """
        logging.info("start Simulation: " + str(endpoint_request.start_simulation(self.sim_id)))
        """ check simulation status """
        logged = False
        while endpoint_request.check_simulation(self.sim_id)['status'] == 'in Progress':
            if not logged:
                logging.info("simulation status: " + str(endpoint_request.check_simulation(self.sim_id)))
                logged = True
                time.sleep(5.0)
        logging.info("simulation finished with " + str(endpoint_request.check_simulation(self.sim_id)))
        """ get result csv """
        try:
            result_csv = (endpoint_request.get_result_csv(self.sim_id))
        except Exception:
            self.fail("Result CSV not available")

    def test_start_sim_only_idf(self):
        logging.info("Start Simulation...")
        response = endpoint_request.start_simulation_only_idf(self.sim_id)
        logging.info("Done!")
        self.assertTrue(response['success'])


class TestEndpointsWithInvalidID(unittest.TestCase):
    sim_id = 'InvalidSimIDInvalidSimID'
    error_string = "'InvalidSimIDInvalidSimID' is not a valid ObjectId, it must be a 12-byte input or a 24-character hex string"

    def test_get_sim_info(self):
        logging.info("Getting Simulation Info...")
        response = endpoint_request.get_simulation(self.sim_id)
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], self.error_string)

    def test_edit_idf_file(self):
        logging.info("Edit IDF Data...")
        response = endpoint_request.edit_idf_file(self.sim_id, utils.encode_file_to_base64("room.idf"))
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], self.error_string)

    def test_edit_epw_file(self):
        logging.info("Edit EPW Data...")
        response = endpoint_request.edit_epw_file(self.sim_id, utils.encode_file_to_base64("SanFranciscoWeather"
                                                                                           ".epw"))
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], self.error_string)

    def test_edit_csv_file(self):
        logging.info("Edit CSV Data...")
        response = endpoint_request.edit_csv_file(self.sim_id, utils.encode_file_to_base64("occupancy.csv"))
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], self.error_string)

    def test_delete_sim(self):
        logging.info("Delete Simulation...")
        response = endpoint_request.delete_simulation(self.sim_id)
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], self.error_string)

    def test_check_sim_status(self):
        logging.info("Check Simulation Status...")
        response = endpoint_request.check_simulation(self.sim_id)
        logging.info("Done!")
        self.assertEqual(response['status'], 'No Status found for ' + self.sim_id)

    def test_start_sim(self):
        logging.info("Start Simulation...")
        response = endpoint_request.start_simulation(self.sim_id)
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], self.error_string)

    def test_start_sim_only_idf(self):
        logging.info("Start Simulation...")
        response = endpoint_request.start_simulation_only_idf(self.sim_id)
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], self.error_string)


class TestEndpointsWithIdNone(unittest.TestCase):
    sim_id = None

    def test_get_sim_info(self):
        logging.info("Getting Simulation Info...")
        response = endpoint_request.get_simulation(self.sim_id)
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], {'id': ['Field may not be null.']})

    def test_edit_idf_file(self):
        logging.info("Edit IDF Data...")
        response = endpoint_request.edit_idf_file(self.sim_id, utils.encode_file_to_base64("room.idf"))
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], {'id': ['Field may not be null.']})

    def test_edit_epw_file(self):
        logging.info("Edit EPW Data...")
        response = endpoint_request.edit_epw_file(self.sim_id, utils.encode_file_to_base64("SanFranciscoWeather"
                                                                                           ".epw"))
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], {'id': ['Field may not be null.']})

    def test_edit_csv_file(self):
        logging.info("Edit CSV Data...")
        response = endpoint_request.edit_csv_file(self.sim_id, utils.encode_file_to_base64("occupancy.csv"))
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], {'id': ['Field may not be null.']})

    def test_delete_sim(self):
        logging.info("Delete Simulation...")
        response = endpoint_request.delete_simulation(self.sim_id)
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], {'id': ['Field may not be null.']})

    def test_check_sim_status(self):
        logging.info("Check Simulation Status...")
        response = endpoint_request.check_simulation(self.sim_id)
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], {'id': ['Field may not be null.']})

    def test_start_sim(self):
        logging.info("Start Simulation...")
        response = endpoint_request.start_simulation(self.sim_id)
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], {'id': ['Field may not be null.']})

    def test_start_sim_only_idf(self):
        logging.info("Start Simulation...")
        response = endpoint_request.start_simulation_only_idf(self.sim_id)
        logging.info("Done!")
        self.assertFalse(response['errors']['success'])
        self.assertEqual(response['errors']['message'], {'id': ['Field may not be null.']})


if __name__ == '__main__':
    unittest.main()
