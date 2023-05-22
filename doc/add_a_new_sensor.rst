.. |author| replace:: *Wouter van Reeven*

==================
Adding New Sensors
==================

The ts_ess_common and ts_ess_controller projects contain code for a wide variety of sensors, both in terms of functionality and how to conntect to them.
Occasionally a new sensor needs to be added.
This document describes how to do that.

Add New Sensor Code For An Unsupported Sensor Type
==================================================

There are two ways of adding a new sensor type.
The first one is adding it to the existing sensor types in ts_ess_common and the second one is to set up a completely new project.
The existing sensor types in ts_ess_common all are assumed to be connected to a Raspberry Pi, which is described in :ref:`connected-to-rpi`.
For sensors not connected to a Raspberry Pi, a different approach needs to be taken, which is described in :ref:`not-connected-to-rpi`.

.. _connected-to-rpi:

Sensors Connected To A Raspberry Pi
-----------------------------------

This is the preferred way of adding a new sensor.
The sensors are connected to a Raspberry Pi, either via a serial cable or via an FTDI cable that converts the serial connection to a USB connection.
A Docker container is installed on the Raspberry Pi, running a custom TCP/IP server, called the ESS Controller, to which the ESS CSC connects.
The ESS Controller polls the sensors, which generally generate telemetry every second, and converts the sensor telemetry to a common format that the CSC understands.
The ts_ess_common project holds the code for almost all sensors and the conversion of their telemetry plus for mock devices, which are used in the unit tests and when running in simulation mode.

The first step is to subclass `lsst.ts.ess.common.sensor.BaseSensor<https://github.com/lsst-ts/ts_ess_common/blob/develop/python/lsst/ts/ess/common/sensor/base_sensor.py>`_.
The purpose of that class is to parse a line of telemetry as produced by the sensor and to extract the telemetry values as ``int``, ``float`` or ``str``.
See for instance `lsst.ts.ess.common.sensor.Hx85aSensor<https://github.com/lsst-ts/ts_ess_common/blob/develop/python/lsst/ts/ess/common/sensor/omega_hx85a.py>`_.

Those values are then used by `lsst.ts.ess.common.device.BaseDevice<https://github.com/lsst-ts/ts_ess_common/blob/develop/python/lsst/ts/ess/common/device/base_device.py>`_ and its subclasses to prepare the telemetry to be sent to the CSC.
In general, lsst.ts.ess.common.device.BaseDevice should not need to be subclassed since the following subclasses exist:

  * lsst.ts.ess.common.device.MockDevice which is used for all sensors in simulation mode.
  * lsst.ts.ess.controller.device.RpiSerialHat which is used for all sensors connected to a serial port on a Raspberry Pi.
  * lsst.ts.ess.controller.device.VcpFtdi which is used for all sensors connected to a USB port on a Raspberry Pi via an FTDI cable.

The second step is to subclass `lsst.ts.ess.common.device.MockFormatter<https://github.com/lsst-ts/ts_ess_common/blob/develop/python/lsst/ts/ess/common/device/mock_formatter.py>`_.
The purpose of that class is to produce (in general random) telemetry both for the unit tests and for the simulation mode.
See for instance `lsst.ts.ess.common.device.MockHx85aFormatter<https://github.com/lsst-ts/ts_ess_common/blob/develop/python/lsst/ts/ess/common/device/mock_hx85_formatter.py>`_.

Add unit tests for the formatter and sensor in the tests directory.
See for instance `this unit test for the HX85A sensor<https://github.com/lsst-ts/ts_ess_common/blob/develop/tests/test_mock_hb85a_device.py>`_ and `this generic test case<https://github.com/lsst-ts/ts_ess_common/blob/develop/tests/test_all_sensors.py>`_.

.. _not-connected-to-rpi:

Sensors Not Connected To A Raspberry Pi
---------------------------------------

If the sensor needs to be connected to via any other way than a Raspberry Pi, then probably a new package lsst.ts.ess.XXX with code that subclasses lsst.ts.ess.common.BaseDataClient is required.
This was done for some specific sensors that require a LabJack connection, which only applies to very specific sensors that need to be read in a very specific way.
The code for the LabJack sensors resides in `ts_ess_labjack<https://github.com/lsst-ts/ts_ess_labjack/>`_.

In case the sensor doesn't require an additional python dependency, the code may be included in the CSC project directly.
This was done for the `Young 32400 Weather Station<https://github.com/lsst-ts/ts_ess_csc/blob/develop/python/lsst/ts/ess/csc/data_client/young_32400_weather_station_data_client.py>`_ and the `Siglent SSA3000X Spectrum Analyzer<https://github.com/lsst-ts/ts_ess_csc/blob/develop/python/lsst/ts/ess/csc/data_client/siglent_ssa3000x_spectrum_analyzer_data_client.py>`_.
Unit tests were created for `Young 32400 Weather Station<https://github.com/lsst-ts/ts_ess_csc/blob/develop/tests/test_young_32400_weather_station_data_client.py>`_ and the `Siglent SSA3000X Spectrum Analyzer<https://github.com/lsst-ts/ts_ess_csc/blob/develop/tests/test_siglent_ssa3000x_spectrum_analyzer_data_client.py>`_ as well.

