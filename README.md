# OWNd

This package is an event listener and command forwarder for the OpenWebNet protocol.

It is mainly intended to be used in an Home-Assistant integration.

At this point most events are understood.
WHO = 5 (Burglar Alarm) event support is limited and needs further development.
Many commands are implemented, mostly within the requirements of Home-Assistant.

## Testing OWNd

Testing OWNd is pretty simple. 
Clone this repository and then:

```
cd <OWNd checkout folder>
pip3 install .
python3 -m OWNd --help    # to visualize possible options
```

To attempt connection to the first available OpenWebNet gateway in the local area network you 
can run:

```
python3 -m OWNd
```

This will use [SSDP](https://en.wikipedia.org/wiki/Simple_Service_Discovery_Protocol) to discover
all supported gateways and pick the first one.

Alternatively, if you want to skip the SSDP discovery step, you can provide the IP address, port 
and MAC address of the gateway from command-line:

```
python3 -m OWNd --address <IP address> --port <PORT> --password <PASS> --mac <MAC address>
```

Note that all these details can be retrieved using bTICINO Home+Project Android application.