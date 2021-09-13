""" This module handles TCP connections to the OpenWebNet gateway """

import asyncio
import hmac
import hashlib
import string
import random
import logging
from urllib.parse import urlparse

from .discovery import find_gateways, get_gateway, get_port
from .message import OWNMessage, OWNSignaling


class OWNGateway:
    def __init__(self, discovery_info: dict):
        # Attributes potentially provided by user
        self.address = (
            discovery_info["address"] if "address" in discovery_info else None
        )
        self._password = (
            discovery_info["password"] if "password" in discovery_info else None
        )
        # Attributes retrieved from SSDP discovery
        self.ssdp_location = (
            discovery_info["ssdp_location"]
            if "ssdp_location" in discovery_info
            else None
        )
        self.ssdp_st = (
            discovery_info["ssdp_st"] if "ssdp_st" in discovery_info else None
        )
        # Attributes retrieved from UPnP device description
        self.device_type = (
            discovery_info["deviceType"] if "deviceType" in discovery_info else None
        )
        self.friendly_name = (
            discovery_info["friendlyName"] if "friendlyName" in discovery_info else None
        )
        self.manufacturer = (
            discovery_info["manufacturer"] if "manufacturer" in discovery_info else None
        )
        self.manufacturer_url = (
            discovery_info["manufacturerURL"]
            if "manufacturerURL" in discovery_info
            else None
        )
        self.model_name = (
            discovery_info["modelName"] if "modelName" in discovery_info else None
        )
        self.model_number = (
            discovery_info["modelNumber"] if "modelNumber" in discovery_info else None
        )
        # self.presentationURL = (
        #     discovery_info["presentationURL"]
        #     if "presentationURL" in discovery_info
        #     else None
        # )
        self.serial_number = (
            discovery_info["serialNumber"] if "serialNumber" in discovery_info else None
        )
        self.udn = discovery_info["UDN"] if "UDN" in discovery_info else None
        # Attributes retrieved from SOAP service control
        self.port = discovery_info["port"] if "port" in discovery_info else None

    @property
    def unique_id(self) -> str:
        return self.serial_number

    @unique_id.setter
    def unique_id(self, unique_id: str) -> None:
        self.serial_number = unique_id

    @property
    def host(self) -> str:
        return self.address

    @host.setter
    def host(self, host: str) -> None:
        self.address = host

    @property
    def firmware(self) -> str:
        return self.model_number

    @firmware.setter
    def firmware(self, firmware: str) -> None:
        self.model_number = firmware

    @property
    def serial(self) -> str:
        return self.serial_number

    @serial.setter
    def serial(self, serial: str) -> None:
        self.serial_number = serial

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

        if (
            ("address" not in discovery_info or discovery_info["address"] is None)
            and "ssdp_location" in discovery_info
            and discovery_info["ssdp_location"] is not None
        ):
            discovery_info["address"] = urlparse(
                discovery_info["ssdp_location"]
            ).hostname

        if "port" in discovery_info and discovery_info["port"] is None:
            if (
                "ssdp_location" in discovery_info
                and discovery_info["ssdp_location"] is not None
            ):
                discovery_info["port"] = await get_port(discovery_info["ssdp_location"])
            elif "address" in discovery_info and discovery_info["address"] is not None:
                return await cls.find_from_address(discovery_info["address"])
            else:
                return await cls.get_first_available_gateway(
                    password=discovery_info["password"]
                    if "password" in discovery_info
                    else None
                )

        return cls(discovery_info)


