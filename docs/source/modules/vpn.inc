vpn
---

The upribox uses OpenVPN [#OpenVPN]_ as a VPN service to protect your communication security on the road. This can be used to
protect your sensitive information when using public WiFi hotspots. The role creates the necessary certificates and
keys and installs and sets up the service.

.. note::
    For security reasons OpenVPN is *not* executed as root and uses SHA384 for the packet HMAC authentication and AES-256 (CBC mode) for encryption.