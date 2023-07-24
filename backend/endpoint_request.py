import logging
import requests
import json
import utils
import time

logging.basicConfig(level=logging.INFO)


def init_simulation():
    """
    Initialize new simulation in backend
    :return: Simulation ID
    """
    url = "http://localhost:5000/simulation"
    response = requests.request("POST", url, headers={}, data="")
    return response.json()


def get_simulation(sim_id):
    """
    Returns specific DB entry for sim_id
    """
    url = "http://localhost:5000/simulation"
    payload = json.dumps({
        'id': sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def edit_idf_file(sim_id, modified_idf_base64_string):
    """
    Edit idf File for specific Simulation with sim_id
    """
    url = "http://localhost:5000/idf"
    payload = json.dumps({
        'id': sim_id,
        'data': modified_idf_base64_string
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def get_idf_file(sim_id):
    """
    Get idf File for specific Simulation with sim_id from input simulation
    """
    url = "http://localhost:5000/idf"
    payload = json.dumps({
        'id': sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def edit_epw_file(sim_id, modified_epw_base64_string):
    """
    Edit epw File for specific Simulation with sim_id
    """
    url = "http://localhost:5000/weather"
    payload = json.dumps({
        'id': sim_id,
        'data': modified_epw_base64_string
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def get_epw_file(sim_id):
    """
    Get epw File for specific Simulation with sim_id from input simulation
    """
    url = "http://localhost:5000/weather"
    payload = json.dumps({
        'id': sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def edit_csv_file(sim_id, modified_csv_base64_string):
    """
    Edit csv File for specific Simulation with sim_id
    """
    url = "http://localhost:5000/occupancy"
    payload = json.dumps({
        'id': sim_id,
        'data': modified_csv_base64_string
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def get_csv_file(sim_id):
    """
    Get csv File for specific Simulation with sim_id from input simulation
    """
    url = "http://localhost:5000/occupancy"
    payload = json.dumps({
        'id': sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def delete_simulation(sim_id):
    """
    Remove Simulation from DB with sim_id
    """
    url = "http://localhost:5000/simulation"
    payload = json.dumps({
        "id": sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("DELETE", url, headers=headers, data=payload)
    return response.json()


def delete_results(sim_id):
    """
    Remove results from DB with sim_id
    """
    url = "http://localhost:5000/result"
    payload = json.dumps({
        "id": sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("DELETE", url, headers=headers, data=payload)
    return response.json()


def get_overview():
    """
    Get Overview over all DB entries
    """
    url = "http://localhost:5000/simulation/overview"
    response = requests.request("GET", url, headers={}, data={})
    return response.json()


def start_simulation(sim_id):
    """
    Start simulation
    """
    url = "http://localhost:5000/simulation/control"
    payload = json.dumps({
        "id": sim_id,
        "height": 8.88,
        "length": 7.77,
        "width": 6.66,
        "orientation": 0,
        "start_day": 29,
        "start_month": 12,
        "start_year": 2022,
        "end_day": 30,
        "end_month": 12,
        "end_year": 2022,
        "infiltration_rate": 0.0019
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def check_simulation(sim_id):
    """
    Check simulation status
    """
    url = "http://localhost:5000/simulation/control"
    payload = json.dumps({
        "id": sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def get_result(sim_id):
    """
    Get result for simulation id
    """
    url = "http://localhost:5000/result"
    payload = json.dumps({
        "id": sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def get_result_overview():
    """
    Returns all result entries
    """
    url = "http://localhost:5000/result/overview"
    response = requests.request("GET", url, headers={}, data={})
    return response.json()


def get_result_csv(sim_id):
    """
    Get result for simulation id formatted as csv
    """
    url = "http://localhost:5000/result/csv"
    payload = json.dumps({"id": sim_id})
    headers = {'Content-Type': 'application/json'}
    response = requests.request("GET", url, headers=headers, data=payload)
    return response


def get_metadata(sim_id):
    """
    Get metadata from simulation
    """
    url = "http://localhost:5000/metadata"
    payload = json.dumps({
        "id": sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def start_simulation_only_idf(sim_id):
    """
    Start a simulation with just the idf- and the epw-file
    """
    url = "http://localhost:5000/simulation/control/onlyidf"
    payload = json.dumps({"id": sim_id})
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def get_simulation_series_List(sim_id):
    """
    Get results for Simulation Series
    """
    url = "http://localhost:5000/series/results"
    payload = json.dumps({
        "id": sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def edit_simulation_series_occupancy(sim_id, modified_idf_base64_string):
    """
    Edit occupancy csv for Simulation Series
    """
    url = "http://localhost:5000/series/occupancy"
    payload = json.dumps({
        'id': sim_id,
        'data': modified_idf_base64_string
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def get_simulation_series_control(sim_id):
    """
    To get status of simulation series
    """
    url = "http://localhost:5000/series/run"
    payload = json.dumps({
        'id': sim_id,
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def post_sim_series_room(sim_id, modified_idf_base64_string):
    """
    Start series simulation with the idf-file
    """
    url = "http://localhost:5000/series/idf"
    payload = json.dumps({
        'id': sim_id,
        'data': modified_idf_base64_string
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def post_start_sim_series(payload):
    """
    Start series simulation
    """
    url = "http://localhost:5000/series/create"
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def post_sim_series_epw(sim_id, modified_epw_base64_string):
    """
    Edit epw File for Simulation series with sim_id
    """
    url = "http://localhost:5000/series/weather"
    payload = json.dumps({
        'id': sim_id,
        'data': modified_epw_base64_string
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def start_series_simulation(sim_id):
    """
    Start simulation series
    """
    url = "http://localhost:5000/series/run"
    payload = json.dumps({
        'id': sim_id,
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def post_reopensim(sim_id):
    """
    Reopen an old simulation
    """
    url = "http://localhost:5000/reopensim"
    payload = json.dumps({
        "id": sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


if __name__ == '__main__':
    """ request sequence to quickly start a simulation """
    try:
        """ initialize new simulation """
        simulation_id = init_simulation()
        logging.info(simulation_id)
        """ get simulation info with id """
        logging.info(get_simulation(simulation_id))
        """ edit idf with id """
        logging.info(edit_idf_file(simulation_id, utils.encode_file_to_base64("room.idf")))
        """ edit idf with id """
        logging.info(edit_epw_file(simulation_id, utils.encode_file_to_base64("SanFranciscoWeather.epw")))
        """ edit idf with id """
        logging.info(edit_csv_file(simulation_id, utils.encode_file_to_base64("occupancy.csv")))
        """ get simulation with id """
        logging.info(get_simulation(simulation_id)['idf_filename'])
        """ start Simulation """
        logging.info("start Simulation: " + str(start_simulation(simulation_id)['success']))
        """ check simulation status """
        logged = False
        while check_simulation(simulation_id)['status'] == 'in Progress':
            if not logged:
                logging.info("simulation status: " + str(check_simulation(simulation_id)))
                logged = True
                time.sleep(5.0)
        logging.info("simulation finished with " + str(check_simulation(simulation_id)))
        """ get metadata with id """
        test = get_metadata(simulation_id)
        logging.info(test)
        """ get result overview """
        logging.info(get_result_overview())
        """ delete simulation with id """
        del_response = False
        """ check response if delete was successful """
        if del_response:
            logging.info("Deleted Simulation successfully")
        else:
            logging.error("Error while deleting Simulation")
        """ get overview over all simulation in DB """
    except Exception as e:
        logging.error("[main]: An unspecified error occurred. Log:" + str(e))