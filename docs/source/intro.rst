###############
Getting started
###############

*********************
Hardware requirements
*********************

Table of recommended hardware
=============================

.. note::
   Since upribox v0.5 we support the Pi3 natively, so no
   additional WiFi dongle is required. The Pi3 WiFi however
   supports only one active Hotspot. You can not yet activate the
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

Please note that version 2 of the TL-WN722N WiFi dongle uses a different chipset and is not supported anymore.

The upribox software works with Raspberry Pi 1 as well, but the
performance for adblocking is considerable worse. Other potentially
suitable USB WiFi hardware for the Raspberry Pi 2 can be found in the `Pi(rate)Box
Wiki <https://piratebox.cc/raspberry_pi:piratebox_wifi_compatibility>`__.

.. rubric:: Links to Hardware

.. [#f1] Raspberry Pi 3 `[Element14] <https://www.element14.com/community/community/raspberry-pi/raspberrypi3>`__  `[Amazon.com] <https://www.amazon.com/Raspberry-Pi-RASP-PI-3-Model-Motherboard/dp/B01CD5VC92>`__
.. [#f2] Raspberry Pi 2 `[Element14] <http://element14.com/raspberrypi2>`__ `[Adafruit] <https://www.adafruit.com/products/2358>`__
.. [#f3] Sandisk SDHC 8GB `[Amazon.com] <https://www.amazon.com/SanDisk-MicroSDHC-Standard-Packaging-SDSDQUAN-008G-G4A/dp/B00M55C0VU/>`__
.. [#f4] Power Supply `[Amazon.com] <https://www.amazon.com/Kootek-Universal-Charger-Raspberry-External/dp/B00GWDLJGS>`__ `[Adafruit] <https://www.adafruit.com/products/1995>`__
.. [#f5] TL-WN722N Wireless USB adapter `[Amazon.com] <https://www.amazon.com/TP-LINK-TL-WN722N-Wireless-Adapter-External/dp/B002SZEOLG>`__


************
Installation
************

See the `official Raspberry Pi
documentation <https://www.raspberrypi.org/documentation/installation/installing-images/>`__
for pointers on how to install the upribox image on the SD card. Upon
the first boot the SSH/VPN keys are automatically re-generated (this
will take a couple of minutes), and the system partitions are resized to
use the entire size of the SD card. In the following you also find a
list of required (and tested hardware) for the upribox software. Make
sure that you use a compatible USB WiFi dongle!

***********
User manual
***********

Default passwords
=================

-  **Silent WiFi** (SSID: *upribox* ), **Ninja WiFi** (SSID:
   *upribox-ninja*), password: *changeme*
-  **SSH/Webinterface** login: *upri* password: *changethedefaults!*

.. _web_interface:

Web Interface
=============

Once you are connect to either of the upribox wifi networks (Silent or
Ninja) you can access the upribox Webinterface via the following URI:
http://upri.box.

.. _customization:

Customization
=============

There are two possible ways to adapt the settings of your upribox: use the Web Interface, or use *custom facts*. Configuration options
that are important for all users are available in the Web Interface, special configuration options for tech-savvy users can be manually
set using SSH.

.. note::
    The upribox Software update mechanisms ensures that the system remains in a consistent state. Manual changes to configuration files
    are therefore overwritten by the periodic software update process of the upribox.

The custom configuration options of the upribox Software are stored in **/etc/ansible/fact.d/**. Example for these configuration
facts can be found here: :download:`local_facts.tar.gz <examples/local_facts.tar.gz>`.

Advanced Network Settings
-------------------------

static network configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Connect to your upribox via SSH and create a **interfaces.fact** file in
the */etc/ansible/facts.d* directory. The following interfaces
configuration, will set the upribox to use a static IP configuration:

::

    {
        "general": {
            "mode": "static"
        },
        "static": {
            "ip": "10.203.95.160",
            "netmask": "255.255.255.0",
            "gateway": "10.203.95.254",
            "dns": "10.203.50.233 10.203.95.250"
        }
    }

Make sure to adapt the *ip*,\ *netmask*,\ *gateway*, and *dns* values to
reflect your setup. Once you created the *interfaces.fact* file, run
``sudo upri-config.py restart_network`` to configure the network device
and finally ``sudo reboot`` to start the upribox with the static IP
setup.

custom VPN server port
----------------------

Connect to your upribox via SSH and use the
following commands to set a custom *port* and *protocol* for the upribox
OpenVPN server:

::

    sudo upri-config.py set_vpn_connection 1194/UDP
    sudo upri-config.py restart_vpn
    sudo upri_conifg.py restart_firewall

Make sure to use a correct port - protocol combination: valid ports are
between *1025* and *65535* (**unprivileged ports**), and protocol can be
either **UDP** or **TCP**. If you want to access your upribox's VPN
server over **443/TCP** (standard HTTPS port) you need to set a custom
port-forwarding rule in your router: set your VPN server to a
unprivileged TCP port e.g. 4300/TCP and then forward port 443/TCP to
port 4300/TCP of your upribox.

custom wifi channel
-------------------

Connect to your upribox via SSH and use the
following commands to set a custom *channel* for the upribox
WiFi:

::

    sudo upri-config.py set_wifi_channel 3
    sudo upri-config.py restart_wlan

Valid WiFi channels are numbers between 1 and 10.

de/activate WiFi
----------------

If you have ssh enabled you can connect to your upribox and deactivate both, Ninja and Silent WiFi:

::

    sudo upri-config.py enable_silent no
    sudo upri-config.py restart_silent
    sudo upri-config.py enable_tor no
    sudo upri-config.py restart_tor

To activate them again replace "no" with "yes". If you activate Ninja WiFi, you have to activate Silent WiFi as well.
