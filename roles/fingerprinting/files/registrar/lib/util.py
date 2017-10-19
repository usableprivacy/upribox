import sqlite3
from datetime import datetime

from netaddr import EUI, IPAddress
from netaddr.core import AddrFormatError

_COLUMNS = ['ip', 'mac', 'dhcp_fingerprint', 'dhcp_vendor', 'hostname']
# _COLUMNS = ['ip', 'mac', 'dhcp_fingerprint', 'dhcp_vendor', 'hostname', 'device_name', 'user_agent', 'score']
# _DEFAULT_MODE = "SL"
# _MODE_COLUMN = "mode"
_DEFAULT_VALUES = {"mode": "SL"}

EXCEPTED_MAC = [EUI("00:00:00:00:00:00")]
EXCEPTED_IP = [IPAddress("0.0.0.0")]


def insert_or_update_fingerprint(conn, **kwargs):
    id = None
    if kwargs and kwargs.get("ip", None) and kwargs.get("mac", None):
        params = {key: value for key, value in kwargs.iteritems() if key in _COLUMNS}
        timestamps = {"last_seen": str(datetime.now())}
        try:
            with conn:
                # implicit conn.commit
                c = conn.cursor()
                try:
                    c.execute(
                        "INSERT INTO devices_deviceentry (%s) VALUES (%s)" % (
                            ",".join(params.keys() + _DEFAULT_VALUES.keys() + timestamps.keys()),
                            ",".join("?" * (len(params) + len(_DEFAULT_VALUES) + len(timestamps)))
                        ), params.values() + _DEFAULT_VALUES.values() + timestamps.values()
                    )
                    id = c.lastrowid
                except sqlite3.IntegrityError as sqlie:
                    if "UNIQUE constraint failed: devices_deviceentry.mac" in sqlie.message:
                        c.execute(
                            "UPDATE devices_deviceentry SET %s where mac=?" % ("=?,".join(params.keys() + timestamps.keys()) + "=?", ),
                            params.values() + timestamps.values() + [params['mac']]
                        )
                        c.execute("SELECT id FROM devices_deviceentry WHERE mac=?", (params['mac'], ))
                        try:
                            id = c.fetchone()[0]
                        except (TypeError, IndexError):
                            raise ValueError("Unable to retrieve id of device")
                    else:
                        raise sqlie
        except sqlite3.Error as sqle:
            raise sqle
    else:
        raise TypeError(insert_or_update_fingerprint.__name__ + " needs keyword-only argument ip")

    return id

    # TODO close connection inside function because it is not possible
    # to close conn in another thread
    # closing conn in the sniff_thread is not possible because scapy's sniff blocks for all eternity,
    # other methods are not called inside the child and thread synchronisation on blocked threads is ....
    # also systemexit is not propagated to childs and sending signals to thread is also not possible (without bending reality)


def insert_useragent(conn, useragent, device_id, model=False):
    try:
        with conn:
            # implicit conn.commit
            c = conn.cursor()
            agent_id = None

            try:
                if not model:
                    c.execute("INSERT INTO devices_useragent (agent) VALUES (?)", (useragent, ))
                else:
                    c.execute("INSERT INTO devices_useragent (agent, model) VALUES (?, ?)", (useragent, useragent))
                agent_id = c.lastrowid
            except sqlite3.IntegrityError as sqlie:
                if "UNIQUE constraint failed: devices_useragent.agent" in sqlie.message:
                    c.execute("SELECT id FROM devices_useragent WHERE agent=?", (useragent, ))
                    try:
                        agent_id = c.fetchone()[0]
                    except (TypeError, IndexError):
                        raise ValueError("Unable to retrieve id of useragent string")
                else:
                    raise sqlie

            try:
                if agent_id is not None and device_id is not None:
                    c.execute(
                        "INSERT INTO devices_deviceentry_user_agent (deviceentry_id, useragent_id) values (?, ?)", (str(device_id), str(agent_id))
                    )
            except sqlite3.IntegrityError:
                # entry already exists
                pass

    except sqlite3.Error as sqle:
        raise sqle


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
