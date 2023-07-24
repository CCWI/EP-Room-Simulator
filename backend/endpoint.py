import os
import marshmallow.exceptions
from flask import Flask, jsonify, send_from_directory
from flask_restful import Resource, Api
from pymongo.errors import ConnectionFailure
from webargs import fields
from webargs.flaskparser import use_kwargs, parser, abort
import base64
import db_controller
import simulation
import converterEsoToCsv
import simulationSeries
import get_database

app = Flask(__name__)
api = Api(app)


class Connection(Resource):
    """ Endpoint Class to check the connection status to the Docker Container """

    def get(self):
        """
        GET request for status of docker container
        :return: Bool, representing the status
        """
        try:
            if not get_database.get_db_status():
                raise ConnectionFailure("Failed to connect to MongoDB. Check Docker Container!")
            else:
                return jsonify({'success': True})
        except ConnectionFailure as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500


class Simulation(Resource):
    """ Endpoint class for Simulation """
    id_args = {"id": fields.Str(required=True)}

    @use_kwargs(id_args)
    def get(self, id):
        """
        GET request for simulation entry in DB
        :param id: simulation id selects the simulation
        :return: DB entry for simulation or error message
        """
        try:
            return jsonify(db_controller.get_input_simulation(id)[0])
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500

    def post(self):
        """
        POST request to create a new simulation
        :return: id of new simulation
        """
        return db_controller.get_new_objectID()

    @use_kwargs(id_args)
    def delete(self, id):
        """
        DEL request to delete simulation from DB
        :param id: simulation id selects the simulation to be deleted
        :return: success or error message
        """
        try:
            db_controller.delete_input_file(id)
            return jsonify({'success': True})
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500


class SimulationIdf(Resource):
    """ Endpoint Class for IDF Files """
    id_args = {"id": fields.Str(required=True)}
    post_args = {"id": fields.Str(required=True), "data": fields.Str(required=True)}
    put_args = {"id": fields.Str(required=True), "data": fields.Str(required=True)}

    @use_kwargs(id_args)
    def get(self, id):
        """
        GET request for idf file of a specific simulation
        :param id: simulation id
        :return: idf file of simulation in json format
        """
        return db_controller.get_idf_data(id)

    @use_kwargs(post_args)
    def post(self, id, data):
        """
        POST request for IDF-data
        :param id: simulation id selects the simulation where the idf-data should be modified
        :param data: idf-file as base64-String
        :return: success or error message
        """
        try:
            db_controller.modify_idf_data(id, data)
            return jsonify({'success': True})
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500


class SimulationWeather(Resource):
    """ Endpoint Class for Weather Files """
    id_args = {"id": fields.Str(required=True)}
    put_args = {"id": fields.Str(required=True), "data": fields.Str(required=True)}

    @use_kwargs(id_args)
    def get(self, id):
        """
        GET request for epw file of a specific simulation
        :param id: simulation id
        :return: idf file of simulation in json format
        """
        return jsonify(db_controller.get_epw_data(id))

    @use_kwargs(put_args)
    def post(self, id, data):
        """
        POST request for weather data
        :param id: simulation id selects the simulation where the epw-data should be modified
        :param data: epw-file as base64-String
        :return: success or error message
        """
        try:
            db_controller.modify_epw_data(id, data)
            return jsonify({'success': True})
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500


class SimulationOccupancy(Resource):
    """ Endpoint Class for Occupancy Files """
    put_args = {"id": fields.Str(required=True), "data": fields.Str(required=True)}
    id_args = {"id": fields.Str(required=True)}

    @use_kwargs(id_args)
    def get(self, id):
        """
        GET request for occupancy file of a specific simulation
        :param id: simulation id
        :return: idf file of simulation in json format
        """
        return jsonify(db_controller.get_csv_data(id))

    @use_kwargs(put_args)
    def post(self, id, data):
        """
        POST request for occupancy-data
        :param id: simulation id selects the simulation where the csv-data should be modified
        :param data: csv-file as base64-String
        :return: success or error message
        """
        try:
            db_controller.modify_csv_data(id, data)
            return jsonify({'success': True})
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500


