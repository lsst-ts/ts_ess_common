====================================================
Serial protocol definition for: Aurora Cloud Sensor.
====================================================

Garry Knight.
2021-09-05

This protocol definition for the Aurora Cloud Sensor is compiled only from the instruments
supplied beta manual. The manual was found to contain conflicting definitions within its own
text and incomplete definitions of value formats.
| Hexadecimal values were defined as both upper and lower case alphas. It has been assumed here that they are all upper case.
| Value ranges are incomplete. It is assumed that any value capable of a negative sign has its first character '-'.

Serial Interface & Parameters
=============================

| Serial Interface: RS-232
| BAUD: 9600
| Bits: 8
| Parity: None
| Stop Bits: 1
| Flow Control: None
| Data type: ISO8859-1

Data output by the Aurora Cloud Sensor instrument are:

    - Sensor temperature (deg C) * 100
    - Sky temperature (deg C) * 100
    - Clarity * 100
    - Light * 10
    - Rain * 10

Data is output as it is read and calculated by the instrument at a fixed period of approximately 2 s.
A line terminator is added to the serial data line.

Example Output Line
===================

'$20,FF,00742,02368,02458,-0090,252,032,8FFF,0104,37,00!\\n'

Line Format
===========

========  ======================  ======================================
Data      Type                    Description
========  ======================  ======================================
'$'       ASCII, fixed            Start of frame ('$')
'20,'     Hex, fixed              Header ID ('20')
'FF,'     Hex, fixed              Always 'FF'
'nnnnn,'  Dec, 5-digits ldg zero  Frame sequence number (00000 to 99999)
'nnnnn,'  Dec, 5-digits ldg zero  Sensor temperature * 100
'nnnnn,'  Dec, 5-digits ldg zero  Sky temperature * 100
'nnnnn,'  Dec, 5-digits ldg zero  Leading zeros      Clarity * 100
'nnn,'    Dec, 3-digits ldg zero  Light * 10
'nnn,'    Dec, 3-digits ldg zero  Rain * 10
'hhhh,'   Hex                     Ignore - Used for testing only
'hhhh,'   Dec or hex?             Ignore - Used for testing only
'hh,'     Hex                     Alarm status. Bit-wise alarms (not used)
'00'      Hex, fixed              Always '00'
'!'       ASCII, fixed            End of frame ('!')
'\\n'     ASCII, fixed            Line terminator ('\n')
========  ======================  ======================================

Generally, fields are delimited by ','.
The line is terminated immediately following the signature value by '\\n'.

Line Length
===========
The line length is fixed at 56 characters.

| Delimiter length: 1
| Terminator length: 1

Recommended Integrity Checks
============================

The frame sequence number is a decimal integer. This value is incremented each time the instrument sends another measurement.
The value rolls over to 0 at 99999.
This value may be used to determine missing measurements.

Test for fixed line length of 56 characters (inc. line terminator).

Timeout may be used to determine if the instrument is connected/disconnected.
Timeout should occur if terminator is not received within the timeout period.
The instrument should be configured to 2 second repetition rate. Timeout value 2.2 seconds.

Split output line by comma delimiter and test for correct number of values.
Test for fixed start of frame and end of frame strings.

Test Sky temperature, Clarity, Light and Rain values, and that they are convertible to decimal integer type.
