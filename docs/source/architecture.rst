.. _architecture:

############
Architecture
############

A core technology used in the upribox software is Ansible [#Ansible]_: a python-based configuration management software. Our rationale
behind using Ansible is twofold:

**Reproducibility**
Every setting, installed package etc. should be documented in code. We use Ansible's default push mode to configure the base
image in order to deploy the latest upribox software and harden the base image. All changes we perform on a given base images can
be reproduced (see :ref:`base-image`).

**Continuous delivery**
Ansible enables us to roll out bugfixes as well as new features continuously. Once the upribox software is deployed it
automatically gets changes from our Github repository and deploys them using Ansible's pull mode.

.. note:: Config files are overwritten periodically (see :ref:`customization`).

*******
Modules
*******

Base setup
==========

.. include:: modules/init.inc
.. include:: modules/common.inc
.. include:: modules/unattended_upgrades.inc

Networking
==========

.. include:: modules/arp.inc
.. include:: modules/iptables.inc
.. include:: modules/vpn.inc
.. include:: modules/wlan.inc

Privacy
=======

.. include:: modules/dns.inc
.. include:: modules/dns_ninja.inc
.. include:: modules/dns_unfiltered.inc
.. include:: modules/nginx.inc
.. include:: modules/privoxy.inc
.. include:: modules/tor.inc


User Interface
==============

.. include:: modules/ssh.inc
.. include:: modules/fingerprinting.inc
.. include:: modules/squid.inc
.. include:: modules/django.inc

.. _upri-config:

********************
Configuration Script
********************

In order to apply changes to the configuration of the upribox Django has access to only one configuration script ``upri-config.py`` and its actions:

.. argparse::
   :filename: argparser.py
   :func: create_argparser
   :prog: upri-config.py


.. rubric:: Footnotes

.. [#Ansible] https://www.ansible.com
.. [#UnattendedUpgrades] https://wiki.debian.org/UnattendedUpgrades
.. [#OpenVPN] https://openvpn.net/
.. [#Privoxy] https://www.privoxy.org/
.. [#Tor] https://www.torproject.org/
.. [#Django] https://www.djangoproject.com
.. [#Squid] http://www.squid-cache.org/
