.. _lsst.ts.ess.common.aurora_cloud_sensor:

===================
Aurora Cloud Sensor
===================


Data output by the Aurora Cloud Sensor instrument are:

* Sensor temperature (deg C) * 100
* Sky temperature (deg C) * 100
* Clarity * 100
* Light * 10
* Rain * 10

Data is output as it is read and calculated by the instrument, at a fixed period of approximately 2 second.

Data Format
===========

The data format is a fixed-length line of 56 characters, as follows::

    $20,FF,seq_num sensor_t,sky_t,clarity,light,rain,ignore,ignore,alarm,00!\n

    For example:

    $20,FF,00742,02368,02458,-0090,252,032,8FFF,0104,37,00!\n

where:

* ``$20,FF``: fixed beginning of data. The "20" is the header ID.
* ``seq_num``: sequence number; a 5-digit unsigned integer from 00000 to 99999, at which point it wraps around.
* ``sensor_t``: sensor temperature, as C * 100: a 5-digit integer.
* ``sky_t``: sky temperature (C * 100): a 5-digit integer.
* ``clarity``: clarity (units? * 100): a 5-digit integer.
* ``light``: light intensity (units? * 10): a 3-digit integer.
* ``rain``: rain intensity (units? * 10): a 3-digit integer.
* ``ignore``: ignore these two fields; both of which are 4 hexadecimal digits.
* ``alarm``: alarm stats: a 2-digit unsigned integer.
* ``00!\n``: fixed end of data.

Note that for signed values listed as "n-digit integers" the first of these "digits" may be "-".
So technically the integer is n digits if positive, or n-1 digits with a leading "-" if negative.

Serial Interface
================

* RS-232 protocol
* 9600 baud
* 8 data bits
* 1 stop bit
* no parity
* no flow control
* ASCII format

Warning
=======

This documentation is compiled from the instrument's supplied beta manual.
The manual was found to contain conflicting definitions within its own text and incomplete definitions of value formats.
Hexadecimal values were defined as both upper and lower case alphas. It has been assumed here that they are all upper case.
Value ranges are incomplete; it is assumed that any value capable of a negative sign has its first character '-'.
