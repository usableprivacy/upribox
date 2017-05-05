import sqlite3

_COLUMNS = ['ip', 'mac', 'dhcp_fingerprint', 'dhcp_vendor', 'hostname']
# _COLUMNS = ['ip', 'mac', 'dhcp_fingerprint', 'dhcp_vendor', 'hostname', 'device_name', 'user_agent', 'score']


def insert_or_update_fingerprint(conn, logger=None, **kwargs):
    if kwargs and kwargs.get("ip", None) and kwargs.get("mac", None):
        params = {key: value for key, value in kwargs.iteritems() if key in _COLUMNS}

        try:
            with conn:
                # implicit conn.commit
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO devices_deviceentry (%s) VALUES (%s)" % (",".join(params.keys()), ",".join("?" * len(params))), params.values())
                except sqlite3.IntegrityError as sqlie:
                    if "UNIQUE constraint failed: devices_deviceentry.mac" in sqlie.message:
                        c.execute("UPDATE devices_deviceentry SET %s where mac=?" % ("=?,".join(params.keys()) + "=?",), params.values() + [params['mac']])
                    else:
                        raise sqlie
        except sqlite3.Error as sqle:
            if logger:
                logger.exception(sqle)
            else:
                raise sqle
    else:
        if logger:
            logger.error(insert_or_update_fingerprint.__name__ + "needs keyword-only argument ip")
        raise TypeError(insert_or_update_fingerprint.__name__ + "needs keyword-only argument ip")

    # TODO close connection inside function because it is not possible
    # to close conn in another thread
    # closing conn in the sniff_thread is not possible because scapy's sniff blocks for all eternity,
    # other methods are not called inside the child and thread synchronisation on blocked threads is ....
    # also systemexit is not propagated to childs and sending signals to thread is also not possible (without bending reality)


class DaemonError(Exception):
    """This error class indicates, that the daemon has failed."""
    pass
