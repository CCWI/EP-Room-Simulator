import base64
import logging
import os
import pymongo.errors
from bson import ObjectId
import get_database
import utils


def get_all_input_documents():
    """
    gets all stored documents in the input_simulation collection
    :return: list object containing all saved documents in the input_simulation collection
    """
    collection_name = checkDB_connection_input()
    item_details = collection_name.aggregate([
        {
            "$project": {
                "_id": {
                    "$toString": "$_id"
                },
                "date_of_creation": "$date_of_creation",
                "idf_filename": "$idf_filename",
                "data": "$data",
            }}])
    list_cur = list(item_details)
    return list_cur


def get_all_result_documents():
    """
    gets all stored documents in the simulation_results collection
    :return: list object containing all saved documents in the simulation_results collection
    """
    collection_name = checkDB_connection_result()
    item_details = collection_name.aggregate([
        {
            "$project": {
                "_id": {
                    "$toString": "$_id"
                },
                "date_of_creation": "$date_of_creation",
                "filename": "$filename",
                "input_simulation_id": "$input_simulation_id",
                "idf_data": "$idf_data",
                "status": "$status",
            }}])
    list_cur = list(item_details)
    return list_cur


def get_history():
    """
    gets only id, date of creation and filename of all entries in the result collection
    :return: list item containing all documents of the simulation_results collection
    """
    collection_name = checkDB_connection_result()
    item_details = collection_name.aggregate([
        {
            "$project": {
                "_id": {
                    "$toString": "$_id"
                },
                "input_simulation_id": {
                    "$toString": "$input_simulation_id"
                },
                "date_of_creation": "$date_of_creation",
                "filename": "$filename",
                "status": "$status"
            }}, {"$sort": {"date_of_creation": -1}}, {"$limit": 25}])
    list_cur = list(item_details)
    return list_cur


def get_input_simulation(sim_id):
    """
    gets one entry of the input_simulation collection, filtered by the stored simID
    :param sim_id: ID of a simulation, is created whenever a new simulation is started
    :return: list object containing the matching document of the input_simulation collection
    """
    collection_name = checkDB_connection_input()
    check_simID_input(sim_id, collection_name)
    obj_instance = ObjectId(sim_id)
    return list(collection_name.find({"_id": obj_instance}, {"_id": 0}))


def get_output_simulation(sim_id):
    """
    gets one entry of the simulation_results collection, filtered by the stored simID
    :param sim_id: ID of a simulation, is created whenever a new simulation is started
    :return: list object containing the matching document of the simulation_results collection
    """
    collection_name = checkDB_connection_result()
    check_simID_result(sim_id, collection_name)
    item_details = collection_name.aggregate([
        {
            "$project": {
                "_id": {
                    "$toString": "$_id"
                },
                "sim_id": {
                    "$toString": "$input_simulation_id"
                },
                "date_of_creation": "$date_of_creation",
                "filename": "$filename",
                "idf_data": "$idf_data",
                "status": "$status",
            }}])
    list_cur = list(item_details)
    for item in list_cur:
        data = item
        if data["sim_id"] == sim_id:
            return data


def get_new_objectID():
    """
    inserts empty document in the input_simulation collection to generate a simID
    :return: sim_id: id of the simulation which makes it unique
    """
    collection_name = checkDB_connection_input()
    date = utils.get_date()
    filename = utils.get_date_for_filename()
    item = {
        "date_of_creation": date,
        "idf_filename": "SimInput" + filename,
        "idf_data": "",
        "csv_data": "",
        "epw_data": "",
        "start_day": "",
        "start_month": "",
        "start_year": "",
        "end_day": "",
        "end_month": "",
        "end_year": "",
        "width": "",
        "length": "",
        "height": "",
        "orientation": "",
        "zone_name": "",
        "infiltration_rate": "",
    }
    result_set = collection_name.insert_one(item)
    return str(result_set.inserted_id)


