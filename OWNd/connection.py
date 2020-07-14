""" This module handles TCP connections to the OpenWebNet gateway """

import asyncio
import logging
from urllib.parse import urlparse

from .discovery import find_gateways, get_gateway, get_port
from .message import OWNSignaling, OWNEvent


class OWNGateway():

    def __init__(self, discovery_info: dict):
        # Attributes potentially provided by user
        self.address = discovery_info["address"] if "address" in discovery_info else None
        self._password = discovery_info["password"] if "password" in discovery_info else None
        # Attributes retrieved from SSDP discovery
        self.ssdp_location = discovery_info["ssdp_location"] if "ssdp_location" in discovery_info else None
        self.ssdp_st = discovery_info["ssdp_st"] if "ssdp_st" in discovery_info else None
        # Attributes retrieved from UPnP device description
        self.deviceType = discovery_info["deviceType"] if "deviceType" in discovery_info else None
        self.friendlyName = discovery_info["friendlyName"] if "friendlyName" in discovery_info else None
        self.manufacturer = discovery_info["manufacturer"] if "manufacturer" in discovery_info else None
        self.manufacturerURL = discovery_info["manufacturerURL"] if "manufacturerURL" in discovery_info else None
        self.modelName = discovery_info["modelName"] if "modelName" in discovery_info else None
        self.modelNumber = discovery_info["modelNumber"] if "modelNumber" in discovery_info else None
        #self.presentationURL = discovery_info["presentationURL"] if "presentationURL" in discovery_info else None
        self.serialNumber = discovery_info["serialNumber"] if "serialNumber" in discovery_info else None
        self.UDN = discovery_info["UDN"] if "UDN" in discovery_info else None
        # Attributes retrieved from SOAP service control
        self.port = discovery_info["port"] if "port" in discovery_info else None

    @property
    def id(self) -> str:
        return self.serialNumber
    
    @id.setter
    def id(self, id: str) -> None:
        self.serialNumber = id

    @property
    def host(self) -> str:
        return self.address

    @host.setter
    def host(self, host: str) -> None:
        self.address = host

    @property
    def firmware(self) -> str:
        return self.modelNumber
    
    @firmware.setter
    def firmware(self, firmware: str) -> None:
        self.modelNumber = firmware

    @property
    def serial(self) -> str:
        return self.serialNumber

    @serial.setter
    def serial(self, serial: str) -> None:
        self.serialNumber = serial

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, password: str) -> None:
        self._password = password

    @classmethod
    async def get_first_available_gateway(cls, password: str = None):
        local_gateways = await find_gateways()
        local_gateways[0]["password"] = password
        return cls(local_gateways[0])
    
    @classmethod
    async def find_from_address(cls, address: str):
        if address is not None:
            return cls(await get_gateway(address))
        else:
            return await cls.get_first_available_gateway()

    @classmethod
    async def build_from_discovery_info(cls, discovery_info: dict):

        if "address" in discovery_info and discovery_info["address"] is None and "ssdp_location" in discovery_info and discovery_info["ssdp_location"] is not None:
            discovery_info["address"] = urlparse(discovery_info["ssdp_location"]).hostname
        
        if "port" in discovery_info and discovery_info["port"] is None:
            if "ssdp_location" in discovery_info and discovery_info["ssdp_location"] is not None:
                discovery_info["port"] = await get_port(discovery_info["ssdp_location"])
            elif "address" in discovery_info and discovery_info["address"] is not None:
                return await cls.find_from_address(discovery_info["address"])
            else:
                return await cls.get_first_available_gateway(password = discovery_info["password"] if "password" in discovery_info else None)

        return cls(discovery_info)

