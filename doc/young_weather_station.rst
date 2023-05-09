=====================
Young Weather Station
=====================

Serial Interface
================

Our Young weather station uses a :download:`32400 serial interface<young_weather_station_pdfs/32400 serial interface.pdf>` to read to the instruments.
Our data client expects it to be configured as follows:

* Output data in raw format: PRECIPITATION (if we have a rain sensor) or ASCII (if we don't).
  This consists of a line of ASCII consisting of 6 space-separated 4-digit integers, with a possible starting character and space that can be ignored.
  The formats are essentially the same, the difference being whether the final number is a rain tip counter or can be ignored.
* Output data at regular intervals (without being polled); the choices are 2 Hz or 15 Hz.

As of 2023-02-28 our sensors are:

* :download:`41382VC temperature and humidity sensor<young_weather_station_pdfs/41382VC temperature and humidity sensor.pdf>`
* :download:`61402V barometric pressure sensor<young_weather_station_pdfs/61402V barometric pressure sensor.pdf>`
* :download:`52202 tipping bucket rain gauge<young_weather_station_pdfs/52202 tipping bucket rain gauge.pdf>`
* :download:`05108-45 wind monitor<young_weather_station_pdfs/05108-45 wind monitor.pdf>`