Documentation
=============

The ts_ess_controller package contains documentation that describes the telemetry produced by the sensors.
Any new sensor should be described there as well, following the format of the documentation of the other sensors.
See for instance the `documentation for the HX85A sensor<https://github.com/lsst-ts/ts_ess_controller/blob/develop/doc/omega_hx85a_sensor.rst>`_.

Handling Telemetry From The CSC
===============================

The `ts_ess_csc<https://github.com/lsst-ts/ts_ess_csc/>`_ project contains the following subclasses of ``ts.ess.common.BaseDataClient``:

  * `lsst.ts.ess.csc.data_client.RPiDataClient<https://github.com/lsst-ts/ts_ess_csc/blob/develop/python/lsst/ts/ess/csc/data_client/rpi_data_client.py>`_: General purpose DataClient that connects to an ESS Controller running on a Raspberry Pi.
  * `lsst.ts.ess.csc.data_client.LightningDataClient<https://github.com/lsst-ts/ts_ess_csc/blob/develop/python/lsst/ts/ess/csc/data_client/lightning_data_client.py>`_: DataClient that connects to an ESS Controller running on a Raspberry Pi to which a Boltek Lightning sensor and a Boltek Electric Field Strength sensor are connected.
  * `lsst.ts.ess.csc.data_client.SiglentSSA3000xSpectrumAnalyzerDataClient<https://github.com/lsst-ts/ts_ess_csc/blob/develop/python/lsst/ts/ess/csc/data_client/siglent_ssa3000x_spectrum_analyzer_data_client.py>`_: DataClient that connects to a Siglent SSA3000X Spectrum Analyzer via a TCP/IP connection.
  * `lsst.ts.ess.csc.data_client.Young32400WeatherStationDataClient<https://github.com/lsst-ts/ts_ess_csc/blob/develop/python/lsst/ts/ess/csc/data_client/young_32400_weather_station_data_client.py>`_: DataClient that connects to a Young 32400 Weather Station via a TCP/IP connection.

The ``lsst.ts.ess.csc.data_client.RPiDataClient`` DataClient should be modified if a new sensor, that is connected to a Raspberry Pi, is added.
Any of the others can be used as an example to implement reading telemetry from a server and publishing the telemetry to specific DDS topics.

Set up The Hardware, Configuration And CSC
==========================================

Once all of the above has been done, the hardware, configuration and, if necessary, new CSC can be set up.

Setup The Hardware
------------------

Sensor hardware can be setup and made available in several ways.

Serial sensors may be connected to a Power over Ethernet (PoE) Raspberry Pi as designed by Oliver Weicha.
Those Raspberry Pi devices are enclosed in an aluminium casing that has both serial and USB ports.
The serial ports provide power for the sensor.
Note that very likely a modified serial cable, that transfers the power to the sensor, needs to be fabricated.
The Rubin Observatory electronics team may be able to help out, so contact Felipe Dariuch for assistance is necessary.

Serial sensors can also be connected to the USB port of any Raspberry Pi (Oliver Weicha type or ordinary) via an FTDI cable.
Note that Prolific cables are not supported.

Sensors can also be connected to LabJack devices, for which support exists in the ts_ess_labjack project.

Setup The Configuration
-----------------------

The ESS configuration is kept inside ``ESS`` directory in the `ts_config_ocs<https://github.com/lsst-ts/ts_config_ocs/>`_ project.
In case a new sensor type gets added, the version of the configuration should probably be increased.
Remember that the increased configuration version needs to be set `here<https://github.com/lsst-ts/ts_ess_csc/blob/develop/python/lsst/ts/ess/csc/config_schema.py#L31>`_ in the ts_ess_csc project as well!

The configuration schema can be found `here <https://github.com/lsst-ts/ts_ess_common/blob/develop/python/lsst/ts/ess/common/config_schema.py>`_.

Whether or not a new CSC needs to be setup, depends mostly on the type of sensor that is added and whether that sensor is connected to a new Raspberry Pi/LabJack or an existing one.
If a new CSC needs to be setup, the type should be ESS and the index as follows:

  * Between 1 and 99: general purpose
  * Between 101 and 199: MTDome
  * Between 202 and 299: ATDome

Add A New CSC To ArgoCD And LOVE
--------------------------------

In case a new CSC has to be added, it needs to be added to ArgoCD and LOVE.
For this, please contact the build and deployment team in the ts-build slack channel.

Add The New Sensor To Confluence
--------------------------------

A comprehensive list of all ESS CSCs and what sensors they read can be found at `confluence <https://confluence.lsstcorp.org/display/LTS/ESS+CSC+Index+Registry>`_.
Make sure to add your new sensor and, if necessary, CSC to that page.
Note that in all cases, the configuration in ts_ess_controller is leading over the confluence page.

Contact Personnel
=================

This procedure was last modified on March 3, 2023.

This procedure was written by |author|.
