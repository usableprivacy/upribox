wlan
----

This role is responsible for installing and configuring all WiFi and network related services such as hostapd or
isc-dhcp-server.
Interface wlan0 is used as the WiFi interface for the Silent Mode whereas a virtual interface wlan0_0 is added in case
of an activated Ninja Mode.

Silent Mode
^^^^^^^^^^^

Silent Mode creates a wireless network with the default SSID *upribox*. If your device is connected to this network ads
and trackers will automatically be blocked.

Ninja Mode
^^^^^^^^^^

Ninja Mode results in a separate wireless network with the default SSID *upribox-ninja* and blocks ads and trackers as
well but in addition the traffic will be routed through the Tor_ network.