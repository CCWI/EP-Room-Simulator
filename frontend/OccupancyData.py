import json
import logging
import os.path
import sys
from datetime import datetime
import pandas as pd
from werkzeug.datastructures import MultiDict

file_modification_path = './occupancy_cache/Modify_OCP.csv'


def checkTimeFrame():
    """
    Simple function which determines if the timeframe exists --> is required in order to check if dataframe makes sense
    :return: Boolean
    """
    try:
        if os.path.exists("./meta_data/date.json"):
            return True
        else:
            raise Exception("[Occupancy]: The timeframe for the simulation could not be found.")
    except Exception as e:
        setErrorNotification(str(e))


def loadTimeFrame():
    """
    Loads the given date from the json file and stores them in an instantiated class
    """
    try:
        with open("./meta_data/date.json", 'r') as file:
            data = json.load(file)
            DataStorage.start_date = datetime.strptime(str(data['start_date']), '%Y-%m-%d').date()
            DataStorage.end_date = datetime.strptime(str(data['end_date']), '%Y-%m-%d').date()
    except Exception as e:
        setErrorNotification(str(e))


def saveCSV(Dataframe):
    """
    Simple function save a dataframe to a specific csv file. Can be moved to a utility file later on.
    :param Dataframe: Standard dataframe with all necessary modifications to be made
    :return:
    """
    try:
        Dataframe.to_csv(file_modification_path, lineterminator='\n', sep=',', index=False)
        logging.info("[OccupancyData]: Successfully saved the modification dataframe.")
    except Exception as e:
        logging.error(
            "[OccupancyData]: An unspecified error occurred while saving the modified dataframe. Log: " + str(e))
        setErrorNotification(str(e))


def extractData(webRequest):
    """
    This function gets the webrequest as raw unedited combined multi-dictionary and turns it into a usable dataframe
    :param webRequest: Combined multi dict directly from the webpage. Contains the table
    :return: Dataframe with the converted datasets
    """
    try:
        unrefined_table = MultiDict(webRequest.values)
        row_count = len(unrefined_table)
        base_dataframe = pd.DataFrame()
        for i in range(0, row_count, 1):
            row_data = []
            row_frame = pd.DataFrame()
            try:
                row_data = unrefined_table.getlist(f'javascript_data[{i}][]')
                row_frame = pd.DataFrame(row_data).T
            except Exception:
                continue
            base_dataframe = pd.concat([base_dataframe, row_frame], axis=0)

        base_dataframe.columns = ["Date", "Start (HH:MM)", "End (HH:MM)", "# People", "Window"]
        return base_dataframe
    except Exception as e:
        logging.error(
            "[OccupancyData]: An unspecified error occurred while extracting the data from the webrequest. Error-Log: " + str(
                e))
        setErrorNotification("The occupancy table is empty.")


def sortByDate(baseDataFrame):
    """
    Function that converts all strings in the date column int to datetime objects.
    After sorting the dates, the datetime objects will be returned as strings in order to be comparable to the dataframe.
    Possible to convert the entire column within the dataframe --> but is a potential error source
    :param baseDataFrame:
    :return:
    """
    try:
        initial_date_list = baseDataFrame['Date'].to_list()
        converted_dates = []
        sorted_dates = []
        sorted_dataframe = pd.DataFrame()
        for entry in initial_date_list:
            date_time_obj = datetime.strptime(str(entry), '%Y-%m-%d').date()
            converted_dates.append(date_time_obj)
        converted_dates = set(converted_dates)
        converted_dates = sorted(converted_dates)
        for entry in converted_dates:
            date = entry.strftime('%Y-%m-%d')
            sorted_dates.append(date)
        for entry in sorted_dates:
            entry_row = baseDataFrame.loc[baseDataFrame['Date'] == entry]
            if len(entry_row) > 1:
                time_sorted = sortByTime(entry_row)
                if time_sorted is None:
                    raise Exception("[Occupancy]: Failed to sort the rows by time.")
                else:
                    sorted_dataframe = pd.concat([sorted_dataframe, time_sorted], axis=0)
            else:
                sorted_dataframe = pd.concat([sorted_dataframe, entry_row], axis=0)
        return sorted_dataframe
    except Exception as e:
        logging.error(
            "[OccupancyData]: An unspecified error occurred while sorting the dataframe. Error-Log: " + str(e))
        setErrorNotification(str(e))


def sortByTime(DataFrame):
    """
    Works similar to sortByDate --> In this function everything gets sorted by the colum 'Start (HH:MM)'
    :param DataFrame: Part of the initial dataframe that contains rows with identical dates
    :return: dataframe sorted by start time
    """
    try:
        time_sorted = pd.DataFrame()
        initial_start_date = DataFrame['Start (HH:MM)'].to_list()
        sorted_start_date = []
        converted_start_date = []
        for entry in initial_start_date:
            time_obj = datetime.strptime(str(entry), '%H:%M').time()
            sorted_start_date.append(time_obj)
        sorted_start_date = sorted(sorted_start_date)
        for entry in sorted_start_date:
            time = entry.strftime('%H:%M')
            converted_start_date.append(time)

        for entry in converted_start_date:
            entry_row = DataFrame.loc[DataFrame['Start (HH:MM)'] == entry]
            time_sorted = pd.concat([time_sorted, entry_row], axis=0)

        return time_sorted
    except Exception as e:
        logging.error(
            "[OccupancyData]: An unspecified error occurred while sorting the dataframe. Error-Log: " + str(e))
        setErrorNotification(str(e))
        return None


