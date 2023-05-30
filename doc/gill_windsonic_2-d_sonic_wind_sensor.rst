.. _lsst.ts.ess.common.gill_windsonic_2-d_sonic_wind_sensor:

###################################
GILL Winsonic 2-D Sonic Wind Sensor
###################################

The GILL Windsonic 2-D Sonic Wind Sensor (Anemometer) measures wind speed and direction.

Data output by the Anemometer instrument is:

    - Wind Speed
    - Wind Direction

Data is output as it is read and calculated by the instrument at a fixed period of approximately 1.0 seconds.

The model we have is ``Winsonic1-L``.

Output Format
=============

The output format we use is as follows::

    <STX>Q,[ddd],sss.ss,M,nn,<ETX>cc\r\n

Where:

* [...] indicates an field that may not be present; the "[" and "]" are not printed.
* ``<STX>``: start of text character: ASCII value 2
* ``Q``: unit identifier; "Q" is the default, which we use, but in theory we could set this to any letter A-Z.
* ``ddd`` wind direction (degrees) in the range 000 - 359.
  *This field is omitted* if the wind speed is below 0.05 m/s.
* ``sss.ss`` wind speed (m/s)
* ``M``: units of measurement; "M" indicates m/sec.
* ``nn``: status code, one of:

    * 00: OK
    * 01: axis 1 failed
    * 02: axis 2 failed
    * 04: both axes failed
    * 08: NVM chucksum failed
    * 09: ROM checksum failed

* ``<ETX>``: end of text character: ASCII value 3
* ``cc``: checksum: the ``exclusive or`` of the bytes between (and not including) the <STX> and <ETX>characters.

Example Output
--------------

In the following examples ?? indicates the checksum.
I don't know the correct values.

Example with wind direction (wind speed ≥ 0.05 m/s)::

    <STX>Q,036,002.57,M,00,<ETX>??

Example without wind direction (wind speed \< 0.05 m/s)::

    Q,,000.04,M,00,<ETX>??

Serial Interface & Parameters
=============================

* RS-232
* 9600 baud
* 8 bits
* no parity
* 1 stop bit
* no flow control
* ASCII data format

Manuals
=======

* :download:`WindSonic User Manual <gill_pdfs/1405-PS-019-Windsonic-manual-Issue-30.pdf>`
