.. _lsst.ts.ess.common.particulate_matter_sensor:

==========================
Particulate Matter Sensor
==========================

The Sensirion SPS30 particulate matter sensor measures:

* Particle size concentrations (PM1.0, PM2.5, PM4.0, PM10)
* Particle number concentrations
* Typical particle size

Data is output in a specific format with checksum verification.

Data Format
===========

The data format follows this pattern::

    <STX>sensor_name,timestamp,size1,size2,size3,size4,size5,conc1,conc2,conc3,conc4,conc5,num1,num2,num3,num4,num5,typical_size,location,status<ETX>checksum\r\n

    For example:

    \x02SPS30,1609459250.12,12.34,23.45,34.56,45.67,56.78,123.45,234.56,345.67,456.78,567.89,1234.56,2345.67,3456.78,4567.89,5678.90,0.42,TestLocation,00\x0367\r\n

where:

* ``<STX>`` (\x02): Start of text character
* ``sensor_name``: Sensor identifier (SPS30)
* ``timestamp``: Unix timestamp with fractional seconds
* ``size1-size5``: Particle sizes (µm) as floating point numbers
* ``conc1-conc5``: Mass concentrations (µg/m³) as floating point numbers
* ``num1-num5``: Number concentrations (#/cm³) as floating point numbers
* ``typical_size``: Typical particle size (µm)
* ``location``: Installation location string
* ``status``: 2-digit status code (00 = good)
* ``<ETX>`` (\x03): End of text character
* ``checksum``: 2-digit hexadecimal checksum (sum of all bytes modulo 256)

Serial Interface
===============

* UART protocol
* 115200 baud
* 8 data bits
* 1 stop bit
* no parity
* ASCII format

Checksum Calculation
===================

The checksum is computed as::

    sum(ord(char) for char in checksum_string) % 256

where checksum_string is all data between <STX> and status (inclusive).

Status Codes
===========

* ``00``: Normal operation
* Other values indicate sensor warnings or errors

Note
====

Invalid measurements are reported as:
* ``-1.00`` for particle sizes
* ``-1.000`` for concentrations
* ``-1.00`` for typical particle size
