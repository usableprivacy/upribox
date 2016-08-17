#!/usr/bin/env python
# coding=utf-8
"""This script is used to control the Apate ARP spoofing daemon."""
import logging
import sys
import signal
import os
import json
import lockfile

from daemon import runner

from lib import daemon_app

CONFIG_FILE = "/etc/apate/config.json"
"""Path of the config file for the Apate ARP spoofing daemon."""
CONFIG_OPTIONS = ('logfile', 'pidfile', 'interface', 'stderr', 'stdout', 'mode')
"""Options that need to be present in the config file."""


def main():
    """This script is used to initialise and command the Apate ARP spoofing daemon.
    It parses the configuration file at CONFIG_FILE and checks for the necessary Options
    CONFIG_OPTIONS. The daemon needs to be run as root.
    """
    # check if run as root
    if os.geteuid() != 0:
        print "This daemon needs to be run as root"
        sys.exit(1)

    # parse configuration file
    try:
        with open(CONFIG_FILE) as config:
            data = json.load(config)
    except ValueError as ve:
        print "Could not parse the configuration file"
        print str(ve)
        sys.exit(3)
    except IOError as ioe:
        print "An error occurred while trying to open the configuration file"
        print str(ioe)
        sys.exit(4)

    # check if all necessary options are present in config file
    if not all(val in data for val in CONFIG_OPTIONS):
        print "The configuration file does not include all necessary options"
        sys.exit(2)

    # set up logger for daemon
    logger = logging.getLogger("DaemonLog")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(data['logfile'])
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # catch error which could arise during initialisation
    try:
        # when configured to use the holistic spoofing mode
        if data['mode'] == "holistic":
            dapp = daemon_app.HolisticDaemonApp(logger, str(data['interface']), data['pidfile'], data['stdout'], data['stderr'])
        else:
            # selective spoofing mode is default
            dapp = daemon_app.SelectiveDaemonApp(logger, str(data['interface']), data['pidfile'], data['stdout'], data['stderr'])
    except Exception as e:
        logger.error("An error happened during initialsising the daemon process - terminating process")
        logger.exception(e)
        sys.exit(1)

    # intialise daemon
    daemon_runner = runner.DaemonRunner(dapp)
    # don't close logfile
    daemon_runner.daemon_context.files_preserve = [handler.stream]
    # start cleanup routine when stopping the daemon
    daemon_runner.daemon_context.signal_map[signal.SIGTERM] = dapp.exit

    # command daemon
    try:
        daemon_runner.do_action()
    except runner.DaemonRunnerError as dre:
        print str(dre)
    except lockfile.LockTimeout as lt:
        # runner only catches AlreadyLocked, which is not thrown if a timeout was specified other than None or 0
        # Following is thrown otherwise and slips through:
        # LockTimeout: Timeout waiting to acquire lock for /var/run/apate/apate.pid
        # though this should not be logged as an exception

        # restart fails if timeout is set to 0 or None
        print str(lt)
    except Exception as e:
        # log stacktrace of exceptions that should not occur to logfile
        logger.error("Exception at do_action()")
        logger.exception(e)


if __name__ == "__main__":
    main()
