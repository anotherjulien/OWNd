""" This module contains the definition of the main daemon class.
This is the central point of control of the whole daemon """

import threading

from OWNd.connection import OWNConnection
from OWNd.message import *

class OWNDaemon(threading.Thread):
    """ Main listening loop for the whole daemon """

    def __init__(self, connection, handler, logger=None):
        """ Initialize the instance
        Arguments
        connection: a scsgate.Connection object
        handler: callback function to invoke whenever a new message
            is received
        logger: instance of logger
        """

        threading.Thread.__init__(self)
        self._connection = connection
        self._handler = handler
        self._terminate = False
        self._logger = logger

    def run(self):
        """ Starts the thread """

        while True:
            if self._terminate:
                self._logger.info("Exiting OWNd listener")
                self._connection.close()
                break
            
            message = self._connection.getNext()
            if message is not None:
                self._logger.debug("Received: {}".format(message))
                if message.isEvent():
                    self._logger.debug("Sending message to handler.")
                    self._handler(message)

    def stop(self):
        """ Blocks the thread, performs cleanup of the associated
        connection """
        self._terminate = True