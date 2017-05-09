.. _fingerprinting:

fingerprinting
--------------

The upribox provides a service called *registrar* which gathers MAC address, IP address and hostname of a device and
saves the information into the database. A separate script uses the user-agents provided by squid and tries to extract
a model name of the device. These names are later on suggested to the user in the web interface as a way to identify his
or her device in a list of other devices on the network. Furthermore the chosen name acts as a label in the device overview.