class SimulationOverview(Resource):

    def get(self):
        """
        GET request to get an overview over all available simulations in the DB
        :return: MongoDB collection in json format
        """
        return jsonify(db_controller.get_all_input_documents())


class SimulationControl(Resource):
    id_args = {"id": fields.Str(required=True)}
    run_args = {"id": fields.Str(required=True),
                "height": fields.Float(required=True),
                "length": fields.Float(required=True),
                "width": fields.Float(required=True),
                "orientation": fields.Int(required=True),
                "zone_name": fields.Str(required=True),
                "start_day": fields.Int(required=True),
                "start_month": fields.Int(required=True),
                "start_year": fields.Int(required=True),
                "end_day": fields.Int(required=True),
                "end_month": fields.Int(required=True),
                "end_year": fields.Int(required=True),
                "infiltration_rate": fields.Float(required=True)}

    @use_kwargs(id_args)
    def get(self, id):
        """
        GET request to get the status of a simulation
        :param id: simulation id
        :return: status in json format
        """
        return simulation.check_simulation_status(id)

    @use_kwargs(run_args)
    def post(self, id, height, length, width, orientation, zone_name, start_day, start_month, start_year, end_day,
             end_month,
             end_year, infiltration_rate):
        """
        POST request to start a simulation. Before a simulation can run a new simulation has to be created and
        IDF, weather and occupancy data has to be added. Metadata for the simulation is added with this request.
        :param id: id of the simulation to be executed
        :param height: room height
        :param length: room length
        :param width: room width
        :param orientation: room orientation, (0° is North)
        :param start_day: start day of simulation timeframe
        :param start_month: start month of simulation timeframe
        :param start_year: start year of simulation timeframe
        :param end_day: end day of simulation timeframe
        :param end_month: end month of simulation timeframe
        :param end_year: end year of simulation timeframe
        :param infiltration_rate: infiltration rate to be used for the simulation
        :return: success or error message
        """
        meta_data_dict = {
            "height": height,
            "length": length,
            "width": width,
            "orientation": orientation,
            "zone_name": zone_name,
            "start_day": start_day,
            "start_month": start_month,
            "start_year": start_year,
            "end_day": end_day,
            "end_month": end_month,
            "end_year": end_year,
            "infiltration_rate": infiltration_rate}
        try:
            db_controller.check_files(id)
            simulation.start_simulation_thread(id, meta_data_dict)
            return jsonify({'success': True})
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500


class SimulationControlIDF(Resource):
    id_args = {"id": fields.Str(required=True)}

    @use_kwargs(id_args)
    def get(self, id):
        """
        GET request to get the status of a simulation
        :param id: simulation id
        :return: status in json format
        """
        return simulation.check_simulation_status(id)

    @use_kwargs(id_args)
    def post(self, id):
        """
        POST request to start a simulation. Before a simulation can run a new simulation has to be created and
        IDF data has to be added.
        :param id: id of the simulation to be executed
        :return: success or error message
        """
        try:
            csv_data = "Not available"
            csv_data_bytes = csv_data.encode('utf-8')
            encoded_csv_data = base64.b64encode(csv_data_bytes)
            encoded_csv_data_string = encoded_csv_data.decode('utf-8')
            db_controller.modify_csv_data(id, encoded_csv_data_string)
            simulation.start_simulation_thread(id)
            return jsonify({'success': True})
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500


