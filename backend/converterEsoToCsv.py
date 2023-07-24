import configparser
import csv
import logging
import os
import pandas as pd
from datetime import datetime, timedelta
import parseidf


class DataConverterEsoCsv:
    """
    Build as a class for easier usage
    """
    base_directory = os.getcwd() + '/eso_output/'
    result_directory = os.getcwd() + '/csv_output/'

    def __init__(self, simId):
        self.new_csv = str(simId) + "_output.csv"
        if os.path.exists(self.base_directory + simId + "_output.eso"):
            self.path = self.base_directory + simId + "_output.eso"
        else:
            raise Exception("eso converter: eso-file not found!")

    def getZoneNameFromESO(self):
        """Returns the zone name used in an eso file (based on the first occurence of 'Zone Air Temperature [C] !TimeStep')"""
        with open(self.path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            for row in csv_reader:
                if (len(row) > 3) and (row[3] == 'Zone Air Temperature [C] !TimeStep'):
                    return row[2]
    def getZoneValue(self, value:str, zone:str=None):
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
            with open(self.path) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=",")
                for row in csv_reader:
                    if len(row) > 3 and (row[2] == zone.upper() or row[2] == zone.lower() or row[2] == zone) and \
                            row[3] == value:
                        return row[0]
            raise Exception("Not found")
        except Exception as e:
            logging.error("[Gatherer]: Failed to retrieve zone value. Log: " + value + " " + str(e))


    def retrieve_data(self, value:str, zone:str=None):
        """
        Function is generally identical to the base work --> modification due to being completely rewritten and adjusted
        :param value: name of the searched value (e.g.Zone Air Temperature [C] !TimeStep)
        :param zone: name of the zone
        :return: found values are appended to an array and returned
        """
        dataset = []
        enable_data_collection = False
        try:
            if zone == None:
                zone = self.getZoneNameFromESO()
            # Identify which id the requested value has in order to identify the data belonging to this tag
            row_id = self.getZoneValue(value, zone)
            # Read file for the identified id
            with open(self.path) as eso_file:
                eso_reader = csv.reader(eso_file, delimiter=',')
                for row in eso_reader:
                    # Read the file row-wise: the data begins after the data dictionary
                    if (len(row)) > 1 and row[1] == "RUNPERIOD":
                        enable_data_collection = True
                    if enable_data_collection and row[0] == row_id and len(row) == 2:
                        dataset.append(float(row[1]))
                return dataset
        except Exception as e:
            logging.error(f"[Gatherer]: Failed to retrieve data for {value}. Log: " + str(e))
            return dataset


    def readDateFromIdf(self, date_type):
        """
        Read the date from the idf  file.
        :param date_type: Either start_date or end_date, defines which date is to be extracted
        """
        with open(os.getcwd() + '\\tmp\\Output.idf') as f:
            idf = parseidf.parse(f.read())
            if date_type == 'start_date':
                month = int(idf['RUNPERIOD'][0][2])
                day = int(idf['RUNPERIOD'][0][3])
                year = idf['RUNPERIOD'][0][4]
                return str(year) + '-' + str(month) + '-' + str(day)
            elif date_type == 'end_date':
                month = idf['RUNPERIOD'][0][5]
                day = idf['RUNPERIOD'][0][6]
                year = idf['RUNPERIOD'][0][7]
                return str(year) + '-' + str(month) + '-' + str(day)


    def GatherAllData(self):
        """
        Main function: as the name suggests the data required for the plot is gathered here
        Every variable is collected as an array and turned into a dataframe (all_data_df)
        The zone variable is important for the collection and needs to be adjusted if the variable changes within the idf-file
        :return: all_data_df
        """
        # Create a dataframe with all simulated values. Combine it with occupancy
        start_date = self.readDateFromIdf('start_date')
        end_date = self.readDateFromIdf('end_date')
        config = configparser.ConfigParser()
        config.read('config.ini')
        view_config = config['EnergyPlus']
        outdoor = "Environment"
        try:
            zone_air_temperature = self.retrieve_data("Zone Air Temperature [C] !TimeStep")
            zone_co2_concentration = self.retrieve_data("Zone Air CO2 Concentration [ppm] !TimeStep")
            zone_rel_humidity = self.retrieve_data("Zone Air Relative Humidity [%] !TimeStep")
            outdoor_air_pressure = self.retrieve_data("Site Outdoor Air Barometric Pressure [Pa] !TimeStep", zone=outdoor)
            outdoor_air_drybulb = self.retrieve_data("Site Outdoor Air Drybulb Temperature [C] !TimeStep", zone=outdoor)
            timeframe = self.createTimeFrame(start_date, end_date)
            windows = self.gatherWindows()
            occupancy = self.gatherOccupancy()
            all_data_df = pd.DataFrame(list(
                zip(timeframe, zone_air_temperature, zone_co2_concentration, zone_rel_humidity, outdoor_air_pressure,
                    outdoor_air_drybulb, occupancy, windows)),
                columns=["time", "zone_air_temperature", "zone_co2_concentration", "zone_rel_humidity",
                         "outdoor_air_pressure",
                         "outdoor_air_drybulb", "occupancy", "window"])
            all_data_df.set_index("time", inplace=True)
            self.saveCsv(all_data_df)
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
                    """
                    Without this counter the last date would be missing
                    """
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
            file_path = os.getcwd() + '\\tmp\\occupancy.csv'
            dataframe = pd.read_csv(file_path, sep="|")
            return dataframe['occupants'].values
        except Exception as e:
            logging.error("[Converter_ESO_to_CSV]: Failed to gather the existing occupancy file. Error-Log: " + str(e))


    def gatherWindows(self):
        """
        Reads the opened windows from the cache and converts the entries to a list
        :return: array with occupants values
        """
        try:
            file_path = os.getcwd() + '\\tmp\\occupancy.csv'
            dataframe = pd.read_csv(file_path, sep="|")
            return dataframe['win1'].values
        except Exception as e:
            logging.error("[Converter_ESO_to_CSV]: Failed to gather the existing occupancy file. Error-Log: " + str(e))


    def saveCsv(self, all_data_df):
        """
        Saves the csv file
        """
        file_path = self.result_directory + self.new_csv
        all_data_df.to_csv(file_path, index_label="date")