def insert_input_file(sim_id, idf_data, csv_data, epw_data):
    """
    inserts a document into the input_simulation collection. Creates a timestamp and a unique filename
    and stores everything together with the given params into the simulation_input collection
    :param sim_id: ID of a simulation, is created whenever a new simulation is started
    :param idf_data: to base64 encoded .idf file
    :param csv_data: to base64 encoded .csv file
    :param epw_data: to base64 encoded .epw file
    """
    collection_name = checkDB_connection_input()
    check_simID_input(sim_id, collection_name)
    date = utils.get_date()
    filename = utils.get_date_for_filename()
    obj_instance = ObjectId(sim_id)
    item = {"$set": {'date_of_creation': date,
                     'idf_filename': "SimulationInput" + filename,
                     'idf_data': idf_data,
                     'csv_data': csv_data,
                     'epw_data': epw_data}}
    collection_name.update_one({"_id": obj_instance}, item)


def delete_input_file(sim_id):
    """
    deletes one specific document in the input_simulation collection selected by simId
    :param sim_id: ID of a simulation, is created whenever a new simulation is started
    """
    collection_name = checkDB_connection_input()
    check_simID_input(sim_id, collection_name)
    obj_instance = ObjectId(sim_id)
    collection_name.delete_one({"_id": obj_instance})


def delete_result(sim_id):
    """
    deletes one result in the simulation_results collection selected by simId
    :param sim_id: ID of a simulation, is created whenever a new simulation is started
    """
    collection_name = checkDB_connection_result()
    check_simID_result(sim_id, collection_name)
    obj_instance = ObjectId(sim_id)
    collection_name.delete_one({"input_simulation_id": obj_instance})


def modify_idf_data(sim_id, idf_data):
    """
    updates an existing document in the input_simulation collection with a new .idf file
    selected by simId
    :param sim_id: ID of a simulation, is created whenever a new simulation is started
    :param idf_data: to base64 encoded .idf file
    """
    collection_name = checkDB_connection_input()
    check_simID_input(sim_id, collection_name)
    obj_instance = ObjectId(sim_id)
    new_values = {"$set": {'idf_data': idf_data}}
    collection_name.update_one({"_id": obj_instance}, new_values)


def modify_csv_data(sim_id, csv_data):
    """
     updates an existing document in the input_simulation collection with a new .csv file
     selected by simId
     :param sim_id: ID of a simulation, is created whenever a new simulation is started
     :param csv_data: to base64 encoded .csv file
     """
    collection_name = checkDB_connection_input()
    check_simID_input(sim_id, collection_name)
    obj_instance = ObjectId(sim_id)
    new_values = {"$set": {'csv_data': csv_data}}
    collection_name.update_one({"_id": obj_instance}, new_values)


def modify_epw_data(sim_id, epw_data):
    """
     updates an existing document in the input_simulation collection with a new .epw file
     selected by simId
     :param sim_id: ID of a simulation, is created whenever a new simulation is started
     :param epw_data: to base64 encoded .epw file
     """
    collection_name = checkDB_connection_input()
    check_simID_input(sim_id, collection_name)
    obj_instance = ObjectId(sim_id)
    new_values = {"$set": {'epw_data': epw_data}}
    collection_name.update_one({"_id": obj_instance}, new_values)


def check_files(sim_id):
    """
    Check if idf file, weather data and occupancy data was added to the server before the simulation runs
    """
    collection_name = checkDB_connection_input()
    check_simID_input(sim_id, collection_name)
    obj_instance = ObjectId(sim_id)
    idf_data = 'idf_data'
    epw_data = 'epw_data'
    csv_data = 'csv_data'
    idf_file = collection_name.find_one({"_id": obj_instance}, {idf_data: 1})
    idf_variable = idf_file['idf_data']
    if idf_variable == '':
        raise ValueError("IDF File is missing. Please provide a valid IDF File!")
    epw_file = collection_name.find_one({"_id": obj_instance}, {epw_data: 1})
    epw_variable = epw_file['epw_data']
    if epw_variable == '':
        raise ValueError("Weather File is missing. Please provide a valid Weather (epw) File!")
    csv_file = collection_name.find_one({"_id": obj_instance}, {csv_data: 1})
    csv_variable = csv_file['csv_data']
    if csv_variable == '':
        raise ValueError("Occupancy File is missing. Please provide a valid csv File!")


