---
layout: default
title: Use of API
parent: REST API
nav_order: 2
---

# Use of API

Here are some examples on how to use the REST API. Example code may be run in a [Jupyter Notebook](https://jupyter.org/). 

| Table of contents                                                                        |                                                                                                                                                                                                                                              
|------------------------------------------------------------------------------------------|
| [Import statements](#import-statements)                                                  |
| [Check if docker is running](#check-if-docker-is-running)                                |
| [Create a new simulation](#create-a-new-simulation)                                      |
| [Upload files for simulation](#upload-files-for-simulation)                              |
| [Set parameter/metadata for simulation](#set-parameters/metadata-for-simulation)         |
| [Start a simulation](#start-a-simulation)                                                |
| [Results](#results)                                                                      |
| [View simulations inputs of a simulation](#-view-simulation-inputs-of-a-simulation)      |
| [Overview of all simulations in database](#overview-on-all-simulations-in-database)      |
| [Delete a simulation](#delete-a-simulation)                                              |
| [Delete result entry of a simulation](#delete-result-entry-of-a-simulation)              |
| [Quick simulation with idf and epw file only](#simulation-with-only-an-idf-and-epw-file) |
| [Reopen an old simulation](#reopen-an-old-simulation)                                    |
| [Simulation Series](#simulation-series)                                                  |

## Import statements
```
import requests
import base64
import json
import pandas as pd
import esoreader
import random
import time
import io
from datetime import datetime
```
If an error occurs please check if all packages are installed. 

## Check if the backend is running

```
response = requests.get("http://localhost:5000/status")
response.json()
```
Response: 
```
{'success': True}
```

## Create a new simulation
Create a new sim ID.  

```
response = requests.post("http://localhost:5000/simulation")
response.json()
```
Response: 
```
'64998548b04d0bcba8f22b4d'
```

Set the sim ID as a variable. 

```
simID = response.json()
print("The simulation ID is", simID)
```
Response: 
```
The simulation ID is 64998548b04d0bcba8f22b4d
```
Returns the information about a simulation with the sim ID from the previous request. 
```
response = requests.get("http://localhost:5000/simulation", json={"id": simID})
response.json()
```
Response: 
```
{'csv_data': '',
 'date_of_creation': '2023-06-26-14:32',
 'end_day': '',
 'end_month': '',
 'end_year': '',
 'epw_data': '',
 'height': '',
 'idf_data': '',
 'idf_filename': 'SimInput08228370',
 'infiltration_rate': '',
 'length': '',
 'orientation': '',
 'start_day': '',
 'start_month': '',
 'start_year': '',
 'width': '',
 'zone_name': ''}
```

## Upload files for simulation

Define the paths for all simulation files. 
Each simulation requires an .idf, .epw, and .csv file.
```
idf_file = 'example_room.idf'                    # room model
epw_file = 'SanFranciscoWeather.epw'             # weather data
csv_file = 'occupancy_1day.csv'                  # occupancy data
```
Upload files. Files need to be encoded!
```
#idf file
with open(idf_file, 'rb') as f:
    encoded_object = base64.encodebytes(f.read()).decode('utf-8')

    params = {
     "id":   simID,
     "data": encoded_object
    }
    response = requests.post("http://localhost:5000/idf", json=params)

    response.json() if response.status_code == 200 else print("Failed with status code", response.status_code)
```
```
#epw file
with open(epw_file, 'rb') as f:
    encoded_object = base64.encodebytes(f.read()).decode('utf-8')
    
    params = {
     "id":   simID,
     "data": encoded_object
    }
    response = requests.post("http://localhost:5000/weather", json=params)

    response.json() if response.status_code == 200 else print("Failed with status code", response.status_code)
```
```
#csv file
with open(csv_file, 'rb') as f:
    encoded_object = base64.encodebytes(f.read()).decode('utf-8')
    
    params = {
     "id":   simID,
     "data": encoded_object
    }
    response = requests.post("http://localhost:5000/occupancy", json=params)

    response.json() if response.status_code == 200 else print("Failed with status code", response.status_code)
```
To check if the files are uploaded check the contents in the input simulation collection. 
```
#idf file
response = requests.get("http://localhost:5000/idf", json={"id": simID})
response.json() if response.status_code == 200 else print("Failed with status code", response.status_code)
```
Response (contens of idf file): 
```
'Version,22.2;\n\n  Timestep,6;\n\n  LifeCycleCost:Parameters,\n
Life Cycle Cost Parameters,
!- Name\n    EndOfYear,
!- Discounting Convention\n    ConstantDollar,
!- Inflation Approach\n    0.03,
!- Real Discount Rate\n    ,
!- Nominal Discount Rate\n    ,
!- Inflation\n    ,
!- Base Date Month\n    2011,
!- Base Date Year\n    ,
!- Service Date Month\n    2011,
!- Service Date Year\n    25,
!- Length of Study Period in Years\n    ,
!- Tax rate\n    None;
!- Depreciation Method\n\n  LifeCycleCost:UsePriceEscalation,\n
U.S. Avg  Commercial.... ..... ..... ..... 
```

```
#csv file/occupancy
response = requests.get("http://localhost:5000/occupancy", json={"id": simID})
response.json() if response.status_code == 200 else print("Failed with status code", response.status_code)
```
Response (contens of csv file): 
```
'day|time|occupants|win1\n
0|00:00:00|0|0\n
0|00:01:00|0|0\n
0|00:02:00|0|0\n
0|00:03:00|0|0\n
0|00:04:00|0|0\n
0|00:05:00|0|0\n
0|00:06:00|0|0\n
.... ..... .....
.... ..... .....
```

## Set parameters/metadata for simulation

Define the parameters. Set the timeframe and room parameters for the simulation. The zone name can be found in the idf file. If the zone name does not match the zone name in the idf file an energy plus error will occur. 


```
params = {
 "id": simID,
 "height": 3,
 "length": 5,
 "width": 4,
 "orientation":0,
 "start_day": 1,
 "start_month": 6,
 "start_year": 2022,
 "end_day": 1,
 "end_month": 6,
 "end_year": 2022,
 "infiltration_rate": 0.0019, 
 "zone_name": "example_office"
}
```

## Start a simulation

```
response = requests.post("http://localhost:5000/simulation/control", json=params)
response.json()
```
Response: 
```
{'success': True}
```
Check the status of the simulation: 
```
response = requests.get("http://localhost:5000/simulation/control", json={"id": simID})
response.json()
```
Response: 
```
{'status': 'done'}
```

## Results

Check the results of the simulation. This will fail until the simulation has completed sucessfully.  

```
response = requests.get("http://localhost:5000/result", json={"id": simID})
response.json()
```
Response: 
```
{'_id': '649850234b93c9929aa94e93',
 'date_of_creation': '2023-06-25-16:33',
 'eso_data': 'UHJvZ3JhbSBWZXJzaW9.... ...... ......
```

To see the results in a table this endpoint can be used.
```
response = requests.get("http://localhost:5000/result/csv", json={"id": simID})
response 
```
To view the csv data in a table use the following:
```
csv_data = io.BytesIO(response.content)
df = pd.read_csv(csv_data)
df.head()
```

|#|date|zone_air_temperature	|zone_co2_concentration	|zone_rel_humidity|outdoor_air_pressure	|outdoor_air_drybulb	|occupancy	|window|
|-|-|-|-|-|-|-|-|-|
|0	|2022-06-01 00:00	|22.444013	|1108.273413	|63.958120	|95590.316667	|13.03	|0	|0|
|1	|2022-06-01 00:01	|22.440291	|1107.175398	|63.947149	|95588.633333	|12.96	|0	|0|
|2	|2022-06-01 00:02	|22.436333	|1106.078853	|63.936722	|95586.950000	|12.89	|0	|0|
|3	|2022-06-01 00:03	|22.432135	|1104.983774	|63.926852	|95585.266667	|12.82	|0	|0|
|4	|2022-06-01 00:04	|22.427712	|1103.890163	|63.917489	|95583.583333	|12.75	|0	|0|

## View simulation inputs of a simulation 

Returns the metadata of a simulation. This will only return the inforamtion after the simulation was run and the data was saved in the databse. 

```
response = requests.get("http://localhost:5000/metadata", json={"id": simID})
response.json()
```
Response: 
```
{'end_day': 1,
 'end_month': 6,
 'end_year': 2022,
 'height': 3.0,
 'infiltration_rate': 0.0019,
 'length': 5.0,
 'orientation': 0,
 'start_day': 1,
 'start_month': 6,
 'start_year': 2022,
 'width': 4.0,
 'zone_name': 'example_office'}
```

## Overview of all simulations in database

Run this, to get an overview of all performed simulations. The response will return all results from the simulation_result collection. 

```
response = requests.get("http://localhost:5000/result/overview")
response.json()
```
Response: 
```
[{'_id': '64993e61b7d43a7d7567209e',
  'date_of_creation': '2023-06-26-09:29',
  'filename': 'SimOutput37167285',
  'input_simulation_id': '64993e3cb7d43a7d7567208f',
  'status': 'done'},
 {'_id': '64993cb7b7d43a7d7567208a',
  'date_of_creation': '2023-06-26-09:22',
  'filename': 'SimOutput31360632',
  'input_simulation_id': '64993c94b7d43a7d7567207b',
  'status': 'done'},
 {'_id': '64993bd25b2b5cbc3201e909',
  'date_of_creation': '2023-06-26-09:18',
  'filename': 'SimOutput42576916',
  'input_simulation_id': '64993b915b2b5cbc3201e8fa',
  'status': 'done'},
.... ..... .....
```

## Delete a simulation

Example how to delete a simulation from the input_simulation collection in the database (The results will not be deleted). 

```
simID = "6498250b03aeca892a58ab98"
response = requests.delete("http://localhost:5000/simulation", json={"id": simID})
response.json()
```
Response: 
```
{'success': True}
```

## Delete result entry of a simulation

```
simID = "64984fee4b93c9929aa94e83"
response = requests.delete("http://localhost:5000/result", json={"id": simID})
response.json()
```
Response: 
```
{'success': True}
```

## Quick simulation with idf and epw file only

It is possible to run a simulation and only upload an idf and epw file. But different endpoints need to be used. Here is an example: 

First initiate a new simulation. 

```
response = requests.post("http://localhost:5000/simulation")
response.json()
```
Response: 
```
'64998256b04d0bcba8f22b40'
```

And set the sim ID

```
simID = response.json()
print("The simulation ID is", simID)
```
Response: 
```
The simulation ID is 64998256b04d0bcba8f22b40
```
Upload the idf and epw file: 
```
idf_file = 'example_room.idf'                    # room model
epw_file = 'SanFranciscoWeather.epw'             # weather data
```
The files can be uploaded as described [previously](#upload-files-for-simulation).

Start the simulation with the correct endpoint: 

```
response = requests.post("http://localhost:5000/simulation/control/onlyidf", json={"id": simID})
response.json()
```
Response: 
```
{'success': True}
```

Check the status of the simulation.

```
response = requests.get("http://localhost:5000/simulation/control", json={"id": simID})
response.json()
```
Response: 
```
{'status': 'done'}
```

Check if results are in database. This will fail until the simulation has completed successfully

```
response = requests.get("http://localhost:5000/result", json={"id": simID})
response)
```

Return the status of an simulation which was run with only an idf and epw file (same response like simulation/control)

```
response = requests.get("http://localhost:5000/simulation/control/onlyidf", json={"id": simID})
response.json()
```
Response: 
```
{'status': 'done'}
```

## Reopen an old simulation

It is possible to reopen an old simulation. This means all the input data which was used in the simulation will be available again and it is possible to edit the parameter and start a new simulation. This will not change the data of the old simulation ID. It will always initiate a new simulation. 

To reopen an old simulation, the sim ID from the database is needed. The GET request will return all input data. This is necessary to copy the parameters for the simulation. 

```
simID = "64998548b04d0bcba8f22b4d"
response = requests.get("http://localhost:5000/reopensim", json={"id": simID})
response.json()
```
Response: 
```
[{'end_day': 1,
  'end_month': 6,
  'end_year': 2022,
  'height': 3.0,
  'infiltration_rate': 0.0019,
  'length': 5.0,
  'orientation': 0,
  'start_day': 1,
  'start_month': 6,
  'start_year': 2022,
  'width': 4.0,
  'zone_name': 'example_office'},
 '  Version,22.2;\n\n  Timestep,6;\n\n  LifeCycleCost:Parameters,\n    Life Cycle Cost Parameters,  !- Name\n    EndOfYear,               !- Discounting Convention\n    ConstantDollar,          !- Inflation Approach\n    0.03,                    !- Real Discount Rate\n    ,                        !- Nominal Discount Rate\n    ,                        !- Inflation\n    ,                        !- Base Date Month\n    2011,                    !- ..... ...... ...... .....
```

With the post request a new simulation is created in the database. The parameter here is the sim ID from the old simulation. This request retrieves all inforamtion from the old simulation and inserts it in the database with a new sim ID. It will return the sim ID from the new simulation. With this sim ID it is possible to edit the data or upload new files. The csv, idf and epw file were all automatically uploaded in the dadabase with the new sim ID. To change the data use the requests from above (upload files, set metadata, etc.)


```
response = requests.post("http://localhost:5000/reopensim", json={"id": simID})
response.json()
```
Response: 
```
'64998873b04d0bcba8f22b76'
```

Copy now the sim ID and set the sim ID in the parameters. Copy the parameters from above (GET request)(but only parameter, not the information about the files) and now its possible to run a new simulation. It is not required to upload the files here because the csv, idf and epw files from the old simulation were uploaded to the database. But it it necessary to insert here the paramerters again, because the POST reqeust from simulation/control expects the parameters in the request body. 

```
simID = "64998873b04d0bcba8f22b76"
params = {
 "id": simID,
 'end_day': 1,
 'end_month': 6,
 'end_year': 2022,
 'height': 3.0,
 'infiltration_rate': 0.0019,
 'length': 5.0,
 'orientation': 0,
 'start_day': 1,
 'start_month': 6,
 'start_year': 2022,
 'width': 4.0,
 'zone_name': 'example_office'}

response = requests.post("http://localhost:5000/simulation/control", json=params)
response.json()
```
Response: 
```
{'success': True}
```
Check status of simulation
```
response = requests.get("http://localhost:5000/simulation/control", json={"id": simID})
response.json()
```
Response: 
```
{'status': 'done'}
```

## Simulation Series

A simulation series will run mulitple simulation with the same idf, epw  and csv file but the room parameters can be adjusted. Here is an example on how to create a series. 

Information: a series will take some time depending on the variations! Upload of files, create a simulation etc. will all take more time than a single simulation!

```
params = {
    "height": 7,
    "height_max": 8,
    "height_iter": 1,
    "length": 11,
    "length_max": 12,
    "length_iter": 1,
    "width": 4,
    "width_max": 6,
    "width_iter": 1,
    "orientation": 0,
    "orientation_max": 0,
    "orientation_iter": 0,
    "start_day": 17,
    "start_month": 5,
    "start_year": 2023,
    "end_day": 17,
    "end_month": 5,
    "end_year": 2023,
    "infiltration_rate": 0.0019,
    "infiltration_rate_max": 0.0019,
    "infiltration_rate_iter": 0
}
response = requests.post("http://localhost:5000/series/create", json=params)
response.json()
```
Response: 
```
'649995ebb04d0bcba8f239a4'
```

Set sim ID

```
sim_ser_id = response.json()
print(sim_ser_id)
```
Response: 
```
649995ebb04d0bcba8f239a4
```

Height: 7 - 8 Length: 11 - 12 Width: 4 - 5 - 6 => 12 Variationen (2 * 2 * 3)
This example will run 12 simulation. When the simulation is startet it can take a while! It depends on the number of simulations!

Add files to simulation 

```
idf_file = 'example_room.idf'                    # room model
epw_file = 'SanFranciscoWeather.epw'             # weather data
csv_file = 'occupancy_1day.csv'                  # occupancy data
```
The files can be uploaded as described [previously](#upload-files-for-simulation).

Start a simulation series

```
response = requests.post("http://localhost:5000/series/run", json={"id": sim_ser_id})
response.json()
```
Response: 
```
{'success': True}
```
Return status of simulation

```
response = requests.get("http://localhost:5000/series/run", json={"id": sim_ser_id})
response.json()
```
Response if simulation is still running: 
```
{'status': 'in Progress'}
```
Response if all simulations were successful: 
```
{'status': 'done'}
```

To get an overview of all run simulations run
```
response = requests.get("http://localhost:5000/series/results", json={"id": sim_ser_id})
response.json()
```

Response (list of all created simulations in a series): 
```
['6499c476475b75d3e877b615',
 '6499c476475b75d3e877b619',
 '6499c476475b75d3e877b61d',
 '6499c476475b75d3e877b621',
 '6499c476475b75d3e877b625',
 '6499c476475b75d3e877b629',
 '6499c476475b75d3e877b62d',
 '6499c476475b75d3e877b631',
 '6499c476475b75d3e877b635',
 '6499c476475b75d3e877b639',
 '6499c476475b75d3e877b63d',
 '6499c476475b75d3e877b641']
```
