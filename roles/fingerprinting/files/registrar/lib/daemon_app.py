# coding=utf-8
"""This module provides several classes that are used to implement a ARP spoofing daemon.

Classes:
    _DaemonApp: Abstract class, that should be inherited.
    HolisticDaemonApp: Inherits _DaemonApp and implements the holistist spoofing mode.
    SelectiveDaemonApp: Inherits _DaemonApp and implements the selective spoofing mode.
    DaemonError: Error that indicates the daemon's failure.

"""
import os
import logging
import time
import threading

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import conf

from sniff_thread import RegistrarSniffThread


class DaemonApp(object):
    """This is an abstract class, which should be inherited to define the
    Apate daemon's behaviour."""

    def __init__(self, logger, interface, pidfile, stdout, stderr):
        """Initialises several things needed to define the daemons behaviour.

        Args:
            logger (logging.Logger): Used for logging messages.
            interface (str): The network interface which should be used. (e.g. eth0)
            pidfile (str): Path of the pidfile, used by the daemon.
            stdout (str): Path of stdout, used by the daemon.
            stderr (str): Path of stderr, used by the daemon.
            dns_file (str): Path of file containing the nameservers.

        Raises:
            DaemonError: Signalises the failure of the daemon.
        """
        # disable scapys verbosity global
        conf.verb = 0

        self.stdin_path = os.devnull
        self.stdout_path = stdout
        self.stderr_path = stderr
        self.pidfile_path = pidfile
        self.pidfile_timeout = 5
        # self.pidfile_timeout = 0

        self.logger = logger
        self.interface = interface

        self.sniffthread = RegistrarSniffThread(self.interface, logger)
        self.sniffthread.daemon = True
        self.sleeper = threading.Condition()

    def exit(self, signal_number, stack_frame):
        """This method is called if the daemon stops."""
        #self.sniffthread.stop()
        # with self.sleeper:
        #     self.sleeper.notify_all()
        raise SystemExit()

    def run(self):
        """This method should be overriden to define the daemon's behaviour."""
        self.sniffthread.start()
        while True:
            # do some regular work here
            time.sleep(60)
        # self.sniffthread.join()
        # try:
        #     with self.sleeper:
        #         self.sleeper.wait()
        # except RuntimeError as e:
        #     # this error is thrown by the with-statement when the thread is stopped
        #     if len(e.args) > 0 and e.args[0] == "cannot release un-acquired lock":
        #         return
        #     else:
        #         raise e


class DaemonError(Exception):
    """This error class indicates, that the daemon has failed."""
    pass
