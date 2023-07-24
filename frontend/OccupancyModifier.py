import logging
import os
import pandas as pd

file_base_path = './occupancy_cache/Base_OCP.csv'
file_modification_path = './occupancy_cache/Modify_OCP.csv'
file_finished_path = './occupancy_cache/Simulation_OCP.csv'


def discoverOccupancy(filePath):
    """
    Simple function to check if the base csv file exists
    :return Boolean True/False:
    """
    return os.path.isfile(filePath)


def loadCSV():
    """
    Simple function to lead the base csv file and transform it into a dataframe
    :return: base_frame dataframe with base information
    """
    try:
        base_frame = pd.read_csv(filepath_or_buffer=file_base_path, sep='|')
        return base_frame
    except Exception as e:
        logging.error("[OccupancyModifier]: Failed to load the base csv file. Error-Log: " + str(e))
        return None


def saveCSV(Dataframe):
    """
    Simple function to save a modified dataframe to the given path
    :param Dataframe: Modified pd.Dataframe
    """
    try:
        Dataframe.to_csv(file_finished_path, index=False, lineterminator='\n', sep='|')
        logging.info("[OccupancyModifier]: Successfully saved the modified base file.")
    except Exception as e:
        logging.error("[OccupancyModifier]: Failed to load the base csv file. Error-Log: " + str(e))


def loadChangeDataframe():
    """Function to load modification csv file"""
    try:
        modify_frame = pd.read_csv(file_modification_path, sep=',')
        return modify_frame
    except Exception as e:
        logging.error("[OccupancyModifier]: Failed to load the modification csv file. Error-Log: " + str(e))
        return None


def modifyBase(base_dataframe, mod_row):
    """
    Function to modify the base_dataframe based on the given row
    The base_dataframe will be searched until the fitting time slot is reached
    Until the mod_flag is false again: each row gets modified according to the given values
    :param base_dataframe: dataframe which should be changed according to the modification data
    :param mod_row: modification data (row of a dataframe)
    :return: Modified dataframe
    """
    try:
        day = mod_row.iat[0, 0]
        start_time = mod_row.iat[0, 1]
        end_time = mod_row.iat[0, 2]
        occupants = mod_row.iat[0, 3]
        window = mod_row.iat[0, 4]
        mod_flag = False
        for i in range(0, len(base_dataframe), 1):
            if base_dataframe.iat[i, 0] == day:
                if base_dataframe.iat[i, 1] == start_time:
                    mod_flag = True
                if base_dataframe.iat[i, 1] == end_time:
                    mod_flag = False
                    # This way the last row with the end time is included
                    if int(occupants) == 0:
                        base_dataframe.iat[i, 3] = window
                    else:
                        base_dataframe.iat[i, 2] = occupants
                        base_dataframe.iat[i, 3] = window
                if mod_flag:
                    if int(occupants) == 0:
                        base_dataframe.iat[i, 3] = window
                    else:
                        base_dataframe.iat[i, 2] = occupants
                        if int(window) == 1:
                            base_dataframe.iat[i, 3] = window

        return base_dataframe
    except Exception as e:
        logging.error("[OccupancyModifier]: Failed to modify the dataframe. Error-Log: " + str(e))
        return base_dataframe


def modifyCSV_Main():
    """
    Main function for the csv modification.
    Function loads and checks all dataframes required for the change.
    After the successful modification, the finished dataframe will be saved to a directory.
    """
    try:
        # Check if the base file exists
        if not discoverOccupancy(file_base_path):
            raise Exception("Base csv file does not exist!")
        base_frame = loadCSV()
        adjusted_frame = base_frame

        # Check if the modification file exists
        if not discoverOccupancy(file_modification_path):
            raise Exception("Modification csv file does not exist!")
        modify_frame = loadChangeDataframe()
        for i in range(0, len(modify_frame), 1):
            adjusted_frame = modifyBase(adjusted_frame, modify_frame.loc[[i]])
        saveCSV(adjusted_frame)
        return True
    except Exception as e:
        logging.error("[OccupancyModifier]: Failed to modify the base csv file. Error-Log: " + str(e))
        return None