class OWNSession:
    """Connection to OpenWebNet gateway"""

    SEPARATOR = "##".encode()

    def __init__(
        self,
        gateway: OWNGateway = None,
        connection_type: str = "test",
        logger: logging.Logger = None,
    ):
        """Initialize the class
        Arguments:
        logger: instance of logging
        address: IP address of the OpenWebNet gateway
        port: TCP port for the connection
        password: OpenWebNet password
        """

        self._gateway = gateway
        self._type = connection_type.lower()
        self._logger = logger

        self._stream_reader: asyncio.StreamReader
        self._stream_writer: asyncio.StreamWriter

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

        retry_count = 0
        retry_timer = 1

        while True:
            try:
                if retry_count > 2:
                    self._logger.error(
                        "Test session connection still refused after 3 attempts."
                    )
                    return None
                (
                    self._stream_reader,
                    self._stream_writer,
                ) = await asyncio.open_connection(
                    self._gateway.address, self._gateway.port
                )
                break
            except ConnectionRefusedError:
                self._logger.warning(
                    "Test session connection refused, retrying in %ss.", retry_timer
                )
                await asyncio.sleep(retry_timer)
                retry_count += 1
                retry_timer *= 2

        try:
            result = await self._negotiate()
            await self.close()
        except ConnectionResetError:
            error = True
            error_message = "password_retry"
            self._logger.error(
                "Negotiation reset while opening %s session. Wait 60 seconds before retrying.",
                self._type,
            )

            return {"Success": not error, "Message": error_message}

        return result

    async def connect(self):
        self._logger.debug("Opening %s session.", self._type)

        retry_count = 0
        retry_timer = 1

        while True:
            try:
                if retry_count > 4:
                    self._logger.error(
                        "%s session connection still refused after 5 attempts.",
                        self._type.capitalize(),
                    )
                    return None
                (
                    self._stream_reader,
                    self._stream_writer,
                ) = await asyncio.open_connection(
                    self._gateway.address, self._gateway.port
                )
                return await self._negotiate()
            except (ConnectionRefusedError, asyncio.IncompleteReadError):
                self._logger.warning(
                    "%s session connection refused, retrying in %ss.",
                    self._type.capitalize(),
                    retry_timer,
                )
                await asyncio.sleep(retry_timer)
                retry_count += 1
                retry_timer = retry_count * 2
            except ConnectionResetError:
                self._logger.warning(
                    "%s session connection reset, retrying in 60s.",
                    self._type.capitalize(),
                )
                await asyncio.sleep(60)
                retry_count += 1

    async def close(self) -> None:
        """Closes the connection to the OpenWebNet gateway"""
        self._stream_writer.close()
        await self._stream_writer.wait_closed()
        self._logger.debug("%s session closed.", self._type.capitalize())

    async def _negotiate(self) -> dict:

        type_id = 0 if self._type == "command" else 1
        error = False
        error_message = None

        self._logger.debug("Negotiating %s session.", self._type)

        self._stream_writer.write(f"*99*{type_id}##".encode())
        await self._stream_writer.drain()

        raw_response = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
        resulting_message = OWNSignaling(raw_response.decode())
        self._logger.debug("Reply: %s", resulting_message)

        if resulting_message.is_nack():
            self._logger.error("Error while opening %s session.", self._type)
            error = True
            error_message = "connection_refused"

        raw_response = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
        resulting_message = OWNSignaling(raw_response.decode())
        if resulting_message.is_nack():
            error = True
            error_message = "negotiation_refused"
            self._logger.debug("Reply: %s", resulting_message)
            self._logger.error("Error while opening %s session.", self._type)
        elif resulting_message.is_sha():
            self._logger.debug("Received SHA challenge: %s", resulting_message)
            if self._gateway.password is None:
                error = True
                error_message = "password_required"
                self._logger.warning(
                    "Connection requires a password but none was provided."
                )
                self._stream_writer.write("*#*0##".encode())
                await self._stream_writer.drain()
            else:
                if resulting_message.is_sha_1():
                    self._logger.debug("Detected SHA-1 method.")
                    method = "sha1"
                elif resulting_message.is_sha_256():
                    self._logger.debug("Detected SHA-256 method.")
                    method = "sha256"
                self._logger.debug("Accepting challenge, initiating handshake.")
                self._stream_writer.write("*#*1##".encode())
                await self._stream_writer.drain()
                raw_response = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
                resulting_message = OWNSignaling(raw_response.decode())
                if resulting_message.is_nonce():
                    server_random_string_ra = resulting_message.nonce
                    self._logger.debug("Received Ra.")
                    key = "".join(random.choices(string.digits, k=56))
                    client_random_string_rb = self._hex_string_to_int_string(
                        hmac.new(key=key.encode(), digestmod=method).hexdigest()
                    )
                    self._logger.debug("Generated Rb.")
                    hashed_password = f"*#{client_random_string_rb}*{self._encode_hmac_password(method=method, password=self._gateway.password, nonce_a=server_random_string_ra, nonce_b=client_random_string_rb)}##"  # pylint: disable=line-too-long
                    self._logger.debug("Sending %s session password.", self._type)
                    self._stream_writer.write(hashed_password.encode())
                    await self._stream_writer.drain()
                    try:
                        raw_response = await asyncio.wait_for(
                            self._stream_reader.readuntil(OWNSession.SEPARATOR),
                            timeout=5,
                        )
                        resulting_message = OWNSignaling(raw_response.decode())
                        if resulting_message.is_nack():
                            error = True
                            error_message = "password_error"
                            self._logger.error(
                                "Password error while opening %s session.", self._type
                            )
                        elif resulting_message.is_nonce():
                            self._logger.debug("Received HMAC response.")
                            hmac_response = resulting_message.nonce
                            if hmac_response == self._decode_hmac_response(
                                method=method,
                                password=self._gateway.password,
                                nonce_a=server_random_string_ra,
                                nonce_b=client_random_string_rb,
                            ):
                                self._logger.debug("Server identity confirmed.")
                                self._stream_writer.write("*#*1##".encode())
                                await self._stream_writer.drain()
                            else:
                                self._logger.error(
                                    "Server identity could not be confirmed."
                                )
                                self._stream_writer.write("*#*0##".encode())
                                await self._stream_writer.drain()
                                error = True
                                error_message = "negociation_error"
                                self._logger.error(
                                    "Error while opening %s session: HMAC authentication failed.",
                                    self._type,
                                )
                    except asyncio.IncompleteReadError:
                        error = True
                        error_message = "password_error"
                        self._logger.error(
                            "Password error while opening %s session.", self._type
                        )
                    except asyncio.TimeoutError:
                        error = True
                        error_message = "password_error"
                        self._logger.error(
                            "Password timeout error while opening %s session.",
                            self._type,
                        )
        elif resulting_message.is_nonce():
            self._logger.debug("Received nonce: %s", resulting_message)
            if self._gateway.password is not None:
                hashed_password = f"*#{self._get_own_password(self._gateway.password, resulting_message.nonce)}##"  # pylint: disable=line-too-long
                self._logger.debug("Sending %s session password.", self._type)
                self._stream_writer.write(hashed_password.encode())
                await self._stream_writer.drain()
                raw_response = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
                resulting_message = OWNSignaling(raw_response.decode())
                self._logger.debug("Reply: %s", resulting_message)
                if resulting_message.is_nack():
                    error = True
                    error_message = "password_error"
                    self._logger.error(
                        "Password error while opening %s session.", self._type
                    )
                elif resulting_message.is_ack():
                    self._logger.debug(
                        "%s session established.", self._type.capitalize()
                    )
            else:
                error = True
                error_message = "password_error"
                self._logger.error(
                    "Connection requires a password but none was provided for %s session.",
                    self._type,
                )
        elif resulting_message.is_ack():
            self._logger.debug("Reply: %s", resulting_message)
            self._logger.debug("%s session established.", self._type.capitalize())
        else:
            error = True
            error_message = "negotiation_failed"
            self._logger.debug(
                "Unexpected message during negotiation: %s", resulting_message
            )

        return {"Success": not error, "Message": error_message}

    def _get_own_password(self, password, nonce, test=False):
        start = True
        num1 = 0
        num2 = 0
        password = int(password)
        if test:
            print("password: %08x" % (password))
        for character in nonce:
            if character != "0":
                if start:
                    num2 = password
                start = False
            if test:
                print("c: %s num1: %08x num2: %08x" % (character, num1, num2))
            if character == "1":
                num1 = (num2 & 0xFFFFFF80) >> 7
                num2 = num2 << 25
            elif character == "2":
                num1 = (num2 & 0xFFFFFFF0) >> 4
                num2 = num2 << 28
            elif character == "3":
                num1 = (num2 & 0xFFFFFFF8) >> 3
                num2 = num2 << 29
            elif character == "4":
                num1 = num2 << 1
                num2 = num2 >> 31
            elif character == "5":
                num1 = num2 << 5
                num2 = num2 >> 27
            elif character == "6":
                num1 = num2 << 12
                num2 = num2 >> 20
            elif character == "7":
                num1 = (
                    num2 & 0x0000FF00
                    | ((num2 & 0x000000FF) << 24)
                    | ((num2 & 0x00FF0000) >> 16)
                )
                num2 = (num2 & 0xFF000000) >> 8
            elif character == "8":
                num1 = (num2 & 0x0000FFFF) << 16 | (num2 >> 24)
                num2 = (num2 & 0x00FF0000) >> 8
            elif character == "9":
                num1 = ~num2
            else:
                num1 = num2

            num1 &= 0xFFFFFFFF
            num2 &= 0xFFFFFFFF
            if character not in "09":
                num1 |= num2
            if test:
                print("     num1: %08x num2: %08x" % (num1, num2))
            num2 = num1
        return num1

    def _encode_hmac_password(
        self, method: str, password: str, nonce_a: str, nonce_b: str
    ):
        if method == "sha1":
            message = (
                self._int_string_to_hex_string(nonce_a)
                + self._int_string_to_hex_string(nonce_b)
                + "736F70653E"
                + "636F70653E"
                + hashlib.sha1(password.encode()).hexdigest()
            )
            return self._hex_string_to_int_string(
                hashlib.sha1(message.encode()).hexdigest()
            )
        elif method == "sha256":
            message = (
                self._int_string_to_hex_string(nonce_a)
                + self._int_string_to_hex_string(nonce_b)
                + "736F70653E"
                + "636F70653E"
                + hashlib.sha256(password.encode()).hexdigest()
            )
            return self._hex_string_to_int_string(
                hashlib.sha256(message.encode()).hexdigest()
            )
        else:
            return None

    def _decode_hmac_response(
        self, method: str, password: str, nonce_a: str, nonce_b: str
    ):
        if method == "sha1":
            message = (
                self._int_string_to_hex_string(nonce_a)
                + self._int_string_to_hex_string(nonce_b)
                + hashlib.sha1(password.encode()).hexdigest()
            )
            return self._hex_string_to_int_string(
                hashlib.sha1(message.encode()).hexdigest()
            )
        elif method == "sha256":
            message = (
                self._int_string_to_hex_string(nonce_a)
                + self._int_string_to_hex_string(nonce_b)
                + hashlib.sha256(password.encode()).hexdigest()
            )
            return self._hex_string_to_int_string(
                hashlib.sha256(message.encode()).hexdigest()
            )
        else:
            return None

    def _int_string_to_hex_string(self, int_string: str) -> str:
        hex_string = ""
        for i in range(0, len(int_string), 2):
            hex_string += f"{int(int_string[i:i+2]):x}"
        return hex_string

    def _hex_string_to_int_string(self, hex_string: str) -> str:
        int_string = ""
        for i in range(0, len(hex_string), 1):
            int_string += f"{int(hex_string[i:i+1], 16):0>2d}"
        return int_string


