.. _lsst.ts.ess.common.snmp:

====
SNMP
====

This document describes the support for SNMP.

SNMP means Simple Network Management Protocol.

All SNMP info for a device is described in an MIB_.

MIB
===

Wikipedia_ gives the following description of MIB files and their contents:

    A management information base (MIB) is a database used for managing the entities in a communication network.
    Most often associated with the Simple Network Management Protocol (SNMP), the term is also used more generically in contexts such as in OSI/ISO Network management model.
    While intended to refer to the complete collection of management information available on an entity, it is often used to refer to a particular subset, more correctly referred to as MIB-module.

    Objects in the MIB are defined using a subset of Abstract Syntax Notation One (ASN.1) called "Structure of Management Information Version 2 (SMIv2)".

    The database is hierarchical (tree-structured) and each entry is addressed through an object identifier (OID_).

.. _Wikipedia: https://en.wikipedia.org/wiki/Management_information_base

Each MIB may define a `Module Identity`_ and defines one or more `Object Identifier`_'s and `Object Type`_'s.

Module Identity
---------------
An MIB may define a Module Identity.
These contain generic MIB module information that can be used by sub-modules.
Vendors may use this, for instance, for defining their specific top level OID_ that is common to all MIBs of their hardware.

Object Identifier
-----------------
Not to be confused with OID_.
An Object Identifier defines a branch in the MIB tree.
Each branch may contain other branches or `Object Type`_ leaves.
Branches are used to create a hierarchical tree with the leaves the items that emit telemetry.

Object Type
-----------
Object Types are the leaves of the MIB tree and define the entities for which telemetry gets emitted.
There are several kinds of Object Types, among which

    - True leaves.

        These contains a one on one correspondence with telemetry emitted via SNMP.
        For instance, the Schneider MIB contains a `midSerialNumber` leaf which corresponds to the device serial number SNMP telemetry item.

    - Descriptive leaves.

        These contain information that needs to be used to know which leaves correspond to which telemetry.
        For instance, the Raritan MIB contains an `inletDeviceCapabilities` bitmask leaf which describes which capabilities the device has.
        When retrieving the `measurementsInletSensorValue` telemetry leaves, the final digits of their OIDs need to be compared to the bitmask to know which quantity each telemetry item represents.

        It is important to note that SNMP does not support float values.
        It only supports int and string values.
        Float values, for which the accuracy is such that decimal places are important, get converted to ints by multiplying by a power of ten sufficiently high to shift the float value by the required amount of decimal places.
        This amount is available in the MIB so at all times the float values can be reconstructed.

        For instance, apart from the `inletDeviceCapabilities` bitmask leaf mentioned earlier, the Raritan MIB it contains an `inletSensorsUnits` leaf and an `inletSensorDecimalDigits` leaf.
        The `measurementsInletSensorValue` telemetry values need to be interpreted with the corresponding unit and number of decimal digits to be converted from int to float.

    - Table leaves.

        Some telemetry items are grouped together in tables.
        A table is a group of leaves that contain telemetry for several items.
        For instance, the Eaton MIB contains a `xupsInputTable` item composed of the `xupsInputVoltage`, `xupsInputCurrent` and `xupsInputWatts` items.
        Each table may be repeated more than once depending on how many hardware components provide the items in the table.
        The description of the table contains information about which leaf defines how ofter the table is repeated.

    - Index leaves.

        For each table an index leaf needs to be defined.
        The index leaf defines which other leaves form part of the table.
        For instance, the aforementioned Eaton `xupsInputTable` contains a `xupsInputEntry` index leaf which defines which leaves are part of the table.
        Note that index leaves are not part of the SNMP telemetry.

OID
---
An Object IDentifier (OID) is a unique sequence of numbers representing a branch or a leaf.
A leaf OID is contains the OIDs of all branches it lies under.
Depending on the type of leaf, the digit that defines the leaf in the MIB may or may not be the final digit.

Some examples that (hopefully) will make this clear.

    - The top level OID for SNMP is `.1.3.6.1` which means `iso.org.dod.internet`.
    - The sysDescr OID is `.1.3.6.1.2.1.1.1` where the `2` refers to the `mgmt` branch in SNMPv2.

        The telemetry is emitted on OID `1.3.6.1.2.1.1.1.0` (note the trailing `0`).

    - All companies (or enterprises) can register their OIDs under the `.1.3.6.1.4.1` branch.

        The `4` is for the `private` branch and the trailing `1` for the `enterprises` branch.
        Some of the hardware at the summit use the following OIDs under the enterprises branch:

            - Eaton: 534

                The Eaton XUPS OID is `.1.3.6.1.4.1.534.1` and the Eaton OID (534) is a Module Identity.

            - Schneider Electric: 3833
            - Raritan: 13742
            - SynAccess: 21728

                Note that these are referred to as NetBooter in the code.

Traps
-----

An SNMP Trap is an event that gets sent in case of a sudden change that indicates an alarm or the end of an alarm.
No support for traps has been built in ts_ess_common.

MIB Tree Holder
===============

In order to parse MIBs a MIB Tree Holder class was implemented.
This custom class parses the MIBs included in `data` directory in the the ts_ess_common project.
As such the MIB Tree Holder provides a translation from the OIDs to the XML telemetry items for each type of hardware.
As a matter of fact, the MIB Tree Holder was used to generate the XML using additional input files.
That code is not part of this project.

SNMP Implementation
===================

All low level SNMP infrastrucuture is provided by the pysnmp_ project.
That project uses pyasn1_ for its data types.
Due to code reorganizations in both projects after SNMP support was added to ts_ess_common, both dependencies have been pinned to avoid pulling in the latest versions.

SNMP supports getting telemetry via several commands which are all implemented in the `nextCmd` method of pysnmp.
The `nextCmd` method takes several parameters, representing the host and port to connect to, the community data and the OID to query.
Since the `nextCmd` method is synchronous, it needs to be wrapped in an asyncio `run_in_executor` call to not be blocking.

The community data is a configurable string that is required and depends on the configuration of the SNMP device.
By default it is set to `public` and for many SNMP devices at the summit it has been modified.
See the configuration in ts_config_ocs for more details.

In order to support simulation mode of the ESS CSC, an SNMP server simulator was implemented.
This server simulator returns random values for int, float and string items.

Future Work
===========

As described in the previous section, newer versions of pysnmp_ and pyasn1_ are available.
In order to be able to switch to these newer versions, code changes in the ts_ess_common project are necessary.
The newer version of pysnmp provides both MIB parsing into Python objects and an SNMP server simulator.

For now no upgrade to the newer versions is foreseen.
It has not been decided to switch to the MIB parser and/or SNMP server simulator if the pysnmp and pyasn1 dependency versions get updated.

.. _pysnmp: https://www.pysnmp.com/
.. _pyasn1: https://pypi.org/project/pyasn1/
