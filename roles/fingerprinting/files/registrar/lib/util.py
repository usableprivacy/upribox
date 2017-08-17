import sqlite3
from netaddr import IPAddress, EUI
from netaddr.core import AddrFormatError

_COLUMNS = ['ip', 'mac', 'dhcp_fingerprint', 'dhcp_vendor', 'hostname']
# _COLUMNS = ['ip', 'mac', 'dhcp_fingerprint', 'dhcp_vendor', 'hostname', 'device_name', 'user_agent', 'score']
# _DEFAULT_MODE = "SL"
# _MODE_COLUMN = "mode"
_DEFAULT_VALUES = {
    "mode": "SL"
}

EXCEPTED_MAC = [EUI("00:00:00:00:00:00")]
EXCEPTED_IP = [IPAddress("0.0.0.0")]

def insert_or_update_fingerprint(conn, **kwargs):
    if kwargs and kwargs.get("ip", None) and kwargs.get("mac", None):
        params = {key: value for key, value in kwargs.iteritems() if key in _COLUMNS}

        try:
            with conn:
                # implicit conn.commit
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO devices_deviceentry (%s) VALUES (%s)" %
                              (",".join(params.keys() + _DEFAULT_VALUES.keys()), ",".join("?" * (len(params) + len(_DEFAULT_VALUES)))), params.values() + _DEFAULT_VALUES.values())
                except sqlite3.IntegrityError as sqlie:
                    if "UNIQUE constraint failed: devices_deviceentry.mac" in sqlie.message:
                        c.execute("UPDATE devices_deviceentry SET %s where mac=?" % ("=?,".join(params.keys()) + "=?",), params.values() + [params['mac']])
                    else:
                        raise sqlie
        except sqlite3.Error as sqle:
            raise sqle
    else:
        raise TypeError(insert_or_update_fingerprint.__name__ + " needs keyword-only argument ip")

    # TODO close connection inside function because it is not possible
    # to close conn in another thread
    # closing conn in the sniff_thread is not possible because scapy's sniff blocks for all eternity,
    # other methods are not called inside the child and thread synchronisation on blocked threads is ....
    # also systemexit is not propagated to childs and sending signals to thread is also not possible (without bending reality)

def check_preconditions(ip, mac):
    try:
        ip = IPAddress(ip)
        mac = EUI(mac)
    except (AddrFormatError, TypeError):
        return False

    if ip in EXCEPTED_IP or mac in EXCEPTED_MAC:
        return False

    return True

class DaemonError(Exception):
    """This error class indicates, that the daemon has failed."""
    pass
