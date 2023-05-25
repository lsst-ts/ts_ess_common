.. _lsst.ts.ess.common.boltek_EFM-100C_sensor:

==================================================
Boltek EFM-100C Atmospheric Electric Field Monitor
==================================================

Data output by the EFM-100C instrument are:

    - Polarity of the electric field (+/-)
    - Electric field level (kV/m)

Data is output as it is read and calculated by the instrument at a fixed period of approximately 50 ms.

Example Output Line
===================

Examples::

    $+00.65,0*CE\r\n
    $+00.65,0*CE\r\n
    $+00.64,0*CD\r\n

Data Format
===========

Data is formatted as a fixed-length line, as follows::

    $+level,f*CE\r\n
    
where:

* ``$`` indicates indicate the start of the telemetry.
* ``s``: polarity sign: either "+" or "-".
* ``level``: electric field level (kV/m). Zero padded decimal value between 00.00 and 20.00.
* ``f``: fault indicater: either 0 (no fault) or 1 (fault).
* ``cc``: checksum signature; a two character hexadecimal value.

Serial Interface
================

* RS-232 protocol
* 19200 baud
* 8 data bits
* 1 stop bit
* no parity
* no flow control
* ISO8859-1 format

Manual
======

* :download:`EFM-100C User Manual <boltek_pdfs/EFM-100C Manual.pdf>`
