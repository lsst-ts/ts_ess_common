.. py:currentmodule:: lsst.ts.ess.common

.. _lsst.ts.ess.common:

##################
lsst.ts.ess.common
##################

This package contains code to read environmental sensor data and documentation for those sensors.

Contributing
============

``lsst.ts.ess.common`` is developed at https://github.com/lsst-ts/ts_ess_common.
You can find Jira issues for this module using `labels=ts_ess_common <https://jira.lsstcorp.org/issues/?jql=project%3DDM%20AND%20labels%3Dts_ess_common>`_.

.. toctree::
   add_a_new_sensor
   :maxdepth: 1

Sensors 
=======

Documentation for sensors read by the ESS, including those read by other ts_ess packages (ts_ess_controller and ts_ess_labjack).

.. toctree::
   auroracloud_sensor
   boltek_EFM-100C_sensor
   boltek_LD-250_sensor
   campbellscientific_CSAT3BH_sensor
   gill_windsonic_2-d_sonic_wind_sensor
   omega_hx80a_series_sensors
   sel_temperature_sensor
   young_weather_station
   :maxdepth: 1

Python API reference
====================

.. automodapi:: lsst.ts.ess.common
   :no-main-docstr:

Version History
===============

.. toctree::
    version_history
    :maxdepth: 2
