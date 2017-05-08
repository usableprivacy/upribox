dns
---
The upribox uses the *dnsmasq* daemon to filter DNS requests. This role set-ups *dnsmasq* on all interfaces and listens for requests.
Filtered domains are loaded from `/etc/dnsmasq.d`.