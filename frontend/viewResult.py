import io
import json
import time
import logging
import os
import pandas as pd
from flask import render_template, Blueprint, request, make_response
import startSim
import plotly.graph_objects as go
import home
from plotly.subplots import make_subplots
import endpoint_connector
import OutputGatherer
import fileEncode

viewResult_Blueprint = Blueprint('viewResult', __name__, template_folder='templates')

@viewResult_Blueprint.route('/viewResult', methods=['GET'])
def viewResultGet():
    """
    GET-function triggers the data collection and displays the basic template.
    """
    try:
        date_dict = None
        check = updateBaseValues()
        if not check:
            raise Exception("Base values were not identified correctly. Plot data cannot be gathered")
        if ResultHelper.new_simulation:
            Gatherer = OutputGatherer.DataGatherer()
            ResultHelper.MainDataFrame = Gatherer.GatherAllData()
            path = os.getcwd() + '/output_data/output_df.json'
            # wait until output dataframe is written to file, so it can be read
            while True:
                try:
                    os.rename(path, path)
                    break
                except OSError:
                    time.sleep(0.1)
            # read output dataframe
            ResultHelper.MainDataFrame = pd.read_json(path)
        else:
            resp = endpoint_connector.get_result_csv(ResultHelper.simID)
            csv_data = io.BytesIO(resp.content)
            ResultHelper.MainDataFrame = pd.read_csv(csv_data, index_col=[0])
        home.setSimStatus(False)

        return render_template('viewResult.html')

    except Exception as e:
        logging.error("[ResultView]: An unspecified error occurred. Log: " + str(e))
        return render_template('viewResult.html')


def updateBaseValues():
    """
    This function is used to get the output.eso file from the backend based on the given id.
    If an id is given via url, then  this function gets the old output.eso result file for the url given id.
    :return: Bool, to check if the output exists
    """
    try:
        # Update SimValue
        simulation_id = request.args.get('simulation_id')

        if simulation_id is not None:
            # Update Class element to precise the type of simulation
            # in this case: Open an old simulation
            ResultHelper.new_simulation = False
            # Update SimValue
            ResultHelper.simID = simulation_id
            retrieveOutput(simulation_id)
            if ResultHelper.simID is None:
                raise Exception("Failed to update SimID")
            return True
        else:
            # Update SimValue
            ResultHelper.simID = startSim.SimHelper.sim_id
            retrieveOutput(str(startSim.SimHelper.sim_id))
            if ResultHelper.simID is None:
                raise Exception("Failed to update SimID")
            return True


    except Exception as e:
        logging.error("[ResultView]: Failed to update base values. Log:" + str(e))
        ResultHelper.global_error = str(e)
        return False


