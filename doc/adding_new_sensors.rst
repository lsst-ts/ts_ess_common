.. py:currentmodule:: lsst.ts.ess.common

.. _lsst.ts.ess.common.adding_new_sensors:

==================
Adding New Sensors
==================

This package (ts_ess_common), `ts_ess_controller`_, and `ts_ess_labjack`_ contain code to handle a wide variety of sensors.
But occasionally a new kind of sensor needs to be added, and this document describes how to do that.

Software
========

How you write code for a new kind of sensor depends on how the sensor serves data.
There are several cases:

* The sensor serves data via TCP/IP, without needing a special library that is hard to install.

  In this case an ESS instance running on Kubernetes can directly connect to the sensor.
  To support this, write a subclass of `data_client.BaseDataClient` that handles your sensor.
  One example is `data_client.Young32400WeatherStationDataClient`.
  Note that the `sensor.BaseSensor` and `device.BaseDevice` are not used for this case.

  If communication needs a special library that is easy to install, ask the telescope and site group to add it to the standard execution environment so it is available to ts_ess_common and ts_ess_csc.

* The sensor serves data via USB, FTDI or some other protocol that is not visible from Kubernetes.

  In this case we connect the sensor to a Power over Ethernet (PoE) Raspberry Pi as designed by Oliver Weicha.
  The RPi then relays the data to the `data_client.RPiDataClient`.
  See :ref:`connected-to-rpi` for details on how to handle this.

* The sensor serves data via an RS-232 or RS-485 serial interface.

  There are two options:

  * If you power the sensor in the conventional way, attach a serial-to-ethernet adapter and see the TCP/IP case above.
  * If you want to power the sensor through the serial connector (a custom technique),
    see the USB/FTDI case above and use a Power over Ethernet (PoE) Raspberry Pi as designed by Oliver Weicha.

  In theory you can use an RPi even if the sensor is powered conventionally, but we do not recommend this for new types of sensors.

* The sensor serves data via TCP/IP but requires a special library that is hard to install.

  In this case an ESS instance running on Kubernetes can directly connect to the sensor, but we don't want to burden ts_ess_common or ts_ess_csc with the library.
  To support this, create a new ts_ess_X package that requires the library, then write a subclass of `data_client.BaseDataClient` that supports your sensor.

* The sensor has analog and/or binary outputs.

  Connect the sensor to one or more inputs of a LabJack T4 or T7.
  Then see if one of the LabJack data clients in `ts_ess_labjack`_ can handle it.
  If not, write a new LabJack data client in `ts_ess_labjack`_.
  Note: `ts_ess_labjack`_ is a separate package because it relies on a special library (LabJack LJM) that is hard to install.

.. _connected-to-rpi:

Sensors Connected To A Raspberry Pi
-----------------------------------

The sensors are connected to a Raspberry Pi, either via a serial cable or via an FTDI cable that converts the serial connection to a USB connection.
A Docker container is installed on the Raspberry Pi, running a custom TCP/IP server, called the ESS Controller, to which the ESS CSC connects.
The ESS Controller polls the sensors, which generally generate telemetry every second, and converts the sensor telemetry to a common format that the CSC understands.
The ts_ess_common project holds the code for almost all sensors and the conversion of their telemetry plus for mock devices, which are used in the unit tests and when running in simulation mode.

The first step is to subclass `sensor.BaseSensor`.
The purpose of that class is to parse a line of telemetry as produced by the sensor and to extract the telemetry values as ``int``, ``float`` or ``str``.
See for instance `sensor.Hx85baSensor`.

Those values are then used by `device.BaseDevice` and its subclasses to prepare the telemetry to be sent to the CSC.
In general, device.BaseDevice should not need to be subclassed since the following subclasses exist:

  * device.MockDevice which is used for all sensors in simulation mode.
  * lsst.ts.ess.controller.device.RpiSerialHat which is used for all sensors connected to a serial port on a Raspberry Pi.
  * lsst.ts.ess.controller.device.VcpFtdi which is used for all sensors connected to a USB port on a Raspberry Pi via an FTDI cable.

