import time
import logging
import threading
import eppy.runner.run_functions

import utils
import converterEsoToCsv
from utils import read_from_conf
from Room_Helper import Room_Helper
from Simulation_Helper import Simulation_Helper
from db_controller import get_epw_data, get_idf_data, insert_result, save_metadata, get_output_simulation, get_metadata

logging.basicConfig(level=logging.INFO)

QUEUE = []
IDD_PATH = read_from_conf("EnergyPlus", "iddPath")
co2_outdoor = int(read_from_conf("EnergyPlus", "co2OutdoorValue"))


def start_simulation_worker(sim_id):
    """
    start a simulation for a given ID
    :param sim_id: Simulation ID
    """
    # global RUN
    global QUEUE
    # RUN = True
    logging.info("[simulation_worker]: " + time.strftime("%Y-%m-%d %H:%M:%S") + " - waiting for simulation jobs")
    logging.info("[simulation_worker]: started simulation for sim_id: " + sim_id + " at "
                 + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    try:
        # add id to queue for status 'in Progress'
        QUEUE.append(sim_id)
        metadata = get_metadata(sim_id)
        run(sim_id, metadata)
    except ValueError as e:
        logging.error("Value error " + str(e))
        insert_result(sim_id, "", str(e))
    except StopIteration as e:
        logging.error("corrupted csv was used " + str(e))
        insert_result(sim_id, "", "corrupted CSV-file")
    except eppy.runner.run_functions.EnergyPlusRunError as e:
        logging.error("EnergyPlus returned an Error, please check epw file, metadata energy-plus filepaths " +
                      "and the following energyplus error message: " + str(e))
        insert_result(sim_id, "", "EnergyPlus Error - check the error-file (...\\backend\\eppy_output\\eplusout.err)")
    except IndexError as e:
        logging.error("Index error: " + str(e))
        insert_result(sim_id, "", "Index error: " + str(e))
    except FileNotFoundError as e:
        logging.error("FileNotFoundError: " + str(e))
        insert_result(sim_id, "", str(e))
    except Exception:
        raise
    finally:
        # remove id from queue for status
        QUEUE.remove(sim_id)


def start_simulation_thread(sim_id, meta_data_dict=None):
    """
    saves metadata for simulation and starts simulation in separate thread
    :param sim_id: id of simulation
    :param meta_data_dict: metadata for simulation
    """
    if meta_data_dict is not None:
        save_metadata(sim_id, meta_data_dict)
    simulation_worker_thread = threading.Thread(target=start_simulation_worker,
                                                args=[sim_id], daemon=True)
    simulation_worker_thread.start()


def check_simulation_status(sim_id):
    """
    simulation status lookup
    :param sim_id: id of simulation
    :return: dictionary with status of simulation
    """
    value = {'status': ''}
    if sim_id in QUEUE:
        value['status'] = 'in Progress'
        return value
    else:
        try:
            value['status'] = get_output_simulation(sim_id)['status']
        except Exception as e:
            value['status'] = "No Status found for " + str(sim_id)
            logging.error("[Simulation] Exception during simulation status check: " + str(e))
        finally:
            return value


def run(input_id, meta_data_dict):
    """
    Runs a Simulation for a given db_id, idf file can be given
    :param input_id: simulation id of the started simulation
    :param meta_data_dict: dictionary object which contains necessary data for energy plus (e.g. infiltration rate,
    start and end period, room params)
    :return: objectID of saved result document in the simulation_results collection
    """
    # reading the required files out of mongodb. inputIDF and epw is read from database
    # rest is read from config file and from tmp folder
    idf_file = "tmp/adjustedIDF.idf"
    get_idf_data(input_id, "room.idf")
    idf_room_file = "tmp/room.idf"
    get_epw_data(input_id, "Weatherfile.epw")
    epw_file = "tmp/Weatherfile.epw"
    idd_file = read_from_conf("EnergyPlus", "iddPath")

    if all(value == '' for value in meta_data_dict.values()):
        simulation_helper = Simulation_Helper(idf_room_file, epw_file, idd_file)
        simulation_helper.request_zone_temperature()
        simulation_helper.request_zone_air_co2_concentration()
        simulation_helper.request_site_outdoor_air_barometric_pressure()
        simulation_helper.request_site_outdoor_air_drybulb_temperature()
        simulation_helper.request_zone_air_humidity()

        simulation_helper.run_simulation(input_id)

        # create byte64 strings in simulation helper class
        idf_string = simulation_helper.save_output_idf(input_id)
        simulation_helper.save_output_eso(input_id)
        status = "done"

        # Save result in output collection and return object id of inserted output
        result_set = insert_result(input_id, idf_string, status)
        return result_set
    else:
        # Calculation of infiltration rate. Volume flow rate is needed for energyplus.
        infiltration_rate = meta_data_dict["infiltration_rate"]
        volume_flow_infiltration_rate = utils.mass_flow_rate_to_volume_flow_rate(infiltration_rate)

        # Error handling of the given metadata
        if meta_data_dict["width"] <= 0 or meta_data_dict["length"] <= 0 or meta_data_dict["height"] <= 0:
            raise ValueError("room size invalid")
        if meta_data_dict["start_day"] <= 0 \
                or meta_data_dict["start_month"] <= 0 \
                or meta_data_dict["start_year"] <= 0 \
                or meta_data_dict["end_day"] <= 0 \
                or meta_data_dict["end_month"] <= 0 \
                or meta_data_dict["end_year"] <= 0:
            raise ValueError("run period invalid")
        if meta_data_dict["infiltration_rate"] < 0:
            raise ValueError("infiltration rate invalid")

        # beginning of room size adjustment
        room_helper = Room_Helper(idf_room_file, epw_file, idd_file)

        # identification of zone name (pick first one from idf file)
        zone = room_helper.getFirstZoneNameFromIDF()
        logging.info("simulating zone: " + zone)

        # beginning of changing the room size, the stored idf in input mongoDB is used to make a new
        # adjustedIDF.idf file which gets an occupancy schedule in later steps
        room_helper.updateRoomSize(meta_data_dict["width"], meta_data_dict["length"], meta_data_dict["height"])
        room_helper.updateOrientation(meta_data_dict["orientation"] % 360)
        # end of room size adjustment, new adjustedIDF.idf is stored in tmp

        # begin to modify other parameters of the adjustedIDF.idf with new room size
        simulation_helper = Simulation_Helper(idf_file, epw_file, idd_file)
        # fix hvac
        simulation_helper.update_heating_limit_of_airflow_and_sensible_heating_capacity("Autosize", "Autosize")

        simulation_helper.set_run_period(meta_data_dict["start_year"], meta_data_dict["start_month"],
                                     meta_data_dict["start_day"], meta_data_dict["end_year"],
                                     meta_data_dict["end_month"], meta_data_dict["end_day"])

        # use constant co2 outer values to plot co2 results
        simulation_helper.add_constant_carbon_dioxide_schedule(co2_outdoor)

        # change infiltration rate
        simulation_helper.update_infiltration_rate_in_design_flow_rate_object(volume_flow_infiltration_rate)

        # Request values to show them in the resulting .ESO-file
        simulation_helper.request_zone_temperature()
        simulation_helper.request_zone_air_co2_concentration()
        simulation_helper.request_site_outdoor_air_barometric_pressure()
        simulation_helper.request_site_outdoor_air_drybulb_temperature()
        simulation_helper.request_zone_air_humidity()

        co2_generation_rate = float(read_from_conf("EnergyPlus", "co2GenerationRate"))
        activity_level = float(read_from_conf("EnergyPlus", "ActivityLevel"))

        # beginning of adding the occupancy with people and window openings
        # all data will be retrieved of the provided csv stored by id in the input_simulation schema
        csv_column_of_occupancy = 2
        csv_column_of_windows = 3

        max_number_of_occupants = utils.get_maximum_occupants(input_id)
        start_date = "{}-{}-{}".format(meta_data_dict["start_year"], meta_data_dict["start_month"],
                                   meta_data_dict["start_day"])
        end_date = "{}-{}-{}".format(meta_data_dict["end_year"], meta_data_dict["end_month"], meta_data_dict["end_day"])
        run_period = (start_date, end_date)

        # start of the scheduling block
        utils.correct_csv_data(input_id, run_period)
        occupancy_data = utils.read_from_csv_file_as_fractional(input_id, max_number_of_occupants,
                                                                csv_column_of_occupancy)
        ventilation_data = utils.read_from_csv_as_0_1_values(input_id, csv_column_of_windows)

        simulation_helper.set_occupancy(zone, run_period, occupancy_data, max_number_of_occupants, co2_generation_rate,
                                        activity_level)
        simulation_helper.set_ventilation(zone, run_period, ventilation_data)
        # end of the scheduling block

        # run simulation and store outputs in eppy_output directory
        simulation_helper.run_simulation(input_id)

        # create byte64 strings in simulation helper class
        idf_string = simulation_helper.save_output_idf(input_id)
        simulation_helper.save_output_eso(input_id)
        converter = converterEsoToCsv.DataConverterEsoCsv(input_id)
        converter.GatherAllData()
        status = "done"

        # Save result in output collection and return object id of inserted output
        result_set = insert_result(input_id, idf_string, status)
        return result_set
