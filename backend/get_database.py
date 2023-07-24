# connects a client to mongodb and creates a database
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import utils


def get_db_status():
    """
    Check the connection to the docker container
    """
    try:
        maxSevSelDelay = 1
        client = MongoClient(serverSelectionTimeoutMS=maxSevSelDelay)
        client.server_info()
        return True
    except ServerSelectionTimeoutError as err:
        return False


def get_database():
    """
    Creates a connection to the mongoDB database on the port specified in config.ini
    :return MongoDb client Object which refers to the projektstudium database
    """
    # provide MongoDB url to connect python to mongodb with pymongo
    connection_string = utils.read_from_conf("MongoDB", "Connection_String")
    # create a connection using MongoClient
    client = MongoClient(connection_string)
    # create the database
    return client['projektstudium']


def get_input_simulation_collection():
    """
    Establishes a connection to the input_simulation collection in the projektstudium database
    :return: collection object of the input_simulation collection for usage with mongodb operations (select, read,..)
    """
    dbname = get_database()
    collection_name = dbname["input_simulation"]
    return collection_name


def get_run_collection():
    """
    Establishes a connection to the simulation_run collection in the projektstudium database
    :return: collection object of the simulation_run collection for usage with mongodb operations (select, read,...)
    """
    dbname = get_database()
    collection_name = dbname["simulation_run"]
    return collection_name


def get_result_collection():
    """
    Establishes a connection to the simulation_results collection in the projektstudium database
    :return: collection object of the simulation_results collection for usage with mongodb operations (select, read,...)
    """
    dbname = get_database()
    collection_name = dbname["simulation_results"]
    return collection_name


def get_simulation_series_collection():
    """
    Establishes a connection to the simulation_series collection in the projektstudium database
    :return: collection object of the simulation_series collection for usage with mongodb operations (select, read,...)
    """
    dbname = get_database()
    collection_name = dbname["simulation_series"]
    return collection_name
