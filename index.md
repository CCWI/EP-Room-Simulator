---
layout: default
title: Home
nav_order: 1
description: "Get to know the tool EnergyPlus Room Simulator."
permalink: /
---
# EnergyPlus Room Simulator

<br>
<img src="images/Room.jpg" alt="Screenshot" width="70%">

*Screenshot from the application*

This program is intended to simplify the application of EnergyPlus for room climate simulation.
It is a Python-based web application that allows the simulation of indoor climate (temperature, humidity, CO2) in standalone rooms (zones) for data generation purposes using the simulation software EnergyPlus.

For this, an easy-to-use and straightforward GUI is provided, along with a REST API supporting the automation of simulations. It is possible to simulate the indoor climate of a room with individual IDF and EPW files. Furthermore, adjustments can be made to occupancy (presence of people and window openings), room dimensions, room orientation, and infiltration rate. Before starting the simulation, the modified version of a room model can be visualized. After the simulation, plots of the simulation results can be displayed, and the simulation results can be downloaded as a CSV file and an ESO file. All inputs and outputs are persistently stored in a NoSQL database (MongoDB).

This documentation provides you with information on how to install and use this tool.


<br>

### Demo Videos

To get an impression of the tool before installing it, you may view the following demo videos.

Preparing a Simulation | Running Simulation and Viewing Results
:-: | :-:
<video src='https://github.com/CCWI/EP-Room-Simulator/assets/50439280/bf6f2125-4470-466f-a481-45366c657abf' width=120></video> | <video src='https://github.com/CCWI/EP-Room-Simulator/assets/50439280/00da33b5-bbf7-45fc-992a-9c9b667bbbb9' width=120></video>



