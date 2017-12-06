
.. note::
   If you bought a pre-assembled upribox from our online store you do not have to read this guide since everything is
   already set up and you only have to complete the simple tasks described in the enclosed manual.

In a few easy steps you can build your own upribox and won't get bothered anymore by annoying ads and trackers (see :ref:`silent`).
Additionally you can use your upribox to surf the web anonymously via Tor (see :ref:`ninja`) and set it up to be your
OpenVPN server which secures your connection in unprotected WiFis and lets you benefit from the ad-blocking features
on the road (see :ref:`vpn`).



Installation
============

You can download the latest upribox image from `Github <https://github.com/usableprivacy/upribox/releases>`__ and verify its integrity and authenticity with the provided signature file and PGP key (see :ref:`signed-releases`).
See the `official Raspberry Pi documentation <https://www.raspberrypi.org/documentation/installation/installing-images/>`__
for pointers on how to install the upribox image on the SD card. Upon
the first boot the SSH/VPN keys are automatically re-generated (this
will take a couple of minutes).


Hardware requirements
---------------------

In the following you will find a list of required (and tested) hardware for the upribox software.

Table of recommended hardware
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+--------------+------------------------------------------------+
|              |      Raspberry Pi 3 [#f1]_                     |
+==============+================================================+
| SD Card      |      microSDHC Class 10 (min. 4GB) [#f3]_      |
+--------------+------------------------------------------------+
| Power Supply |      Micro USB 5V/2A [#f4]_                    |
+--------------+------------------------------------------------+
| WiFi         |      onboard                                   |
+--------------+------------------------------------------------+

.. [#f1] Raspberry Pi 3 `[Element14] <https://www.element14.com/community/community/raspberry-pi/raspberrypi3>`__  `[Amazon.com] <https://www.amazon.com/Raspberry-Pi-RASP-PI-3-Model-Motherboard/dp/B01CD5VC92>`__
.. [#f3] Sandisk SDHC 8GB `[Amazon.com] <https://www.amazon.com/SanDisk-MicroSDHC-Standard-Packaging-SDSDQUAN-008G-G4A/dp/B00M55C0VU/>`__
.. [#f4] Power Supply `[Amazon.com] <https://www.amazon.com/Kootek-Universal-Charger-Raspberry-External/dp/B00GWDLJGS>`__ `[Adafruit] <https://www.adafruit.com/products/1995>`__

User manual
===========

.. _web_interface:

Web Interface
-------------

Once you are connected to the upribox WiFi network you can access the upribox web interface via one of the following URIs:

- `http://upri.box <http://upri.box/>`_
- `https://upri.box:4300 <https://upri.box:4300/>`_

In case your device is not connected to the upribox WiFi network and the traffic is not routed through the upribox, you can still access the web interface via:

- `http://upribox.local <http://upribox.local/>`_
- `https://upribox.local:4300 <https://upribox.local:4300/>`_

(see :ref:`integration`)

Default passwords
-----------------

If you used the latest community upribox image for setting up your own privacy box you need the following passwords for accessing it:

===============================  ============   ======================
Login                            User           Default Password
===============================  ============   ======================
Wifi (SSID: upribox)             \-              changeme
Web Interface / SSH              upri           changethedefaults!
===============================  ============   ======================


It is important that you change the passwords upon the first login in the admin section of the web interface.
New passwords should have at least 8 characters containing lower-case, upper-case, numbers and special characters.

If you bought a pre-assembled upribox from our online store,
the SSH password of your upribox is configured to be the equal to your webinterface password.

Updates
-------

The upribox performs an auto-update every **hour**, which includes software updates via ansible and updates from github.
The blocking rules for privoxy and DNS are updated every **four hours**.

Please note that this process overwrites manual changes to configuration files. To conduct persistent manual changes you have to use *custom facts* (see :ref:`customization`).
