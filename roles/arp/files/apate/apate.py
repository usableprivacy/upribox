from lib import daemon_app
from daemon import runner
import logging
import sys
import signal
import lockfile
import os


def main():

    if os.geteuid() != 0:
        print "This daemon needs to be run as root"
        sys.exit(1)

    # set up logger for daemon
    logger = logging.getLogger("DaemonLog")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler("/var/log/log/apate/apate.log")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # this should be in config file
    interface = "eth0"

    # catch error with could arise during initialisation
    try:
        dapp = daemon_app.DaemonApp(logger, interface)
    except Exception as e:
        logger.error("An error happened during initialsising the daemon process - terminating process")
        logger.exception(e)
        sys.exit(1)

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
        print str(lt)
    except Exception:
        # log stacktrace of exceptions that should not occur to logfile
        logger.exception("Exception at do_action()")

        # runner only catches AlreadyLocked, which is not thrown if a timeout was specified other than None or 0
        # Following is thrown otherwise and slips through:
        # LockTimeout: Timeout waiting to acquire lock for /var/run/apate/apate.pid
        # though this should not be logged as an exception

        # restart fails if timeout is set to 0 or None

if __name__ == "__main__":
    main()