class SimulationResult(Resource):
    id_args = {"id": fields.Str(required=True)}

    @use_kwargs(id_args)
    def get(self, id):
        """
        GET request for eso-file output of energyplus
        :param id: simulation id
        :return: eso-file as base64-string
        """
        try:
            result = db_controller.get_output_simulation(id)
            result_file = open("eso_output/" + id + "_output.eso", 'rb')
            result_data = result_file.read()
            result_file.close()
            result['eso_data'] = base64.encodebytes(result_data).decode('utf-8')
            return jsonify(result)
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500

    @use_kwargs(id_args)
    def delete(self, id):
        """
        DEL request to delete Results from DB
        :param id: simulation id selects the results to be deleted
        :return: success or error message
        """
        try:
            db_controller.delete_result(id)
            return jsonify({'success': True})
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500


class Metadata(Resource):
    id_args = {"id": fields.Str(required=True)}

    @use_kwargs(id_args)
    def get(self, id):
        """
        GET request for metadata of a specific simulation
        :param id: simulation id
        :return: metadata of simulation in json format
        """
        return jsonify(db_controller.get_metadata(id))


class SimulationResultOverview(Resource):

    def get(self):
        """
        GET request for an overview of all available results in the DB
        :return: MongoDB result collection without eso-data or idf-data
        """
        return jsonify(db_controller.get_history())


class SimulationResultCsv(Resource):
    id_args = {"id": fields.Str(required=True)}

    @use_kwargs(id_args)
    def get(self, id):
        """
        GET request for the results. Differs to '/result' in the response format.
        :return: csv-file as string (Content-Type: "application/vnd.ms-excel")
        """
        file_path_csv = os.getcwd() + '/csv_output'
        file_csv = id + '_output.csv'
        file_path_eso = os.getcwd() + '/eso_output'
        file_eso = id + '_output.eso'
        if os.path.exists(file_path_csv + '/' + file_csv):
            try:
                return send_from_directory(directory=file_path_csv, path=file_csv, as_attachment=True)
            except Exception as e:
                return {"errors": "CSV-File found, but could not be sent. " + str(e)}, 500
        elif os.path.exists(file_path_eso + '/' + file_eso):
            try:
                converter = converterEsoToCsv.DataConverterEsoCsv(id)
                converter.GatherAllData()
            except Exception as e:
                return {"errors": "ESO-File found, but could not be converted. " + str(e)}, 500
            try:
                return send_from_directory(directory=file_path_csv, path=file_csv, as_attachment=True)
            except Exception as e:
                return {"errors": "CSV-File found, but could not be sent. " + str(e)}, 500
        else:
            return {"errors": "File not found! Check the Simulation Id!"}, 500


class SimulationReopen(Resource):
    id_args = {"id": fields.Str(required=True)}

    @use_kwargs(id_args)
    def get(self, id):
        """
        GET request to retrieve data from an old simulation
        :params id: simulation id
        :return: Sim id of new simulation
        """
        try:
            # get metadata from old simulation
            metadata = db_controller.get_metadata(id)
            # get files from old simulation
            idf_file = db_controller.get_idf_data(id)
            epw_file = db_controller.get_epw_data(id)
            csv_file = db_controller.get_csv_data(id)
            return jsonify(metadata, idf_file, epw_file, csv_file)
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500

    @use_kwargs(id_args)
    def post(self, id):
        """
        GET request to retrieve data from an old simulation to reopen a new simulation
        :params id: simulation id
        :return: Sim id of new simulation
        """
        try:
            # get metadata from old simulation
            metadata = db_controller.get_metadata(id)
            # get files from old simulation
            idf_file = db_controller.get_idf_data(id)
            idf_bytes = idf_file.encode('utf-8')
            base64_idf = base64.b64encode(idf_bytes)
            base64_idf_file = base64_idf.decode('utf-8')
            epw_file = db_controller.get_epw_data(id)
            epw_bytes = epw_file.encode('utf-8')
            base64_epw = base64.b64encode(epw_bytes)
            base64_epw_file = base64_epw.decode('utf-8')
            csv_file = db_controller.get_csv_data(id)
            csv_bytes = csv_file.encode('utf-8')
            base64_csv = base64.b64encode(csv_bytes)
            base64_csv_file = base64_csv.decode('utf-8')
            # create a new simulation
            new_sim_id = db_controller.get_new_objectID()
            db_controller.save_metadata(new_sim_id, metadata)
            # save files in new input
            db_controller.modify_idf_data(new_sim_id, base64_idf_file)
            db_controller.modify_epw_data(new_sim_id, base64_epw_file)
            db_controller.modify_csv_data(new_sim_id, base64_csv_file)
            return str(new_sim_id)
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500