The second step is to subclass `device.MockFormatter`.
The purpose of that class is to produce (in general random) telemetry both for the unit tests and for the simulation mode.
See for instance `device.MockHx85aFormatter`.

The next step is to modify ``data_client.RPiDataClient`` to read data from your new sensor.

Finally, add unit tests for the formatter and sensor in the tests directory.
See for instance this `unit test for the HX85A sensor <https://github.com/lsst-ts/ts_ess_common/blob/develop/tests/test_mock_hb85a_device.py>`_ and this `generic test case <https://github.com/lsst-ts/ts_ess_common/blob/develop/tests/test_all_sensors.py>`_.

Documentation
=============

Add documentation for the sensor to the doc directory of this package (ts_ess_common), including the vendor's user guide (if available in pdf or rst format) following the format of the documentation of the other sensors.

Set up The Hardware, Configuration And CSC
==========================================

Once all of the above has been done, set up the hardware, configuration and, if necessary, new CSC can be set up.

Set Up The Hardware
-------------------

Sensor hardware can be setup and made available in several ways.

* Serial sensors that you wish to power from the serial cable:

  Connect the sensor to a Power over Ethernet (PoE) Raspberry Pi as designed by Oliver Weicha.
  Those Raspberry Pi devices are enclosed in an aluminium casing that has both serial and USB ports, and the serial ports includes pins that provide power.
  Construct a special serial cable that receives power from the serial port on the Raspberry Pi end, and distributes it where it is needed on the sensor end.
  The Rubin Observatory electronics team may be able to help out.

* Serial sensors power that you wish to power in the conventional:

  Connect the sensor to a serial-to-ethernet adapter sing a conventional serial cable, and configure the serial-to-ethernet adapter.

  Such serial sensors can also be connected to the USB port of any Raspberry Pi (Oliver Weicha type or ordinary) via an FTDI cable, but we do not recommend this for new sensors.
  Note that Prolific cables are not supported.

* Sensors with analog or binary outputs:

  Connect the sensor to a LabJack T4 or T7 module.
  These are read by data clients in `ts_ess_labjack`_.

Configuration the CSC
---------------------

ESS configuration is kept inside the ``ESS`` directory in the `ts_config_ocs`_ repo.

The first step is to increment the version number of the ESS configuration, as follows:

* Create a new version directory in the ESS directory in `ts_config_ocs`_, and copy the config files from the most recent existing version directory.
* Specify the new version in the `title of the config schema <https://github.com/lsst-ts/ts_ess_csc/blob/develop/python/lsst/ts/ess/csc/config_schema.py#L31>`_ in the ts_ess_csc project.

Then update the appropriate configuration file(s) to support the new sensor (or sensors).
To do this, you must decide whether to read the sensor using an existing ESS instance (value of sal_index) or a new instance.

* If the new sensor is connected to existing Raspberry Pis or LabJacks, add the sensor configuration to the existing ESS instance that reads that device.
* If not, you have the choice of using existing ESS CSC instance or a new instance:

    * A new instance is preferred if the new sensor (or new set of sensors) is high bandwidth, to avoid overloading an existing ESS instance.
    * An existing instance is preferred if the new sensor is in some way related to an existing set of sensors.

If you want a new CSC instance, pick an unused sal_index from the appropriate range:

  * 1 - 99: general purpose.
  * 101 - 199: MTDome.
  * 201 - 299: ATDome.
  * 301 - 399: Outside.

Note: we may decide to allow 100, 200, and 300 at some point.

Request Updates for LOVE and, if required, ArgoCD
-------------------------------------------------

New sensors should be added to the LOVE display and possibly one or more Chronograf dashboards.

If you added a new ESS CSC instance, it must be to be added to ArgoCD.
For this please contact the build and deployment team in the ts-build Slack channel.

.. _ts_config_ocs: https://github.com/lsst-ts/ts_config_ocs
.. _ts_ess_controller: https://ts-ess-controller.lsst.io
.. _ts_ess_labjack: https://ts-ess-labjack.lsst.io
