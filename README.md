#OWNd

This package is an event listener and command forwarder for the OpenWebNet protocol.

It is mainly intended to be used in an Home-Assistant integration.

At this point most events are understood, except for WHO = 4 (Heating system) which has not been implemented yet.
WHO = 5 (Burglar Alarm) event support is also limited for
Basic commands are only implemented for WHO = 1 (Lighting) and WHO = 2 (Automation). More will come