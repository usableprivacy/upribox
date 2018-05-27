wlan
----

This role is responsible for installing and configuring all WiFi and network related services such as hostapd or
isc-dhcp-server.
Interface wlan0 is used as the WiFi interface for the upribox and to provide a wireless network with the default SSID *upribox*.
Depending on the mode activated for a specific device, ads and trackers will automatically be blocked
and the traffic might be routed through the Tor [#Tor]_ network.
