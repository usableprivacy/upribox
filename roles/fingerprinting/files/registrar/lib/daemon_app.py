# coding=utf-8
"""This module provides several classes that are used to implement a ARP spoofing daemon.

Classes:
    _DaemonApp: Abstract class, that should be inherited.
    HolisticDaemonApp: Inherits _DaemonApp and implements the holistist spoofing mode.
    SelectiveDaemonApp: Inherits _DaemonApp and implements the selective spoofing mode.
    DaemonError: Error that indicates the daemon's failure.

"""
import logging
import os
import threading
import time

from misc_thread import SSDPDiscoveryThread
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import conf
from sniff_thread import RegistrarSniffThread, _SniffThread

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)


class DaemonApp(object):
    """This is an abstract class, which should be inherited to define the
    Apate daemon's behaviour."""

    def __init__(self, logger, config):
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
        self.stdout_path = config['stdout']
        self.stderr_path = config['stderr']
        self.pidfile_path = config['pidfile']
        self.pidfile_timeout = 5
        # self.pidfile_timeout = 0

        self.logger = logger
        self.interface = None if config['interface'].lower() == 'all' else config['interface']
        self.django_db = config['django-db']

        # self.sniffthread = RegistrarSniffThread(self.interface, logger, self.django_db)
        # self.sniffthread.daemon = True
        self.sleeper = threading.Condition()

        self.threads = {}
        # Initialise threads
        self.threads['sniffthread'] = RegistrarSniffThread(self.interface, logger, self.django_db)
        self.threads['ssdpthread'] = SSDPDiscoveryThread(self.interface)

        # declare all threads as deamons
        for worker in self.threads:
            self.threads[worker].daemon = True

    def exit(self, signal_number, stack_frame):
        """This method is called if the daemon stops."""
        # self.sniffthread.stop()
        # with self.sleeper:
        #     self.sleeper.notify_all()
        # self.sniffthread.stop()
        raise SystemExit()

    def run(self):
        """This method should be overriden to define the daemon's behaviour."""
        # try:
        # self.sniffthread.start()
        for worker in self.threads:
            self.threads[worker].start()
        while True:
            # do some regular work here
            time.sleep(60)
            # except SystemExit as se:
            #     self.logger.info("sysexit")
            #     self.logger.info(str(threading.enumerate()))
            #     for thr in threading.enumerate():
            #         if isinstance(thr, _SniffThread):
            #             thr.stop()
            #     raise se
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
