---
layout: default
title: Installation
nav_order: 2
---

# Installation

Requirements to install the software Indoor Climate Simulation:

* Windows or Linux OS (Recommended: Ubuntu or Mint)
* [Installation of Python 3.10](https://www.python.org/)
* [Installation of EnergyPlus (developed at version 22-2-0)](https://energyplus.net/)
* [Installation of Docker (developed at version 20.10.23)](https://www.docker.com/)
* [Installation of Node.js (developed at version 20.3.1)](https://learn.microsoft.com/en-us/windows/dev-environment/javascript/nodejs-on-windows)

## Instructions

To install the software for the first time, the "install.py" script must be called with the "python install.py" command. To do this, the user must be in the project folder and not call this script from parent/subordinate folders. The script then creates a virtual environment (venv) for the installation of required python packages and activates it. After that, all required packages will be installed into the virtual environment using pip. Once these steps are completed, the Docker image "mongo" is downloaded in the current version of Docker Hub. After the download is complete, a Docker container is created named "simulation_db". When these steps are done, the frontend and backend will be started. At the end of the complete installation, two cmd shells should be open in which the two program parts run. Under *localhost:100* the GUI should be accessible and usable.  
To start the software after the installation has been completed, it must be ensured that the venv is activated before the script "install.py" is called again. In this case, the script will only start the created container "simulation_db" and both frontend and backend. The program should then be usable without a complete reinstallation. After installing or restarting the program, two Python applications and a MongoDB Docker container should be running on the machine. 
Different network ports are blocked by the software at this point. Port 100 runs the frontend based on the Flask framework, while port 5000 is where the REST API, also based on Flask, waits for requests. The MongoDB container also blocks port 27017 and the Node.js server, running the visualization is on port 50715.

## Note 
The script performs either a complete installation or just a start of the resources and the program. The full installation includes creating a Python VENV virtual environment, downloading and starting the MongoDB image and container, installing all required Python packages, and starting the frontend and backend."Just starting" involves starting the existing MongoDB Docker container and the program. Note that for a complete installation, a system path will be checked for equality. This check is only successful if no virtual environment is enabled. So, to do a completely fresh installation, all existing, currently activated virtual environments must be deactivated. If you just want to start the programs (if an installation has already been executed), you must manually activate the dedicated venv.

## Data Storage

Input

To run simulations with EnergyPlus, some data is needed. Specifically, an .idf file for the room model and a .csv file containing occupancy and window opening data, plus some required metadata such as start date, end date, infiltration rate, and room dimensions. All this data is persistently stored in the MongoDB Collection simulation-input. In addition, the entries receive a filename and a timestamp.


Output

The program executes EnergyPlus simulations. The results of such simulations are different output files of EnergyPlus. These are stored in the project folder in the *eppy_output* directory, and most of them will be overwritten with each simulation run. The .idf files that are used for the simulation are not surpassed by this. These are tagged and stored permanently in the folder. The EnergyPlus output file, the .eso file will be tagged and stored in the *eso_output* folder. These will not be overwritten, which means that with each successful simulation, an additional .eso file will be created in this folder. Used .idf and .csv files are persistently stored in the MongoDB collection *simulation-output*. The time frame, as well as a filename, are also stored in addition to the data mentioned above.


## Installation under Linux

For the installation under Linux, there are shell scripts with the extension ".sh" available. The installation is  analogous to the bash scripts. To start the backend, the config.ini in the backend directory must be adjusted. Here is an example configuration in which EnergyPlus was installed in the /opt/ directory:

```
[EnergyPlus]
EplusPath = /opt/EnergyPlus-22.2.0
iddPath = /opt/EnergyPlus-22.2.0/Energy+.idd
```

If the installation is made on a server and should be accessible by clients, the frontend_config.ini in the frontend directory must also be adjusted:

```
[Frontend]
IP = 0.0.0.0
Port = 80
```

By setting the IP address to 0.0.0.0, the web server runs on all available network adapters. Often only a few ports are allowed by the firewall within a network. The port 100 is configured in the frontend as default. Because this is not standard and therefore is often blocked, it is recommended to change the port to the standard HTTP port 80.


# Parameterization & Configuration

The configuration of the most important software parameters for the backend can be done in the config.ini, which is located in the folder "indoor-climate-simulation/backend". The following parameters can be set:

| Parameter | Description                                                                                                                                                                                                                                                                                                                             | Section |
|--------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
|EplusPath| Path to the EnergyPlus installation on the local machine. This path must be specified here. Example: C:/EnergyPlusV22-2-0                                                                                                                                                                                                               | EnergyPlus
|iddPath| Path to the .idd file of EnergyPlus. This path must be specified to start simulations. The path must lead to the folder of the EnergyPlus installation. Idd-files which are located in other directories will lead to error messages. Example: C:/EnergyPlusV22-2-0/Energy+.idd                                                         |EnergyPlus|
|co2OutdoorValue| Result of the WarmUp simulation and value to be applied for outdoor CO2 during the actual simulation. The value must be specified in ppm (particles per million).<br> The default is 400 ppm.                                                                                                                                           |EnergyPlus|
|co2GenerationRate| CO2 generation rate of a human. The default is 0.0000000382.                                                                                                                                                                                                                                                                            |EnergyPlus|
|ActivityLevel| The activity level of a human in the simulation. Based on information from the American Society of Heating, Refrigerating and Air-Conditioning (ANSHRAE) of the American National Standard Institute (ANSI) (ANSI/ASHRAE 55-2010), the default is set to 108 (mix of 55% reading, 40% typing, 3% filing sitting and 2% walking around). |EnergyPlus|
|OutputDirectoryName| Name of the output directory to be created and used for output EnergyPlus files. <br>The default is "eppy_output".                                                                                                                                                                                                                      |EnergyPlus|
|Connection_String | Connection string used to connect to the room climate MongoDB. The correct port must be specified. By default, the default Docker port (27017) is used. The "mongodb://" is required and should not be changed. <br>Example: mongodb://localhost:27017                                                                                  |MongoDB|


The frontend configuration is contained in a separate file in the frontend directory *frontend_config.ini* and includes the following parameters:

| Parameter | Description                                                                                                                                                                                                                                     | Section |
|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| IP        | The IP address where the frontend can be reached.                                                                                                                                                                                               |frontend|
| Port      | The port where the frontend can be reached.                                                                                                                                                                                                     |frontend|
| Address   | The address or IP where the backend can be reached by the frontend.                                                                                                                                                                             |backend|
| Port      | The port where the backend can be reached by the frontend.                                                                                                                                                                                      |backend|


For more information regarding configurations (e.g. config.ini), please refer to [Error Management](https://kathisa.github.io/indoorclimatesimulation/ErrorManagement.html).