class OWNSession():
    """ Connection to OpenWebNet gateway """

    SEPARATOR = '##'.encode()

    def __init__(self, gateway: OWNGateway = None, connection_type: str = "test", logger: logging.Logger = None):
        """ Initialize the class
        Arguments:
        logger: instance of logging
        address: IP address of the OpenWebNet gateway
        port: TCP port for the connection
        password: OpenWebNet password
        """
        
        self._gateway = gateway
        self._type = connection_type.lower()
        self._logger = logger

        self._stream_reader : asyncio.StreamReader
        self._stream_writer : asyncio.StreamWriter

    @property
    def gateway(self) -> OWNGateway:
        return self._gateway

    @gateway.setter
    def gateway(self, gateway: OWNGateway) -> None:
        self._gateway = gateway

    @property
    def password(self) -> str:
        return str(self._password)

    @password.setter
    def password(self, password: str) -> None:
        self._password = password

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @logger.setter
    def logger(self, logger: logging.Logger) -> None:
        self._logger = logger

    @property
    def connection_type(self) -> str:
        return self._type

    @connection_type.setter
    def connection_type(self, connection_type: str) -> None:
        self._type = connection_type.lower()

    @classmethod
    async def test_gateway(cls, gateway: OWNGateway) -> dict:
        connection = cls(gateway)
        return await connection.test_connection()

    async def test_connection(self) -> dict:

        self._stream_reader, self._stream_writer = await asyncio.open_connection(self._gateway.address, self._gateway.port)
        result = await self._negotiate()
        await self.close()

        return result

    async def close(self) -> None:
        """ Closes the event connection to the OpenWebNet gateway """
        self._stream_writer.close()
        await self._stream_writer.wait_closed()
        self._logger.info("%s session closed.", self._type.capitalize())
    
    async def _negotiate(self) -> dict:

        type_id = 0 if self._type == "command" else 1
        error = False
        error_message = None
        default_password = "12345"
        default_password_used = False

        self._logger.info("Negotiating %s session.", self._type)

        self._stream_writer.write(f"*99*{type_id}##".encode())
        await self._stream_writer.drain()

        raw_response = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
        resulting_message = OWNSignaling(raw_response.decode())
        self._logger.debug("Reply: %s", resulting_message)
        if resulting_message.is_NACK():
            self._logger.error("Error while opening %s session.", self._type)
            error = True
            error_message = "connection_refused"

        raw_response = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
        resulting_message = OWNSignaling(raw_response.decode())
        if resulting_message.is_NACK():
            error = True
            error_message = "negotiation_refused"
            self._logger.debug("Reply: %s", resulting_message)
            self._logger.error("Error while opening %s session.", self._type)
        elif resulting_message.is_SHA():
            error = True
            error_message = "unsupported_authentication"
            self._logger.info("Received SHA challenge: %s", resulting_message)
            self._logger.error("Error while opening %s session: HMAC authentication not supported.", self._type)
        elif resulting_message.is_nonce():
            self._logger.info("Received nonce: %s", resulting_message)
            if self._gateway.password is None:
                error_message = "password_required"
                self._logger.warning("Connection requires a password but none was provided, trying default.")
                default_password_used = True
                hashedPass = f"*#{self._get_own_password(default_password, resulting_message.nonce)}##"
            else:
                hashedPass = f"*#{self._get_own_password(self._gateway.password, resulting_message.nonce)}##"
            self._logger.info("Sending %s session password.", self._type)
            self._stream_writer.write(hashedPass.encode())
            await self._stream_writer.drain()
            raw_response = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
            resulting_message = OWNSignaling(raw_response.decode())
            self._logger.debug("Reply: %s", resulting_message)
            if resulting_message.is_NACK():
                error = True
                if error_message != "password_required":
                    error_message = "password_error"
                self._logger.error("Password error while opening %s session.", self._type)
            elif resulting_message.is_ACK():
                if default_password_used:
                    error_message = "default_password"
                    self._gateway.password = default_password
                self._logger.info("%s session established.", self._type.capitalize())
        elif resulting_message.is_ACK():
            self._logger.debug("Reply: %s", resulting_message)
            self._logger.info("%s session established.", self._type.capitalize())

        return {"Success": not error, "Message": error_message}

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

class OWNEventSession(OWNSession):

    def __init__(self, gateway: OWNGateway = None, logger: logging.Logger = None):
        super().__init__(gateway = gateway, connection_type = "event", logger = logger)

    @classmethod
    async def connect_to_gateway(cls, gateway: OWNGateway):
        connection = cls(gateway)
        await connection.connect

    async def connect(self):
        self._logger.info("Opening event session.")
        self._stream_reader, self._stream_writer = await asyncio.open_connection(self._gateway.address, self._gateway.port)
        await self._negotiate()
    
    async def get_next(self):
        """ Acts as an entry point to read messages on the event bus.
        It will read one frame and return it as an OWNMessage object """
        try:
            data = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
            return OWNEvent.parse(data.decode())
        except asyncio.exceptions.IncompleteReadError:
            return None

    async def close(self):
        """ Closes the event connection to the OpenWebNet gateway """
        self._stream_writer.close()
        await self._stream_writer.wait_closed()
        self._logger.info("Event session closed.")

class OWNCommandSession(OWNSession):

    def __init__(self, gateway: OWNGateway = None, logger: logging.Logger = None):
        super().__init__(gateway = gateway, connection_type = "command", logger = logger)

    @classmethod
    async def send_to_gateway (cls,  message: str, gateway: OWNGateway):
        connection = cls(gateway)
        await connection.send(message)

    async def send(self, message: str):
        """ Send the attached message on a new 'command' connection
        that  is then immediately closed """

        self._logger.info("Opening command session.")

        command_stream_reader, command_stream_writer = await asyncio.open_connection(self._gateway.address, self._gateway.port)
        message_string = str(message).encode()
        negotiation_result = await self._negotiate()
        
        if negotiation_result["Success"]:
            command_stream_writer.write(message_string)
            await command_stream_writer.drain()
            raw_response = await command_stream_reader.readuntil(OWNSession.SEPARATOR)
            resulting_message = OWNSignaling(raw_response.decode())
            if resulting_message.is_NACK():
                command_stream_writer.write(message_string)
                await command_stream_writer.drain()
                raw_response = await command_stream_reader.readuntil(OWNSession.SEPARATOR)
                resulting_message = OWNSignaling(raw_response.decode())
                if resulting_message.is_NACK():
                    self._logger.error("Could not send message %s.", message)
                elif resulting_message.is_ACK():
                    self._logger.info("Message %s was successfully sent.", message)
            elif resulting_message.is_ACK():
                self._logger.info("Message %s was successfully sent.", message)
            else:
                self._logger.info("Message %s received response %s.", message,  resulting_message)

        command_stream_writer.close()
        await command_stream_writer.wait_closed()

        self._logger.info("Command session closed.")