.. _lsst.ts.ess.common.boltek_LD-250_sensor:

================================
Boltek LD-250 Lightning Detector
================================

The LD-250 outputs three different kinds of data:

1. Strike rate and and alarm status.
   This is output as it is calculated by the instrument at a fixed period of approximately 1 second.

2. Noise level too high.
   This is output when the noise level in the sensor is too high and the strike signal is lost.
   The noise threshold is configurable in the detector.

3. Strike detected.
   This is output when strikes are detected.

Data Formats
============

Strike rate and Alarm Status
----------------------------

Status data is formatted as a variable-length line, as follows::

    $WIMST,csr,tsr,ca,sa,az*cc\r\n

    for example:

    $WIMST,0,0,0,0,000.0*42\r\n

where:

* ``$WIMST``: indicates that this strike rate and alarm status data.
* ``csr``: close strike rate (strikes/minute); an integer between 0 and 999.
* ``tsr``: total strike rate (strikes/minute); an integer value between 0 and 999.
* ``ca``: close alarm status: 0: not active, 1: active.
* ``sa``: severe alarm status: 0: not active, 1: active.
* ``az``: sensor azimuth heading (deg); a zero padded decimal value between 000.0 and 359.9.
* ``cc``: checksum signature; a two character hexadecimal value.

Noise Level Too High
--------------------

Noise level too high data is formatted a fixed-length line, as follows::

    $WIMLN*cc\r\n

    for example:

    $WIMLN*CE\r\n

Where:

* ``$WIMLN`` indicates that this is "noise level too high" data.
* ``cc``: checksum signature; a two character hexadecimal value.

Strike Detected
---------------

Strike detected data is formatted as a variable-length line, as follows::

    $WIMLI,10,11,000.0*42\r\n

    for example:

    $WIMLI,csd,usd,az*42\r\n

where:

* ``$WIMLI`` indicate that this is strike data.
* ``csd``: corrected strike distance (miles); an integer value between 0 and 300.
* ``usd``: uncorrected strike distance (miles); an integer value between 0 and 300.
* ``az``: strike azimuth bearing (deg); a zero-padded decimal value between 000.0 and 359.9.
* ``cc``: checksum signature; a two character hexadecimal value.

Serial Interface
================

* RS-232 protocol
* 19200 baud
* 8 data bits
* 1 stop bit
* no parity
* no flow control
* ASCII format

Manual
======

* :download:`LD-250 User Manual <boltek_pdfs/LD-250 Manual.pdf>`
