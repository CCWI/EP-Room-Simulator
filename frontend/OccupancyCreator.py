import logging
from datetime import datetime, timedelta
import pandas as pd


def createCSV(StartDate, EndDate):
    """
    This function creates a csv-file based on the given start and end date
    It serves as basis on which the specific occupancy can be entered
    :param StartDate: Date given in YYYY-MM-DD form by the ocpEdit file (serves as starting point)
    :param EndDate:  Date given in YYYY-MM-DD form by the ocpEdit file (serves as end point)
    """
    filepath = './occupancy_cache/Base_OCP.csv'
    try:
        multi_day_sim = False
        # Convert the given string dates into proper date variables
        start_date = datetime.strptime(StartDate, '%Y-%m-%d')
        end_date = datetime.strptime(EndDate, '%Y-%m-%d')
        current_date = start_date

        # Analyze the date -> even if the timeframe is just two days:
        # the occupancy requires at least 10080 lines (7 days)
        day_range = end_date - start_date
        if day_range.days != 0:
            multi_day_sim = True

        # To get a correct occupancy -> the dRange must always be dividable by seven without any remainders
        if multi_day_sim:
            if day_range.days < 7:
                alternate_date = day_range
                while (alternate_date.days * 1440) < 10080:
                    alternate_date += timedelta(days=1)
                    end_date += timedelta(days=1)
                    day_range = alternate_date

        day_list = createZeroList(multi_day_sim, day_range.days, True)
        time_list = createTimeList(current_date, end_date)
        occupants_list = createZeroList(multi_day_sim, day_range.days, False)
        win_list = createZeroList(multi_day_sim, day_range.days, False)

        occupancy_frame = pd.DataFrame(list(zip(day_list, time_list, occupants_list, win_list)),
                                       columns=["day", "time", "occupants", "win1"])

        occupancy_frame.to_csv(filepath, index=False, lineterminator='\n', sep='|')
    except Exception as e:
        logging.error("[OccupancyCreator]: Failed to create base csv-file. Log: " + str(e))


def createZeroList(multi_day_sim, dRange, day):
    """
    Create lists filled with zeros to serve as a base for the csv file
    :param multi_day_sim: (Boolean) for multi_day_sim sims
    :param dRange: (Int) Required length of the list
    :param day: (Boolean) Determines if the list is for a day
    :return zero_list: List filled with zeros (if day = False)
    """
    try:
        zero_list = []
        current_day = 0
        if not multi_day_sim:
            for i in range(0, 1440, 1):
                zero_list.append(int(current_day))
            return zero_list
        if day:
            while current_day <= dRange:
                for i in range(0, 1440, 1):
                    zero_list.append(int(current_day))
                current_day += 1
            return zero_list
        else:
            while current_day <= dRange:
                for i in range(0, 1440, 1):
                    zero_list.append(int(0))
                current_day += 1
            return zero_list
    except Exception as e:
        logging.error("[OccupancyCreator]: Failed to create the day list for the base csv-file. Log: " + str(e))
        return None


def createTimeList(current_Date, End_Date):
    """
    Creating the time list for the base csv occupancy file
    :param current_Date:
    :param End_Date:
    :return time_list: list containing one entry per minute between the start and end_date
    """
    try:
        single_day_counter = 0
        # Build a proper time list from the given dates --> Only hours and minutes are required!!
        time_list = [current_Date.strftime('%H:%M:%S')]
        # For a single day: Only 1440 lines are required in order to create an entire day.
        if current_Date == End_Date:
            while single_day_counter < 1439:
                single_day_counter += 1
                current_Date += timedelta(minutes=1)
                time_list.append(current_Date.strftime('%H:%M:%S'))
        # For multiple days:
        # until the end date ist reached, the process works normally and uses the single_day for the last date
        else:
            while current_Date != End_Date:
                current_Date += timedelta(minutes=1)
                time_list.append(current_Date.strftime('%H:%M:%S'))
            while single_day_counter < 1439:
                single_day_counter += 1
                current_Date += timedelta(minutes=1)
                time_list.append(current_Date.strftime('%H:%M:%S'))

        return time_list

    except Exception as e:
        logging.error("[OccupancyCreator]: Failed to create the timeframe for the base csv file. Log: " + str(e))
        return None
