import time
import logging
import signal
import sys

from connection import OWNConnection
from message import *
from daemon import OWNDaemon

class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.
    """
    pass

def exit_gracefully(signum, frame):
    raise ServiceExit

def main():
    """ Package entry point! """

    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    # create logger with 'OWNd'
    logger = logging.getLogger('OWNd')
    logger.setLevel(logging.DEBUG)
    # create console handler which logs even debug messages
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(ch)

    if len(sys.argv) > 1:
        _address = sys.argv[1]
        _port = sys.argv[2]
        _password = sys.argv[3]

    try:
        _connection = OWNConnection(logger, _address, _port, _password)
        _daemon = OWNDaemon(_connection, handler, logger)
        #_daemon.daemon = True
        _daemon.start()
        while True:
            time.sleep(0.5)
    except ServiceExit:
        try:
            _daemon.stop()
            _daemon.join()
            sys.exit(0)
        except KeyboardInterrupt:
            sys.exit(1)

def handler(message):
    print(message.humanReadableLog)

if __name__ == "__main__":
    main()