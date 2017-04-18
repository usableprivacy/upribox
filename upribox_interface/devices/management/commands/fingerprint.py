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
            print "Fingerprinting device with IP/MAC %s/%s ...\n" % (device.ip, device.mac)
            for ua_entry in device.user_agent.filter(model=None).iterator():
                print "Parsing User-Agent \"%s\" ..." % (ua_entry.agent)
                user_agent = parse(ua_entry.agent)
                print "   Browser: %s\n   OS: %s\n   Device: %s\n" % (str(user_agent.browser), str(user_agent.os), str(user_agent.device))
                model = user_agent.device.model
                brand = user_agent.device.brand
                family = user_agent.os.family
                name = ""
                if model:
                    if brand and "Generic" not in brand:
                        name = brand + " "
                    name = name + model
                    print "Chosen device name: \"%s\"\n" % (name)
                    ua_entry.model = name
                    ua_entry.save()
                elif family and family != "Other":
                    print "Chosen device name: \"%s\"\n" % (family)
                    ua_entry.model = family
                    ua_entry.save()
                else:
                    print "No proper device name found for this device\n"