def insert_result(input_simulation_id, idf_string, status):
    """
    inserts a document into the simulation_results collection. Creates a timestamp and a unique filename.
    :param input_simulation_id: ID of a document in the input_simulation collection
    :param idf_string: to base64 encoded .idf file
    :param status: status of the simulation
    :return: generated ObjectID for the stored document in the simulation_results collection
    """
    collection_name = checkDB_connection_result()
    date = utils.get_date()
    filename = utils.get_date_for_filename()
    input_id = ObjectId(input_simulation_id)
    idf_data = idf_string
    sim_status = status
    item = {
        "date_of_creation": date,
        "filename": "SimOutput" + filename,
        "input_simulation_id": input_id,
        "idf_data": idf_data,
        "status": sim_status,
    }
    try:
        result_set = collection_name.insert_one(item)
    except pymongo.errors.DocumentTooLarge:
        idf_error_string = "File to large for MongoDB. File can be found at \"backend\\eppy_output\\" + str(input_id) + \
                     "_used_IDF.idf\"."
        logging.info("[Simulation_Helper]: " + str(idf_error_string))
        idf_bytes = idf_error_string.encode('utf-8')
        encoded_idf = base64.b64encode(idf_bytes)
        encoded_idf_string = encoded_idf.decode('utf-8')
        item = {
            "date_of_creation": date,
            "filename": "SimOutput" + filename,
            "input_simulation_id": input_id,
            "idf_data": encoded_idf_string,
            "status": sim_status,
        }
        result_set = collection_name.insert_one(item)
        os.replace("tmp/Output.idf", "eppy_output/" + input_simulation_id + "_used_IDF.idf")
    return result_set.inserted_id


def get_idf_data(sim_id, output_filename=None):
    """
    retrieves a stored .idf file of the input_simulation collection and decodes it back to its original file or
    string
    :param sim_id: ID of a simulation, is created whenever a new simulation is started
    :param output_filename: how the file should be named if not directly stored into a variable
    :return: decoded string
    """
    data = get_input_simulation(sim_id)
    return utils.decode_from_base64_string(data[0]['idf_data'], output_filename)


def get_csv_data(sim_id, output_filename=None):
    """
     retrieves a stored .csv file of the input_simulation collection and decodes it back to its original file or
     string
     :param sim_id: ID of a simulation, is created whenever a new simulation is started
     :param output_filename: how the file should be named if not directly stored into a variable
     :return: decoded string
     """
    data = get_input_simulation(sim_id)
    return utils.decode_from_base64_string(data[0]['csv_data'], output_filename)


def get_epw_data(sim_id, output_filename=None):
    """
     retrieves a stored .epw file of the input_simulation collection and decodes it back to its original file or
     string
     :param sim_id: ID of a simulation, is created whenever a new simulation is started
     :param output_filename: how the file should be named if not directly stored into a variable
     :return: decoded string
     """
    data = get_input_simulation(sim_id)
    return utils.decode_from_base64_string(data[0]['epw_data'], output_filename)


def get_eso_data(sim_id, output_filename=None):
    """
     retrieves a stored .eso file of the input_simulation collection and decodes it back to its original file
     or string
     :param sim_id: ID of a simulation, is created whenever a new simulation is started
     :param output_filename: how the file should be named if not directly stored into a variable
     :return: decoded string
     """
    data = get_output_simulation(sim_id)
    return utils.decode_from_base64_string(data[0]['eso_data'], output_filename)


def get_used_idf(sim_id, output_filename=None):
    """
     retrieves a stored .idf file of the simulation_results collection and decodes it back to its original file or
     string
     :param sim_id: ID of a simulation, is created whenever a new simulation is started
     :param output_filename: how the file should be named if not directly stored into a variable
     :return: decoded string
     """
    data = get_output_simulation(sim_id)
    return utils.decode_from_base64_string(data[0]['idf_data'], output_filename)


def save_metadata(sim_id, metadata_dict):
    """
    saves metadata used for simulations into the input_simulation collection
    :param sim_id: ID of a simulation, is created whenever a new simulation is started
    :param metadata_dict: dictionary containing all necessary metadata
    """
    collection_name = checkDB_connection_input()
    check_simID_input(sim_id, collection_name)
    obj_instance = ObjectId(sim_id)
    item = {"$set": {'start_day': metadata_dict["start_day"],
                     'start_month': metadata_dict["start_month"],
                     'start_year': metadata_dict["start_year"],
                     'end_day': metadata_dict["end_day"],
                     'end_month': metadata_dict["end_month"],
                     'end_year': metadata_dict["end_year"],
                     'width': metadata_dict["width"],
                     'length': metadata_dict["length"],
                     'height': metadata_dict["height"],
                     'orientation': metadata_dict["orientation"],
                     'zone_name': metadata_dict["zone_name"],
                     'infiltration_rate': metadata_dict["infiltration_rate"]}}
    collection_name.update_one({"_id": obj_instance}, item)