class OWNEventSession(OWNSession):
    def __init__(self, gateway: OWNGateway = None, logger: logging.Logger = None):
        super().__init__(gateway=gateway, connection_type="event", logger=logger)

    @classmethod
    async def connect_to_gateway(cls, gateway: OWNGateway):
        connection = cls(gateway)
        await connection.connect()

    async def get_next(self):
        """Acts as an entry point to read messages on the event bus.
        It will read one frame and return it as an OWNMessage object"""
        try:
            data = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
            return OWNMessage.parse(data.decode())
        except asyncio.IncompleteReadError:
            self._logger.warning("Connection interrupted, reconnecting...")
            await self.connect()
            return None
        except AttributeError:
            self._logger.exception("Received data could not be parsed into a message:")
            return None
        except ConnectionError:
            self._logger.exception("Connection error:")
            return None
        except Exception:  # pylint: disable=broad-except
            self._logger.exception("Event session crashed.")
            return None


class OWNCommandSession(OWNSession):
    def __init__(self, gateway: OWNGateway = None, logger: logging.Logger = None):
        super().__init__(gateway=gateway, connection_type="command", logger=logger)

    @classmethod
    async def send_to_gateway(cls, message: str, gateway: OWNGateway):
        connection = cls(gateway)
        await connection.connect()
        await connection.send(message)

    @classmethod
    async def connect_to_gateway(cls, gateway: OWNGateway):
        connection = cls(gateway)
        await connection.connect()

    async def send(self, message: str, is_status_request: bool = False):
        """Send the attached message on an existing 'command' connection,
        actively reconnecting it if it had been reset."""

        try:
            self._stream_writer.write(str(message).encode())
            await self._stream_writer.drain()
            raw_response = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
            resulting_message = OWNMessage.parse(raw_response.decode())
            if (
                isinstance(resulting_message, OWNSignaling)
                and resulting_message.is_nack()
            ):
                self._stream_writer.write(str(message).encode())
                await self._stream_writer.drain()
                raw_response = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
                resulting_message = OWNSignaling(raw_response.decode())
                if resulting_message.is_nack():
                    self._logger.error("Could not send message %s.", message)
                elif resulting_message.is_ack():
                    if not is_status_request:
                        self._logger.info("Message %s was successfully sent.", message)
                    else:
                        self._logger.debug("Message %s was successfully sent.", message)
            elif (
                isinstance(resulting_message, OWNSignaling)
                and resulting_message.is_ack()
            ):
                if not is_status_request:
                    self._logger.info("Message %s was successfully sent.", message)
                else:
                    self._logger.debug("Message %s was successfully sent.", message)
            else:
                self._logger.debug(
                    "Message %s received response %s.", message, resulting_message
                )
                raw_response = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
                resulting_message = OWNSignaling(raw_response.decode())
                if resulting_message.is_nack():
                    self._logger.error("Could not send message %s.", message)
                elif resulting_message.is_ack():
                    if not is_status_request:
                        self._logger.info("Message %s was successfully sent.", message)
                    else:
                        self._logger.debug("Message %s was successfully sent.", message)

        except (ConnectionResetError, asyncio.IncompleteReadError):
            self._logger.debug("Command session connection reset, retrying...")
            await self.connect()
            await self.send(message=message, is_status_request=is_status_request)
        except Exception:  # pylint: disable=broad-except
            self._logger.exception("Command session crashed.")
            return None
