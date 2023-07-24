import os
import logging
import threading
from eppy.modeleditor import IDF

import utils
import simulation
import db_controller

SIM_SERIES_QUEUE = []


def create_sim_series(meta_data_dict):
    """
    Create the simulation ids
    :param meta_data_dict: Dictionary with values for the 5 parameters
    :return: Simulation series id
    """
    check_simulation_parameters(meta_data_dict)

    sim_ids = []
    sim_series_id = db_controller.create_Simulation_Series()
    i = 1
    height_list = calc_param_list(meta_data_dict["height"], meta_data_dict["height_max"], meta_data_dict["height_iter"])
    width_list = calc_param_list(meta_data_dict["width"], meta_data_dict["width_max"], meta_data_dict["width_iter"])
    length_list = calc_param_list(meta_data_dict["length"], meta_data_dict["length_max"], meta_data_dict["length_iter"])
    orientation_list = calc_param_list(meta_data_dict["orientation"], meta_data_dict["orientation_max"],
                                       meta_data_dict["orientation_iter"])
    infiltration_list = calc_param_list(meta_data_dict["infiltration_rate"], meta_data_dict["infiltration_rate_max"],
                                        meta_data_dict["infiltration_rate_iter"])

    for x_height in height_list:
        for x_width in width_list:
            for x_length in length_list:
                for x_orientation in orientation_list:
                    for x_infiltration in infiltration_list:
                        # 1. step: Create simIds and put them in a list
                        sim_id = db_controller.get_new_objectID()
                        sim_ids.append(sim_id)

                        # 2. step: save the simIds in the simulationSeries Collection
                        db_controller.update_simSer(sim_series_id, "input_" + str(i), str(sim_id))
                        i += 1

                        # 3. step: save the different variations of rooms
                        meta_data_dict_actual = {
                            "height": x_height,
                            "width": x_width,
                            "length": x_length,
                            "orientation": x_orientation,
                            "start_day": meta_data_dict["start_day"],
                            "start_month": meta_data_dict["start_month"],
                            "start_year": meta_data_dict["start_year"],
                            "end_day": meta_data_dict["end_day"],
                            "end_month": meta_data_dict["end_month"],
                            "end_year": meta_data_dict["end_year"],
                            "infiltration_rate": x_infiltration,
                            "zone_name": "zone_name"}
                        db_controller.save_metadata(sim_id, meta_data_dict_actual)
    return sim_series_id


def check_simulation_parameters(meta_data_dict):
    """
    Check the simulation parameters for consistency
    :param meta_data_dict: simulation series parameters
    :return: no return value, raises Exception
    """
    if meta_data_dict["height"] <= 0 or meta_data_dict["height_max"] <= 0:
        raise ValueError("The Height cannot be 0 or negative!")
    if meta_data_dict["length"] <= 0 or meta_data_dict["length_max"] <= 0:
        raise ValueError("The Length cannot be 0 or negative!")
    if meta_data_dict["width"] <= 0 or meta_data_dict["width_max"] <= 0:
        raise ValueError("The Width cannot be 0 or negative!")
    if meta_data_dict["height_iter"] == 0 or meta_data_dict["length_iter"] == 0 or meta_data_dict["width_iter"] == 0:
        logging.info("Iteration step 0 found. Only minimum Value used.")


def calc_param_list(min_val, max_val, step_size):
    """
    Calculate the number of variations for a given min, max, iterator set
    If the iterator is set to 0 only the starting value is returned
    => while max_value >= min_value + n*step_size if min < max
    => while max_value <= min_value - n*step_size if min > max
    :param min_val: start value
    :param max_val: end value
    :param step_size: the step size
    :return: list with values to iterate over
    """
    result = []
    current_val = min_val
    if step_size == 0 or min_val == max_val:
        result.append(current_val)
    elif min_val < max_val and step_size != 0:
        while current_val <= max_val:
            result.append(current_val)
            current_val += abs(step_size)
    elif min_val > max_val and step_size != 0:
        while current_val >= max_val:
            result.append(current_val)
            current_val -= abs(step_size)
    if len(result) == 0:
        raise ValueError("[Simulation Series Initializing] Bad Parameters in Dictionary")
    return result