def checkAndAdjustDate(dataframe):
    """
    Verify the given dates and adjust the values to fit the Base_OCP.csv layout
    :param dataframe: sorted dataframe returned after the sortByDate Function was executed
    :return: adjusted dataframe: dataframe with the new day values
    """
    try:

        for row in range(0, len(dataframe), 1):
            row_date = datetime.strptime(str(dataframe.iat[row, 0]), '%Y-%m-%d').date()
            day = (row_date - DataStorage.start_date).days
            if day >= 0 >= (row_date - DataStorage.end_date).days:
                dataframe.iat[row, 0] = day
            else:
                raise Exception(f"[Occupancy]: The given date ({row_date}) is not between the start and end date!")
        adjusted_dataframe = checkAndAdjustTime(dataframe)
        return adjusted_dataframe
    except Exception as e:
        logging.error(
            "[OccupancyData]: An unspecified error occurred while adjusting the dates of the dataframe. Error-Log: "
            + str(e))
        setErrorNotification(str(e))
        return None


def checkAndAdjustTime(dataframe):
    """
    Checking the given start and end times in two waves:
    First check verifies that the end time comes after the start time
    Second check looks for overlaps between the different entries
    :param dataframe: dataframe with adjusted dates
    :return: dataframe: dataframe with basic verification checks
    """
    try:
        # First check
        for row in range(0, len(dataframe), 1):
            start_time = datetime.strptime(str(dataframe.iat[row, 1]), '%H:%M').time()
            end_time = datetime.strptime(str(dataframe.iat[row, 2]), '%H:%M').time()
            if not start_time < end_time:
                if start_time == end_time:
                    raise Exception(
                        f"[Occupancy]: The given end time ({end_time}) cannot be identical to the given start time ({start_time})!")
                raise Exception(
                    f"[Occupancy]: The given end time ({end_time}) cannot be smaller than the given start time ({start_time})!")

        # Second check
        day_list = set(dataframe['Date'].to_list())
        for day in day_list:
            select_dataframe = dataframe.loc[dataframe['Date'] == day]
            if len(select_dataframe) > 1:
                current_index = 0
                for o_row in range(0, len(select_dataframe), 1):
                    # Get the start date and examine if it overlaps with any other timeframe
                    start_time = datetime.strptime(str(select_dataframe.iat[o_row, 1]), '%H:%M').time()
                    end_time = datetime.strptime(str(select_dataframe.iat[o_row, 2]), '%H:%M').time()
                    for i_row in range(0, len(select_dataframe), 1):
                        if i_row == current_index:
                            continue
                        else:
                            row_start_time = datetime.strptime(str(select_dataframe.iat[i_row, 1]), '%H:%M').time()
                            row_end_time = datetime.strptime(str(select_dataframe.iat[i_row, 2]), '%H:%M').time()
                            if row_start_time == end_time:
                                raise Exception(
                                    f"[Occupancy]: There are overlapping times at {row_start_time} o'clock in line "
                                    f"{i_row + 1} and {o_row + 1}.")
                            if row_start_time <= start_time < row_end_time:
                                raise Exception(
                                    f"[Occupancy]: There are multiple entries for an overlapping time slot "
                                    f"between {row_start_time} and {row_end_time}. "
                                    f"(Lines: {i_row + 1} and {o_row + 1})")
                            if row_start_time <= end_time < row_end_time:
                                raise Exception(
                                    f"[Occupancy]: There are multiple entries for an overlapping time slot "
                                    f"between {row_start_time} and {row_end_time}. "
                                    f"(Lines: {o_row + 1} and {i_row + 1})")
                    current_index += 1
            # Adjust time to HH:MM:SS-Format
        for row in range(0, len(dataframe), 1):
            dataframe.iat[row, 1] = str(dataframe.iat[row, 1]) + ":00"
            dataframe.iat[row, 2] = str(dataframe.iat[row, 2]) + ":00"
        return dataframe
    except Exception as e:
        logging.error(str(e))
        setErrorNotification(str(e))
        return None


def verifyOccupancyData(webRequest):
    """
    Function serves as initial check if the values entered on the webpage make any sense at all
    The values will be checked on whether they are within the given timeframe or if they contradict each other
    :param webRequest: Request generated by the table form in the html 'ocpCustom.html'
    """
    try:
        if not checkTimeFrame():
            return None
        loadTimeFrame()
        base_dataframe = extractData(webRequest)
        sorted_dataframe = sortByDate(base_dataframe)
        if sorted_dataframe is None:
            raise Exception("[Occupancy]: Failed to sort the dataframe.")
        adjusted_dataframe = checkAndAdjustDate(sorted_dataframe)
        saveCSV(adjusted_dataframe)
    except Exception as e:
        logging.error(
            "[OccupancyData]: An unspecified error occurred while verifying the data within the webrequest. Error-Log: " + str(
                e))
        setErrorNotification(str(e))


def setErrorNotification(Error):
    """
    Used to create a json file with the given error and stop the current thread (sys.exit())
    :param Error: error-string which should be written into the error file
    """
    error = {'Error': str(Error)}
    error_json = json.dumps(error, indent=1)
    with open("./meta_data/ocp_error.json", "w") as file:
        file.write(error_json)
    sys.exit()


class DataStorage:
    start_date = None
    end_date = None
