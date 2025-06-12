.. py:currentmodule:: lsst.ts.ess.common

.. _lsst.ts.ess.common.version_history:

###############
Version History
###############

.. towncrier release notes start

v0.23.0 (2025-06-12)
====================

New Features
------------

- Switched to ruff. (`DM-50895 <https://rubinobs.atlassian.net//browse/DM-50895>`_)


Bug Fixes
---------

- Rewrote DataClient lifecycle. (`DM-50895 <https://rubinobs.atlassian.net//browse/DM-50895>`_)
- Fixed TcpipDataClient connecting and disconnecting. (`DM-50895 <https://rubinobs.atlassian.net//browse/DM-50895>`_)
- Avoided asyncio warnings in unit tests. (`DM-50895 <https://rubinobs.atlassian.net//browse/DM-50895>`_)


Performance Enhancement
-----------------------

- Stopped using asyncio.TimeoutError. (`DM-50895 <https://rubinobs.atlassian.net//browse/DM-50895>`_)


v0.22.0 (2025-05-15)
====================

New Features
------------

- Moved all DataClients here from ts_ess_csc. (`DM-50822 <https://rubinobs.atlassian.net//browse/DM-50822>`_)
- Added GecThermalscannerDataClient. (`DM-50822 <https://rubinobs.atlassian.net//browse/DM-50822>`_)


Documentation
-------------

- Added Sensirion SPS30 particulate matter sensor support and documentation. (`DM-50330 <https://rubinobs.atlassian.net//browse/DM-50330>`_)


API Removal or Deprecation
--------------------------

- Moved all SNMP code to ts_ess_epm. (`DM-50822 <https://rubinobs.atlassian.net//browse/DM-50822>`_)


v0.21.2 (2025-05-07)
====================

Bug Fixes
---------

- Limited telemetry rate to prevent excessive amounts of error messages. (`DM-50598 <https://rubinobs.atlassian.net//browse/DM-50598>`_)


v0.21.1 (2025-04-17)
====================

Bug Fixes
---------

- Improve error handling and loop control. (`DM-49805 <https://rubinobs.atlassian.net//browse/DM-49805>`_)
- Fix package version file generation. (`DM-49805 <https://rubinobs.atlassian.net//browse/DM-49805>`_)
- Avoid `asyncio_default_fixture_loop_scope` pytest warning. (`DM-49805 <https://rubinobs.atlassian.net//browse/DM-49805>`_)


v0.21.0
=======

* Fix compatibility with pysnmp >= 5.0.0 for Python3.12.

v0.20.0
=======

* Incorporate code for electrical power management and other SNMP operations.
* Add support for Raritan PDUs.
* Pin conda dependency versions.
* Set `upload_dev` in the conda Jenkinsfile to true.
* Add documentation describing the SNMP infrastructure.
* Add registration for the EarthquakeDataClient.

Requires:

* ts_tcpip 2.0
* ts_utils 1.2

v0.19.4
=======

* Improve temperature simulator and processor.

Requires:

* ts_tcpip 2.0
* ts_utils 1.2

v0.19.3
=======

* Improve and update weather station documentation.

Requires:

* ts_tcpip 2.0
* ts_utils 1.2

v0.19.2
=======

* Make sure that the TcpipDataClient connects to the configured host and port.

Requires:

* ts_tcpip 2.0
* ts_utils 1.2

v0.19.1
=======

* Revert renaming classes and files.

Requires:

* ts_tcpip 2.0
* ts_utils 1.2

v0.19.0
=======

* Rename classes and files for more clarity.
* Add TcpipDevice class.
* Add TcpipDataClient class.

Requires:

* ts_tcpip 2.0
* ts_utils 1.2

v0.18.4
=======

* Fix the conda recipe.

Requires:

* ts_tcpip 2.0
* ts_utils 1.2

v0.18.3
=======

* Fix air turbulence speed magnitude calculation.
* Update Jira URL.

Requires:

* ts_tcpip 2.0
* ts_utils 1.2

v0.18.2
=======

* Update the version of ts-conda-build to 0.4 in the conda recipe.

Requires:

* ts_tcpip 2.0
* ts_utils 1.2

v0.18.1
=======

