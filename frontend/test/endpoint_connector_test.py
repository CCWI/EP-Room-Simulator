import logging

import backend
from frontend.endpoint_connector import init_simulation, get_simulation, edit_idf_file, edit_epw_file, edit_csv_file, \
    start_simulation, delete_simulation, get_overview

if __name__ == '__main__':
    try:

        """ initialize new simulation """
        simulation_id = init_simulation()
        logging.info(simulation_id)
        """ get simulation info with id """
        logging.info(get_simulation(simulation_id))
        """ edit idf with id """
        logging.info(edit_idf_file(simulation_id, backend.utils.encode_file_to_base64("room.idf")))
        """ edit idf with id """
        logging.info(edit_epw_file(simulation_id, backend.utils.encode_file_to_base64("SanFranciscoWeather.epw")))
        """ edit idf with id """
        logging.info(edit_csv_file(simulation_id, backend.utils.encode_file_to_base64("occupancy.csv")))
        """ get simulation with id to check edit """
        logging.info(get_simulation(simulation_id))
        """ start Simulation """
        logging.info("start Simulation: " + str(start_simulation(simulation_id)['success']))
        """ delete simulation with id """
        del_response = delete_simulation(simulation_id)['success']
        del_response = False
        """ check response if delete was successful """
        if del_response:
            logging.info("Deleted Simulation successfully")
        else:
            logging.error("Error while deleting Simulation")
        """ get overview over all simulation in DB """

        logging.info(get_overview())
    except Exception as e:
        logging.error("[main]: An unspecified error occurred. Log:" + str(e))
