import redis
from netaddr import IPNetwork
import util


class ApateRedis(object):
    __PREFIX = "apate"
    __DELIMITER = ":"
    __IP = "ip"
    __NETWORK = "net"
    __DB = 5
    __TTL = 259200

    def __init__(self, network, logger):
        self.redis = redis.StrictRedis(host="localhost", port=6379, db=self.__DB)
        self.network = network
        self.logger = logger

    def add_device(self, ip, mac, network=None, enabled=True, force=False):
        if not self._check_device_disabled(ip, network or self.network.network) or force:
            self._add_device_to_network(ip, network or self.network.network)
            return self._add_entry(self._get_device_name(ip, network or self.network.network, enabled=enabled), mac)

    def remove_device(self, ip, network=None, enabled=True):
        self._del_device_from_network(ip, network or self.network.network)
        return self._del_device(self._get_device_name(ip, network or self.network.network, enabled=enabled))

    def get_device_mac(self, ip, network=None, enabled=True):
        return self.redis.get(self._get_device_name(ip, network or self.network.network, enabled=enabled))

    def get_devices(self, network=None):
        return self.redis.smembers(self._get_network_name(network or self.network.network))

    def get_devices_values(self, filter=False, network=None, enabled=True):
        # list may contain null values
        devs = self.get_devices(network=network or self.network.network)
        if not devs:
            return []
        else:
            vals = self.redis.mget([self._get_device_name(dev, network or self.network.network, enabled=True) for dev in devs])

            res = zip(devs, vals)

            return res if not filter else [x for x in res if x[1] and x[1] != str(None)]  # filter(None, res)

    def _add_entry(self, key, value):
        return self.redis.set(key, value, ApateRedis.__TTL)

    def _del_device(self, device):
        return self.redis.delete(device)

    def _get_device_name(self, ip, network, enabled=None):
        if enabled is None:
            return ApateRedis.__DELIMITER.join((ApateRedis.__PREFIX, ApateRedis.__NETWORK, str(network), ApateRedis.__IP, str(ip)))
        else:
            return ApateRedis.__DELIMITER.join((ApateRedis.__PREFIX, ApateRedis.__NETWORK, str(network), ApateRedis.__IP, str(ip), str(int(enabled))))

    def _get_network_name(self, network):
        return ApateRedis.__DELIMITER.join((ApateRedis.__PREFIX, ApateRedis.__NETWORK, str(network)))

    def _add_device_to_network(self, ip, network):
        return self.redis.sadd(ApateRedis.__DELIMITER.join((ApateRedis.__PREFIX, ApateRedis.__NETWORK, str(network))), str(ip))

    def _del_device_from_network(self, ip, network):
        return self.redis.srem(ApateRedis.__DELIMITER.join((ApateRedis.__PREFIX, ApateRedis.__NETWORK, str(network))), str(ip))

    # True if disabled
    def _check_device_disabled(self, ip, network):
        return self.redis.get(self._get_device_name(ip, network, enabled=False)) is not None

    def get_pubsub(self, ignore_subscribe_messages=True):
        return self.redis.pubsub(ignore_subscribe_messages=ignore_subscribe_messages)

    def disable_device(self, ip, network=None):
        self._toggle_device(ip, network or self.network.network, enabled=False)

    def enable_device(self, ip, network=None):
        self._toggle_device(ip, network or self.network.network, enabled=True)

    def _toggle_device(self, ip, network, enabled):
        self.add_device(ip, self.get_device_mac(ip, network, enabled=not enabled), network, enabled=enabled, force=True)
        self.remove_device(ip, network, enabled=not enabled)
