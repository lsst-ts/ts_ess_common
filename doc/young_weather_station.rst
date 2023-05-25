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

Manuals
=======

Manuals for the serial interface and sensors:

* :download:`05108-45 wind monitor <young_pdfs/05108-45 wind monitor.pdf>`
* :download:`32400 serial interface <young_pdfs/32400 serial interface.pdf>`
* :download:`41382VC temperature and humidity sensor <young_pdfs/41382VC temperature and humidity sensor.pdf>`
* :download:`52202 tipping bucket rain gauge <young_pdfs/52202 tipping bucket rain gauge.pdf>`
* :download:`61402V barometric pressure sensor <young_pdfs/61402V barometric pressure sensor.pdf>`
