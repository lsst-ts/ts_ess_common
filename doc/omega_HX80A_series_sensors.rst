.. _lsst.ts.ess.common.omega_hx80a_series_sensors:

====================================
Omega HX80A Series Humidity+ Sensors
====================================

Omega HX80A series sensors measure relative humidity, air temperature, and either barometric pressure or dew point, depending on the model.
We use the following two models:

* HX85BA: relative humidity, air temperature, and barometric pressure (preferred).
* HX85A: relative humidity, air temperature, and dew point.

When buying new sensors we strongly recommend buying HX85BA sensors, because we would rather read barometric pressure and compute dew point ourselves.

Output Format
=============

By default the Omega HX85A and HX85BA sensors output data every 1.35 seconds.
You can also issue commands to these sensors, but there should be no need.

HX85BA (barometric pressure)::

    %RH=h.hh,AT°C=t.tt,Pmb=p.pp\n\r

    for example:

    %RH=38.86,AT°C=24.32,Pmb=911.40\n\r

HX85A (dew point)::

    %RH=h.hh,AT°C=t.tt,DP°C=d.dd\n\r

    for example:

    %RH=38.86,AT°C=24.32,DP°C=9.57\n\r

Where:

* The number of digits before the decimal point is variable (rather than zero-padded).
* h.hh is relative humidity (%).
* t.tt is air temperature (C).
* p.pp is barometric pressure (mbar).
* d.dd is dew point (C).

Notes:

* The line terminator ``\n\r`` is unusual in two ways:
 
    * The characters are reversed from the standard ``\r\n``.
    * The termination characters are not sent immediately following the line, but appear 1 ms preceding the following line.
    
    This may require some care in managing the receiver code.

* We don't know how the unit handles errors; the manual does not say.
* The degree symbol ° is hex F8.

Serial Interface
================

* RS-232 protocol
* 19200 baud
* 8 data bits
* 1 stop bit
* no parity
* no flow control
* ISO8859-1 format

Manuals
=======

* :download:`HX80A series operators manual <omega_pdfs/HX80A series operators manual.pdf>`
* :download:`HX80A series sensors <omega_pdfs/HX80A series sensors.pdf>`
