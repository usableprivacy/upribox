django
------

The upribox user interface (see :ref:`web_interface-label`) is based on the Python Web framework Django_.
The role is responsible for installing the requirements to a virtual environment, copying the web interface files,
setting up the database and installing service like a supervisor (for the rqworker) and the application container uWSGI.
When deploying this role the upribox also starts a cleanup process for the saved statistic files removing data older than 6 months.

.. note::
    For privacy reasons the upribox does not keep the adblocking logfile with timestamps and URLs but tries to aggregate
    the information as soon as possible to store only the information that is needed for the statistics and to to assure
    anonymity.

In order to apply changes to the configuration of the upribox Django has access to only one configuration script ``upri-config.py`` and its methods:

- set_ssid
- set_password
- set_tor_ssid
- set_tor_password
- restart_wlan
- enable_tor
- enable_silent
- restart_tor
- restart_silent
- enable_vpn
- set_vpn_connection
- set_wlan_channel
- restart_vpn
- enable_ssh
- restart_ssh
- enable_apate
- enable_static_ip
- restart_apate
- parse_logs
- parse_user_agents
- generate_profile
- delete_profile
- restart_firewall
- enable_device
- disable_device
- set_ip
- configure_devices
- set_dns_server
- set_netmask
- set_gateway
- restart_network
- set_dhcpd
- restart_dhcpd