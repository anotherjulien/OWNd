""" This module handles TCP connections to the OpenWebNet gateway """

from message import *
from discovery import get_port, get_gateway, find_gateways

import asyncio
import logging
from urllib.parse import urlparse

class OWNGateway():

    def __init__(self, discovery_info: dict):
        self.ssdp_location = discovery_info["ssdp_location"] if "ssdp_location" in discovery_info else None
        self.ssdp_st = discovery_info["ssdp_st"] if "ssdp_st" in discovery_info else None
        # Attributes for accessing info from retrieved UPnP device description
        self.deviceType = discovery_info["deviceType"] if "deviceType" in discovery_info else None
        self.friendlyName = discovery_info["friendlyName"] if "friendlyName" in discovery_info else None
        self.manufacturer = discovery_info["manufacturer"] if "manufacturer" in discovery_info else None
        self.manufacturerURL = discovery_info["manufacturerURL"] if "manufacturerURL" in discovery_info else None
        self.modelName = discovery_info["modelName"] if "modelName" in discovery_info else None
        self.modelNumber = discovery_info["modelNumber"] if "modelNumber" in discovery_info else None
        self.presentationURL = discovery_info["presentationURL"] if "presentationURL" in discovery_info else None
        self.serialNumber = discovery_info["serialNumber"] if "serialNumber" in discovery_info else None
        self.UDN = discovery_info["UDN"] if "UDN" in discovery_info else None
        self.address = discovery_info["address"] if "address" in discovery_info else None
        self.port = discovery_info["port"] if "port" in discovery_info else None


    @classmethod
    async def get_first_available_gateway(cls):
        local_gateways = await find_gateways()
        return cls(local_gateways[0])

    @classmethod
    async def build_from_discovery_info(cls, discovery_info: dict):

        if "address" in discovery_info and discovery_info["address"] is None and "ssdp_location" in discovery_info and discovery_info["ssdp_location"] is not None:
            discovery_info["address"] = urlparse(discovery_info["ssdp_location"]).hostname
        
        if "port" in discovery_info and discovery_info["port"] is None:
            if "ssdp_location" in discovery_info and discovery_info["ssdp_location"] is not None:
                discovery_info["port"] = await get_port(discovery_info["ssdp_location"])
            elif "address" in discovery_info and discovery_info["address"] is not None:
                return await build_from_address(discovery_info["address"])
            else:
                return await cls.get_first_available_gateway()

        return cls(discovery_info)

    @classmethod
    async def build_from_address(cls, address: str):
        if address is not None:
            return cls(await get_gateway(address))
        else:
            return await get_first_available_gateway()

class OWNConnection():
    """ Connection to OpenWebNet gateway """

    SEPARATOR = '##'.encode()

    def __init__(self, gateway: OWNGateway = None, password: str = None):
        """ Initialize the class
        Arguments:
        logger: instance of logging
        address: IP address of the OpenWebNet gateway
        port: TCP port for the connection
        password: OpenWebNet password
        """
        
        self._gateway = gateway
        self._password = password
        self._logger = None

    @property
    def gateway(self) -> OWNGateway:
        return self._gateway

    @gateway.setter
    def gateway(self, gateway: OWNGateway) -> None:
        self._gateway = gateway

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, password: str) -> None:
        self._password = password

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @logger.setter
    def logger(self, logger: logging.Logger) -> None:
        self._logger = logger

    async def test_connection(self) -> bool:

        event_stream_reader, event_stream_writer = await asyncio.open_connection(self._address, self._port)
        result = await self._negociate(reader=event_stream_reader, writer=event_stream_writer, is_command=False)
        event_stream_writer.close()
        await event_stream_writer.wait_closed()

        return result

    async def connect(self):

        if self._gateway.serialNumber is not None:
            self._logger.info("{} server running firmware {} has serial {}.".format(self._gateway.modelName, self._gateway.modelNumber, self._gateway.serialNumber))

        self._logger.info("Opening event session.")
        self._event_stream_reader, self._event_stream_writer = await asyncio.open_connection(self._gateway.address, self._gateway.port)
        await self._negociate(reader=self._event_stream_reader, writer=self._event_stream_writer, is_command=False)

    async def close(self):
        """ Closes the event connection to the OpenWebNet gateway """
        self._event_stream_writer.close()
        await self._event_stream_writer.wait_closed()
        self._logger.info("Event session closed.")

    async def send(self, message):
        """ Send the attached message on a new 'command' connection
        that  is then immediately closed """

        while not self.is_ready:
            await asyncio.sleep(0.5)

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
            if self._password is None:
                self._logger.warning("Connection requires a password but none was provided, trying default.")
                hashedPass = "*#{}##".format(self._get_own_password(12345, resulting_message.nonce))
            else:
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