.. _security:

########
Security
########

When we designed the upribox architecture and features security was the first thing on our minds.
We wanted to create a box that protects your privacy while surfing the web and we knew that our ambitions would be in vain if we endangered this valuable asset with the mechanisms that were supposed to guard it. For this reason every new feature has to undergo a strict security evaluation before it is rolled out to you. In this process we test the new feature in its entirety and validate that the other security mechanism are still intact.
The following chapter covers these security mechanisms and features and tries to give you additional understanding of our thoughts behind them:

****************
General Security
****************

Unattended Upgrades
===================

The software package unattended-upgrades is responsible for automatically keeping the upribox current with the latest security updates. We configured your upribox in a way that it searches for important updates every day and installs them without the need of any interaction with you.
In more detail the package will perform the follwing tasks:

- update the package lists
- download upgradeable packages
- upgrade packages
- remove downloaded packages that are not available anymore in the sources (every three weeks)


Passwords
=========

If you ordered a fully assembled upribox from our website you will find your passwords for the webinterface, SSH and both WiFis in the included manual. These passwords were generated with a cryptographically secure pseudo-random number generator (CSPRNG) which means that the program that created the passwords used operating system specific randomness sources which leads to high unpredictablity.
Upriboxes that you assembled yourself with the provided community image are pre-configured with passwords that can be changed in the webinterface. Only secure passwords with a minimum of 8 characters containing lower-case, upper-case, numbers and special characters are accpeted by the system.


SSH/VPN Keys
============

When generating a new profile for OpenVPN we create a new pair of certificate (also known as public key) and private key for this profile.
Furthermore, we ensure that every upribox has a different SSH/VPN keys by re-generating them automatically upon the first boot on every bought upribox but also on upriboxes that you built with the community image.

Least Privilege
===============

The upribox architecture follows the principle of least privilege. This means that every part of the system (such as a process, script or user) is only able to access and modify those parts of the system that are necessary for the completion of its tasks.
One example for this implementation is that only the central configuration script *upri-config.py* (see :ref:`django-label`) is able to modify files with root privileges.

*******
Privacy
*******

Logs
====

Your upribox saves log files in memory instead of the SD card. This helps to extend the life time of the card and protects your privacy since data on the RAM disk are deleted regularly.

User Statistics
===============

To calculate the necessary data for the statistics the upribox aggregates and anonymises information by calculating the sum of blocked contents and filtered domains over a specific time. This procedure ensures that nobody can make assumptions about another user's internet behaviour.
Furthermore, the calculated information is only stored on the upribox itself and never leaves it.

************
Cryptography
************

Raspberry Pi Hardware RNG
========================

A common problem with small devices like the upribox is that the hardware and the operating system do not provide enough entropy for a cryptographically secure generation of random numbers. This is a crucial requirement for a fast and secure calculation of keys. The Raspberry Pi has an included random number generator in its hardware. To feed the Raspberry Pi hardware RNG to the entropy pool at */dev/random* that is used in the upribox' Python scripts the package rng-tools is used.

Certificate Pinning
===================

To get the latest filter rules your upribox communicates with our backend server which provides a self-signed SSL certificate to ensure the authenticity of the received updates. Your upribox uses certificate pinning to associate the server with the expected certificate and is so able to detect an attempted attack immediately.

Strong Ciphers/Hashes for OpenVPN
=================================

For the VPN feature of the upribox we use OpenVPN which is *not* executed as root and uses the strong cryptographic hash function SHA384 for the packet HMAC authentication and AES-256 (CBC mode) for encryption.

Signed Releases
===============

On our `website <https://upribox.org/download/>`__ you can download our latest community image and verify its integrity with the provided signature file.
