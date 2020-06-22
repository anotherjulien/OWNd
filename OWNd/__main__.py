import time
import logging

from connection import OWNConnection
from message import *
from daemon import OWNDaemon

def main():
    """ Package entry point! """

    # create logger with 'spam_application'
    logger = logging.getLogger('spam_application')
    logger.setLevel(logging.DEBUG)
    # create console handler which logs even debug messages
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(ch)

    _connection = OWNConnection(logger, "10.42.2.201", 20000, '12345')
    _daemon = OWNDaemon(_connection, handler, logger)
    _daemon.start()

    switchOfficeOn = OWNCommand.switchON(32)
    _connection.send(switchOfficeOn)
    
    time.sleep(2)

    switchOfficeOff = OWNCommand.switchOFF(32)
    _connection.send(switchOfficeOff)

    time.sleep(15)

    _daemon.stop()


def handler(message):
    print(str(message))

if __name__ == "__main__":
    main()