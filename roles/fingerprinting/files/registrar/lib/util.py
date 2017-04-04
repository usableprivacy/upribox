import sqlite3

_COLUMNS = ['ip', 'mac', 'dhcp_fingerprint', 'dhcp_vendor', 'hostname', 'device_name', 'user_agent', 'final']


def insert_or_update_fingerprint(conn, logger=None, **kwargs):
    if kwargs and kwargs.get("ip", None):
        params = {key: value for key, value in kwargs.iteritems() if key in _COLUMNS}

        try:
            with conn:
                # implicit conn.commit
                c = conn.cursor()
                c.execute("SELECT final FROM devices_deviceentry WHERE ip=?", (params['ip'],))
                data = c.fetchone()
                if not data:
                    c.execute("INSERT INTO devices_deviceentry (%s) VALUES (%s)" % (",".join(params.keys()), ",".join("?" * len(params))), params.values())
                elif not data[0]:
                    # if entry not final
                    # if not data[0] and len(parts[1]) > 1:
                    c.execute("UPDATE devices_deviceentry SET %s where ip=?" % ("=?,".join(params.keys()) + "=?",), params.values() + [params['ip']])
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
