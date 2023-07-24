import logging
import requests
import json
import configparser

logging.basicConfig(level=logging.INFO)


def check_status():
    """
    Check the connection status
    """
    url = "http://" + Connector.url + ":" + Connector.port + "/status"
    headers = {'Content-Type': 'application/json'}
    response = requests.request("GET", url, headers=headers)
    return response.json()


def init_simulation():
    """
    Initialize new simulation in backend
    :return: Simulation ID
    """
    url = "http://" + Connector.url + ":" + Connector.port + "/simulation"
    response = requests.request("POST", url, headers={}, data="")
    return response.json()


def get_simulation(sim_id):
    """ Returns specific DB entry for sim_id"""
    url = "http://" + Connector.url + ":" + Connector.port + "/simulation"
    payload = json.dumps({
        'id': sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def edit_idf_file(sim_id, modified_idf_base64_string):
    """ Edit idf File for specific Simulation with sim_id """
    url = "http://" + Connector.url + ":" + Connector.port + "/idf"
    payload = json.dumps({
        'id': sim_id,
        'data': modified_idf_base64_string
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def edit_epw_file(sim_id, modified_epw_base64_string):
    """ Edit epw File for specific Simulation with sim_id """
    url = "http://" + Connector.url + ":" + Connector.port + "/weather"
    payload = json.dumps({
        'id': sim_id,
        'data': modified_epw_base64_string
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def edit_csv_file(sim_id, modified_csv_base64_string):
    """ Edit csv File for specific Simulation with sim_id """
    url = "http://" + Connector.url + ":" + Connector.port + "/occupancy"
    payload = json.dumps({
        'id': sim_id,
        'data': modified_csv_base64_string
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def delete_simulation(sim_id):
    """ Remove Simulation from DB with sim_id """
    url = "http://" + Connector.url + ":" + Connector.port + "/simulation"
    payload = json.dumps({
        "id": sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("DELETE", url, headers=headers, data=payload)
    return response.json()


def delete_result(sim_id):
    """ Remove Results from DB with sim_id """
    url = "http://" + Connector.url + ":" + Connector.port + "/result"
    payload = json.dumps({
        "id": sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("DELETE", url, headers=headers, data=payload)
    return response.json()


def get_overview():
    """ Get Overview over all DB entries """
    url = "http://" + Connector.url + ":" + Connector.port + "/simulation/overview"
    response = requests.request("GET", url, headers={}, data={})
    return response.json()


def start_simulation(sim_id, date_dict, param_dict):
    """Start simulation """
    url = "http://" + Connector.url + ":" + Connector.port + "/simulation/control"
    payload = json.dumps({
        "id": sim_id,
        "height": param_dict['Height'],
        "length": param_dict['Length'],
        "width": param_dict['Width'],
        "orientation": param_dict['Orientation'],
        "zone_name": param_dict['zone_name'],
        "start_day": date_dict['start_day'],
        "start_month": date_dict['start_month'],
        "start_year": date_dict['start_year'],
        "end_day": date_dict['end_day'],
        "end_month": date_dict['end_month'],
        "end_year": date_dict['end_year'],
        "infiltration_rate": param_dict['Infiltration']
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def check_simulation(sim_id):
    """ check simulation status """
    url = "http://" + Connector.url + ":" + Connector.port + "/simulation/control"
    payload = json.dumps({
        "id": sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def get_result(sim_id):
    """ get result for simulation id """
    url = "http://" + Connector.url + ":" + Connector.port + "/result"
    payload = json.dumps({
        "id": sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def get_result_csv(sim_id):
    """ Get result for simulation id formatted as csv """
    url = "http://" + Connector.url + ":" + Connector.port + "/result/csv"
    payload = json.dumps({"id": sim_id})
    headers = {'Content-Type': 'application/json'}
    response = requests.request("GET", url, headers=headers, data=payload)
    return response


def get_result_overview():
    """ returns all result entries """
    url = "http://" + Connector.url + ":" + Connector.port + "/result/overview"
    response = requests.request("GET", url, headers={}, data={})
    return response.json()


def get_metadata(sim_id):
    """ get metadata from simulation """
    url = "http://" + Connector.url + ":" + Connector.port + "/metadata"
    payload = json.dumps({
        "id": sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def start_simulation_only_idf(sim_id):
    """Start a simulation with just the idf- and the epw-file"""
    url = "http://" + Connector.url + ":" + Connector.port + "/simulation/control/onlyidf"
    payload = json.dumps({"id": sim_id})
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def get_reopensim(sim_id):
    """ reopen an old simulation """
    url = "http://" + Connector.url + ":" + Connector.port + "/reopensim"
    payload = json.dumps({
        "id": sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def get_idf_file(sim_id):
    """ get idf File for specific Simulation with sim_id from input simulation"""
    url = "http://" + Connector.url + ":" + Connector.port + "/idf"
    payload = json.dumps({
        'id': sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def get_epw_file(sim_id):
    """ get epw File for specific Simulation with sim_id from input simulation"""
    url = "http://" + Connector.url + ":" + Connector.port + "/weather"
    payload = json.dumps({
        'id': sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def get_csv_file(sim_id):
    """ get csv File for specific Simulation with sim_id from input simulation"""
    url = "http://" + Connector.url + ":" + Connector.port + "/occupancy"
    payload = json.dumps({
        'id': sim_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


class Connector:
    config = configparser.ConfigParser()
    config.read('frontend_config.ini')
    backend = config['Backend']
    url = str(backend['Address'])
    port = str(backend['Port'])
