.. py:currentmodule:: lsst.ts.ess.common

.. _lsst.ts.ess.common.version_history:

###############
Version History
###############

v0.3.0
======

* Moved all device reply validating code from ts.ess.controller to ts.ess.common.
* Moved all sensors code from ts.ess.controller to ts.ess.common.
* Moved code to determine what sensor is connected from ts.ess.controller to ts.ess.common.

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
