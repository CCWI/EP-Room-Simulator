from flask import Flask
import configparser
from fileHandler import fileHandler_Blueprint
from startSimOnlyIdf import startSimOnlyIdf_Blueprint
from startSim import startSim_Blueprint
from home import home_Blueprint
from editParameters import editParameters_Blueprint
from viewResult import viewResult_Blueprint
from simulationHistory import simHistory_Blueprint
from OccupancyUpload import ocpUpload_Blueprint
from OccupancyCustom import ocpCustom_Blueprint
from flask_cors import CORS


UPLOAD_FOLDER = 'idf_cache'

def create_app():
    """
    Factory pattern used for creating the frontend app
    Typical for flask all blueprints (pages) must be registered
    Config allows to set certain default values (allowed files or upload paths)
    :return: flask app
    """
    frontendApp = Flask(__name__, template_folder='template')
    frontendApp.config['UPLOAD_PATH'] = UPLOAD_FOLDER
    frontendApp.config['UPLOAD_EXTENSIONS'] = ['.idf', '.csv', '.epw']
    frontendApp.config['TEMPLATES_AUTO_RELOAD'] = True
    frontendApp.register_blueprint(home_Blueprint)
    frontendApp.register_blueprint(fileHandler_Blueprint)
    frontendApp.register_blueprint(editParameters_Blueprint)
    frontendApp.register_blueprint(startSim_Blueprint)
    frontendApp.register_blueprint(viewResult_Blueprint)
    frontendApp.register_blueprint(simHistory_Blueprint)
    frontendApp.register_blueprint(ocpUpload_Blueprint)
    frontendApp.register_blueprint(ocpCustom_Blueprint)
    frontendApp.register_blueprint(startSimOnlyIdf_Blueprint)
    CORS(frontendApp, origins='http://localhost:50715')
    return frontendApp


class DocumentClass:
    currentFileName = None


if __name__ == '__main__':
    frontend = create_app()
    config = configparser.ConfigParser()
    config.read('frontend_config.ini')
    frontend_config = config['Frontend']
    frontend.run(host=frontend_config['IP'], port=int(frontend_config['Port']), debug=True)
