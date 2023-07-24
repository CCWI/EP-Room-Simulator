import base64
import logging
import os
from pathlib import Path


def encodeFile(filename, data_type):
    """
    Main function which retrieves the file, encodes it as byte 64 file and saves it in the 64_cache directory
    :param filename: String --> Is required to detect the correct file based on the given name
    :param data_type: String --> Determines which directory is used
    """
    try:
        if data_type == "idf":
            file = getIDFFile(filename)
        elif data_type == "csv":
            file = getCSVFile(filename)
        elif data_type == "epw":
            file = getEPWFile(filename)
        else:
            raise Exception("Invalid type!")
        if file is None:
            raise Exception("The requested file could not be found.")
        input_filename = filename.split(".")[0]
        output_file = os.getcwd() + '/64_cache/' + str(input_filename) + '_' + str(data_type) + '_converted64.dat'
        base64.encode(open(file, 'rb'), open(output_file, 'wb'))
    except Exception as e:
        logging.error("[FileEncoder]: An unspecified error occurred during the file encoding. Log: " + str(e))


def getIDFFile(filename):
    """
    Checks the idf cache directory for the given filename
    :param filename: String --> used for the file identification
    :return: file or None
    """
    try:
        file = os.getcwd() + '/idf_cache/' + str(filename) + '.idf'
        # Check whether file really exists
        fileCheck = Path(file)
        if fileCheck.is_file():
            return file
        else:
            return None
    except Exception as e:
        logging.error("[FileEncoder]: An unspecified error occurred during the idf file retrieval. Log " + str(e))


def getCSVFile(filename):
    """Identical to IDF-File"""
    try:
        file = os.getcwd() + '/occupancy_cache/' + str(filename) + '.csv'
        # Check whether file really exists
        fileCheck = Path(file)
        if fileCheck.is_file():
            return file
        else:
            raise Exception(f'[FileEncoder]: The requested file ({filename}.csv could not be found.')
    except Exception as e:
        logging.error("[FileEncoder]: An unspecified error occurred during the csv file retrieval. Log " + str(e))


def getEPWFile(filename):
    """Identical to IDF-File"""
    try:
        file = os.getcwd() + '/epw_cache/' + str(filename) + '.epw'
        # Check whether file really exists
        fileCheck = Path(file)
        if fileCheck.is_file():
            return file
        else:
            raise Exception("File does not exist!")
    except Exception as e:
        logging.error("[FileEncoder]: An unspecified error occurred during the epw file retrieval. Log " + str(e))
        return None


def extractString(filename, data_type):
    """
    Extracts the file content as string based on the given file name and data type
    :param filename: str --> determines file
    :param data_type: str --> determines file
    :return: file_data as string
    """
    try:
        if filename is None:
            return None
        input_filename = filename.split(".")[0]
        output_file = os.getcwd() + '/64_cache/' + str(input_filename) + '_' + str(data_type) + '_converted64.dat'
        b64file = open(output_file, 'rb')
        file_data = b64file.read()
        return file_data
    except Exception as e:
        logging.error(
            "[FileEncoder]: An unspecified error occurred during data extraction from the given file. Log:" + str(e))



def b64Decoder(string):
    """
    Used to decode a b64 into a normal string with utf-8 coding
    :param string: b64-string
    :return: utf-8 string
    """
    safe_encode = base64.b64decode(string).decode('utf-8')
    return safe_encode
