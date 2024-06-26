.. _lsst.ts.ess.common.young_weather_station:

=====================
Young Weather Station
=====================

Our Young weather station uses a :download:`32400 serial interface <young_pdfs/32400 serial interface.pdf>` to read to the instruments.
Our data client expects it to be configured as follows:

* Output data in raw format: PRECIPITATION (if we have a rain sensor) or ASCII (if we don't).
  This consists of a line of ASCII consisting of 6 space-separated 4-digit integers, with a possible starting character and space that can be ignored.
  The formats are essentially the same, the difference being whether the final number is a rain tip counter or can be ignored.
* Output data at regular intervals (without being polled).

The desired jumper settings are:

* Without a rain gauge: A=0, B=0, C=0: output data in ASCII format at 2 Hz (at 9600 baud).
* With a rain gauge: A=1, B=0, C=1: output data in PRECIP format at 15 Hz (at 9600 baud).
  Note that PRECIP format is essentially identical to ASCII; the difference is the meaning of the VIN4 field.
* W2=232, W3=232: output using RS-232.
  1 start, 8 data, and 1 stop bit, no flow control.

Serial Interface Parameters
===========================

In the configuration we use:

* RS-232
* 9600 baud
* 8 bits
* no parity
* 1 stop bit
* no flow control
* ASCII data format

Scale and offset
================

The Young serial interface outputs counts which need to be converted to the telemetry values in the correct units.
Section 3.2 on page 1 of the serial interface manual explains how the counts from VIN1, VIN2, VIN3 and VIN4 need to be converted.
Page 4 of the serial interface manual contains the ASCII format of the serial data.
The manuals of the respective instruments contain the conversion scales and offsets to use.
Combining all of that we see that:

* Wind speed needs a scale of 0.0834 and an offset of 0 to get values in m/s.
* Wind direction needs a scale of 0.1 and an offset of 0 to get values in º.
* Temperature (VIN1) counts need to be divided by 4 to convert them from mV to serial values.
  The temperature range is from -50 ºC to 50 ºC (meaning a range of 100 ºC) for values from 0 to 1000 mV.
  This means that the scale needs to be::

    100 / 1000 / 4 = 0.025

  and the offset -50.
* Humidity (VIN2) counts need to be divided by 4 to convert them from mV to serial values.
  The humidity range is from 0 % to 100 % for values from 0 to 1000 mV.
  This means that the scale needs to be::

    100 / 1000 / 4 = 0.025

  and the offset 0.
* Barometric pressure (VIN3) counts need to be divided by 4 and then multiplied by 5 to convert them from mV to serial values.
  Applying the conversion from section 4.1 of the the barometric pressure sensor manual::

    hPa = 0.12 * mV + 500

  means that the counts values can be directly converted with::

    hPa = 0.15 * counts + 500

  or for values in Pa instead of hPa::

    Pa = 15.0 * counts + 500

  resulting in a scale of 15.0 and an offset of 500.
* Rain tip (VIN4) counts need to be divided by 4 and then multiplied by 5 to convert them from mV to serial values.
  The conversion from page 1 of the the tipping bucket rain gauge manual indicates that each tip count value corresponds to 0.1 mm.
  The tip values range from 0 to 9999 (so 10000 values) and the VIN4 values range from 0 to 5000.
  This means that the scale needs to be 0.1 * 10000 * 5 / 5000 / 4 = 0.25

Manuals
=======

Manuals for the serial interface and sensors:

* :download:`05108-45 wind monitor <young_pdfs/05108-45 wind monitor.pdf>`
* :download:`32400 serial interface <young_pdfs/32400 serial interface.pdf>`
* :download:`41382VC temperature and humidity sensor <young_pdfs/41382VC temperature and humidity sensor.pdf>`
* :download:`52202 tipping bucket rain gauge <young_pdfs/52202 tipping bucket rain gauge.pdf>`
* :download:`61402V barometric pressure sensor <young_pdfs/61402V barometric pressure sensor.pdf>`
