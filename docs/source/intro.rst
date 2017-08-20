***************
Getting Started
***************

**Welcome to our upribox Getting Started guide!**

.. note::
   If you bought a pre-assembled upribox from our online store you do not have to read this guide since everything is
   already set up and you only have to complete the simple tasks described in the enclosed manual.

In a few easy steps you can build your own upribox and won't get bothered anymore by annoying ads and trackers (see :ref:`silent`).
Additionally you can use your upribox to surf the web anonymously via Tor (see :ref:`ninja`) and set it up to be your
OpenVPN server which secures your connection in unprotected WiFis and lets you benefit from the ad-blocking features
on the road (see :ref:`vpn`).



Installation
============

You can download the latest upribox image from our `website <https://upribox.org/download/>`__ and verify its integrity and authenticity with the provided signature file and PGP key (see :ref:`signed-releases`).
See the `official Raspberry Pi documentation <https://www.raspberrypi.org/documentation/installation/installing-images/>`__
for pointers on how to install the upribox image on the SD card. Upon
the first boot the SSH/VPN keys are automatically re-generated (this
will take a couple of minutes).


Hardware requirements
---------------------

In the following you will find a list of required (and tested) hardware for the upribox software. On the Raspberry Pi 2 make
sure that you use a compatible USB WiFi dongle!

Table of recommended hardware
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::
   Since upribox v0.5 we support the Pi3 natively, so no
   additional WiFi dongle is required. The Pi3 WiFi however
   supports only one active Hotspot. You cannot activate the
   **Ninja WiFi** on the Pi3 without an additional WiFi dongle.

+--------------+------------------------+---------------------------+
|              | Raspberry Pi 3 [#f1]_  | Raspberry Pi 2 [#f2]_     |
+==============+========================+===========================+
| SD Card      |      microSDHC Class 10 (min. 4GB) [#f3]_          |
+--------------+------------------------+---------------------------+
| Power Supply |      Micro USB 5V/2A [#f4]_                        |
+--------------+------------------------+---------------------------+
| WiFi         |       onboard          | TL-WN722N **v1** [#f5]_   |
+--------------+------------------------+---------------------------+

.. warning::
   Please note that version 2 of the TL-WN722N WiFi dongle uses a different WiFi chipset and is not supported anymore.

The upribox software works with Raspberry Pi 1 as well, but the
performance for ad-blocking is considerable worse. Other potentially
suitable USB WiFi hardware for the Raspberry Pi 2 can be found in the `Pi(rate)Box
Wiki <https://piratebox.cc/raspberry_pi:piratebox_wifi_compatibility>`__.

.. [#f1] Raspberry Pi 3 `[Element14] <https://www.element14.com/community/community/raspberry-pi/raspberrypi3>`__  `[Amazon.com] <https://www.amazon.com/Raspberry-Pi-RASP-PI-3-Model-Motherboard/dp/B01CD5VC92>`__
.. [#f2] Raspberry Pi 2 `[Element14] <http://element14.com/raspberrypi2>`__ `[Adafruit] <https://www.adafruit.com/products/2358>`__
.. [#f3] Sandisk SDHC 8GB `[Amazon.com] <https://www.amazon.com/SanDisk-MicroSDHC-Standard-Packaging-SDSDQUAN-008G-G4A/dp/B00M55C0VU/>`__
.. [#f4] Power Supply `[Amazon.com] <https://www.amazon.com/Kootek-Universal-Charger-Raspberry-External/dp/B00GWDLJGS>`__ `[Adafruit] <https://www.adafruit.com/products/1995>`__
.. [#f5] TL-WN722N Wireless USB adapter `[Amazon.com] <https://www.amazon.com/TP-LINK-TL-WN722N-Wireless-Adapter-External/dp/B002SZEOLG>`__


User manual
===========

.. _web_interface:

Web Interface
-------------

Once you are connected to either of the upribox WiFi networks (Silent or
Ninja) you can access the upribox web interface via the following URI:
**http://upri.box**. (see :ref:`integration`)

Default passwords
-----------------

If you used the latest upribox image for setting up your own privacy box you need the following passwords for accessing it:

-  **Silent WiFi** (SSID: *upribox* ), **Ninja WiFi** (SSID:
   *upribox-ninja*), password: *changeme*
-  **SSH/web interface** login: *upri* password: *changethedefaults!*

Please change the passwords upon the first login in the admin section of the web interface. New passwords have to be at least 8 characters long containing lower-case, upper-case, numbers and special characters.

*******
Updates
*******

The upribox performs an auto-update every **four hours**. This includes:

 * Blocking rules for privoxy and DNS
 * Software updates via ansible + updates from github

Please note that this process overwrites manual changes to configuration files. To conduct persistent manual changes you have to use *custom facts* (see :ref:`customization`).
