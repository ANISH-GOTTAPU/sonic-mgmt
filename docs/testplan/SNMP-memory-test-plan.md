# SNMP-memory test plan

* [Overview](#Overview)
   * [Scope](#Scope)
   * [Testbed](#Testbed)
* [Setup configuration](#Setup%20configuration)
* [Test cases](#Test%20cases)

## Overview
The purpose is to test that SNMP memory MIB objects are functioning properly on the SONIC switch DUT.

### Scope
The test is targeting a running SONIC system with fully functioning configuration. The purpose of the test is not to test specific API, but functional testing of SNMP on SONIC system.

### Testbed
The test will run on any testbeds.

## Setup configuration
This test requires no specific setup.

## Test
Retrieve facts for a device using SNMP, and compare it to system values.

## Test cases
### Test case test_snmp_memory
#### Test steps
* Retrieve facts for a device using SNMP
* Get expected values for a device from system
* Compare that facts received by SNMP are equal to values received from system
* Run script that should slightly load RAM memory
* Retrieve facts for a device using SNMP, verify that SNMP value differs from system data less that 4%