class SimulationSeries(Resource):
    run_args = {"height": fields.Float(required=True),
                "height_max": fields.Float(required=True),
                "height_iter": fields.Float(required=True),
                "length": fields.Float(required=True),
                "length_max": fields.Float(required=True),
                "length_iter": fields.Float(required=True),
                "width": fields.Float(required=True),
                "width_max": fields.Float(required=True),
                "width_iter": fields.Float(required=True),
                "orientation": fields.Int(required=True),
                "orientation_max": fields.Int(required=True),
                "orientation_iter": fields.Int(required=True),
                "start_day": fields.Int(required=True),
                "start_month": fields.Int(required=True),
                "start_year": fields.Int(required=True),
                "end_day": fields.Int(required=True),
                "end_month": fields.Int(required=True),
                "end_year": fields.Int(required=True),
                "infiltration_rate": fields.Float(required=True),
                "infiltration_rate_max": fields.Float(required=True),
                "infiltration_rate_iter": fields.Float(required=True)}

    @use_kwargs(run_args)
    def post(self, height, height_max, height_iter, length, length_max, length_iter, width, width_max, width_iter,
             orientation, orientation_max, orientation_iter, start_day, start_month, start_year, end_day, end_month,
             end_year, infiltration_rate, infiltration_rate_max, infiltration_rate_iter):
        """
        POST request to start a simulation. Before a simulation can run a new simulation has to be created and
        IDF, weather and occupancy data has to be added. Metadata for the simulation is added with this request.
        :param height: min room height
        :param height_max: max room height
        :param height_iter: iteration step for the room height
        :param length: min room length
        :param length_max: max room length
        :param length_iter: iteration step for the room length
        :param width: min room width
        :param width_max: max room width
        :param width_iter: iteration step for the room width
        :param orientation: room orientation, (0° is North)
        :param orientation_max: max room orientation
        :param orientation_iter: iteration step for the room orientation
        :param start_day: start day of simulation timeframe
        :param start_month: start month of simulation timeframe
        :param start_year: start year of simulation timeframe
        :param end_day: end day of simulation timeframe
        :param end_month: end month of simulation timeframe
        :param end_year: end year of simulation timeframe
        :param infiltration_rate: min infiltration rate to be used for the simulation
        :param infiltration_rate_max: max infiltration rate
        :param infiltration_rate_iter: iteration step for the
        :return: success or error message
        """
        meta_data_dict = {
            "height": height,
            "height_max": height_max,
            "height_iter": height_iter,
            "length": length,
            "length_max": length_max,
            "length_iter": length_iter,
            "width": width,
            "width_max": width_max,
            "width_iter": width_iter,
            "orientation": orientation,
            "orientation_max": orientation_max,
            "orientation_iter": orientation_iter,
            "start_day": start_day,
            "start_month": start_month,
            "start_year": start_year,
            "end_day": end_day,
            "end_month": end_month,
            "end_year": end_year,
            "infiltration_rate": infiltration_rate,
            "infiltration_rate_max": infiltration_rate_max,
            "infiltration_rate_iter": infiltration_rate_iter}
        try:
            return simulationSeries.create_sim_series(meta_data_dict)
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500


