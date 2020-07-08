import asyncio
import aiohttp
import email.parser
import errno
import logging
import socket
import xml.dom.minidom

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
        self.transport = transport

    def datagram_received(self, data, addr):
        data = data.decode()

        if data.startswith("HTTP/"):
            response = SSDPResponse.parse(data)
            if response.headers_dictionary['USN'].startswith("uuid:pnp-webserver-") | response.headers_dictionary['USN'].startswith("uuid:pnp-scheduler-") | response.headers_dictionary['USN'].startswith("uuid:pnp-scheduler201-") | response.headers_dictionary['USN'].startswith("uuid:pnp-touchscreen-") | response.headers_dictionary['USN'].startswith("uuid:pnp-myhomeserver1-"):
                self._recvq.put_nowait((addr[0], response.headers_dictionary['LOCATION']))

    def error_received(self, exc):
        self._excq.put_nowait(exc)

    def connection_lost(self, exc):
        if exc is not None:
            self._excq.put_nowait(exc)

        if self._transport is not None:
            self._transport.close()
            self._transport = None

def _get_soap_body(ns: str, action: str) -> str:
    soap_body = """
<?xml version="1.0"?>

<soap:Envelope
xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding">

<soap:Body>
<m:{1} xmlns:m="{0}">
</m:{1}>
</soap:Body>

</soap:Envelope>
    """.format(ns, action)
    return soap_body

async def _discover_details(URL) -> dict:

    result = dict()
    device_type = ""
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as resp:
            resp_text = await resp.text()   
            xml_response = xml.dom.minidom.parseString(resp_text).documentElement
            result["manufacturer"] = xml_response.getElementsByTagName("manufacturer")[0].childNodes[0].data
            result["manufacturer_URL"] = xml_response.getElementsByTagName("manufacturerURL")[0].childNodes[0].data
            result["model_name"] = xml_response.getElementsByTagName("modelName")[0].childNodes[0].data
            result["firmware_version"] = xml_response.getElementsByTagName("modelNumber")[0].childNodes[0].data
            result["serial_number"] = xml_response.getElementsByTagName("serialNumber")[0].childNodes[0].data
            device_type = xml_response.getElementsByTagName("deviceType")[0].childNodes[0].data
        await session.close()

    service_ns = "urn:schemas-bticino-it:service:openserver:1"
    service_action = "getopenserverPort"
    service_control = "upnp/pwdControl"
    soap_body = _get_soap_body(service_ns, service_action)
    
    soap_action = "{}#{}".format(service_ns, service_action)
    headers = {
        'SOAPAction': '"{}"'.format(soap_action),
        'Host': "{}".format(URL[7:-1]),
        'Content-Type': 'text/xml',
        'Content-Length': str(len(soap_body)),
    }

    ctrl_url = "{}{}".format(URL, service_control)

    async with aiohttp.ClientSession() as session:
        resp = await session.post(ctrl_url, data=soap_body, headers=headers)
        resp_text = await resp.text()
        soap_response = xml.dom.minidom.parseString(resp_text).documentElement
        result["port"] = soap_response.getElementsByTagName("Port")[0].childNodes[0].data

        await session.close()

    return result

async def find_gateways() -> list:

    return_list = list()

    # Getting a list of local interfaces IPv4 address
    local_addresses = list({i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None, family=socket.AF_INET)})

    # Start the asyncio loop.
    loop = asyncio.get_running_loop()
    recvq = asyncio.Queue()
    excq = asyncio.Queue()

    search_request = SSDPRequest(
        "M-SEARCH",
        headers={
            "MX": "2",
            "ST": "upnp:rootdevice",
            "MAN": '"ssdp:discover"',
            "HOST": "239.255.255.250:1900",
            "Content-Length": "0",
        },
    )

    for address in local_addresses:
        transport, protocol = await loop.create_datagram_endpoint(lambda: SimpleServiceDiscoveryProtocol(recvq, excq), local_addr=(address,0), family=socket.AF_INET)
        transport.sendto(bytes(search_request), ("239.255.255.250", 1900))
        try:
            await asyncio.sleep(2)
        finally:
            transport.close()

    while not recvq.empty():
        gateway_address = await recvq.get()
        gateway_details = await _discover_details(gateway_address[1])
        gateway_details["address"] = gateway_address[0]

        return_list.append(gateway_details)
    
    return return_list

if __name__ == "__main__":
    local_gateways = asyncio.run(find_gateways())

    for gateway in local_gateways:
        print("Address: {}".format(gateway["address"]))
        print("Port: {}".format(gateway["port"]))
        print("Manufacturer: {}".format(gateway["manufacturer"]))
        print("Model: {}".format(gateway["model_name"]))
        print("Firmware: {}".format(gateway["firmware_version"]))
        print("Serial: {}".format(gateway["serial_number"]))
        print()
