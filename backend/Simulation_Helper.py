# this is a helper class to provide all functions to modify an idf file for a simulation
import os
import utils
from eppy.modeleditor import IDF
from datetime import datetime, date, timedelta

eplus_path = utils.read_from_conf("EnergyPlus", "EplusPath")


def create_output_dir_if_not_exists():
    """
    Creates an output directory for eppy files of non-existent.
    """
    path = utils.read_from_conf("EnergyPlus", "OutputDirectoryName")
    if not os.path.exists(path):
        os.makedirs(path)


class Simulation_Helper:
    def __init__(self, idf_file, epw_file, idd_file):
        """
        Constructor to use the helper methods in the main simulation run method in simulation.py
        """
        IDF.setiddname(idd_file)
        self.IDF = IDF(idf_file, epw_file)
        self.set_timestep(60)

    def run_simulation(self, input_id):
        """
        Run the simulation and save the results. The output can be found in the directory eppy_output. Output
        Variables like the ones request with @request_output_variables can be found in the resulting ESO-files within
        the eppy_output directory.
        """
        create_output_dir_if_not_exists()
        self.IDF.saveas("./eppy_output/" + input_id + "_used_IDF.idf")
        output_directory = "./eppy_output"
        self.IDF.run(output_directory=output_directory)

    def save_output_idf(self, input_id):
        """
        Moves the output IDF-file from eppy output to tmp and encodes it to base64
        :return: IDF-file as byte64 String
        """
        os.replace("eppy_output/" + input_id + "_used_IDF.idf", "tmp/Output.idf")
        idf_string = utils.encode_file_to_base64("Output.idf")
        return idf_string

    def save_output_eso(self, input_id):
        """
        Moves the output ESO-file from eppy output into the eso_output directory and changes the filename
        """
        os.replace("eppy_output/eplusout.eso", "eso_output/" + input_id + "_output.eso")

    def set_run_day(self, year, month, day):
        """
        Set RunPeriod for simulation to one specified day
        """
        self.set_run_period(year, month, day, year, month, day)

    def set_run_period(self, start_year, start_month, start_day, end_year, end_month, end_day):
        """
        Set a time period for the simulation.
        If no RunPeriod-object is defined, a RunPeriod-object will be created.
        """
        if len(self.IDF.idfobjects["Runperiod"]) == 0:
            self.IDF.newidfobject("Runperiod")
        PERIOD = self.IDF.idfobjects["Runperiod"][-1]
        PERIOD.Name = "RunPeriod"
        PERIOD.Begin_Month = start_month
        PERIOD.Begin_Day_of_Month = start_day
        PERIOD.Begin_Year = start_year
        PERIOD.End_Month = end_month
        PERIOD.End_Day_of_Month = end_day
        PERIOD.End_Year = end_year

    def set_timestep(self, param):
        """
        Set timestep-size of reported values, requested with frequency "TimeStep".
        """
        if len(self.IDF.idfobjects["Timestep"]) == 0:
            self.IDF.newidfobject("Timestep")

        TIMESTEP = self.IDF.idfobjects["Timestep"][0]
        TIMESTEP.Number_of_Timesteps_per_Hour = param

    def add_output_variable(self, output_variable_name, frequency="TimeStep"):
        """
        Add Output Variable. Value can be found in created \\eppy_output\\*.eso file after running the simulation.
        """
        OUTPUT_VARIABLE = self.IDF.newidfobject("Output:Variable")
        OUTPUT_VARIABLE.Key_Value = "*"
        OUTPUT_VARIABLE.Variable_Name = output_variable_name
        OUTPUT_VARIABLE.Reporting_Frequency = frequency

    def request_site_outdoor_air_drybulb_temperature(self):
        """
        Request output of Site Outdoor Air Drybulb Temperature.
        Values can be found in created \\eppy_output\\*.eso file after running the simulation.
        """
        self.add_output_variable("Site Outdoor Air Drybulb Temperature")

    def request_zone_air_co2_concentration(self):
        """
        Request output of Zone Air CO2 Concentration.
        Values can be found in created \\eppy_output\\*.eso file after running the simulation.
        """
        self.add_output_variable("Zone Air CO2 Concentration")

    def request_zone_air_humidity(self):
        """
        Request output of Zone Air CO2 Concentration.
        Values can be found in created \\eppy_output\\*.eso file after running the simulation.
        """
        self.add_output_variable("Zone Air Relative Humidity")

    def request_zone_temperature(self):
        """
        Request output of Zone Air CO2 Concentration.
        Values can be found in created \\eppy_output\\*.eso file after running the simulation.
        """
        self.add_output_variable("Zone Air Temperature")

    def request_site_outdoor_air_barometric_pressure(self):
        """
        Request output of Zone Air CO2 Concentration.
        Values can be found in created \\eppy_output\\*.eso file after running the simulation.
        """
        self.add_output_variable("Site Outdoor Air Barometric Pressure")

    def add_constant_carbon_dioxide_schedule(self, carbon_dioxide_value: int):
        """
        Adding or overwriting an Outdoor Carbon Dioxide Balance Object and setting its Outdoor CO2 Concentration Value
        within a schedule.
        Needed for requesting CO2 concentration.
        """
        if len(self.IDF.idfobjects["ZoneAirContaminantBalance"]) == 0:
            self.IDF.newidfobject("ZoneAirContaminantBalance")

        ZONE_AIR_CONTAMINANT_BALANCE = self.IDF.idfobjects["ZoneAirContaminantBalance"][0]
        ZONE_AIR_CONTAMINANT_BALANCE.Carbon_Dioxide_Concentration = "Yes"
        ZONE_AIR_CONTAMINANT_BALANCE.Outdoor_Carbon_Dioxide_Schedule_Name = "OUTDOOR_CO2_SCHED"

        schedulename = "OUTDOOR_CO2_SCHED_LIMIT"
        self.add_schedule_type_limits(schedulename, 0.0, 1000.0, "Continuous", "Dimensionless")
        self.add_constant_schedule("OUTDOOR_CO2_SCHED", str(carbon_dioxide_value), schedulename)

    def add_schedule_type_limits(self, name: str, lower_limit: float, upper_limit: float, numeric_type: str,
                                 unit_type: str):
        """
        Creates an ScheduleTypeLimits object.
        """
        SCHEDULE_TYPE_LIMITS = self.IDF.newidfobject("ScheduleTypeLimits")
        SCHEDULE_TYPE_LIMITS.Name = name
        SCHEDULE_TYPE_LIMITS.Lower_Limit_Value = lower_limit
        SCHEDULE_TYPE_LIMITS.Upper_Limit_Value = upper_limit
        SCHEDULE_TYPE_LIMITS.Numeric_Type = numeric_type
        SCHEDULE_TYPE_LIMITS.Unit_Type = unit_type

    def update_infiltration_rate_in_design_flow_rate_object(self, volume_infiltration_rate: float, id=-1):
        """
        Update infiltration rate in an existing ZoneInfiltration:DesignFlowRate-object for
        calculation method "Flow/Zone".
        """
        ZONE_INFILTRATION_DESIGN_FLOW_RATE = self.IDF.idfobjects["ZoneInfiltration:DesignFlowRate"][id]
        ZONE_INFILTRATION_DESIGN_FLOW_RATE.Design_Flow_Rate_Calculation_Method = "Flow/Zone"
        ZONE_INFILTRATION_DESIGN_FLOW_RATE.Design_Flow_Rate = str(volume_infiltration_rate)
        ZONE_INFILTRATION_DESIGN_FLOW_RATE.Flow_Rate_per_Exterior_Surface_Area = ""

    def remove_design_flow_rate_object(self, volume_infiltration_rate: float, id):
        """
        Update infiltration rate in an existing ZoneInfiltration:DesignFlowRate object for
        calculation method "Flow/Zone".
        """
        ZONE_INFILTRATION_DESIGN_FLOW_RATE = self.IDF.idfobjects["ZoneInfiltration:DesignFlowRate"][id]
        ZONE_INFILTRATION_DESIGN_FLOW_RATE.Design_Flow_Rate_Calculation_Method = "Flow/Zone"
        ZONE_INFILTRATION_DESIGN_FLOW_RATE.Design_Flow_Rate = str(volume_infiltration_rate)
        ZONE_INFILTRATION_DESIGN_FLOW_RATE.Flow_per_Exterior_Surface_Area = ""

    def add_constant_schedule(self, name: str, hourly_value: str, schedule_type_limits_name: str = ""):
        """
        Creates a constant schedule by settings its name. its constant value and the name of its ScheduleTypeLimit.
        """
        SCHEDULE_CONSTANT_CO2 = self.IDF.newidfobject("Schedule:Constant")
        SCHEDULE_CONSTANT_CO2.Name = name
        SCHEDULE_CONSTANT_CO2.Schedule_Type_Limits_Name = schedule_type_limits_name
        SCHEDULE_CONSTANT_CO2.Hourly_Value = hourly_value

    def add_constant_day_schedule_1440items(self, name: str, value):
        """
        Creates a constant schedule for a day consisting of 1440 items, so one per minute.
        """
        SCHEDULE = self.IDF.newidfobject("Schedule:Day:List")
        SCHEDULE.Name = name
        SCHEDULE.Minutes_per_Item = 1
        for index in range(1, 1440):
            field_attribute = 'Value_{}'.format(index)
            setattr(SCHEDULE, field_attribute, value)

    def set_ventilation(self, zone, run_period, ventilation_data,
                        ventilated_windows='all', opening_area_per_window=1.025,
                        delete_other_ventilation_objects=True):
        """
        Overall function to add ventilation data to an idf object.
        :param self: used idf object
        :param zone: zone name to add ventilation to
        :param run_period: tuple of simulation start and end date in format Y-m-d, e.g. ('2023-01-01', '2023-01-14')
        :param ventilation_data: 2D-array of shape (d, 1440) for d days of data.
                                 Each value represents the fraction of openness between 0 and 1
        :param ventilated_windows: number of windows that adhere to the ventilation schedule,
                                   or 'all' to select all available windows of the zone
        :param opening_area_per_window: max. opening area of the window in m²
        :param delete_other_ventilation_objects:
               boolean, whether to delete previous ventilation objects from the idf object (defaults to True)
        """
        # delete previous ventilation objects
        if delete_other_ventilation_objects:
            for i in range(0, len(self.IDF.idfobjects["ZoneVentilation:WindandStackOpenArea"])):
                self.IDF.removeidfobject(self.IDF.idfobjects["ZoneVentilation:WindandStackOpenArea"][0])

        # write ventilation data to schedules
        start_day = int(run_period[0].split("-")[2])
        start_month = int(run_period[0].split("-")[1])
        start_year = int(run_period[0].split("-")[0])
        start_date = date(start_year, start_month, start_day)

        end_day = int(run_period[1].split("-")[2])
        end_month = int(run_period[1].split("-")[1])
        end_date = date(start_year, end_month, end_day)

        i = 0
        while start_date <= end_date:
            self.create_day(start_date, ventilation_data[i], schedule_prefix="VENTILATION")
            i += 1
            start_date += timedelta(days=1)

        self.create_day(0, [0 for i in range(0, 1440)], schedule_prefix="VENTILATION")
        self.create_year(run_period, schedule_prefix="VENTILATION")

        # generate a ventilation object
        if ventilated_windows == 'all':
            ventilated_windows = len(self.IDF.idfobjects['FenestrationSurface:Detailed'])  # count windows
        vent = self.IDF.newidfobject("ZoneVentilation:WindandStackOpenArea")
        vent.Name = "ZoneVentilationObject"
        vent.Zone_or_Space_Name = zone
        vent.Opening_Area = opening_area_per_window * ventilated_windows
        vent.Opening_Area_Fraction_Schedule_Name = "VENTILATION_YEAR_SCHEDULE"

    def set_occupancy(self, zone, run_period, occupancy_data,
                      max_number_of_occupants, generation_rate_co2, activity_level,
                      delete_other_occupants=True):
        """
        Overall function to add occupancy data to an idf object.
        :param self: used idf object
        :param zone: zone name to add occupancy to
        :param run_period: tuple of simulation start and end date in format Y-m-d, e.g. ('2023-01-01', '2023-01-14')
        :param occupancy_data: 2D-array of shape (d, 1440) for d days of data.
                               Each value represents the number of occupants present
                                between 0 and max_number_of_occupants.
        :param max_number_of_occupants: maximum number of occupants that are allowed to be present in the zone
        :param generation_rate_co2: CO2 generation rate to be used in the simulation
        :param activity_level: activity level of occupants to be used in the simulation
        :param delete_other_occupants:
            boolean, whether to delete previous occupants from the idf object (defaults to True)
        """

        #  delete previous schedules and people objects
        if delete_other_occupants:
            for i in range(0, len(self.IDF.idfobjects['People'])):
                self.IDF.removeidfobject(self.IDF.idfobjects['People'][0])

        # create schedule type limits
        self.IDF.newidfobject(
            "SCHEDULETYPELIMITS",
            Name="OCCLMTS",
            Lower_Limit_Value=0,
            Upper_Limit_Value=1,
            Numeric_Type="Continuous")

        # write occupancy data to schedules
        start_day = int(run_period[0].split("-")[2])
        start_month = int(run_period[0].split("-")[1])
        start_year = int(run_period[0].split("-")[0])
        start_date = date(start_year, start_month, start_day)

        end_day = int(run_period[1].split("-")[2])
        end_month = int(run_period[1].split("-")[1])
        end_date = date(start_year, end_month, end_day)

        i = 0
        while start_date <= end_date:
            self.create_day(start_date, occupancy_data[i])
            i += 1
            start_date += timedelta(days=1)

        self.create_day(0, [0 for i in range(0, 1440)])
        self.create_year(run_period)

        # create activity
        activity_schedule = self.IDF.newidfobject("Schedule:Constant")
        activity_schedule.Name = "CONSTANT_OCCUPANT_ACTIVITY_SCHEDULE"
        activity_schedule.Hourly_Value = str(activity_level)

        # create people objects
        p = self.IDF.newidfobject("People")
        p.Name = "OCCUPANTS"
        p.Zone_or_ZoneList_or_Space_or_SpaceList_Name = zone
        p.Number_of_People_Schedule_Name = "OCCUPANCY_YEAR_SCHEDULE"
        p.Activity_Level_Schedule_Name = "CONSTANT_OCCUPANT_ACTIVITY_SCHEDULE"
        p.Carbon_Dioxide_Generation_Rate = str(generation_rate_co2)
        p.Number_of_People_Calculation_Method = "People"
        p.Number_of_People = str(max_number_of_occupants)

    def calculate_simulation_days(self, run_period):
        """
        Calculates the number of days to be simulated for a passed run period.
        :param run_period: tuple of simulation start and end date in format Y-m-d, e.g. ('2023-01-01', '2023-01-14')
        """
        return (datetime.strptime(run_period[1], '%Y-%m-%d')
                - datetime.strptime(run_period[0], '%Y-%m-%d')).days + 1

    def create_day(self, schedule_date, values, schedule_prefix="OCCUPANCY"):
        """
        Creates a day schedule for day d using the passed values
        and creates a week schedule where each day references the created day schedule.
        :param self: used idf object
        :param schedule_date: day
        :param list values: list of 1440 values to be written into the day schedule
        :param str schedule_prefix: prefix put in front of the schedule names
        """
        # create day schedule
        day = self.IDF.newidfobject("Schedule:Day:List")
        day.Name = schedule_prefix + "_SCHEDULE_DAY_" + str(schedule_date)
        day.Minutes_per_Item = 1
        day.Schedule_Type_Limits_Name = "OCCLMTS"
        for i in range(0, 1440):
            setattr(day, 'Value_' + str(i + 1), values[i])

    def create_week_schedules(self, week_number, year, start_date, end_date, schedule_prefix="OCCUPANCY"):
        # create week schedule
        week = self.IDF.newidfobject("Schedule:Week:Daily")
        week.Name = schedule_prefix + "_SCHEDULE_" + str(year) + "_" + str(week_number)

        # Sunday
        tmp_date = datetime.strptime(f'{year}-{week_number}-0', "%Y-%U-%w").date()
        if (tmp_date >= start_date) and (tmp_date <= end_date):
            week.Sunday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_" + str(tmp_date)
        else:
            week.Sunday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        # Monday
        tmp_date = datetime.strptime(f'{year}-{week_number}-1', "%Y-%U-%w").date()
        if (tmp_date >= start_date) and (tmp_date <= end_date):
            week.Monday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_" + str(tmp_date)
        else:
            week.Monday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        # Tuesday
        tmp_date = datetime.strptime(f'{year}-{week_number}-2', "%Y-%U-%w").date()
        if (tmp_date >= start_date) and (tmp_date <= end_date):
            week.Tuesday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_" + str(tmp_date)
        else:
            week.Tuesday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        # Wednesday
        tmp_date = datetime.strptime(f'{year}-{week_number}-3', "%Y-%U-%w").date()
        if (tmp_date >= start_date) and (tmp_date <= end_date):
            week.Wednesday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_" + str(tmp_date)
        else:
            week.Wednesday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        # Thursday
        tmp_date = datetime.strptime(f'{year}-{week_number}-4', "%Y-%U-%w").date()
        if (tmp_date >= start_date) and (tmp_date <= end_date):
            week.Thursday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_" + str(tmp_date)
        else:
            week.Thursday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        # Friday
        tmp_date = datetime.strptime(f'{year}-{week_number}-5', "%Y-%U-%w").date()
        if (tmp_date >= start_date) and (tmp_date <= end_date):
            week.Friday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_" + str(tmp_date)
        else:
            week.Friday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        # Saturday
        tmp_date = datetime.strptime(f'{year}-{week_number}-6', "%Y-%U-%w").date()
        if (tmp_date >= start_date) and (tmp_date <= end_date):
            week.Saturday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_" + str(tmp_date)
        else:
            week.Saturday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        # Special Days not needed
        week.Holiday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        week.WinterDesignDay_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        week.SummerDesignDay_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        week.CustomDay1_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        week.CustomDay2_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"

    def create_week_schedules_zero(self, week_number, year, schedule_prefix="OCCUPANCY"):
        # create week schedule
        week = self.IDF.newidfobject("Schedule:Week:Daily")
        week.Name = schedule_prefix + "_SCHEDULE_" + str(year) + "_" + str(week_number)

        week.Sunday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        week.Monday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        week.Tuesday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        week.Wednesday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        week.Thursday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        week.Friday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        week.Saturday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        week.Holiday_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        week.WinterDesignDay_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        week.SummerDesignDay_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        week.CustomDay1_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"
        week.CustomDay2_ScheduleDay_Name = schedule_prefix + "_SCHEDULE_DAY_0"

    def create_year(self, run_period, schedule_prefix="OCCUPANCY"):
        """
        Creates a year schedule referencing the week schedules generated by the function create_day().
        Before and after the run period (set by the function set_runperiod()),
        an unoccupied schedule (schedule day 0) is referenced.
        :param self: used idf object
        :param run_period: tuple of simulation start and end date in format Y-m-d, e.g. ('2023-01-01', '2023-01-14')
        :param schedule_prefix: prefix put in front the schedule name
        """
        start_day = int(run_period[0].split("-")[2])
        start_month = int(run_period[0].split("-")[1])
        start_year = int(run_period[0].split("-")[0])
        start_date = date(start_year, start_month, start_day)

        end_day = int(run_period[1].split("-")[2])
        end_month = int(run_period[1].split("-")[1])
        end_date = date(start_year, end_month, end_day)

        schedule = self.IDF.newidfobject("Schedule:Year")
        schedule.Name = schedule_prefix + "_YEAR_SCHEDULE"
        schedule.Schedule_Type_Limits_Name = "OCCLMTS"

        fs = 1  # field set number (in year schedule)

        current_week_number = date(start_year, 1, 1).strftime('%U')
        last_week_number = date(start_year, 12, 31).strftime('%U')

        while int(current_week_number) <= int(last_week_number):
            if int(current_week_number) == 0:
                schedule.ScheduleWeek_Name_1 = schedule_prefix + "_SCHEDULE_" + str(start_year) + "_" + str(
                    current_week_number)
                schedule.Start_Month_1 = 1
                schedule.Start_Day_1 = 1
                schedule.End_Month_1 = 1
                schedule.End_Day_1 = datetime.strptime(f'{start_year}-{current_week_number}-6',
                                                       "%Y-%U-%w").date().day

                if int(start_date.strftime('%U')) == 0:
                    self.create_week_schedules(current_week_number, start_year, start_date, end_date, schedule_prefix)
                else:
                    self.create_week_schedules_zero(current_week_number, start_year, schedule_prefix)
                fs += 1
                tmp_date = datetime.strptime(f'{start_year}-{current_week_number}-6', "%Y-%U-%w").date() + timedelta(
                    days=1)
                current_week_number = tmp_date.strftime('%U')

            elif int(current_week_number) == int(last_week_number):
                schedule["ScheduleWeek_Name_" + str(fs)] = schedule_prefix + "_SCHEDULE_" + str(start_year) + "_" + str(
                    current_week_number)
                schedule["Start_Month_" + str(fs)] = 12
                schedule["Start_Day_" + str(fs)] = datetime.strptime(f'{start_year}-{current_week_number}-0',
                                                                     "%Y-%U-%w").date().day
                schedule["End_Month_" + str(fs)] = 12
                schedule["End_Day_" + str(fs)] = 31

                if (int(start_date.strftime('%U')) >= int(current_week_number)) and (
                        int(end_date.strftime('%U')) <= int(current_week_number)):
                    self.create_week_schedules(current_week_number, start_year, start_date, end_date, schedule_prefix)
                else:
                    self.create_week_schedules_zero(current_week_number, start_year, schedule_prefix)
                fs += 1
                current_week_number = "54"  # closes the while loop

            else:
                schedule["ScheduleWeek_Name_" + str(fs)] = schedule_prefix + "_SCHEDULE_" + str(start_year) + "_" + str(
                    current_week_number)
                schedule["Start_Month_" + str(fs)] = datetime.strptime(f'{start_year}-{current_week_number}-0',
                                                                       "%Y-%U-%w").date().month
                schedule["Start_Day_" + str(fs)] = datetime.strptime(f'{start_year}-{current_week_number}-0',
                                                                     "%Y-%U-%w").date().day
                schedule["End_Month_" + str(fs)] = datetime.strptime(f'{start_year}-{current_week_number}-6',
                                                                     "%Y-%U-%w").date().month
                schedule["End_Day_" + str(fs)] = datetime.strptime(f'{start_year}-{current_week_number}-6',
                                                                   "%Y-%U-%w").date().day

                if (int(start_date.strftime('%U')) >= int(current_week_number)) and (
                        int(end_date.strftime('%U')) <= int(current_week_number)):
                    self.create_week_schedules(current_week_number, start_year, start_date, end_date, schedule_prefix)
                else:
                    self.create_week_schedules_zero(current_week_number, start_year, schedule_prefix)
                fs += 1
                tmp_date = datetime.strptime(f'{start_year}-{current_week_number}-6', "%Y-%U-%w").date() + timedelta(
                    days=1)
                current_week_number = tmp_date.strftime('%U')

    def update_heating_limit_of_airflow_and_sensible_heating_capacity(self, airflow_limit_in_m3_s: float = 0,
                                                                      sensible_heating_capacity_in_w: float = 0):
        """
        If an ZoneHVAC Object is implemented, change the limits for heating.
        """

        ZONE_HVAC_IDEAL_LOAD_AIR_SYSTEM = self.IDF.idfobjects["ZoneHVAC:IdealLoadsAirSystem"][-1]
        ZONE_HVAC_IDEAL_LOAD_AIR_SYSTEM.Heating_Limit = "LimitFlowRateAndCapacity"
        ZONE_HVAC_IDEAL_LOAD_AIR_SYSTEM.Maximum_Heating_Air_Flow_Rate = str(airflow_limit_in_m3_s)
        ZONE_HVAC_IDEAL_LOAD_AIR_SYSTEM.Maximum_Sensible_Heating_Capacity = str(sensible_heating_capacity_in_w)
        pass

    def remove_fenestration_surfaces(self):
        """
        Remove fenestration.
        Implemented for testing the theory, the fenestration implementation could be misconfigured.
        """
        while len(self.IDF.idfobjects["FenestrationSurface:Detailed"]) != 0:
            FENESTRATIN_SURFACE = self.IDF.idfobjects["FenestrationSurface:Detailed"][-1]
            self.IDF.removeidfobject(FENESTRATIN_SURFACE)
