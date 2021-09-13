""" OWNd mechanism for discovering gateways on local network """

import asyncio
import email.parser
import socket
import xml.dom.minidom
from urllib.parse import urlparse

import aiohttp


class SSDPMessage:
    """Simplified HTTP message to serve as a SSDP message."""

    def __init__(self, version="HTTP/1.1", headers=None):
        if headers is None:
            headers = []
        elif isinstance(headers, dict):
            headers = headers.items()

        self.version = version
        self.headers = list(headers)
        self.headers_dictionary = {}
        for header in self.headers:
            self.headers_dictionary.setdefault(header[0], header[1])

    @classmethod
    def parse(cls, msg):
        """
        Parse message a string into a :class:`SSDPMessage` instance.
        Args:
            msg (str): Message string.
        Returns:
            SSDPMessage: Message parsed from string.
        """
        raise NotImplementedError()

    @classmethod
    def parse_headers(cls, msg):
        """
        Parse HTTP headers.
        Args:
            msg (str): HTTP message.
        Returns:
            (List[Tuple[str, str]]): List of header tuples.
        """
        return list(email.parser.Parser().parsestr(msg).items())

    def __str__(self):
        """Return full HTTP message."""
        raise NotImplementedError()

    def __bytes__(self):
        """Return full HTTP message as bytes."""
        _bytes = self.__str__().encode().replace(b"\n", b"\r\n")
        _bytes = _bytes + b"\r\n\r\n"
        return _bytes


class SSDPResponse(SSDPMessage):
    """Simple Service Discovery Protocol (SSDP) response."""

    def __init__(self, status_code, reason, **kwargs):
        self.status_code = int(status_code)
        self.reason = reason
        super().__init__(**kwargs)

    @classmethod
    def parse(cls, msg):
        """Parse message string to response object."""
        lines = msg.splitlines()
        version, status_code, reason = lines[0].split()
        headers = cls.parse_headers("\r\n".join(lines[1:]))
        return cls(
            version=version, status_code=status_code, reason=reason, headers=headers
        )

    def __str__(self):
        """Return complete SSDP response."""
        lines = list()
        lines.append(" ".join([self.version, str(self.status_code), self.reason]))
        for header in self.headers:
            lines.append("%s: %s" % header)
        return "\n".join(lines)


class SSDPRequest(SSDPMessage):
    """Simple Service Discovery Protocol (SSDP) request."""

    def __init__(self, method, uri="*", version="HTTP/1.1", headers=None):
        self.method = method
        self.uri = uri
        super().__init__(version=version, headers=headers)

    @classmethod
    def parse(cls, msg):
        """Parse message string to request object."""
        lines = msg.splitlines()
        method, uri, version = lines[0].split()
        headers = cls.parse_headers("\r\n".join(lines[1:]))
        return cls(version=version, uri=uri, method=method, headers=headers)

    def __str__(self):
        """Return complete SSDP request."""
        lines = list()
        lines.append(" ".join([self.method, self.uri, self.version]))
        for header in self.headers:
            lines.append("%s: %s" % header)
        return "\n".join(lines)


class SimpleServiceDiscoveryProtocol(asyncio.DatagramProtocol):
    """
    Simple Service Discovery Protocol (SSDP).
    SSDP is part of UPnP protocol stack. For more information see:
    https://en.wikipedia.org/wiki/Simple_Service_Discovery_Protocol
    """

    def __init__(self, recvq, excq):
        """
        @param recvq    - asyncio.Queue for new datagrams
        @param excq     - asyncio.Queue for exceptions
        """
        self._recvq = recvq
        self._excq = excq

        # Transports are connected at the time a connection is made.
        self._transport = None

    def connection_made(self, transport):
        self._transport = transport

    def datagram_received(self, data, addr):
        data = data.decode()

        if data.startswith("HTTP/"):
            response = SSDPResponse.parse(data)
            if (
                response.headers_dictionary["USN"].startswith("uuid:pnp-webserver-")
                or response.headers_dictionary["USN"].startswith("uuid:pnp-scheduler-")
                or response.headers_dictionary["USN"].startswith(
                    "uuid:pnp-scheduler201-"
                )
                or response.headers_dictionary["USN"].startswith(
                    "uuid:pnp-touchscreen-"
                )
                or response.headers_dictionary["USN"].startswith(
                    "uuid:pnp-myhomeserver1-"
                )
                or response.headers_dictionary["USN"].startswith(
                    "uuid:upnp-Basic gateway-"
                )
                or response.headers_dictionary["USN"].startswith(
                    "uuid:upnp-IPscenariomodule-"
                )
                or response.headers_dictionary["USN"].startswith(
                    "uuid:upnp-IPscenarioModule-"
                )
            ):

                self._recvq.put_nowait(
                    {
                        "address": addr[0],
                        "ssdp_location": response.headers_dictionary["LOCATION"],
                        "ssdp_st": response.headers_dictionary["ST"],
                    }
                )

    def error_received(self, exc):
        self._excq.put_nowait(exc)

    def connection_lost(self, exc):
        if exc is not None:
            self._excq.put_nowait(exc)

        if self._transport is not None:
            self._transport.close()
            self._transport = None


