#!/usr/bin/env python
from os.path import join
from lib.settings import VENV

activate_script = join(VENV, "bin", "activate_this.py")
execfile(activate_script, dict(__file__=activate_script))

from lib import argparser, filter_update, backup
from lib import parser as logparser
from network import wlan, apate, misc, net, device
from vpn import vpn, port_forward, remove_portfwd

import sys
import logging
logging.basicConfig(stream=sys.stdout, level=logging.WARNING)


# add your custom actions here
ALLOWED_ACTIONS = {
    'set_ssid': wlan.action_set_ssid,
    'set_password': wlan.action_set_password,
    'restart_wlan': wlan.action_restart_wlan,
    'enable_silent': wlan.action_set_silent,
    'restart_silent': wlan.action_restart_silent,
    'enable_vpn': vpn.action_set_vpn,
    'set_vpn_connection': vpn.action_set_vpn_connection,
    'set_wlan_channel': wlan.action_set_wlan_channel,
    'restart_vpn': vpn.action_restart_vpn,
    'enable_ssh': misc.action_set_ssh,
    'restart_ssh': misc.action_restart_ssh,
    'enable_apate': apate.action_set_apate,
    'enable_static_ip': net.action_set_static_ip,
    'restart_apate': apate.action_restart_apate,
    'parse_logs': logparser.action_parse_logs,
    'parse_user_agents': logparser.action_parse_user_agents,
    'generate_profile': vpn.action_generate_profile,
    'delete_profile': vpn.action_delete_profile,
    'restart_firewall': net.action_restart_firewall,
    # 'enable_device': apate.action_enable_device,
    # 'disable_device': apate.action_disable_device,
    'set_ip': net.action_set_ip,
    'configure_devices': device.action_configure_devices,
    'set_dns_server': net.action_set_dns_server,
    'set_netmask': net.action_set_netmask,
    'set_gateway': net.action_set_gateway,
    'restart_network': net.action_restart_network,
    'set_dhcpd': net.action_set_dhcpd,
    'restart_dhcpd': net.action_restart_dhcpd,
    'torify_device': device.action_torify_device,
    'exclude_device': device.action_exclude_device,
    'untorify_device': device.action_untorify_device,
    'include_device': device.action_include_device,
    'silent_device': device.action_silent_device,
    'check_device': device.action_check_device,
    'filter_update': filter_update.action_filter_update,
    'vpn_forward': port_forward.action_forward,
    'vpn_unforward': remove_portfwd.action_remove_forward,
    'backup_settings': backup.action_backup,
    "restore_settings": backup.action_restore,
}


# return values:
# 0: ok
# 1: syntax error
# 2: invalid number of arguments
# 3: invalid action


def main():

    parser = argparser.create_argparser()

    args = vars(parser.parse_args())
    # print args
    # append empty second parameter if none given
    if len(args) == 1:
        args['arg'] = ''

    action = args['action']
    subarg = args['arg']

    # check if requested actions is valid
    if action in ALLOWED_ACTIONS:
        print "action: %s" % action
        return ALLOWED_ACTIONS[action](subarg)

if __name__ == "__main__":
    exit(main())
