===================================================================================
Serial protocol definition for: Boltek EFM-100C Atmospheric Electric Field Monitor.
===================================================================================

Wouter van Reeven.
2022-11-11

Serial Interface & Parameters
=============================

| Serial Interface: RS-232
| BAUD: 19200
| Bits: 8
| Parity: None
| Stop Bits: 1
| Flow Control: None
| Data type: ISO8859-1

Data output by the EFM-100C instrument are:

    - Polarity of the electric field (+/-)
    - Electric field level (kV/m)

Data is output as it is read and calculated by the instrument at a fixed period of approximately 50 ms.
A line terminator is added to the serial data line.

Example Output Line
===================

| '$+00.65,0*CE\\r\\n'
| '$+00.65,0*CE\\r\\n'
| '$+00.64,0*CD\\r\\n'

Line Format
===========

A line consists of:

    - $-sign to indicate the start of the telemetry.
    - Polarity sign. Either + or -.
    - Zero-padded electric field level (kV/m). Zero padded decimal value between 00.00 and 20.00.
    - Fault indicater. Either 0 (no fault) or 1 (fault).
    - Signature. Two character hexadecimal value.

The electric field level is delimited by ','.
The fault indicator is delimited by '*'.
The line is terminated immediately following the signature value by '\\r\\n'.

Line Length
===========
The line length is fixed.

| Delimiter length: 1
| Terminator length: 1
