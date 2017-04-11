#!/usr/bin/env python
# coding=utf-8
from django.core.management.base import NoArgsCommand
from devices.models import DeviceEntry, DeviceName, UserAgent
from user_agents import parse

#
# parse user-agent for device name
#
class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        print "Starting fingerprinting devices..."
        for device in DeviceEntry.objects.all().iterator():
            print "Fingerprinting device with IP " + device.ip + " ...\n"
            for ua_string in device.user_agent.all().iterator():
                print "Parsing User-Agent \"" + ua_string + "\" ..."
                user_agent = parse(ua_string)
                print "   Browser: " + user_agent.browser + "\n    OS: " + user_agent.os + "\n   Device: " + user_agent.device + "\n"
                model = user_agent.device.model
                if device != "Other":
                    device_name = DeviceName(name=model)
                    device_name.save()
                    device.add(device_name)
                else:
                    print "Ignore this device name ..."