* Handle telemetry formatting exceptions for the Campbell Scientific CSAT3B 3-D anemometer.
* Correct terminator of the Campbell Scientific CSAT3B 3-D anemometer.

Requires:

* ts_tcpip 2.0
* ts_utils 1.2

v0.18.0
=======

* Add AuxTelCameraCoolantPressureProcessor class.
* Make AirTurbulenceProcessor more generic.
* Consolidate Lightning and RPi data clients into one class.
* Add unit tests for new data client and processor classes.

Requires:

* ts_tcpip 2.0
* ts_utils 1.2

v0.17.0
=======

* Move data client classes to submodule.
* Add common code from ts_ess_csc.

Requires:

* ts_tcpip 1.1
* ts_utils 1.0

v0.16.8
=======

* Set barometric pressure values to a more realistic range.
* Improve the description of the conversion of the weather station barometric pressure.

Requires:

* ts_tcpip 1.1
* ts_utils 1.0

v0.16.7
=======

* Make BaseDataClient an async context manager.

Requires:

* ts_tcpip 1.1
* ts_utils 1.0

v0.16.6
=======

* Fix reconnection issue in BaseReadLoopDataClient.

Requires:

* ts_tcpip 1.1
* ts_utils 1.0

v0.16.5
=======

* Add explanation for scale and offset to the Young weather station documentation.

Requires:

* ts_tcpip 1.1
* ts_utils 1.0

v0.16.4
=======

* Make BaseReadLoopDataClient automatically reconnect if configured to do so.

Requires:

* ts_tcpip 1.1
* ts_utils 1.0

v0.16.3
=======

* Explicitly use the value of string enums.
  This apparently is necessary for Python 3.11.

Requires:

* ts_tcpip 1.1
* ts_utils 1.0

v0.16.2
=======

* Stop using pytest in library code.
  This makes it safe to import the test_utils module even in production code.

Requires:

* ts_tcpip 1.1
* ts_utils 1.0

v0.16.1
=======

* Move sensor documentation here from ts_ess_common and expand and update the documentation.
* Sensors: in doc strings replace detailed explanations of the interface with links to the documentation.

Requires:

* ts_tcpip 1.1
* ts_utils 1.0

v0.16.0
=======

* Use ts_tcpip OneClientReadLoopServer.
  This requires ts_tcpip 1.1.
* Fix missing API docs.

Requires:

* ts_tcpip 1.1
* ts_utils 1.0

v0.15.0
=======

* Add compatibility with ts_tcpip 1.1.
  Also lose compatibility with ts_tcpip < 1.0.
* Remove scons support.
* Git hide egg info and simplify .gitignore.
* `TestDataClient` and `TestReadLoopDataClient`: mark as not pytest test cases, to eliminate pytest warnings.
* Fix some warnings.
  This change requires ts_tcpip 1.0.
* Further refinements for ts_pre_commit_config:

  * Delete ``setup.cfg``; it has been replaced by ``.flake8``.
  * ``conda/meta.yaml``: remove setup.cfg (and the obsolete script_env section).

Requires:

* ts_tcpip 1.1
* ts_utils 1.0

v0.14.0
=======

* Add BaseReadLoopDataClient which reattempts to read data when a TimeoutError happens up to a configurable number of consecutive timeouts.
* Add MockReadLoopDataClient for unit testing of BaseReadLoopDataClient.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.13.0
=======

* Use ts_pre_commit_conf.
* Use DevelopPipeline.
* Make mock device ID independent of device type.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.12.0
=======

* Add `compute_dew_point_magnus` function.
  Remove the correponding ``compute_dew_point`` static method of `Hx85baSensor`.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.11.2
=======

* Add aioserial and jsonschema to conda recipe dependencies.
* Add __repr__ to BaseSensor and BaseDevice.
* Promoted several instance variables to class variables to simplify the code and get rid of constructors in all sensor classes.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.11.1
=======

* Remove root workaround from Jenkinsfile.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.11.0
=======

* Rename the WindSensor to WindsonicSensor and add a mock formatter for the simulation mode.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.10.3
=======

* pre-commit: update mypy and types-PyYAML versions.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.10.2
=======

* Introduce alias for the type of the sensor data.
* Refactor the sensor unit tests into a single test class.
* Refactor the device unit tests to remove duplicate code.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.10.1
=======

