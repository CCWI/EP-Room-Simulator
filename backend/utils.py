import os
import base64
import logging
import configparser
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

import db_controller

""" this file contains generic utility functions for backend actions """

conf_name = "config.ini"


def get_date():
    """
    gets the current date with datetime method in format Y-M-D-H:M
    :return: date object
    """
    date = datetime.today().strftime('%Y-%m-%d-%H:%M')
    return date


def get_date_for_filename():
    """
    gets the current date with datetime method in format S-Millisecond
    :return: date object
    """
    date = datetime.today().strftime('%S%f')
    return date


def get_filename(file):
    """
    retrieves the filename
    :param file: file for which the name should be retrieved
    :return: string object with filename
    """
    filename = os.path.basename(file)
    return filename


def get_file_path(filename):
    """
    retrieves the filepath, search directory: ./backend/tmp
    :param filename: file to search
    :return: file path
    """
    try:
        file = os.getcwd() + '/tmp/' + str(filename)
        file_check = Path(file)
        if file_check.is_file():
            return file
        else:
            return None
    except Exception as e:
        logging.error("An unspecified error occurred during the file retrieval. Log " + str(e))


def encode_file_to_base64(filename, output_filename=None):
    """
    Encode a file from tmp/ folder into base64
    :param filename: filename of input file
    :param output_filename: if filename is given, output will be saved in file
    :return: string or file_path of encoded data, depends on output_filename
    """
    try:
        file_path = get_file_path(filename)
        if output_filename is None:
            input_file = open(file_path, 'rb')
            input_data = input_file.read()
            input_file.close()
            return base64.encodebytes(input_data).decode('utf-8')
        else:
            output_file_path = os.getcwd() + '/tmp/' + output_filename
            input_file = open(file_path, 'rb')
            output_file = open(output_file_path, 'wb')
            base64.encode(input_file, output_file)
            input_file.close()
            output_file.close()
            return output_file_path
    except Exception as e:
        logging.error("An unspecified error occurred during the file encoding. Log: " + str(e))


def encode_byte_data_to_base64(byte_data, output_filename=None):
    """
    encodes byte data to base64 and returns it or writes it in a file
    :param byte_data: byte data for encoding
    :param output_filename: if filename is given, output will be saved in file
    :return: string or file_path of encoded data, depends on output_filename
    """
    if output_filename is None:
        return base64.encodebytes(byte_data).decode('utf-8')
    else:
        output_file_path = os.getcwd() + '/tmp/' + output_filename
        open(output_file_path, 'wb').write(base64.encodebytes(byte_data))
        return output_file_path


def decode_from_base64_string(base64_string, output_filename=None):
    """
    Decode a base64 string into string or safe as file
    :param base64_string: input base64 string
    :param output_filename: if filename is given, output will be saved in file
    :return: string or file_path of decoded data, depends on output_filename
    """
    decoded_bytes = base64.decodebytes(base64_string.encode('utf-8'))
    decoded_string = decoded_bytes.decode('utf-8')
    if output_filename is None:
        return decoded_string
    else:
        output_file_path = os.getcwd() + '/tmp/' + output_filename
        output_file = open(output_file_path, "wb")
        output_file.write(decoded_bytes)
        output_file.close()
        return output_file_path


def mass_flow_rate_to_volume_flow_rate(mass_flow_infiltration_rate: float, mass_of_air: float = 1.2041):
    """
    Convert mass flow infiltration rate to volume flow infiltration rate, which is used in EnergyPlus.
    :param mass_flow_infiltration_rate: mass flow infiltration rate
    :param mass_of_air: mass of the air (default: 1.2041)
    :return: the division of the two parameters
    """
    return mass_flow_infiltration_rate / mass_of_air


