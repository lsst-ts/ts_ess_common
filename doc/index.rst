.. py:currentmodule:: lsst.ts.ess.common

.. _lsst.ts.ess.common:

##################
lsst.ts.ess.common
##################

This package contains code to read environmental sensor data and documentation for those sensors.

Overview
========

The ESS (Environmental Sensors Suite) reports environmental data, such as temperature, pressure, rain, lightning, and even acceleration.
Note that the ESS is not the only reporter of environmental data; some systems such as cameras and the TMA have their own sensors and report that data directly.
But where practical, we use the ESS, in order to provide a unified interface.

The ESS CSC is coded in `ts_ess_csc`_.
It is an indexed CSC, and each instance reads a specific set of sensors.

Terminology
-----------

* Sensor: a device that measures one or more environmental parameters, such as temperature, pressure, or vibration.
  One "sensor" includes all the different channels of data reported by the device that serves the data.
  For example, multi-channel thermal sensors have multiple temperature probes, and the Omega HX85BA sensor measures relative humidity, air temperature, and barometric pressure.

* Data client: software (subclasses of `BaseDataClient`) that connects to a data server, reads the data, and reports it using SAL.
  Most data clients live in `ts_ess_csc`_ but a few live in packages such as `ts_ess_labjack`_.
  (They do not live in ts_ess_common because they depend on ts_salobj, and that package cannot.)
  Each ESS CSC instance is a collection of data clients that are specified and configured by the CSC's configuration.

Sensors
=======

Most sensors serve their own data (directly or by being plugged into an electronics box provided by the vendor).
Protocols include RS-232, RS-485, TCP/IP, USB, and FTDI.

* Sensors that serve their data via TCP/IP are be directly read by an ESS instance running on Kubernetes.
  These sensors are read by a subclass of `BaseDataClient`.

* Sensors that serve their data via USB or FTDI cannot be directly read by an ESS instance, because software running on Kubernetes cannot read these protocols.
  In this case we run custom software (in `ts_ess_controller`_) on RPis to read the data and transmit it via TCP/IP.
  For this one case, we represent sensors using a subclass of `sensor.BaseSensor`.
  The data is read by ``RpiDataClient`` in `ts_ess_csc`_, or a specialized variant.

* Sensors that serve their data via RS-232 or RS-485 serial are served in two different ways:

  * Some sensors are read by a Raspberry Pi running custom software, as per the "USB or FTDI" case above.
    This includes sensors that receive power from a custom serial cable: our custom Raspberry Pis systems provide power on their RS-232 ports.

  * Other sensors are read by serial-to-ethernet adapters, as per the TCP/IP case mentioned above.

* Sensors that provide analog or binary signals are read by LabJack T4 or T7 modules.
  LabJack modules are read by LabJack data client in `ts_ess_labjack`_.

See :ref:`lsst.ts.ess.common.adding_new_sensors` for more information.

Sensor Documentation
--------------------

Documentation for sensors:

.. toctree::
   aurora_cloud_sensor
   boltek_EFM-100C_sensor
   boltek_LD-250_sensor
   campbell_scientific_CSAT3B_sensor
   gill_windsonic_2-d_sonic_wind_sensor
   omega_HX80A_series_sensors
   sel_multi_channel_temperature_reader
   young_weather_station
   :maxdepth: 1

Related documentation:

.. toctree::
   adding_new_sensors
   rpi_communication_protocol
   :maxdepth: 1

Computing Dew Point
-------------------

.. _lsst.ts.ess.common.magnus_dewpoint_formula:

Sensor that detect relative humidity, air temperature, and barometric pressure should compute and report dew point.
Our standard equation for computing dew point is the :download:`Magnus formula <dewpoint_magnus_formula.pdf>`, as encoded in `compute_dew_point_magnus`.

SNMP Support
============

Documentation for SNMP support:

.. toctree::
   snmp
   :maxdepth: 1

Python API reference
====================

.. automodapi:: lsst.ts.ess.common
   :no-main-docstr:

.. automodapi:: lsst.ts.ess.common.device
   :no-main-docstr:

.. automodapi:: lsst.ts.ess.common.sensor
   :no-main-docstr:

Contributing
============

``lsst.ts.ess.common`` is developed at https://github.com/lsst-ts/ts_ess_common.
You can find Jira issues for this module using `labels=ts_ess_common <https://rubinobs.atlassian.net/issues/?jql=project%3DDM%20AND%20labels%3Dts_ess_common>`_.

Version History
===============

.. toctree::
    version_history
    :maxdepth: 2

.. _ts_ess_controller: https://ts-ess-controller.lsst.io
.. _ts_ess_csc: https://ts-ess-csc.lsst.io
.. _ts_ess_labjack: https://ts-ess-labjack.lsst.io
