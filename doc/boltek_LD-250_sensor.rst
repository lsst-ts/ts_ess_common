=================================================================
Serial protocol definition for: Boltek LD-250 Lightning Detector.
=================================================================

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

Data output by the LD-250 instrument can be status data:

    - Status data indicator
    - Close strike rate (strikes/minute)
    - Total strike rate (strikes/minute)
    - Close alarm status (0: not active, 1: active)
    - Severe alarm status (0: not active, 1: active)
    - Sensor azimuth heading (deg)

or noise data

    - Noise data indicator

or strike data

    - Strike data indicator
    - Corrected strike distance (miles)
    - Uncorrected strike distance (miles)
    - Strike azimuth bearing (deg)

Status data is output as it is calculated by the instrument at a fixed period of approximately 1 s.
Noise data is output if the noise level in the sensor is too high and the strike signal is lost.
The level, below which noise is squelched, can be set in the configuration of the instrument.
Strike data is output as it is read by the instrument and depends on when a strike is detected.
A line terminator is added to the serial data line.

Example Output Lines
====================

Status data:

| '$WIMST,0,0,0,0,000.0*42\\r\\n'

Noise data:

| '$WIMLN*CE\\r\\n'

Strike data:

| '$WIMLI,10,11,000.0*42\\r\\n'

Line Formats
============

A status data line consists of:

    - $-sign to indicate the start of the telemetry.
    - Status data indicator. This is always 'WIMST'.
    - Close strike rate (strikes/minute). Integer value between 0 and 999.
    - Total strike rate (strikes/minute). Integer value between 0 and 999.
    - Close alarm status (0: not active, 1: active)
    - Severe alarm status (0: not active, 1: active)
    - Sensor azimuth heading (deg). Zero padded decimal value between 000.0 and 359.9.
    - Signature. Two character hexadecimal value.

All values, except the sensor heading, are delimited by ','.
The sensor heading is delimted by '*'.
The line is terminated immediately following the signature value by '\\r\\n'.

A noise data line consists of:

    - $-sign to indicate the start of the telemetry.
    - Noise data indicator. This is always 'WIMLN'.
    - Signature. Two character hexadecimal value.

The noise data indicator is delimted by '*'.
The line is terminated immediately following the signature value by '\\r\\n'.

A strike data line consists of:

    - $-sign to indicate the start of the telemetry.
    - Status data indicator. This is always 'WIMLI'.
    - Corrected strike distance (miles). Integer value between 0 and 300.
    - Uncorrected strike distance (miles). Integer value between 0 and 300.
    - Strike azimuth bearing (deg). Zero padded decimal value between 000.0 and 359.9.
    - Signature. Two character hexadecimal value.

All values, except the strike bearing, are delimited by ','.
The strike bearing is delimted by '*'.
The line is terminated immediately following the signature value by '\\r\\n'.

Line Lengths
============
The lines length are variable, depending on the number of digits for the integer values.

| Delimiter length: 1
| Terminator length: 1