def _get_soap_body(namespace: str, action: str) -> str:
    soap_body = f"""
        <?xml version="1.0"?>

        <soap:Envelope
        xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
        soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding">

        <soap:Body>
        <m:{action} xmlns:m="{namespace}">
        </m:{action}>
        </soap:Body>

        </soap:Envelope>
    """
    return soap_body


async def get_port(scpd_location: str) -> int:

    host = urlparse(scpd_location).netloc
    scheme = urlparse(scpd_location).scheme
    try:
        async with aiohttp.ClientSession() as session:

            service_ns = "urn:schemas-bticino-it:service:openserver:1"
            service_action = "getopenserverPort"
            service_control = "upnp/pwdControl"
            soap_body = _get_soap_body(service_ns, service_action)
            soap_action = f"{service_ns}#{service_action}"
            headers = {
                "SOAPAction": f'"{soap_action}"',
                "Host": f"{host}",
                "Content-Type": "text/xml",
                "Content-Length": str(len(soap_body)),
            }

            ctrl_url = f"{scheme}://{host}/{service_control}"
            resp = await session.post(ctrl_url, data=soap_body, headers=headers)
            soap_response = xml.dom.minidom.parseString(
                await resp.text()
            ).documentElement
            await session.close()

        return int(soap_response.getElementsByTagName("Port")[0].childNodes[0].data)
    except aiohttp.client_exceptions.ServerDisconnectedError:
        return 20000
    except aiohttp.client_exceptions.ClientOSError:
        return 20000


async def _get_scpd_details(scpd_location: str) -> dict:

    discovery_info = dict()

    async with aiohttp.ClientSession() as session:
        scpd_response = await session.get(scpd_location)
        scpd_xml = xml.dom.minidom.parseString(
            await scpd_response.text()
        ).documentElement

        discovery_info["deviceType"] = (
            scpd_xml.getElementsByTagName("deviceType")[0].childNodes[0].data
        )
        discovery_info["friendlyName"] = (
            scpd_xml.getElementsByTagName("friendlyName")[0].childNodes[0].data
        )
        discovery_info["manufacturer"] = (
            scpd_xml.getElementsByTagName("manufacturer")[0].childNodes[0].data
        )
        discovery_info["manufacturerURL"] = (
            scpd_xml.getElementsByTagName("manufacturerURL")[0].childNodes[0].data
        )
        discovery_info["modelName"] = (
            scpd_xml.getElementsByTagName("modelName")[0].childNodes[0].data
        )
        discovery_info["modelNumber"] = (
            scpd_xml.getElementsByTagName("modelNumber")[0].childNodes[0].data
        )
        # discovery_info["presentationURL"] = (
        #     scpd_xml.getElementsByTagName("presentationURL")[0].childNodes[0].data
        # )  ## bticino did not populate this field
        discovery_info["serialNumber"] = (
            scpd_xml.getElementsByTagName("serialNumber")[0].childNodes[0].data
        )
        discovery_info["UDN"] = (
            scpd_xml.getElementsByTagName("UDN")[0].childNodes[0].data
        )

        discovery_info["port"] = await get_port(scpd_location)

        await session.close()

    return discovery_info


async def find_gateways() -> list:

    return_list = list()

    # Start the asyncio loop.
    loop = asyncio.get_running_loop()
    recvq = asyncio.Queue()
    excq = asyncio.Queue()

    search_request = bytes(
        SSDPRequest(
            "M-SEARCH",
            headers={
                "MX": "2",
                "ST": "upnp:rootdevice",
                "MAN": '"ssdp:discover"',
                "HOST": "239.255.255.250:1900",
                "Content-Length": "0",
            },
        )
    )

    (
        transport,
        protocol,  # pylint: disable=unused-variable
    ) = await loop.create_datagram_endpoint(
        lambda: SimpleServiceDiscoveryProtocol(recvq, excq), family=socket.AF_INET
    )
    transport.sendto(search_request, ("239.255.255.250", 1900))
    try:
        await asyncio.sleep(2)
    finally:
        transport.close()

    while not recvq.empty():
        discovery_info = await recvq.get()
        discovery_info.update(await _get_scpd_details(discovery_info["ssdp_location"]))

        return_list.append(discovery_info)

    return return_list


async def get_gateway(address: str) -> dict:
    _local_gateways = await find_gateways()
    for _gateway in _local_gateways:
        if _gateway["address"] == address:
            return _gateway


if __name__ == "__main__":
    local_gateways = asyncio.run(find_gateways())

    for gateway in local_gateways:
        print(f"Address: {gateway['address']}")
        print(f"Port: {gateway['port']}")
        print(f"Manufacturer: {gateway['manufacturer']}")
        print(f"Model: {gateway['modelName']}")
        print(f"Firmware: {gateway['modelNumber']}")
        print(f"Serial: {gateway['serialNumber']}")
        print()