def modifyOccupancyData(sim_Ser_Id, data):
    """
    Defines the csv_data for all simulation series ids, saves it in the database
    :param sim_Ser_Id: Simulation Series ID
    :param data: Occupancy data
    """
    try:
        sim_ids = db_controller.get_simSer_idList(sim_Ser_Id)
        for i in sim_ids:
            db_controller.modify_csv_data(i, data)
    except Exception as e:
        logging.error(str(e))


def modifyWeatherData(sim_Ser_Id, data):
    """
    Defines the weather data for all simulation series ids, saves it in the database
    :param sim_Ser_Id: Simulation Series ID
    :param data: E+ epw file
    """
    try:
        sim_ids = db_controller.get_simSer_idList(sim_Ser_Id)
        for i in sim_ids:
            db_controller.modify_epw_data(i, data)
    except Exception as e:
        logging.error(str(e))


def modifyRoomData(sim_Ser_Id, data):
    """
    Defines the room data for all simulations, saves it in the database
    :param sim_Ser_Id: Simulation Series ID
    :param data: E+ idf file
    """
    try:
        sim_ids = db_controller.get_simSer_idList(sim_Ser_Id)
        for sim_id in sim_ids:
            db_controller.modify_idf_data(sim_id, data)
    except Exception as e:
        logging.error(str(e))


def update_zone_name(sim_id):
    """
    Update the zone name in the meta dictionary. Config is updated later.
    :param sim_id: simulation id for a single sim
    """
    idd_file = utils.read_from_conf("EnergyPlus", "iddPath")
    IDF.setiddname(idd_file)
    epw_file = os.getcwd() + '/tmp/Weatherfile.epw'
    db_controller.get_idf_data(sim_id, "Output.idf")
    idf_file = os.getcwd() + '/tmp/Output.idf'
    file = IDF(idf_file, epw_file)
    zone_value = file.idfobjects['Zone'][0].Name
    meta_data_dict = db_controller.get_metadata(sim_id)
    meta_data_dict['zone_name'] = zone_value
    db_controller.save_metadata(sim_id, meta_data_dict)


def start_simulation_series(sim_Ser_Id):
    """
    start simulation_series_worker in separate thread
    :param sim_Ser_Id: id of simulation series
    """
    sim_ser_worker_thread = threading.Thread(target=simulation_series_worker, args=[sim_Ser_Id], daemon=True)
    sim_ser_worker_thread.start()


def simulation_series_worker(sim_Ser_Id):
    """
       start series of simulations, analog to the simulation_worker in the simulation.py file
       :param sim_Ser_Id: Simulation Series ID
       """
    global SIM_SERIES_QUEUE
    result_set = []
    try:
        SIM_SERIES_QUEUE.append(sim_Ser_Id)
        sim_ids = db_controller.get_simSer_idList(sim_Ser_Id)
        for sim_id in sim_ids:
            db_controller.check_files(sim_id)
            update_zone_name(sim_id)
            simulation_worker_thread = threading.Thread(target=simulation.start_simulation_worker,
                                                        args=[sim_id], daemon=True)
            simulation_worker_thread.start()
            simulation_worker_thread.join()
            result_id = db_controller.get_output_simulation(sim_id)['_id']
            result_set.append(result_id)
        i = 1
        for result_id in result_set:
            db_controller.update_simSer(sim_Ser_Id, "output_" + str(i), str(result_id))
            i += 1
    except Exception as e:
        logging.error("[Simulation Series Worker] Failed calculating the simulation series" + str(e))
    finally:
        SIM_SERIES_QUEUE.remove(sim_Ser_Id)


def check_simulation_status(sim_Ser_Id):
    """
    Check the status of a series
    :param sim_Ser_Id: Simulation Series ID
    :return: Simulation Series progress
    """
    value = {'status': ''}
    if sim_Ser_Id in SIM_SERIES_QUEUE:
        value['status'] = 'in Progress'
        return value
    else:
        try:
            input_list = db_controller.get_simSer_idList(sim_Ser_Id)
            output_list = db_controller.get_simSer_idList(sim_Ser_Id, False)
            if len(input_list) == len(output_list):
                value['status'] = 'Done'
        except TypeError:
            value['status'] = "No Status found for " + str(sim_Ser_Id)
        finally:
            return value
