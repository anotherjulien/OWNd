""" This module handles TCP connections to the OpenWebNet gateway """

from OWNd.message import *
import asyncio

class OWNConnection():
    """ Connection to OpenWebNet gateway """

    SEPARATOR = '##'.encode()

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

    async def test_connection(self) -> bool:

        event_stream_reader, event_stream_writer = await asyncio.open_connection(self._address, self._port)
        result = await self._negociate(reader=event_stream_reader, writer=event_stream_writer, is_command=False)
        event_stream_writer.close()
        await event_stream_writer.wait_closed()

        return result


    async def connect(self):

        self._logger.info("Opening event session.")
        self._event_stream_reader, self._event_stream_writer = await asyncio.open_connection(self._address, self._port)
        await self._negociate(reader=self._event_stream_reader, writer=self._event_stream_writer, is_command=False)

    async def close(self):
        """ Closes the event connection to the OpenWebNet gateway """
        self._event_stream_writer.close()
        await self._event_stream_writer.wait_closed()
        self._logger.info("Event session closed.")

    async def send(self, message):
        """ Send the attached message on a new 'command' connection
        that  is then immediately closed """

        self._logger.info("Opening command session.")

        command_stream_reader, command_stream_writer = await asyncio.open_connection(self._address, self._port)
        message_string = str(message).encode()
        
        if await self._negociate(reader=command_stream_reader, writer=command_stream_writer, is_command=True):
            command_stream_writer.write(message_string)
            await command_stream_writer.drain()
            raw_response = await command_stream_reader.readuntil(OWNConnection.SEPARATOR)
            resulting_message = OWNSignaling(raw_response.decode())
            if resulting_message.is_NACK():
                command_stream_writer.write(message_string)
                await command_stream_writer.drain()
                raw_response = await command_stream_reader.readuntil(OWNConnection.SEPARATOR)
                resulting_message = OWNSignaling(raw_response.decode())
                if resulting_message.is_NACK():
                    self._logger.error("Could not send message {}.".format(message))
                elif resulting_message.is_ACK():
                    self._logger.info("Message {} was successfully sent.".format(message))
            elif resulting_message.is_ACK():
                self._logger.info("Message {} was successfully sent.".format(message))
            else:
                self._logger.info("Message {} received response {}.".format(message,  resulting_message))

        command_stream_writer.close()
        await command_stream_writer.wait_closed()

        self._logger.info("Command session closed.")
    
    async def get_next(self):
        """ Acts as an entry point to read messages on the event bus.
        It will read one frame and return it as an OWNMessage object """
        try:
            data = await self._event_stream_reader.readuntil(OWNConnection.SEPARATOR)
            return OWNEvent.parse(data.decode())
        except asyncio.exceptions.IncompleteReadError:
            return None
    
    async def _negociate(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, is_command = False) -> bool:

        _session_type = 0 if is_command else 1
        _error = False

        self._logger.info("Negociating {} session.".format("command" if is_command else "event"))

        writer.write("*99*{}##".format(_session_type).encode())
        await writer.drain()

        raw_response = await reader.readuntil(OWNConnection.SEPARATOR)
        resulting_message = OWNSignaling(raw_response.decode())
        self._logger.debug("Reply: {}".format(resulting_message))
        if resulting_message.is_NACK():
            self._logger.error("Error while opening {} session.".format("command" if is_command else "event"))

        raw_response = await reader.readuntil(OWNConnection.SEPARATOR)
        resulting_message = OWNSignaling(raw_response.decode())
        if resulting_message.is_NACK():
            _error = True
            self._logger.debug("Reply: {}".format(resulting_message))
            self._logger.error("Error while opening {} session.".format("command" if is_command else "event"))
        elif resulting_message.is_SHA():
            _error = True
            self._logger.info("Received SHA challenge: {}".format(resulting_message))
            self._logger.error("Error while opening {} session: HMAC authentication not supported.".format("command" if is_command else "event"))
        elif resulting_message.is_nonce():
            self._logger.info("Received nonce: {}".format(resulting_message))
            hashedPass = "*#{}##".format(self._get_own_password(self._password, resulting_message.nonce))
            self._logger.info("Sending {} session password.".format("command" if is_command else "event"))
            writer.write(hashedPass.encode())
            await writer.drain()
            raw_response = await reader.readuntil(OWNConnection.SEPARATOR)
            resulting_message = OWNSignaling(raw_response.decode())
            self._logger.debug("Reply: {}".format(resulting_message))
            if resulting_message.is_NACK():
                _error = True
                self._logger.error("Password error while opening {} session.".format("command" if is_command else "event"))
            elif resulting_message.is_ACK():
                self._logger.info("{} session established.".format("Command" if is_command else "Event"))
        elif resulting_message.is_ACK():
            self._logger.debug("Reply: {}".format(resulting_message))
            self._logger.info("{} session established.".format("Command" if is_command else "Event"))

        return not _error

    def _get_own_password (self, password, nonce, test=False) :
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