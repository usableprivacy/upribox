# Usable Privacy Box
The [upribox](https://upribox) software is used to create Raspberry Pi images to turn your Raspberry Pi into a privacy-enhancing Wireless router. Main features:
 * Transparent blocking of advertisement/tracking (silent wifi)
 * Transparent adblocking + Tor network (ninja wifi)
 * OpenVPN server for privacy on the road

---

# Getting Started
See the [official Raspberry Pi documentation](https://www.raspberrypi.org/documentation/installation/installing-images/) for pointers on how to install the upribox image on the SD card. Upon the first boot the SSH/VPN keys are automatically re-generated (this will take a couple of minutes), and the system partitions are resized to use the entire size of the SD card. In the following you also find a list of recommended (and tested hardware) for the upribox software. Make sure that you use a compatible USB WiFi dongle!

### [upribox-image-v0_1.zip](https://s3-us-west-2.amazonaws.com/usableprivacy/upribox-image-v0_1.zip) (December 2015)
*SHA1Sum: 8a9744050b78a3411972e2758be53c74adfc5da4*

#### Default passwords
**Silent WiFi** (SSID: *upribox* ), **Ninja WiFi** (SSID: *upribox-ninja*), password: *changeme*. **SSH/Webinterface** login: *upri* password: *changethedefaults!*.

#### Webinterface
Once you are connect to either of the upribox wifi networks (Silent or Ninja) you can access the upribox Webinterface via the following URI: [http://upri.box](http://upri.box).


### List of recommended hardware*
* Raspberry Pi 2 [[Amazon.com]](http://amzn.to/1YewXnz) [[Element14]](http://element14.com/raspberrypi2) [[Adafruit]](https://www.adafruit.com/products/2358)
* microSDHC Class 10 (min. 4GB) [[Amazon.com]](http://amzn.to/1YewW33)
* Power supply [[Amazon]](http://amzn.to/1QhAna9) [[Adafruit]](https://www.adafruit.com/products/1995)
* TL-WN722N Wireless USB adapter [[Amazon.com]](http://amzn.to/1I3zG1v)

*The upribox software works with Raspberry Pi 1 as well, but the performance for adblocking is considerable worse. Other potentially suitable USB WiFi hardware can be found in the [Pi(rate)Box Wiki](https://piratebox.cc/raspberry_pi:piratebox_wifi_compatibility).

### Software updates

The upribox performs an auto-update every **four hours**:

* Blocking rules for privoxy and DNS
* Software updates via ansible + updates from github

---

## Development / Reproducibility

The current upribox image is based on the [Raspbian Wheezy image](https://www.raspberrypi.org/downloads/raspbian/) and customized with [ansible](http://www.ansible.com). The Raspbian image can be staged into *production* or *development* mode.

### Prerequisites
* install ansible 1.9.6 (`sudo pip install ansible==1.9.6`)
* make sure to log into your Raspberry via ssh once because ansible uses ~/.ssh/known_hosts for verification (or disable host verification)
* install sshpass (most likely available in your distribution's repositories)
* make sure you have a public/private key pair for ssh on your development machine. ~/.ssh/id_rsa.pub will be automatically added to the authorized_hosts on the Raspberry

### Development Mode
This mode is intended for testing new features and debugging the upribox software. As such log files are persistent and auto software updates are disabled by default.

#### Getting started
* copy environments/development/inventory.sample to environments/development/inventory
* add your RaspberryPi address(es) in the [upriboxes] section in environments/development/inventory
* run the initial setup with `ansible-playbook -i environments/init/inventory setup.yml`
  This command will log into your Raspberry with the default credentials pi/raspberry, create a new user (upri) and delete pi.
  Add `--ask-pass` if you changed the default password.
* from now on, the config can be deployed with `ansible-playbook -i environments/development/inventory site.yml`

#### Production Mode
* copy environments/production/inventory.sample to environments/production/inventory
* add your RaspberryPi address(es) in the [upriboxes] section in environments/production/inventory
* run the initial setup with `ansible-playbook -i environments/init/inventory setup.yml`
  This command will log into your Raspberry with the default credentials pi/raspberry, create a new user (upri) and delete pi.
  Add `--ask-pass` if you changed the default password.
* from now on, the config can be deployed with `ansible-playbook -i environments/production/inventory site.yml`

---

## License
Copyright (C) 2016 [upribox developers](https://upribox.org/#contact)

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
