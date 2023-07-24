---
layout: default
title: README
nav_exclude: true
---

# EnergyPlus Room Simulator Documentation Page


This is the documentation page for the EnergyPlus Room Simulator, a Python-based web application that allows the simulation of indoor climate (temperature, humidity, CO2) in standalone rooms (zones) for data generation purposes using the simulation software EnergyPlus.

For this, an easy-to-use and straightforward GUI is provided, along with a REST API supporting the automation of simulations. It is possible to simulate the indoor climate of a room with individual IDF and EPW files. Furthermore, adjustments can be made to occupancy (presence of people and window openings), room dimensions, room orientation, and infiltration rate. Before starting the simulation, the modified version of a room model can be visualized. After the simulation, plots of the simulation results can then be displayed, and the simulation results can be downloaded as a CSV file and an ESO file. All inputs and outputs are persistently stored in a NoSQL database (MongoDB).

The application is primarily written in Python and uses the Python package eppy to work with EnergyPlus.
It is divided into a frontend (GUI) and a backend (REST API), which are implemented as two separate Python Flask servers.



The code for this tool can be found [here](https://github.com/CCWI/EP-Room-Simulator)
