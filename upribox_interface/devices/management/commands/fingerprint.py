#!/usr/bin/env python
# coding=utf-8
from django.core.management.base import NoArgsCommand
from devices.models import DeviceEntry
from user_agents import parse

#
# parse user-agent for device name
#
class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        print "Starting fingerprinting devices..."
        for device in DeviceEntry.objects.all().iterator():
            print "Fingerprinting device with IP/MAC " + device.ip + "/" + device.mac + " ...\n"
            for ua_entry in device.user_agent.all().iterator():
                print "Parsing User-Agent \"" + ua_entry.agent + "\" ..."
                user_agent = parse(ua_entry.agent)
                print "   Browser: " + str(user_agent.browser) + "\n   OS: " + str(user_agent.os) + "\n   Device: " + str(user_agent.device) + "\n"
                model = user_agent.device.model
                if device:
                    ua_entry.model = model
                else:
                    print "Ignore this device name ..."