.. _lsst.ts.ess.common.campbell_scientific_CSAT3B_sensor:

=============================================================
Campbell Scientific CSAT3B Three-Dimensional Sonic Anemometer
=============================================================

Data output by the CSAT3B instrument are:

* x-axis wind speed (m/s)
* y-axis wind speed (m/s)
* z-axis wind speed (m/s)
* Sonic temperature (degrees C)

We use the instrument in mode 3: self triggered, filtered, unprompted output.
In this mode data is output as it is read and calculated by the instrument at a fixed period of approximately 100 ms.

Ouput Format
============

The output format is as follows::

    x.xxxxx,y.yyyyy,z,zzzzz,t.tttttt,d,r,cccc\r\n

Where:

* ``x.xxxxx``: wind speed in x (m/s).
* ``y.yyyyy``: wind speed in y (m/s).
* ``z.zzzzz``: wind speed in z (m/s).
* ``t.tttttt``: sonic temperature (C).
* ``d``: diagnostic word: a bit mask of 1-3 digits.
  0 indicates OK; see table 8 in the manual for other values.
* ``r``: record counter: 1-2 digits in the range 0-63.
  This value is incremented for each line of data each, rolling around to 0 for the reading following #63.
* ``cccc``: checksum signature: 4 hexadecimal digits.
* Float values have the precision shown but may have extra digits and a sign to the left of the decimal.

Example Output::

    0.08945,0.06552,0.05726,19.69336,0,5,c3a6\r\n
    0.10103,0.06517,0.05312,19.70499,0,6,3927\r\n
    0.09045,0.04732,0.04198,19.71161,0,7,d7e5\r\n

Checksum Signature
-------------------

The checksum signature may be used to test the integrity of all the characters in the line up to the end of the record counter.
The 4-characters of the signature value must be read as a hex long int to compare with the result of the following algorithm, as provided by the manual::

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

Serial Interface & Parameters
=============================

* RS-485
* 115200 baud
* 8 data bits
* 1 stop bit
* no parity
* no flow control
* ISO8859-1 format

Manuals
=======

* :download:`CSAT3B 3-D Anemometer Product Manual <campbell_scientific_pdfs/CSAT3B 3-D anemometer.pdf>`