def get_metadata(sim_id):
    """
    returns all the metadata stored in the input collection
    :param sim_id: ID of a simulation, is created whenever a new simulation is started
    :return: metadata array containing all necessary metadata
    """
    data = get_input_simulation(sim_id)
    metadata = {}
    metadata_items = ["start_day", "start_month", "start_year", "end_day", "end_month", "end_year",
                      "width", "length", "height", "orientation", "zone_name", "infiltration_rate"]
    for items in metadata_items:
        metadata[items] = data[0][items]
    return metadata


def create_Simulation_Series():
    """
    Inserts an empty document in the simulation_series collection
    :return: sim_series_id: id of the simulation which makes it unique
    """
    collection_name = checkDB_connection_series()
    date = utils.get_date()
    item = {
        "date_of_creation": date,
    }
    result_set = collection_name.insert_one(item)
    return str(result_set.inserted_id)


def update_simSer(sim_Ser_Id, dict_field, sim_id):
    """
    Updates a simulation series document, the simulation series id is created whenever a series is created
    :param sim_Ser_Id: id of a simulation series
    :param dict_field: key to be updated
    :param sim_id: value to be saved
    """
    collection_name = checkDB_connection_series()
    check_simID_input(sim_Ser_Id, collection_name)
    obj_instance = ObjectId(sim_Ser_Id)
    item = {"$set": {dict_field: sim_id}}
    collection_name.update_one({"_id": obj_instance}, item)


def get_simSer_idList(sim_Ser_Id, inputList=True):
    """
    Pull the list of input ids for a given simulation series id
    Exception is thrown, if the output document is None
    :param sim_Ser_Id: Simulation series id
    :param inputList: True Input ID List (Default), False: Output
    :return: List of SimIDs (In- / Output)
    """
    collection_name = checkDB_connection_series()
    obj_instance = ObjectId(sim_Ser_Id)
    check_simID_input(sim_Ser_Id, collection_name)
    document = collection_name.find_one({"_id": obj_instance})
    input_object_ids = []
    if inputList:
        searchstring = "input"
    else:
        searchstring = "output"
    for key, value in document.items():
        if key.startswith(searchstring):
            input_object_ids.append(str(value))
    return input_object_ids


def checkDB_connection_input():
    """
    Calls the collection of MongoDB
    :return: collection name
    """
    collection_name = get_database.get_input_simulation_collection()
    if collection_name is None:
        raise ConnectionError("connection to db was not successful")
    return collection_name


def checkDB_connection_result():
    """
    Calls the collection of MongoDB
    :return: collection name
    """
    collection_name = get_database.get_result_collection()
    if collection_name is None:
        raise ConnectionError("connection to db was not successful")
    return collection_name


def checkDB_connection_series():
    """
    Calls the collection of MongoDB
    :return: collection name
    """
    collection_name = get_database.get_simulation_series_collection()
    if collection_name is None:
        raise ConnectionError("connection to db was not successful")
    return collection_name


def check_simID_input(sim_id, collection_name):
    """
    Checks if the simID is existing in the database
    """
    if sim_id is None:
        raise ValueError("object id cannot be null")
    if len(sim_id) != 24:
        raise ValueError("provided id was not 24 characters long")
    obj_instance = ObjectId(sim_id)
    if not collection_name.count_documents({"_id": obj_instance}, limit=1):
        raise ValueError("The provided simID is not a valid simID in the database. simID does not exist")


def check_simID_result(sim_id, collection_name):
    """
    Checks if the simID is existing in the database
    """
    if sim_id is None:
        raise ValueError("object id cannot be null")
    if len(sim_id) != 24:
        raise ValueError("provided id was not 24 characters long")
    obj_instance = ObjectId(sim_id)
    if not collection_name.count_documents({"input_simulation_id": obj_instance}, limit=1):
        raise ValueError("The provided simID is not a valid simID in the database. simID does not exist")