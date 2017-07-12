.. _customization:

#############
Customization
#############

There are two possible ways to adapt the settings of your upribox by writing
to *custom facts*: use the Web Interface or edit the *custom facts* manually.
Configuration options that are important for all users are available in the Web
Interface, special configuration options for tech-savvy users can be set manually
using SSH.

.. note::
    The upribox Software update mechanisms ensures that the system remains in a
    consistent state. Manual changes to configuration files
    are therefore overwritten by the periodic software update process of the upribox.
    **The only way the persist your changes is by writing to the correspondent custom fact.**

The custom configuration options of the upribox Software are stored in **/etc/ansible/fact.d/**.
Example for these configuration facts can be found here: :download:`local_facts.tar.gz <examples/local_facts.tar.gz>`.

*************************
Advanced Network Settings
*************************

static network configuration
============================

Connect to your upribox via SSH and create an **interfaces.fact** file in
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

::

    sudo upri-config.py restart_network
    sudo reboot

to configure the network device and to restart the upribox with the static IP
setup. (see :ref:`upri-config`)

**********************
custom VPN server port
**********************

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
port-forwarding rule in your router: set your VPN server to an
unprivileged TCP port e.g. 4300/TCP and then forward port 443/TCP to
port 4300/TCP of your upribox. (see :ref:`upri-config`)

*******************
custom wifi channel
*******************

Connect to your upribox via SSH and use the
following commands to set a custom *channel* for the upribox
WiFi:

::

    sudo upri-config.py set_wifi_channel 3
    sudo upri-config.py restart_wlan

Valid WiFi channels are numbers between 1 and 10. (see :ref:`upri-config`)

****************
de/activate WiFi
****************

If you have ssh enabled you can connect to your upribox and deactivate both, Ninja and Silent WiFi:

::

    sudo upri-config.py enable_silent no
    sudo upri-config.py restart_silent
    sudo upri-config.py enable_tor no
    sudo upri-config.py restart_tor

To activate them again replace "no" with "yes". If you activate Ninja WiFi, you have to activate Silent WiFi as well. (see :ref:`upri-config`)