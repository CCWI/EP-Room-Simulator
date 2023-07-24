---
layout: default
title: Architecture
nav_order: 3
---

# Architecture

The application is primarily written in Python and uses the Python package eppy to work with EnergyPlus.
It is divided into a frontend (GUI) and a backend (REST API), which are implemented as two separate Python Flask web servers. Simulation data is saved in an MongoDB instance, provided via a Docker container.
The following figure illustrates this architecture.

![Architecture](images/Architecture.jpg)
*Architecture*
