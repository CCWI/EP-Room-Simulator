from flask import render_template, Blueprint, request
import endpoint_connector
import pandas as pd


simHistory_Blueprint = Blueprint('simulationHistory', __name__, template_folder='templates')


def format_simulation_id(sim_id):
    """
    Helper function to make the sim_id into buttons in the SimulationHistory Table.
    """
    button_html = f'<button class="button-sim-id" type="button" value="{sim_id}" >{sim_id}</button>'
    return button_html


def reopen_simulation(sim_id):
    """Creates a button in every line to reopen this simulation"""
    button_reopen = f'<button class="reopensim-btsn" type="button" value="{sim_id}" >Reopen Simulation with ID {sim_id}</button>'
    return button_reopen


@simHistory_Blueprint.route('/simHistory', methods=['GET'])
def simHistory_GET():
    """
    Simple GET-Function which connects to the given DataBase and extracts the retrieved data into a dataframe
    :return:
    """
    try:
        dbcontent = endpoint_connector.get_result_overview()

        keys = []
        date_of_creation = []
        status_list = []
        reopen = []

        for value in dbcontent:
            keys.append(value['input_simulation_id'])
            date_of_creation.append(value['date_of_creation'])
            status_list.append(value['status'])
            reopen.append(value['input_simulation_id'])

        all_data_df = pd.DataFrame(list(
            zip(keys, date_of_creation, status_list, reopen)),
            columns=["Simulation ID", "Creation Date", "Status", "Reopen Simulation"])

        all_data_df['Simulation ID'] = all_data_df['Simulation ID'].apply(format_simulation_id)

        all_data_df['Reopen Simulation'] = all_data_df['Reopen Simulation'].apply(reopen_simulation)


        return render_template('simulationHistory.html', tables=[all_data_df.to_html(classes='table', escape=False)])

    except Exception as e:
        if str(e) == "string indices must be integers":
            all_data_df = pd.DataFrame(
                columns=["Simulation ID", "Creation Date", "Status", ])
            error_code = "Connection timeout. Please make sure that the backend and database are online."
            return render_template('simulationHistory.html', tables=[all_data_df.to_html(classes='table')],
                                   error_code=str(error_code))
        elif str(e) == "Expecting value: line 1 column 1 (char 0)":
            error_code = "There is currently a simulation in progress. The 'Simulation History' table will be available again soon!"
            return render_template('simulationHistory.html', tables=[], error_code=str(error_code))
        all_data_df = pd.DataFrame(
            columns=["Simulation ID", "Creation Date", "Status", ])
        error_code = "Failed to connect to the data base. Error-Log: " + str(e)
        return render_template('simulationHistory.html', tables=[all_data_df.to_html(classes='table')], error_code=str(error_code))


@simHistory_Blueprint.route('/simHistory/get_ocp')
def checkCsvData():
    """Simple function to get the csv data"""
    sim_id = request.args.get('sim_id')
    csv_data = endpoint_connector.get_csv_file(sim_id)
    return csv_data
