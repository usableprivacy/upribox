import redis
from netaddr import IPNetwork


class ApateRedis(object):
    __PREFIX = "apate"
    __DELIMITER = ":"
    __IP = "ip"
    __NETWORK = "net"
    __DB = 5

    def __init__(self, network):
        self.redis = redis.StrictRedis(host="localhost", port=6379, db=self.__DB)
        self.network = network

    def add_device(self, ip, mac, network=None, enabled=True):
        self._add_device_to_network(ip, network or self.network.network)
        return self._add_entry(self._get_device_name(ip, network or self.network.network, enabled=enabled), mac)

    def remove_device(self, ip, network=None, enabled=True):
        self._del_device_from_network(ip, network or self.network.network)
        return self._del_device(self._get_device_name(ip, network or self.network.network, enabled=enabled))

    def get_devices(self, network=None):
        return self.redis.smembers(self._get_network_name(network or self.network.network))

    def get_devices_values(self, filter=False, network=None, enabled=True):
        # list may contain null values
        devs = self.get_devices(network=network)
        if not devs:
            return []
        else:
            vals = self.redis.mget([self._get_device_name(dev, network or self.network.network, enabled=True) for dev in devs])

            res = zip(devs, vals)

            return res if not filter else [x for x in res if x[1]]  # filter(None, res)

    def _add_entry(self, key, value):
        return self.redis.set(key, value)

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
