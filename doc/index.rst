.. py:currentmodule:: lsst.ts.ess.dataclients

.. _lsst.ts.ess.dataclients:

##################
lsst.ts.ess.dataclients
##################

This package contains data client code for the Environmental Sensor Suite (ESS).
It also contains documentation for most sensors (not including thsoe read by LabJacks; see ts_ess_labjack for that documentation).

Sensors
=======

The following sensors are supported:

.. toctree::
   auroracloud_sensor
   boltek_EFM-100C_sensor
   boltek_LD-250_sensor
   campbellscientific_CSAT3BH_sensor
   gill_windsonic_2-d_sonic_wind_sensor
   omega_hx85a_sensor
   omega_hx85ba_sensor
   sel_temperature_sensor
   young_weather_station
   :maxdepth: 1

Contributing
============

``lsst.ts.ess.dataclients`` is developed at https://github.com/lsst-ts/ts_ess_dataclients.
You can find Jira issues for this module using `labels=ts_ess_dataclients <https://jira.lsstcorp.org/issues/?jql=project%3DDM%20AND%20labels%3Dts_ess_dataclients>`_.

Python API reference
====================

.. automodapi:: lsst.ts.ess.dataclients
   :no-main-docstr:

Version History
===============

.. toctree::
    version_history
    :maxdepth: 1
