==============================================================================================
Serial protocol definition for: Campbell Scientific CSAT3B Three-Dimensional Sonic Anemometer.
==============================================================================================

Garry Knight.
2021-08-24

Serial Interface & Parameters
=============================

| Serial Interface: RS-485
| BAUD: 115200
| Bits: 8
| Parity: None
| Stop Bits: 1
| Flow Control: None
| Data type: ISO8859-1

The instrument must configured to mode 3 , unprompted output via its RS-485 connector at 100 ms repetition rate.

Data output by the CSAT3B instrument are:

    - x-axis wind speed (m/s)
    - y-axis wind speed (m/s)
    - z-axis wind speed (m/s)
    - Sonic temperature (degrees C)

Data is output as it is read and calculated by the instrument at a fixed period of approximately 100 ms.
A line terminator is added to the serial data line.

Example Output Line
===================

| '0.08945,0.06552,0.05726,19.69336,0,5,c3a6\\r\\n'
| '0.10103,0.06517,0.05312,19.70499,0,6,3927\\r\\n'
| '0.09045,0.04732,0.04198,19.71161,0,7,d7e5\\r\\n'

Line Format
===========

A line consists of:

    - x-axis wind speed (m/s). Decimal value.
    - y-axis wind speed (m/s). Decimal value.
    - z-axis wind speed (m/s). Decimal value.
    - Sonic temperature (degrees C). Decimal value.
    - Diagnostic word. Single digit decimal.
    - Record counter. One or two digit value (0-63).
    - Signature. Four character hexadecimal value.

All values are delimited by ','.
The line is terminated immediately following the signature value by '\\r\\n'.

Line Length
===========
The line length is not fixed, and is dependant upon wind speed, temperature values, diagnostic and record counter value.

| Delimiter length: 1
| Terminator length: 1

Recommended Integrity Checks
============================
Diagnostic word is a decimal integer of up to three characters.
Any value other than '0', indicates an instrument problem.

Record counter is a decimal integer. This value is incremented each time the instrument sends another measurement.
The value rolls over to 0 at 63.
This value may be used to determine missing measurements.

Signature may be used to test the integrity of all the characters in the line up to the end of the record counter.
The 4-characters of the signature value must be read and cast to long data to compare with the result of the following algorithm is provided by the instruments manual::

    // signature(), signature algorithm.
    // Standard signature is initialized with a seed of 0xaaaa.
    // Returns signature.
    unsigned short signature(unsigned char* buf, int swath, unsigned short seed) {
    unsigned char msb, lsb;
    unsigned char b;
    int i;
    msb = seed >> 8;
    lsb = seed;
    for (i = 0; i < swath; i++)
    {
    b = (lsb << 1) + msb + *buf++;
    if (lsb & 0x80) b++;
    msb = lsb;
    lsb = b;
    }
    return (unsigned short)((msb << 8) + lsb);

Note that the signature examples provided in the documentation of the Campbell CSAT3B sensor are incorrect.
This was discovered by trial and error using the output of the real sensor.
Signature checking has been disabled in our sensor implementation.

Timeout may be used to determine if the instrument is connected/disconnected.
Timeout should occur if terminator is not received within the timeout period.
The instrument should be configured to 100 ms repetition rate. Timeout value 0.15 seconds.

Split output line by comma delimiter and test for correct number of values.

Test wind speed and temperature value format, and that they are convertible to float data type.
