iptables
--------

In order to be able to configure adblocking (Silent Mode) and Tor (Ninja Mode) for each device separately the upribox
adds and removes iptables rules dynamically. Two lists of MAC addresses - one for devices which don't need adblocking and
one for devices with Tor enabled - are stored in local facts. If a user deactivates adblocking or activates Tor for a device
in the user interface the MAC address will be added to the no_adblocking list and the tor list, respectively. The iptables
rules is immediately copied to ``/etc/iptables/`` and to take effect the service is restarted.