@viewResult_Blueprint.route('/viewResult', methods=['POST'])
def createPlot():
    """
    Main plot function --> receives the cleaned dictionary and creates a plot based on the values
    Plotly is used as main library for interactive plots
    Function doubles as main POST-Function therefore it also is able to handle the download request
    :return:
    """
    cleanedData = None
    if os.path.exists('./meta_data/date.json'):
        with open('./meta_data/date.json') as json_file:
            date_dict = json.load(json_file)
    plot_dataframe = pd.DataFrame()
    fig = go.Figure()
    if 'data_download_csv' in request.form:
        return downloadDataCsv()
    elif 'data_download_eso' in request.form:
        return downloadDataEso()
    else:
        # The main plot function starts here
        try:
            pd.options.plotting.backend = 'plotly'
            raw_data = gatherRequestedData(request)
            if raw_data is not None:
                cleanedData = transformData(raw_data)
            else:
                raise Exception("Data was not extracted successfully from the submitted form")
            try:
                # The main plot generation for two selected variables starts here
                plot_dataframe = ResultHelper.MainDataFrame[
                    [str(cleanedData['plot_1_data']), str(cleanedData['plot_2_data'])]]
                # In order to have a secondary y-axis --> subplots must be enabled
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                # Assign the values to the plot
                plot_1_list_values = plot_dataframe[str(cleanedData['plot_1_data'])].values
                plot_2_list_values = plot_dataframe[str(cleanedData['plot_2_data'])].values
                # The lines get added to the plot based on the values
                fig.add_trace(go.Scatter(x=plot_dataframe.index.values, y=plot_1_list_values,
                                         name=str(getVarNames('plot_1_name', cleanedData))), secondary_y=False)

                fig.add_trace(go.Scatter(x=plot_dataframe.index.values, y=plot_2_list_values,
                                         name=str(getVarNames('plot_2_name', cleanedData))), secondary_y=True)
                # The individual color of the plot lines is adjusted based on the selected colors
                fig.data[0].line.color = str(cleanedData['plot_1_color'])
                fig.data[1].line.color = str(cleanedData['plot_2_color'])
                # Updating the y-axis based on the selected variables
                fig.update_yaxes(title_text=getAxisValues(str(cleanedData['plot_1_data'])), secondary_y=False)
                fig.update_yaxes(title_text=getAxisValues(str(cleanedData['plot_2_data'])), secondary_y=True)
                # A default title gets assigned if the user didn't choose a custom value
                if cleanedData['plot_title'] is not None:
                    fig.update_layout(title_text=str(cleanedData['plot_title']))
                else:
                    fig.update_layout(title_text=getAxisValues(str(cleanedData['plot_1_data'])) + " & " + getAxisValues(
                        str(cleanedData['plot_2_data'])))

            except Exception:
                # If only one plot is selected, the function treats it as an exception
                # The functions remain basically identical, apart from not creating a second plot
                plot_dataframe = ResultHelper.MainDataFrame[
                    [str(cleanedData['plot_1_data'])]]
                plot_1_list_values = plot_dataframe[str(cleanedData['plot_1_data'])].values
                fig.add_trace(go.Scatter(x=plot_dataframe.index.values, y=plot_1_list_values,
                                         name=str(getVarNames('plot_1_name', cleanedData))))
                fig.data[0].line.color = str(cleanedData['plot_1_color'])
                fig.update_yaxes(title_text=getAxisValues(str(cleanedData['plot_1_data'])))
                if cleanedData['plot_title'] is not None:
                    fig.update_layout(title_text=str(cleanedData['plot_title']))
                else:
                    fig.update_layout(title_text=getAxisValues(str(cleanedData['plot_1_data'])))
            # The x-axis gets updated regardless of one or two plots
            if ResultHelper.new_simulation is False:
                sim_date = endpoint_connector.get_metadata(ResultHelper.simID)
                fig.update_xaxes(
                    title_text=("Time: " + str(sim_date['start_year']) + "-" + str(sim_date['start_month']) + "-"
                                + str(sim_date['start_day'])
                                + " - "
                                + str(sim_date['end_year']) + "-" + str(sim_date['end_month']) + "-"
                                + str(sim_date['end_day'])))
            else:
                fig.update_xaxes(
                    title_text=("Time: " + str(date_dict['start_date']) + " - " + str(date_dict['end_date'])))

            fig.show()

            return render_template('viewResult.html')
        except Exception as e:
            logging.error("[ResultView]: An unspecified error occurred while creating the plot. Log: " + str(e))
            ResultHelper.global_error = str(e)
            return render_template('viewResult.html', error=str(ResultHelper.global_error))


def gatherRequestedData(webRequest):
    """
    Extracts the raw values from the webrequest and saves them within a dictionary for further processing
    Detects if one or two plots were selected
    :param webRequest: flask request
    :return: string dictionary
    """
    data_dictionary = {}
    try:
        plot_2_data = webRequest.form.get('plot_2_data')
        # Check status of plot 2
        if plot_2_data != str(0):
            data_dictionary = {'plot_1_data': webRequest.form.get('plot_1_data'),
                               'plot_1_color': webRequest.form.get('plot_1_color'),
                               'plot_2_data': webRequest.form.get('plot_2_data'),
                               'plot_2_color': webRequest.form.get('plot_2_color'),
                               'plot_1_name': webRequest.form.get('var_1_name'),
                               'plot_2_name': webRequest.form.get('var_2_name'),
                               'plot_title': webRequest.form.get('plot_name')}
        else:
            data_dictionary = {'plot_1_data': webRequest.form.get('plot_1_data'),
                               'plot_1_color': webRequest.form.get('plot_1_color'),
                               'plot_1_name': webRequest.form.get('var_1_name'),
                               'plot_title': webRequest.form.get('plot_name')}

        return data_dictionary
    except Exception as e:
        logging.error(str(e))
        return None