class SimulationSeriesOccupancy(Resource):
    occ_data = {"id": fields.Str(required=True), "data": fields.Str(required=True)}

    @use_kwargs(occ_data)
    def post(self, id, data):
        """
        POST request for occupancy data for the simulations in a simulation series
        :param id: simulations series id selects the simulations where the csv-data should be modified
        :param data: csv-file as base64-String
        :return: success or error message
        """
        try:
            simulationSeries.modifyOccupancyData(id, data)
            return jsonify({'success': True})
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500


class SimulationSeriesWeather(Resource):
    weather_data = {"id": fields.Str(required=True), "data": fields.Str(required=True)}

    @use_kwargs(weather_data)
    def post(self, id, data):
        """
        POST request for weather data for the simulations in a simulation series
        :param id: simulations series id selects the simulations where the epw-data should be modified
        :param data: epw-file as base64-String
        :return: success or error message
        """
        try:
            simulationSeries.modifyWeatherData(id, data)
            return jsonify({'success': True})
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500


class SimulationSeriesRoom(Resource):
    room_data = {"id": fields.Str(required=True), "data": fields.Str(required=True)}

    @use_kwargs(room_data)
    def post(self, id, data):
        """
        POST request for room data for the simulations in a simulation series
        :param id: simulations series id selects the simulations where the idf-data should be modified
        :param data: idf-file as base64-String
        :return: success or error message
        """
        try:
            simulationSeries.modifyRoomData(id, data)
            return jsonify({'success': True})
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500


class SimulationSeriesControl(Resource):
    id_args = {"id": fields.Str(required=True)}

    @use_kwargs(id_args)
    def get(self, id):
        """
        GET request to get the status of a simulation series
        :param id: simulations series id
        :return: status in json format
        """
        return simulationSeries.check_simulation_status(id)

    @use_kwargs(id_args)
    def post(self, id):
        """
        POST request to start a simulation series
        :param id: simulations series id
        :return: success or error message
        """
        try:
            simulationSeries.start_simulation_series(id)
            return jsonify({'success': True})
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500


class SimulationSeriesList(Resource):
    id_args = {"id": fields.Str(required=True)}

    @use_kwargs(id_args)
    def get(self, id):
        """
        GET request to get the list of simulation ids
        :param id: simulation series id
        :return: list of all simulation input ids, use for GET results
        """
        try:
            input_list = db_controller.get_simSer_idList(id)
            return input_list
        except Exception as e:
            return {"errors": {'success': False, 'message': str(e)}}, 500


api.add_resource(Connection, '/status')
api.add_resource(Simulation, '/simulation')
api.add_resource(SimulationIdf, '/idf')
api.add_resource(SimulationOverview, '/simulation/overview')
api.add_resource(SimulationControl, '/simulation/control')
api.add_resource(SimulationOccupancy, '/occupancy')
api.add_resource(SimulationWeather, '/weather')
api.add_resource(SimulationResult, '/result')
api.add_resource(SimulationResultOverview, '/result/overview')
api.add_resource(Metadata, '/metadata')
api.add_resource(SimulationResultCsv, '/result/csv')
api.add_resource(SimulationControlIDF, '/simulation/control/onlyidf')
api.add_resource(SimulationReopen, '/reopensim')
api.add_resource(SimulationSeries, '/series/create')
api.add_resource(SimulationSeriesWeather, '/series/weather')
api.add_resource(SimulationSeriesOccupancy, '/series/occupancy')
api.add_resource(SimulationSeriesRoom, "/series/idf")
api.add_resource(SimulationSeriesControl, "/series/run")
api.add_resource(SimulationSeriesList, "/series/results")


@parser.error_handler
def handle_request_parsing_error(err, req, schema, *, error_status_code, error_headers):
    """
    webargs error handler that uses Flask-RESTful's abort function to return
    a JSON error response to the client.
    """
    if error_status_code is None and type(err) is marshmallow.exceptions.ValidationError:
        abort(500, errors={'success': False, 'message': err.messages['json']})
    abort(error_status_code, errors=err.messages)