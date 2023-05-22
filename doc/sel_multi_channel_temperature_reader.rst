.. _lsst.ts.ess.common.sel_multi_channel_temperature_reader:

====================================
SEL Multi-Channel Temperature Reader
====================================

Straight Engineering LLC (SEL) temperature instruments report temperature from multiple sensors.
Different models have different numbers of channels and either support RTD or thermocouple sensors.

Ouput Format
============

Data for each channel is output as it is read by the instrument, at a fixed period of approximately 0.167 seconds.
Data each channel except the final channel is terminated by ",".
Data for the final channel is terminated by ``\r\n``.

Data for each channel is of the form: "Cnn=tttt.tttt" where:

* ``nn`` is the zero-padded channel number.
* Channel 00 is used to report the internal reference temperature for thermocouple sensor units.
  RTD sensors do not report a value for channel 00.
* ``tttt.tttt`` is the temperature (C), in fixed floating-point format.
* A specific temperature value is used to indicate an error; it depends on the sensor type:

  * RTD sensors: ``9999.9990``.
  * Thermocouple sensors: ``-201.0000``.

  An error value typically means that the sensor is disconnected.

Example Output
--------------

Example output for 4-channel RTD instrument, with a 0.167 second pause between each channel::

    C01=0032.1443,C02=0033.0320,C03=-001.3020,C04=-201.0000\r\n

Example output for a 4-channel thermocouple instrument, with a 0.167 second pauses between each channel.
Note the extra channel 00 reading for the internal temperature reference::

    C00=0025.4300,C01=0032.1443,C02=0033.0320,C03=-001.3020,C04=9999.9990\r\n

Serial Interface Parameters
===========================

* RS-232
* 19200 baud
* 8 bits
* no parity
* 1 stop bit
* no flow control
* ASCII data format
