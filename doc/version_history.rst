.. py:currentmodule:: lsst.ts.ess.common

.. _lsst.ts.ess.common.version_history:

###############
Version History
###############

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