* Switch from py.test to pytest.
* Add support for Boltek lightning and electric field intensity sensors.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.10.0
=======

* `DeviceConfig`: add ``num_samples``.
* test_utils: make comparison of computed dew point more robust by rounding the input data to two decimal digits, matching what the sensor reports.
* git ignore ``__pycache__``.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.9.3
======

* Simplify the CSAT3B telemetry validation.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.9.2
======

* Remove signature checking from the Campbell CSAT3B because the vendor documentation describing it is incorrect.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.9.1
======

* Fix CSAT3B telemetry in case of an invalid telemetry signature.
* Restore pytest config.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.9.0
======

* Add support for multiple Python versions for conda.
* Sort imports with isort.
* Install new pre-commit hooks.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.8.0
======

* Add baud_rate configuration key.
* Add support for the Campbell Scientific CSAT3B 3D anemometer.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.7.6
======

* Restore conditional import of lsst.ts.salobj only if type checking.
* ``ups/ts_ess_common.table``: add setupOptional(ts_salobj); it is optional because it is only used for type checking.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.7.5
======

* `ExternalDataClientModules`: add ``LabJackAccelerometerDataClient`` so lsst.ts.labjack is imported if needed.
* Modernize type annotations for Python 3.10.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0

v0.7.4
======

* Add wait_time class variable for mocking of timeouts.
* Add pre-commit config file.
* ``setup.cfg``: specify asyncio_mode=auto.
* Switch to pyproject.toml.
* Convert to pure python noarch conda package.

Requires:

* ts_tcpip 0.4
* ts_utils 1.0


v0.7.3
======

* Remove unneccessary debug log statements.

Requires:

* ts_tcpip 0.3
* ts_utils 1.0


v0.7.2
======

* Remove START and STOP commands.
* Encode sensor name, timestamp, response code and data as separate named entities.

Requires:

* ts_tcpip 0.3
* ts_utils 1.0


v0.7.1
======

* Fix a new mypy error by not checking DM's `lsst/__init__.py` files.

Requires:

* ts_tcpip 0.3
* ts_utils 1.0


v0.7.0
======

* Added support for data clients: classes that communicate with an environmental data server and publish the data as ESS telemetry:

  * Added classes `BaseDataClient` and `MockDataClient`.
  * Added function `get_data_client_class`.
  * Jenkinsfile: update to build and upload documentation, and kill stale jobs.

Requires:

* ts_tcpip 0.3
* ts_utils 1.0


v0.6.1
======

* Made sure that no runtime dependency on pytest is necessary anymore.

Requires:

* ts_tcpip 0.3
* ts_utils 1.0


v0.6.0
======

* Added location to the configuration of the sensors.

Requires:

* ts_tcpip 0.3
* ts_utils 1.0


v0.5.0
======

* Made sure that lost connections are detected and handled such that a new connection can be made.
* Simplified the constructor of MockDevice.

Requires:

* ts_tcpip 0.3
* ts_utils 1.0


v0.4.0
======

* Added computation of the dew point in all humidity sensors that don't provide it themselves.
* Modernized test code.

Requires:

* ts_tcpip 0.3
* ts_utils 1.0


v0.3.0
======

* Moved all device reply validating code from ts.ess.controller to ts.ess.common.
* Moved all sensors code from ts.ess.controller to ts.ess.common.
* Moved code to determine what sensor is connected from ts.ess.controller to ts.ess.common.
* Moved BaseDevice and MockDevice from ts.ess.controller to ts.ess.common.
* Added a unit test for the config schema.
* Moved most of the command handler code and the socket server unit test from ts.ess.controller to ts.ess.common.
* Added tests for all supported devices in the test class for the mock control handler.

Requires:

* ts_tcpip 0.3
* ts_utils 1.0

v0.2.0
======

* Replaced the use of ts_salobj functions with ts_utils functions.

Requires:

* ts_tcpip 0.3
* ts_utils 1.0

v0.1.1
======

* Made sure that the EssController and EssCsc jobs get triggered.

Requires:

* ts_tcpip 0.3

v0.1.0
======

First release of the Environmental Sensors Suite common code package.

* A socket server.
* A command handler infrastructure.
* Common enums.

Requires:

* ts_tcpip 0.3
