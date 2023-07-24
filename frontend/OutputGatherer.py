import configparser
import csv
import glob
import logging
import os
import json
import pandas as pd
from datetime import datetime, timedelta


class DataGatherer:
    """
    Build as a class for easier usage
    """
    base_directory = os.getcwd() + '/output_data/'
    plotting_background_color = 'white'

    def __init__(self):
        self.path = self.base_directory + "result.eso"
        self.new_path = self.base_directory + "result_adjusted.eso"

    def getZoneNameFromESO(self):
        """Returns the zone name used in an eso file (based on the first occurence of 'Zone Air Temperature [C] !TimeStep')"""
        with open(self.new_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            for row in csv_reader:
                if (len(row) > 3) and (row[3] == 'Zone Air Temperature [C] !TimeStep'):
                    return row[2]
    def getZoneValue(self, value: str, zone: str =None):
        """
        Searches for the given value and zone (view definition in retrieve data) and returns the id of the value
        Each value has its own id and is used within the eso file to encode it
        Therefore this function is required for the identification of the values
        :param value: name of the searched value (e.g.Zone Air Temperature [C] !TimeStep)
        :param zone: name of the zone (e.g. Zone_1); if not provided, the zone name is read from the file
        :return: int id of the given value
        """
        try:
            if zone == None:
                zone = self.getZoneNameFromESO()
            with open(self.new_path) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=",")
                for row in csv_reader:
                    if len(row) > 3 and (row[2] == zone.upper() or row[2] == zone.lower() or row[2] == zone) and \
                            row[3] == value:
                        return row[0]
            raise Exception("Not found")
        except Exception as e:
            logging.error("[Gatherer]: Failed to retrieve zone value. Log: " + str(e))

    def retrieve_data(self, value:str, zone:str=None):
        """
        Function is generally identical to the base work --> modification due to being completely rewritten and adjusted
        :param value: name of the searched value (e.g.Zone Air Temperature [C] !TimeStep)
        :param zone: name of the zone (e.g. Zone_1); if not provided, the zone name is read from the file
        :return: found values are appended to an array and returned
        """
        dataset = []
        enableDataCollection = False
        try:
            if zone == None:
                zone = self.getZoneNameFromESO()

            # Identify which id the requested value has in order to identify the data belonging to this tag
            # Two zones present: "Environment" for outside measurements
            row_id = self.getZoneValue(value, zone)

            # Read file for the identified id
            with open(self.new_path) as eso_file:
                eso_reader = csv.reader(eso_file, delimiter=',')
                for row in eso_reader:
                    # Read the file row-wise: the data begins after the data dictionary
                    if (len(row)) > 1 and row[1] == "RUNPERIOD":
                        enableDataCollection = True

                    if enableDataCollection and row[0] == row_id and len(row) == 2:
                        dataset.append(float(row[1]))

                return dataset
        except Exception as e:
            logging.error(f"[Gatherer]: Failed to retrieve data for {value}. Log: " + str(e))
            return dataset

    def GatherAllData(self):
        """
        Main function: as the name suggests the data required for the plot is gathered here
        Every variable is collected as an array and turned into a dataframe (all_data_df)
        The zone variable is important for the collection and needs to be adjusted if the variable changes within
        the idf-file
        :return: all_data_df
        """
        # Create a dataframe with all simulated values. Combine it with occupancy
        if os.path.exists('./meta_data/date.json'):
            with open('./meta_data/date.json') as json_file:
                date_dict = json.load(json_file)
        startDate = date_dict['start_date']
        endDate = date_dict['end_date']
        self.removeLines()
        outdoor = "Environment"
        try:
            zone_air_temperature = self.retrieve_data("Zone Air Temperature [C] !TimeStep")

            zone_co2_concentration = self.retrieve_data("Zone Air CO2 Concentration [ppm] !TimeStep")

            zone_rel_humidity = self.retrieve_data("Zone Air Relative Humidity [%] !TimeStep")

            outdoor_air_pressure = self.retrieve_data("Site Outdoor Air Barometric Pressure [Pa] !TimeStep",
                                                      zone=outdoor)

            outdoor_air_drybulb = self.retrieve_data("Site Outdoor Air Drybulb Temperature [C] !TimeStep", zone=outdoor)

            timeframe = self.createTimeFrame(startDate, endDate)

            windows = self.gatherWindows()

            occupancy = self.gatherOccupancy()

            all_data_df = pd.DataFrame(list(
                zip(timeframe, zone_air_temperature, zone_co2_concentration, zone_rel_humidity, outdoor_air_pressure,
                    outdoor_air_drybulb, occupancy, windows)),
                columns=["time", "zone_air_temperature", "zone_co2_concentration", "zone_rel_humidity",
                         "outdoor_air_pressure",
                         "outdoor_air_drybulb", "occupancy", "window"])

            all_data_df.set_index("time", inplace=True)
            all_data_df.to_json(self.base_directory + '/output_df.json')
            return all_data_df

        except Exception as e:
            logging.error("[Gatherer]: Failed to get all data. Log: " + str(e))

    def createTimeFrame(self, startDate, endDate):
        """
        In order to plot the date correctly a timeframe is necessary
        The timestamps from the occupancy can't be used since they don't have date
        The function creates an array based on the given start and end date
        :param startDate: string based date as used in the ocpCustom
        :param endDate: identical to start date
        :return: array with entries per minute
        """
        try:
            counter = 0
            # Create a custom timeframe to serve as an x-Axis for the graph
            start_date = datetime.strptime(startDate, '%Y-%m-%d')
            end_date = datetime.strptime(endDate, '%Y-%m-%d')
            time_list = []
            current_date = start_date

            if current_date == end_date:
                while counter < 1440:
                    counter += 1
                    time_list.append(current_date.strftime('%Y-%m-%d %H:%M'))
                    current_date += timedelta(minutes=1)
            else:
                while current_date != end_date:

                    time_list.append(current_date.strftime('%Y-%m-%d %H:%M'))
                    current_date += timedelta(minutes=1)
                while counter < 1440:
                    # Without this counter the last date would be missing
                    counter += 1

                    time_list.append(current_date.strftime('%Y-%m-%d %H:%M'))
                    current_date += timedelta(minutes=1)

            return time_list
        except Exception as e:
            logging.error("[Gatherer]: Failed to create timeframe. Log: " + str(e))

    def gatherOccupancy(self):
        """
        Reads the used occupancy from the cache and converts the entries to a list
        :return: array with occupants values
        """
        try:
            root = os.getcwd() + '/occupancy_cache'
            if os.path.exists(root + '/Simulation_OCP.csv'):
                file_path = os.path.join(root, 'Simulation_OCP.csv')
                dataframe = pd.read_csv(file_path, sep="|")
                return dataframe['occupants'].values
            else:
                file_path = glob.glob('./occupancy_cache/*.csv')[0]
                dataframe = pd.read_csv(file_path, sep="|")
                return dataframe['occupants'].values
        except Exception as e:
            logging.error("[Gatherer]: Failed to gather the existing occupancy file. Error-Log: " + str(e))

    def gatherWindows(self):
        """
        Reads the opened windows from the cache and converts the entries to a list
        :return: array with occupants values
        """
        try:
            root = os.getcwd() + '/occupancy_cache'
            if os.path.exists(root + '/Simulation_OCP.csv'):
                file_path = os.path.join(root, 'Simulation_OCP.csv')
                dataframe = pd.read_csv(file_path, sep="|")
                return dataframe['win1'].values
            else:
                file_path = glob.glob('./occupancy_cache/*.csv')[0]
                dataframe = pd.read_csv(file_path, sep="|")
                return dataframe['win1'].values
        except Exception as e:
            logging.error("[Gatherer]: Failed to gather the existing occupancy file. Error-Log: " + str(e))

    def removeLines(self):
        """
        Function remove empty rows from the created file
        """
        with open(self.path, 'r') as output_data, open(self.new_path, 'w') as new_output_data:
            for line in output_data:
                if line.strip():
                    new_output_data.write(line)
