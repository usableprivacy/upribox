# coding=utf-8
"""This module provides the ApateRedis class for managing the Apate Redis DB."""
import redis


class ApateRedis(object):
    """This class is used to manage the Apate Redis DB."""
    __PREFIX = "apate"
    """str: Prefix which is used for every key in the redis db."""
    __DELIMITER = "|"
    """str: Delimiter used for separating parts of keys in the redis db."""
    __IP = "ip"
    """str: Indicator for the IP part of the redis key."""
    __NETWORK = "net"
    """str: Indicator for the network address part of the redis key."""
    __DB = 5
    """int: Redis db which should be used."""
    __TTL = 259200
    """int: Time after which device entries in the redis db expire. (default=3 days)"""
    # __TOGGLED_KEY = __DELIMITER.join((__PREFIX, "toggle"))

    def __init__(self, network, logger):
        """Initialises ApateRedis objects. A connection to the local redis server
        on port 6379 using the database, which is specified by __DB, is established.

        Args:
            network (str): Network IP Address, which should be used per default.
            logger (logging.Logger): Used for logging messages.

        """
        self.redis = redis.StrictRedis(host="localhost", port=6379, db=self.__DB)
        self.network = network
        self.logger = logger

    def add_device(self, ip, mac, network=None, enabled=True, force=False):
        """Adds a device entry to the redis db. Checks if a disabled entry exists,
        if not adds the device to the network redis set and adds a device entry.
        Added devices are automatically removed after __TTL expires.

        Args:
            ip (str): IP address of the device.
            mac (str): MAC (layer 2) address of the device.
            network (str, optional): Network address of the device. If not set, self.network is used instead.
            enabled (bool, optional): Determines if the device should be enabled or disabled. Defaults to True.
            force (bool, optional): Switch used to force the insertion of the device entry (even if a disabled entry already exists).
                Defaults to False.

        Return:
            bool: True if successful, false otherwise.

        """
        # TODO make thread-safe
        if not self.check_device_disabled(ip, network or self.network) or force:
            self._add_device_to_network(ip, network or self.network)
            return self._add_entry(self._get_device_name(ip, network or self.network, enabled=enabled), mac)

    def remove_device(self, ip, network=None, enabled=True):
        """Removes a device from the network redis set and deletes the device entry.

        Args:
            ip (str): IP address of the device.
            network (str, optional): Network address of the device. If not set, self.network is used instead.
            enabled (bool, optional): Determines if the device is enabled or disabled. Defaults to True.

        Results:
            int: Number of devices deleted.

        """
        self._del_device_from_network(ip, network or self.network)
        return self._del_device(self._get_device_name(ip, network or self.network, enabled=enabled))

    def get_device_mac(self, ip, network=None, enabled=True):
        """Returns the mac address (value from the redis db) of the device.

        Args:
            ip (str): IP address of the device.
            network (str, optional): Network address of the device. If not set, self.network is used instead.
            enabled (bool, optional): Determines if the device is enabled or disabled. Defaults to True.

        Returns:
            The mac address of the specified device as str if successful, None otherwise.

        """
        return self.redis.get(self._get_device_name(ip, network or self.network, enabled=enabled))

    def get_devices(self, network=None):
        """Returns a list with ip addresses of devices of the specified network.

        Args:
            network (str, optional): Network address of the device. If not set, self.network is used instead.

        Returns:
            List containing device ip addresses if successful, None otherwise.

        """
        return self.redis.smembers(self._get_network_name(network or self.network))

    def get_devices_values(self, filter_values=False, network=None, enabled=True):
        """Returns a list with tuples containing ip addresses of devices and the mac addresses of
        the devices.

        Args:
            filter_values (bool, optional): Determines if str(None) values should be filtered. Defaults to False.
            network (str, optional): Network address of the device. If not set, self.network is used instead.
            enabled (bool, optional): Determines if the device is enabled or disabled. Defaults to True.

        Returns:
            list: List with tuples containing ip addresses of devices and the mac addresses of
            the devices. May contain str(None) values, if there is no device entry
            for the according ip address and filter_values = False.
            E.g.:
            {"192.168.0.1": "11:22:33:44:55:66", "192.168.0.2": "None"}

        """
        # list may contain null values
        devs = self.get_devices(network=network or self.network)
        if not devs:
            return []
        else:
            vals = self.redis.mget([self._get_device_name(dev, network or self.network, enabled=enabled) for dev in devs])
            res = zip(devs, vals)
            # filter "None" entries if filter_values is True
            return res if not filter_values else [x for x in res if x[1] and x[1] != str(None)]  # filter(None, res)

    def get_pubsub(self, ignore_subscribe_messages=True):
        """Used to get a PubSub object.

        Args:
            ignore_subscribe_messages (bool, optional): Determines if subscriptions messages should be ignored. Defaults to True.

        Returns:
            redis.PubSub: PubSub object, which can be used to subscribe to redis messages.

        """
        return self.redis.pubsub(ignore_subscribe_messages=ignore_subscribe_messages)

    def disable_device(self, ip, network=None):
        """Disables an enabled device in the redis db.
        An enabled entry "apate:net:192.168.0.0:ip:192.168.0.1:1"
        afterwards looks like this "apate:net:192.168.0.0:ip:192.168.0.1:0"

        Args:
            ip (str): IP address of the device.
            network (str, optional): Network address of the device. If not set, self.network is used instead.

        """
        self._toggle_device(ip, network or self.network, enabled=False)

    def enable_device(self, ip, network=None):
        """Enables a disabled device in the redis db.
        An enabled entry "apate:net:192.168.0.0:ip:192.168.0.1:0"
        afterwards looks like this "apate:net:192.168.0.0:ip:192.168.0.1:1"

        Args:
            ip (str): IP address of the device.
            network (str, optional): Network address of the device. If not set, self.network is used instead.

        """
        self._toggle_device(ip, network or self.network, enabled=True)

    def get_database(self):
        """Returns the currently selected redis database.

        Return:
            int: number of selected database

        """
        return self.__DB

    def get_toggled_key(self, network=None):
        # return self.__TOGGLED_KEY
        return self.__DELIMITER.join((self.__PREFIX, "toggle", self.__NETWORK, network or self.network))

    def pop_toggled(self, network=None):
        devs = list(self.redis.smembers(self.get_toggled_key(network=network or self.network)))
        try:
            self.redis.srem(self.get_toggled_key(network=network or self.network), *devs)
        except Exception as e:
            self.logger.exception(e)
        return devs

    def _add_entry(self, key, value):
        # inserted keys expire after __TTL
        return self.redis.set(key, value, ApateRedis.__TTL)

    def _del_device(self, device):
        return self.redis.delete(device)

    @staticmethod
    def _get_device_name(ip, network, enabled=None):
        # example for the return value
        # ip = "192.168.0.1", network = "192.168.0.0", enabled = True  -->  "apate|net|192.168.0.0|ip|192.168.0.1|1"
        if enabled is None:
            # don't include the enabled-section (e.g.: "apate|net|192.168.0.0|ip|192.168.0.1")
            return ApateRedis.__DELIMITER.join((ApateRedis.__PREFIX, ApateRedis.__NETWORK, str(network), ApateRedis.__IP, str(ip)))
        else:
            return ApateRedis.__DELIMITER.join((ApateRedis.__PREFIX, ApateRedis.__NETWORK, str(network), ApateRedis.__IP, str(ip), str(int(enabled))))

    @staticmethod
    def _get_network_name(network):
        # e.g.: network = "192.168.0.0"  -->  "apate|net|192.168.0.0"
        return ApateRedis.__DELIMITER.join((ApateRedis.__PREFIX, ApateRedis.__NETWORK, str(network)))

    def _add_device_to_network(self, ip, network):
        """Adds an IP address to a network (redis set)."""
        return self.redis.sadd(ApateRedis.__DELIMITER.join((ApateRedis.__PREFIX, ApateRedis.__NETWORK, str(network))), str(ip))

    def _del_device_from_network(self, ip, network):
        """Removes an IP address from a network (redis set)."""
        return self.redis.srem(ApateRedis.__DELIMITER.join((ApateRedis.__PREFIX, ApateRedis.__NETWORK, str(network))), str(ip))

    def check_device_disabled(self, ip, network=None):
        # True if devices is disabled
        return self.redis.get(self._get_device_name(ip, network or self.network, enabled=False)) is not None

    def _toggle_device(self, ip, network, enabled):
        # add new device first and delete old device afterwards
        # this is done to avoid race conditions
        self.add_device(ip, self.get_device_mac(ip, network, enabled=not enabled), network, enabled=enabled, force=True)
        self.remove_device(ip, network, enabled=not enabled)
        try:
            self.redis.sadd(self.get_toggled_key(network=network), self._get_device_name(ip, network, enabled=enabled))
        except Exception as e:
            self.logger.exception(e)
