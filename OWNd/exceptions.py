"""Custom exceptions for the OpenWebNet daemon."""


class OpenWebNetError(Exception):
    """General OpenWebNet exception."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None
        super().__init__(self.message)

    def __str__(self):
        if self.message:
            return self.message
        else:
            return "OpenWebNetException has been raised"


class OWNGatewayUnreachableError(OpenWebNetError):
    """Gateway is not currently reachable at that IP/Port."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None
        super().__init__(self.message)


class OWNConnectionRefusedError(OpenWebNetError, ConnectionRefusedError):
    """Gateway is outright refusing the connection."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None
        super().__init__(self.message)


class OWNNegociationRefusedError(OWNConnectionRefusedError):
    """The gateway is accepting to open the connection but refuses to initiate handshake."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None
        super().__init__(self.message)


class OWNAuthenticationError(OpenWebNetError):
    """Generic authentication error."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None
        super().__init__(self.message)


class OWNAuthenticationServiceDisabledError(
    OWNAuthenticationError, ConnectionResetError
):
    """The gateway is throttling down authentication for 60s due to too many failed attempts."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None
        super().__init__(self.message)


class OWNNegociationError(OWNAuthenticationError):
    """Generic (non password related) error during the handshake negociation."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None
        super().__init__(self.message)


class OWNPasswordError(OWNAuthenticationError):
    """The password provided for the connection is wrong."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None
        super().__init__(self.message)


class OWNPasswordMissingError(OWNPasswordError):
    """The connection requires a password but none was provided."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None
        super().__init__(self.message)


class OWNNACKException(OpenWebNetError):
    """NACK message exception."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None
        super().__init__(self.message)