def transformData(data):
    """
    Extracts the data from the dictionary and determines all selected variables and converts them to a dictionary
    :param data: dictionary based on the webrequest
    :return: dictionary with the extracted variables
    """
    plot_1_data_var = None
    plot_1_data_color = None
    plot_2_data_var = None
    plot_2_data_color = None
    plot_1_data_name = None
    plot_2_data_name = None
    plot_title = None
    try:
        # First step: Transform requested data into something useful
        if data['plot_1_data'] == str(1):
            plot_1_data_var = 'zone_air_temperature'
        elif data['plot_1_data'] == str(2):
            plot_1_data_var = 'zone_co2_concentration'
        elif data['plot_1_data'] == str(3):
            plot_1_data_var = 'zone_rel_humidity'
        elif data['plot_1_data'] == str(4):
            plot_1_data_var = 'outdoor_air_drybulb'
        elif data['plot_1_data'] == str(5):
            plot_1_data_var = 'outdoor_air_pressure'
        elif data['plot_1_data'] == str(6):
            plot_1_data_var = 'window'
        else:
            plot_1_data_var = 'occupancy'

        if data['plot_1_color'] == str(1):
            plot_1_data_color = 'Blue'
        elif data['plot_1_color'] == str(2):
            plot_1_data_color = 'Red'
        elif data['plot_1_color'] == str(3):
            plot_1_data_color = 'Green'
        elif data['plot_1_color'] == str(4):
            plot_1_data_color = 'Yellow'
        elif data['plot_1_color'] == str(5):
            plot_1_data_color = 'Grey'
        else:
            plot_1_data_color = 'Black'
        if str(data['plot_1_name']) != "":
            plot_1_data_name = str(data['plot_1_name'])
        try:

            if data['plot_2_data'] == str(1):
                plot_2_data_var = 'zone_air_temperature'
            elif data['plot_2_data'] == str(2):
                plot_2_data_var = 'zone_co2_concentration'
            elif data['plot_2_data'] == str(3):
                plot_2_data_var = 'zone_rel_humidity'
            elif data['plot_2_data'] == str(4):
                plot_2_data_var = 'outdoor_air_drybulb'
            elif data['plot_2_data'] == str(5):
                plot_2_data_var = 'outdoor_air_pressure'
            elif data['plot_2_data'] == str(6):
                plot_2_data_var = 'window'
            else:
                plot_2_data_var = 'occupancy'
            if data['plot_2_color'] == str(1):
                plot_2_data_color = 'Blue'
            elif data['plot_2_color'] == str(2):
                plot_2_data_color = '#FF0000'
            elif data['plot_2_color'] == str(3):
                plot_2_data_color = '#008000'
            elif data['plot_2_color'] == str(4):
                plot_2_data_color = '#FFFF00'
            elif data['plot_2_color'] == str(5):
                plot_2_data_color = '#808080'
            else:
                plot_2_data_color = '#000000'

            if str(data['plot_2_name']) != "":
                plot_2_data_name = str(data['plot_2_name'])

        except Exception:
            logging.info("No second plot selected")
        if str(data['plot_title']) != "":
            plot_title = str(data['plot_title'])

        if plot_2_data_var is None:
            corrected_dictionary = {'plot_1_data': plot_1_data_var,
                                    'plot_1_color': plot_1_data_color,
                                    'plot_1_name': plot_1_data_name,
                                    'plot_title': plot_title}

            return corrected_dictionary
        else:
            corrected_dictionary = {'plot_1_data': plot_1_data_var,
                                    'plot_1_color': plot_1_data_color,
                                    'plot_1_name': plot_1_data_name,
                                    'plot_2_data': plot_2_data_var,
                                    'plot_2_color': plot_2_data_color,
                                    'plot_2_name': plot_2_data_name,
                                    'plot_title': plot_title}

            return corrected_dictionary
    except Exception as e:
        logging.error(str(e))
        ResultHelper.global_error = str(e)

        return None


