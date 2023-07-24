---
layout: default
title: Program
nav_order: 5
has_children: true
---

# Program Features

This web application provides the user with the following functionality:

   * Simulation configuration
      * Upload of an IDF file
      * Upload of an EPW file
      * Selection of the simulation period (Timeframe)
         * Simulation over then span of one day
         * Simulation over the span of several days up to a year
      * Upload of an occupancy CSV file or creating a custom occupancy
      * Adjustment of room parameters (room dimensions and infiltration rate)
   * Running the simulation
   * Running a simulation only with an IDF and EPW file without further adjustments
   * Simulation results
      * Display of selected measured values in graphs
         * Zone air temperature
         * CO2 concentration
         * Outdoor temperature
         * Relative humidity
         * Barometric pressure (outdoor)
         * Occupancy
      * Download of simulation results as CSV file or ESO file
   * Simulation History
      * Overview on previously run simulations
      * Reopen previous simulation results
      * Reopen previous simulations
    * REST API
      * include all functions from above
      * run a simulation series with multiple variations of room variables
