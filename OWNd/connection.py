""" This module handles TCP connections to the OpenWebNet gateway """

from OWNd.message import *
import socket

class OWNConnection():
    """ Connection to OpenWebNet gateway """

    def __init__(self, logger, address='192.168.1.35', port=20000, password='12345'):
        """ Initialize the class
        Arguments:
        logger: instance of logging
        address: IP address of the OpenWebNet gateway
        port: TCP port for the connection
        password: OpenWebNet password
        """

        self._address = address
        self._port = int(port)
        self._password = password
        self._logger = logger

        self._logger.info("Establishing event connection...")

        self._eventSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._eventSocket.connect((self._address, self._port))
        self._write("*99*1##")

        result = OWNSignaling(self._read())
        self._logger.debug("Response: {}".format(result))
        if result.isNACK():
            raise RuntimeError("Error while establishing connection")

        result = OWNSignaling(self._read())
        if result.isNACK():
            raise RuntimeError("Error while establishing connection")
        elif result.isSHA():
            raise RuntimeError("Error while establishing connection : HMAC authentication not supported")
        elif result.isNonce():
            hashedPass = "*#{}##".format(self._ownCalcPass(self._password, result.nonce))
            self._write(hashedPass)
            result = OWNSignaling(self._read())
            if result.isNACK():
                raise RuntimeError("Password error while establishing connection")
            elif result.isACK():
                self._logger.info("Event session established")
        elif result.isACK():
            self._logger.info("Event session established")

    def _write(self, data, socket=None):
        if socket == None:
            socket=self._eventSocket
        socket.send(data.encode())

    def _read(self, socket=None):
        if socket == None:
            socket=self._eventSocket
        return str(socket.recv(1024).decode())

    def close(self):
        """ Closes the event connection to the OpenWebNet gateway """

        self._eventSocket.shutdown(socket.SHUT_RDWR)
        self._eventSocket.close()
        self._logger.debug("Closed connection socket for event session.")

    def send(self, message):
        """ Send the attached message on a new 'command' connection
        that  is then immediately closed """

        _commandSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _commandSocket.connect((self._address, self._port))
        _error = False
        self._logger.debug("Opened connection socket for command session.")
        self._write("*99*0##", _commandSocket)

        result = OWNSignaling(self._read(_commandSocket))
        self._logger.debug("Response: {}".format(result))
        if result.isNACK():
            self._logger.error("Error while establishing command connection")

        result = OWNSignaling(self._read(_commandSocket))
        if result.isNACK():
            _error = True
            self._logger.error("Error while establishing command connection")
        elif result.isSHA():
            _error = True
            self._logger.error("Error while establishing command session: HMAC authentication not supported")
        elif result.isNonce():
            hashedPass = "*#{}##".format(self._ownCalcPass(self._password, result.nonce))
            self._write(hashedPass, _commandSocket)
            result = OWNSignaling(self._read(_commandSocket))
            if result.isNACK():
                _error = True
                self._logger.error("Password error while establishing command session")
            elif result.isACK():
                self._logger.info("Command session established")
        elif result.isACK():
            self._logger.info("Command session established")
        
        if not _error:
            self._write(str(message), _commandSocket)
            result = OWNSignaling(self._read(_commandSocket))
            if result.isNACK():
                self._write(str(message), _commandSocket)
                result = OWNSignaling(self._read(_commandSocket))
                if result.isNACK():
                    self._logger.error("Could not send message {}.".format(message))
                elif result.isACK():
                    self._logger.info("Message {} was successfully sent.".format(message))
            elif result.isACK():
                self._logger.info("Message {} was successfully sent.".format(message))
            else:
                self._logger.info("Message {} received response {}.".format(message,  result))

        _commandSocket.shutdown(socket.SHUT_RDWR)
        _commandSocket.close()
        self._logger.debug("Closed connection socket for command session.")
    
    def getNext(self):
        """ Acts as an entry point to read messages on the event bus.
        It will read one frame and return it as an OWNMessage object """

        return OWNEvent.parse(self._read())
    
    def _ownCalcPass (self, password, nonce, test=False) :
        start = True    
        num1 = 0
        num2 = 0
        password = int(password)
        if test:
            print("password: %08x" % (password))
        for c in nonce :
            if c != "0":
                if start:
                    num2 = password
                start = False
            if test:
                print("c: %s num1: %08x num2: %08x" % (c, num1, num2))
            if c == '1':
                num1 = (num2 & 0xFFFFFF80) >> 7
                num2 = num2 << 25
            elif c == '2':
                num1 = (num2 & 0xFFFFFFF0) >> 4
                num2 = num2 << 28
            elif c == '3':
                num1 = (num2 & 0xFFFFFFF8) >> 3
                num2 = num2 << 29
            elif c == '4':
                num1 = num2 << 1
                num2 = num2 >> 31
            elif c == '5':
                num1 = num2 << 5
                num2 = num2 >> 27
            elif c == '6':
                num1 = num2 << 12
                num2 = num2 >> 20
            elif c == '7':
                num1 = num2 & 0x0000FF00 | (( num2 & 0x000000FF ) << 24 ) | (( num2 & 0x00FF0000 ) >> 16 )
                num2 = ( num2 & 0xFF000000 ) >> 8
            elif c == '8':
                num1 = (num2 & 0x0000FFFF) << 16 | ( num2 >> 24 )
                num2 = (num2 & 0x00FF0000) >> 8
            elif c == '9':
                num1 = ~num2
            else :
                num1 = num2
    
            num1 &= 0xFFFFFFFF
            num2 &= 0xFFFFFFFF
            if (c not in "09"):
                num1 |= num2
            if test:
                print("     num1: %08x num2: %08x" % (num1, num2))
            num2 = num1
        return num1