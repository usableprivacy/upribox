.. _django-label:

django
------

The upribox user interface (see :ref:`web_interface`) is based on the Python Web framework Django [#Django]_.
The role is responsible for installing the requirements to a virtual environment, copying the web interface files,
setting up the database and installing services like a supervisor (for the rqworker) and the application container uWSGI.
By deploying this role the upribox also starts a cleanup process for the saved statistic files removing data older than 6 months.

.. note::
    For privacy reasons the upribox does not keep the adblocking logfile with timestamps and URLs but tries to aggregate
    the information as soon as possible to store only the information that is needed for the statistics and to assure
    anonymity.

In order to apply changes to the configuration of the upribox Django has access to only one configuration script ``upri-config.py`` and its actions:

- set_ssid

  - Sets a new SSID for the Silent WiFi by writing to the fact *wlan*

- set_password

  - Sets a new password for the Silent WiFi by writing to the fact *wlan*

- restart_wlan

  - Triggers the Ansible tasks with the tag *ssid*

- enable_silent

  - Enables/disables the Silent WiFi by writing to the fact *wlan*

- restart_silent

  - Triggers the Ansible tasks with the tag *toggle_silent*

- enable_vpn

  - Enables/disables the VPN by writing to the fact *vpn*

- set_vpn_connection

  - Sets a custom port and protocol for the upribox OpenVPN server by writing to the fact *vpn*

- set_wlan_channel

  - Sets a new WiFi channel for the Silent WiFi by writing to the fact *wlan*

- restart_vpn

  - Triggers the Ansible tasks with the tag *toggle_vpn*

- enable_ssh

  - Enables/disables the ssh by writing to the fact *ssh*

- restart_ssh

  - Triggers the Ansible tasks with the tag *toggle_ssh*

- enable_apate

  - Enables/disables the Apate (see :ref:`arp-label`) by writing to the fact *apate*

- restart_apate

  - Triggers the Ansible tasks with the tag *toggle_apate*

- enable_static_ip

  - Sets the upribox to DHCP or static IP mode by writing to the fact *interfaces*

- set_ip

  - Sets a static IP by writing to the fact *interfaces*

- set_dns_server

  - Sets the DNS server by writing to the fact *interfaces*

- set_netmask

  - Sets subnetmask by writing to the fact *interfaces*

- set_gateway

  - Sets the gateway by writing to the fact *interfaces*

- set_dhcpd

  - Enables/disables the DHCP server by writing to the fact *dhcpd*

- restart_dhcpd

  - Triggers the Ansible tasks with the tag *dhcp_server*

- parse_logs

  - Parses the log files of the services  and aggregates the statistics data

- parse_user_agents

  - Parses the log file of the service squid containing MAC addresses, IP addresses and user-agents and saves the gathered information into the database

- generate_profile

  - Generates openvpn client certificates and saves the generated openvpn client configuration into the database

- delete_profile

  - Revokes previously generated openvpn client certificates

- restart_firewall

  - Triggers the Ansible tasks with the tag *iptables*

- enable_device

  - Enables ARP spoofing via Apate (see :ref:`arp-label`) for a specific device

- disable_device

  - Disables ARP spoofing via Apate (see :ref:`arp-label`) for a specific device

- configure_devices

  - Triggers the Ansible tasks with the tag *configure_devices*

- restart_network

  - Triggers the Ansible tasks with the tag *network_config*
