############
Architecture
############

A core technology used in the upribox software is Ansible_: a python-based configuration management software. Our rationale
behind using Ansible_ is twofold:

**Reproducibility**
Every setting, installed package etc. should be documented in code. We use Ansible's default push mode to configure the base
image in order to to: deploy the latest upribox software and harden the base image. All changes we perform on a given base images can
be reproduced (see :ref:`base-image-label`).

**Continuous delivery**
Ansible_ enables us to roll out bugfixes as well as new features continuously. Once the upribox software is deployed it
automatically gets changes from our Github repository and deploys them using Ansible's pull mode.

.. note:: Config files are overwritten periodically (see :ref:`customization-label`).

*******
Modules
*******

Base setup
==========

.. include:: modules/init.rst
.. include:: modules/common.rst
.. include:: modules/unattended_upgrades.rst

Networking
==========

.. include:: modules/arp.rst
.. include:: modules/iptables.rst
.. include:: modules/vpn.rst
.. include:: modules/wlan.rst

Privacy
=======

.. include:: modules/dns.rst
.. include:: modules/dns_ninja.rst
.. include:: modules/nginx.rst
.. include:: modules/privoxy.rst
.. include:: modules/tor.rst


User Interface
==============

.. include:: modules/django.rst
.. include:: modules/ssh.rst


.. rubric:: Footnotes

.. [Ansible] https://www.ansible.com