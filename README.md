[![upribox Homepage](https://upribox.org/wp-content/uploads/2017/05/upribox-icon-logo-1.png)](https://upribox.org/)

### Privacy made easy for the Raspberry Pi 1, 2, and 3

[![Current releases](https://img.shields.io/badge/release-v0.9-brightgreen.svg)](https://github.com/usableprivacy/upribox/releases) [![Documentation Status](https://img.shields.io/badge/docs-latest-blue.svg)](http://upribox.readthedocs.io/en/latest/) [![GPLv3 License](https://img.shields.io/badge/license-GPLv3-yellow.svg)](https://github.com/usableprivacy/upribox/blob/master/LICENSE) [![Median time to resolve an issue](http://isitmaintained.com/badge/resolution/usableprivacy/upribox.svg)](http://isitmaintained.com/project/usableprivacy/upribox) [![Twitter Follow](https://img.shields.io/twitter/follow/usableprivacy.svg?style=social&label=Follow)](https://twitter.com/usableprivacy)

The [upribox](https://upribox.org) software is used to create Raspberry Pi images to turn your Raspberry Pi into a privacy-enhancing Wireless router. Main features:
* Transparent advertisement- and tracker-blocking (silent wifi)
* Transparent adblocking + Tor network (ninja wifi)
* OpenVPN server for privacy on the road

---

# Getting Started
See the [official Raspberry Pi documentation](https://www.raspberrypi.org/documentation/installation/installing-images/) for pointers on how to install the upribox image on the SD card. Upon the first boot the SSH/VPN keys are automatically re-generated (this will take a couple of minutes), and the system partitions are resized to use the entire size of the SD card.
In the following you also find a list of required (and tested hardware) for the upribox software. Make sure that you use a compatible USB WiFi dongle!

### [upribox-image-v0_9.zip](https://github.com/usableprivacy/upribox/releases/download/v0.9/upribox-image-v0_9.zip) (Jun 2017)
*SHA256: 2557a964b02508dcd7e4a9c5d76367ac9aa4db0517551213bec9fea65aad4a0c*

#### Default passwords
* **Silent WiFi** (SSID: *upribox* ), **Ninja WiFi** (SSID: *upribox-ninja*), password: *changeme*
* **SSH/Webinterface** login: *upri* password: *changethedefaults!*

#### Webinterface
Once you are connect to either of the upribox wifi networks (Silent or Ninja) you can access the upribox Webinterface via the following URI: [http://upri.box](http://upri.box).


### List of recommended hardware*
* Raspberry Pi 2/3 [[Amazon.com]](https://www.amazon.com/Raspberry-Pi-RASP-PI-3-Model-Motherboard/dp/B01CD5VC92) [[Element14]](http://element14.com/raspberrypi2) [[Adafruit]](https://www.adafruit.com/products/2358)
* microSDHC Class 10 (min. 4GB) [[Amazon.com]](https://www.amazon.com/SanDisk-MicroSDHC-Standard-Packaging-SDSDQUAN-008G-G4A/dp/B00M55C0VU/)
* Power supply [[Amazon.com]](https://www.amazon.com/Kootek-Universal-Charger-Raspberry-External/dp/B00GWDLJGS) [[Adafruit]](https://www.adafruit.com/products/1995)
* TL-WN722N Wireless USB adapter [[Amazon.com]](https://www.amazon.com/TP-LINK-TL-WN722N-Wireless-Adapter-External/dp/B002SZEOLG)
* Since Version 0.5 of the upribox we support the Pi3 natively, so no additional WiFI dongle is required. Currently the Pi3 Wifi only supports one active Hotspot, therefore you can not yet activate the **Ninja WiFi** on the Pi3.

*The upribox software works with Raspberry Pi 1 as well, but the performance for adblocking is considerable worse. Other potentially suitable USB WiFi hardware can be found in the [Pi(rate)Box Wiki](https://piratebox.cc/raspberry_pi:piratebox_wifi_compatibility).

### Software updates

The upribox performs an auto-update every **four hours**:

* Blocking rules for privoxy and DNS
* Software updates via ansible + updates from github

---

## License
Copyright (C) 2016 [upribox developers](https://upribox.org/#contact)

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