def read_from_csv_file_as_fractional(input_id, max_number_of_occupants: int,
                                     csv_column: int):
    """
    Read values from CSV-file, divided by "|"-character, and returns an array of floats as fractional from a given
    maximum (highest_value).
    :param input_id: input sim id to get the right occupancy data
    :param max_number_of_occupants: the maximum number of people in a room
    :param csv_column: the colum in the csv-file where the occupancy is saved
    :return: numpy array arranged for each day with 1440 elements each
    """
    file_path = db_controller.get_csv_data(input_id, "occupancy.csv")
    df = pd.read_csv(file_path, sep="|")
    data = df[df.columns[csv_column]]
    data = data / max_number_of_occupants
    data = np.array(data).reshape(-1, 1440)
    return data


def read_from_csv_as_0_1_values(input_id, csv_column: int):
    """
    Rad values from CSV-file, and return an array of 1 and 0
    :param input_id: input sim id to get the right window data
    :param csv_column: the column in the csv-file where the window status is saved
    :return: numpy array arranged for each day with 1440 elements each
    """
    file_path = db_controller.get_csv_data(input_id, "occupancy.csv")
    df = pd.read_csv(file_path, sep="|")
    data = df[df.columns[csv_column]]
    data = np.array(data).reshape(-1, 1440)
    return data


def correct_csv_data(input_id, run_period):
    """
    correct the occupancy file: build an occupancy file with the same length as the simulation time frame
    :param input_id: input sim id to get the right window data
    :param run_period: Simulation timeframe, needed to calculate the length of the occupancy file
    :result: no return, but corrected csv-file in the database
    """
    file_path = db_controller.get_csv_data(input_id, "occupancy.csv")
    df = pd.read_csv(file_path, sep="|", index_col=False)

    number_of_days = (datetime.strptime(run_period[1], '%Y-%m-%d') -
                      datetime.strptime(run_period[0], '%Y-%m-%d')).days + 1

    while number_of_days > len(np.array(df[df.columns[0]]).reshape(-1, 1440)):
        day_value = len(np.array(df[df.columns[0]]).reshape(-1, 1440))
        df = pd.concat([df, read_from_csv_as_empty_data(day_value)], ignore_index=True)

    save_path = get_file_path("occupancy.csv")
    df.to_csv(save_path, sep="|", index=False)

    with open(save_path, 'rb') as f:
        encoded_object = base64.encodebytes(f.read()).decode('utf-8')

    db_controller.modify_csv_data(input_id, encoded_object)


def read_from_csv_as_empty_data(day_value: int = 0):
    """
    Get function for a single day with an empty occupancy and closed windows
    :param day_value: The day in the simulation for which the dataframe is put in (default = 0)
    :return: dataframe with 1440 entries for every minute of a day
    """
    file_path = get_file_path("Simulation_ZeroOCP_ShutWIN.csv")
    df = pd.read_csv(file_path, sep="|", index_col=False)
    df[df.columns[0]] = day_value
    return df


def get_maximum_occupants(input_id, ignore_header=True):
    """
    retrieves the maximum occupants of an occupancy csv file to use for fractional value calculation
    :param input_id: Simulation ID of the running simulation
    :param ignore_header: specifies, if csv headers should be ignored (for iteration purposes)
    :return: The highest number of the occupants column as dataframe
    """
    file_path = "tmp/occupancy.csv"
    csv_string = db_controller.get_csv_data(input_id)
    csv_data = open("tmp/occupancy.csv", "w")
    csv_data.write(csv_string)
    with open(file_path) as csv_file:
        if ignore_header:
            headers = next(csv_file)
        df = pd.read_csv(csv_file, sep='|', index_col=False,
                         names=['day', 'time', 'occupants', 'win1'])
        max_number_of_occupants = df['occupants'].max()
    csv_file.close()
    return max_number_of_occupants


def read_from_conf(section, key):
    """
    get value from the backend config file
    :param section: the section index
    :param key: key-value-pair
    :return: value to the key
    """
    config = configparser.ConfigParser()
    config.read(conf_name)
    return config.get(section, key)


def write_to_conf(section, key, value):
    """
    write value from the backend config file
    :param section: the section index
    :param key: key-value-pair
    :param value: value to write
    """
    config = configparser.ConfigParser()
    config.read(conf_name)
    config.set(section, key, value)
    with open(conf_name, 'w') as conf_file:
        config.write(conf_file)