def getVarNames(string, cleanedData):
    if cleanedData[string] is not None:
        return cleanedData[string]
    else:
        if string == "plot_1_name":
            return getAxisValues(str(cleanedData['plot_1_data']))
        else:
            return getAxisValues(str(cleanedData['plot_2_data']))


def getAxisValues(string):
    """
    Setting the axis values of the plot based on the selected variable
    :param string: basic variable
    :return: string with the corresponding name and measurement
    """
    try:

        if str(string) == "zone_air_temperature":
            return "Zone Air Temperature [C]"
        elif str(string) == "zone_co2_concentration":
            return "Zone Air CO2 Concentration [ppm]"
        elif str(string) == "zone_rel_humidity":
            return "Zone Air Relative Humidity [%]"
        elif str(string) == "outdoor_air_drybulb":
            return "Site Outdoor Air Drybulb Temperature [C]"
        elif str(string) == "outdoor_air_pressure":
            return "Site Outdoor Air Barometric Pressure [Pa]"
        elif str(string) == "window":
            return "Window opening (1=open/0=closed)"
        else:
            return "Occupancy"
    except Exception as e:
        logging.error("[ResultView]: Failed to get correct axis values. Log: " + str(e))
        ResultHelper.global_error = str(e)


def retrieveOutput(simID):
    """
    Retrieving the output eso file as byte64-string --> decoding the string and saving it as eso file for data collection
    :param simID: id used to identify the according output in the database
    """
    try:
        logging.info("[ResultView]: Retrieving the eso output file")
        b64_eso_output = endpoint_connector.get_result(simID)
        eso_string = fileEncode.b64Decoder(b64_eso_output['eso_data'])
        with open('output_data/result.eso', "w") as output_file:
            output_file.write(eso_string)
        if not ResultHelper.new_simulation:
            removeLines()
    except Exception as e:
        logging.error("[ResultView]: Field to retrieve the eso-output file. Log: " + str(e))


def removeLines():
    """
    Copy from the Class OutputGatherer, used in case of reopening old simulation
    Function remove empty rows from the created file.
    Output: a new ESO file (./output_data/result_adjusted.eso)
    """
    with open('output_data/result.eso', 'r') as output_data, \
            open('output_data/result_adjusted.eso', 'w') as new_output_data:
        for line in output_data:
            if line.strip():
                new_output_data.write(line)


def downloadDataCsv():
    """
    Simple function which allows the created dataframe to be downloaded as csv file
    Also used to get previous result files to download as csv file if sim_id is given via url.
    :return: CSV-file
    """
    try:
        resp = make_response(ResultHelper.MainDataFrame.to_csv(index_label='date'))
        resp.headers["Content-Disposition"] = "attachment; filename=export.csv"
        resp.headers["Content-Type"] = "text/csv"
        return resp
    except Exception as e:
        logging.error(str(e))
        ResultHelper.global_error = str(e)
        return render_template('viewResult.html')


def downloadDataEso():
    """
    Simple function which allows the created dataframe to be downloaded as eso file
    :return: ESO-file
    """
    try:
        resp = make_response()
        with open(os.getcwd() + '/output_data/result_adjusted.eso') as f:
            file_data = f.read()
        resp.headers["Content-Disposition"] = "attachment; filename=export.eso"
        resp.headers["Content-Type"] = "text/eso"
        resp.data = file_data
        return resp
    except Exception as e:
        logging.error(str(e))
        ResultHelper.global_error = str(e)
        return render_template('viewResult.html')


class ResultHelper:
    start_date = "2022-12-11"
    end_date = "2022-12-24"
    simID = "6395cd4b643af1cf55594a81"

    MainDataFrame = None
    global_error = None
    new_simulation = True
