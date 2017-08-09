#!/usr/bin/env python
import argcomplete
import argparse


def boolean_completer(prefix, parsed_args, **kwargs):
    return ["yes", "no"]


def create_argparser():

    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(title='Actions',
                                      description='Actions cover tasks that are able to modify the configuration of the upribox',
                                      help='This script accepts the name of an action that shall be executed',
                                      dest='action')

    # create the parser for the "set_ssid" command
    parser_set_ssid = subparser.add_parser('set_ssid',
                                           help='Sets a new SSID for the Silent WiFi by writing to the fact *wlan*')
    parser_set_ssid.add_argument('arg', help='The SSID for the Silent WiFi', metavar="ssid")

    # create the parser for the "set_password" command
    parser_set_password = subparser.add_parser('set_password',
                                               help='Sets a new password for the Silent WiFi by writing to the fact *wlan*')
    parser_set_password.add_argument('arg', help='The SSID for the Silent WiFi', metavar="password")

    # create the parser for the "restart_wlan" command
    subparser.add_parser('restart_wlan', help='Triggers the Ansible tasks with the tag *ssid*')

    # create the parser for the "enable_silent" command
    parser_enable_silent = subparser.add_parser('enable_silent',
                                                help='Enables/disables the Silent WiFi by writing to the fact *wlan*')
    parser_enable_silent.add_argument('arg', help='Whether or not Silent WiFi is enabled ("yes" or "no")',
                                      metavar="boolean", choices=["yes", "no"]).completer = boolean_completer

    # create the parser for the "restart_silent" command
    subparser.add_parser('restart_silent', help='Triggers the Ansible tasks with the tag *toggle_silent*')

    # create the parser for the "enable_vpn" command
    parser_enable_vpn = subparser.add_parser('enable_vpn', help='Enables/disables the VPN by writing to the fact *vpn*')
    parser_enable_vpn.add_argument('arg', help='Whether or not VPN is enabled ("yes" or "no")', metavar="boolean", choices=["yes", "no"]).completer = boolean_completer

    # create the parser for the "set_vpn_connection" command
    parser_set_vpn_connection = subparser.add_parser('set_vpn_connection',
                                                     help='Sets a custom port and protocol for the upribox OpenVPN server by writing to the fact *vpn*')
    parser_set_vpn_connection.add_argument('arg',
                                           help='The port and protocol used for the OpenVPN server (usage: "1194/udp")',
                                           metavar="port_protocol")

    # create the parser for the "set_wlan_channel" command
    parser_set_wlan_channel = subparser.add_parser('set_wlan_channel',
                                                   help='Sets a new WiFi channel for the Silent WiFi by writing to the fact *wlan*')
    parser_set_wlan_channel.add_argument('arg', help='The channel for the Silent WiFi', metavar="channel")

    # create the parser for the "restart_vpn" command
    subparser.add_parser('restart_vpn', help='Triggers the Ansible tasks with the tag *toggle_vpn*')

    # create the parser for the "enable_ssh" command
    parser_enable_ssh = subparser.add_parser('enable_ssh', help='Enables/disables the ssh by writing to the fact *ssh*')
    parser_enable_ssh.add_argument('arg', help='Whether or not SSH is enabled ("yes" or "no")', metavar="boolean", choices=["yes", "no"]).completer = boolean_completer

    # create the parser for the "restart_ssh" command
    subparser.add_parser('restart_ssh', help='Triggers the Ansible tasks with the tag *toggle_ssh*')

    # create the parser for the "enable_apate" command
    parser_enable_apate = subparser.add_parser('enable_apate',
                                               help='Enables/disables the Apate (see arp) by writing to the fact *apate*')
    parser_enable_apate.add_argument('arg', help='Whether or not Apate is enabled ("yes" or "no")', metavar="boolean", choices=["yes", "no"]).completer = boolean_completer

    # create the parser for the "enable_static_ip" command
    parser_enable_static_ip = subparser.add_parser('enable_static_ip',
                                                   help='Sets the upribox to DHCP or static IP mode by writing to the fact *interfaces*')
    parser_enable_static_ip.add_argument('arg', help='Whether or not a static IP is enabled ("yes" or "no")',
                                         metavar="boolean", choices=["yes", "no"]).completer = boolean_completer

    # create the parser for the "restart_apate" command
    subparser.add_parser('restart_apate', help='Triggers the Ansible tasks with the tag *toggle_apate*')

    # create the parser for the "parse_logs" command
    subparser.add_parser('parse_logs', help='Parses the log files of the services  and aggregates the statistics data')

    # create the parser for the "parse_user_agents" command
    subparser.add_parser('parse_user_agents',
                         help='Parses the log file of the service squid containing MAC addresses, IP addresses and user-agents and saves the gathered information into the database')

    # create the parser for the "generate_profile" command
    parser_generate_profile = subparser.add_parser('generate_profile',
                                                   help='Generates openvpn client certificates and saves the generated openvpn client configuration into the database')
    parser_generate_profile.add_argument('arg',
                                         help='The profile ID of a profile that was created in the web interface',
                                         metavar="profile_id")

    # create the parser for the "delete_profile" command
    parser_delete_profile = subparser.add_parser('delete_profile',
                                                 help='Revokes previously generated openvpn client certificates')
    parser_delete_profile.add_argument('arg', help='The profile ID of a profile that was created in the web interface',
                                       metavar="profile_id")

    # create the parser for the "restart_firewall" command
    subparser.add_parser('restart_firewall', help='Triggers the Ansible tasks with the tag *iptables*')

    # # create the parser for the "enable_device" command
    # parser_enable_device = subparser.add_parser('enable_device',
    #                                             help='Enables ARP spoofing via Apate (see arp) for a specific device')
    # parser_enable_device.add_argument('arg', help='The IP address of the device that shall be enabled', metavar="ip")
    #
    # # create the parser for the "disable_device" command
    # parser_disable_device = subparser.add_parser('disable_device',
    #                                              help='Disables ARP spoofing via Apate (see arp) for a specific device')
    # parser_disable_device.add_argument('arg', help='The IP address of the device that shall be disabled', metavar="ip")

    # create the parser for the "set_ip" command
    parser_set_ip = subparser.add_parser('set_ip', help='Sets a static IP by writing to the fact *interfaces*')
    parser_set_ip.add_argument('arg', help='The static IP address for the upribox', metavar="ip")

    # create the parser for the "configure_devices" command
    subparser.add_parser('configure_devices', help='Triggers the Ansible tasks with the tag *configure_devices*')

    # create the parser for the "set_dns_server" command
    parser_set_dns_server = subparser.add_parser('set_dns_server',
                                                 help='Sets the DNS server by writing to the fact *interfaces*')
    parser_set_dns_server.add_argument('arg', help='The DNS server for the upribox', metavar="dns")

    # create the parser for the "set_netmask" command
    parser_set_netmask = subparser.add_parser('set_netmask', help='Sets subnetmask by writing to the fact *interfaces*')
    parser_set_netmask.add_argument('arg', help='The subnetmask for the upribox', metavar="netmask")

    # create the parser for the "set_gateway" command
    parser_set_gateway = subparser.add_parser('set_gateway',
                                              help='Sets the gateway by writing to the fact *interfaces*')
    parser_set_gateway.add_argument('arg', help='The gateway for the upribox', metavar="gateway")

    # create the parser for the "restart_network" command
    subparser.add_parser('restart_network', help='Triggers the Ansible tasks with the tag *network_config*')

    # create the parser for the "set_dhcpd" command
    parser_set_dhcpd = subparser.add_parser('set_dhcpd',
                                            help='Enables/disables the DHCP server by writing to the fact *dhcpd*')
    parser_set_dhcpd.add_argument('arg', help='Whether or not the upribox acts as a DHCP server ("yes" or "no")',
                                  metavar="boolean", choices=["yes", "no"]).completer = boolean_completer

    # create the parser for the "restart_dhcpd" command
    subparser.add_parser('restart_dhcpd', help='Triggers the Ansible tasks with the tag *dhcp_server*')

    # create the parser for the "torify_device" command
    parser_torify_device = subparser.add_parser('torify_device', help='Adds iptables rule to torify a specific device')
    parser_torify_device.add_argument('arg',
                                      help='The MAC address of the device whose traffic shall be routed over the tor network',
                                      metavar="mac")

    # create the parser for the "exclude_device" command
    parser_exclude_device = subparser.add_parser('exclude_device',
                                                 help='Adds iptables rule to disable ad-blocking for a specific device')
    parser_exclude_device.add_argument('arg', help='The MAC address of the device whose traffic shall not be ad-blocked',
                                       metavar="mac")

    # create the parser for the "untorify_device" command
    parser_untorify_device = subparser.add_parser('untorify_device',
                                                  help='Removes iptables rule to untorify a specific device')
    parser_untorify_device.add_argument('arg',
                                        help='The MAC address of the device whose traffic shall not be routed over the tor network',
                                        metavar="mac")

    # create the parser for the "include_device" command
    parser_include_device = subparser.add_parser('include_device',
                                                 help='Removes iptables rule to enable ad-blocking for a specific device')
    parser_include_device.add_argument('arg', help='The MAC address of the device whose traffic shall be ad-blocked',
                                       metavar="mac")

    # create the parser for the "silent_device" command
    parser_silent_device = subparser.add_parser('silent_device',
                                                help='Shortcut for calling of include_device and untorify_device')
    parser_silent_device.add_argument('arg', help='The MAC address of the device whose mode shall be set to silent',
                                      metavar="mac")

    # create the parser for the "check_device" command
    parser_check_device = subparser.add_parser('check_device', help='Checks if device with given ip address is online')
    parser_check_device.add_argument('arg',
                                     help='The IP address of the device to check',
                                     metavar="ip")

    # create the parser for the "filter_update" command
    subparser.add_parser('filter_update', help='updates the filter files')

    # create the parser for the "vpn_forward" command
    parser_vpn_forward = subparser.add_parser('vpn_forward', help='enables vpn port forwarding if possible')
    parser_vpn_forward.add_argument('--debug', action='store_true', help='Print additional debug messages', dest="arg")

    parser_vpn_unforward = subparser.add_parser('vpn_unforward', help='removes vpn port forwarding')
    parser_vpn_unforward.add_argument('--debug', action='store_true', help='Print additional debug messages', dest="arg")

    subparser.add_parser('backup_settings', help='Saves settings and logs to a backup archive')

    parser_restore = subparser.add_parser('restore_settings', help="Restore settings from backup archive")
    parser_restore.add_argument('arg', help='The path of the backup archive',
                                metavar="path")

    argcomplete.autocomplete(parser)

    return parser
