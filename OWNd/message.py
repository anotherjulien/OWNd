""" This module contains OpenWebNet messages definition """

import re


class OWNMessage():

    _ACK = re.compile("^\*#\*1##$") #  *#*1##
    _NACK = re.compile("^\*#\*0##$") #  *#*1##
    _COMMAND_SESSION = re.compile("^\*99\*0##$") #  *99*0##
    _EVENT_SESSION = re.compile("^\*99\*1##$") #  *99*1##
    _NONCE = re.compile("^\*#(\d+)##$") #  *#123456789##
    _SHA = re.compile("^\*98\*(\d)##$") #  *98*SHA##

    _STATUS = re.compile("^\*(?P<who>\d+)\*(?:1000#)?(?P<what>\d+)(?P<what_param>(?:#\d+)*)\*(?P<where>#?\d+)(?P<where_param>(?:#\d+)*)##$") #  *WHO*WHAT*WHERE##
    _STATUS_REQUEST = re.compile("^\*#(?P<who>\d+)\*(?P<where>#?\d+)(?P<where_param>(?:#\d+)*)##$") #  *#WHO*WHERE
    #_STATUS = re.compile("^\*#(?P<who>\d+)\*(?P<what>\d+)(?P<what_param>(?:#\d+)*)\*(?P<where>#?\d+)(?P<where_param>(?:#\d+)*)##$") #  *#WHO*WHAT*WHERE##
    _DIMENSION_WRITING = re.compile("^\*#(?P<who>\d+)\*(?P<where>#?\d+)?(?P<where_param>(?:#\d+)*)?\*#(?P<dimension>\d*)(?P<dimension_param>(?:#\d+)*)?(?P<dimension_value>(?:\*\d+)+)##$") #  *#WHO*WHERE*#DIMENSION*VAL1*VALn##
    _DIMENSION_REQUEST = re.compile("^\*#(?P<who>\d+)\*(?P<where>#?\d+)?(?P<where_param>(?:#\d+)*)?\*(?P<dimension>\d+)##$") #  *#WHO*WHERE*DIMENSION##
    _DIMENSION_REQUEST_REPLY = re.compile("^\*#(?P<who>\d+)\*(?P<where>#?\d+)?(?P<where_param>(?:#\d+)*)?\*(?P<dimension>\d*)(?P<dimension_value>(?:\*\d+)+)##$") #  *#WHO*WHERE*DIMENSION*VAL1*VALn##

    """ Base class for all OWN messages """
    def __init__(self, data):
        self._raw = data

    def isEvent(self):
        return self._family == 'EVENT'

    def isCommand(self):
        return self._family == 'COMMAND'

    def isRequest(self):
        return self._family == 'REQUEST'

    @property
    def entity(self):
        """ The ID of the subject of this message """
        return None

    def __repr__(self):
        return self._raw

    def __str__(self):
        return self._raw

class OWNEvent(OWNMessage):
    """ This class is a subclass of messages. All messages received during an event session are events.
    Dividing this in a subclass provides better clarity """

    def __init__(self, data):
        self._raw = data

        if self._STATUS.match(self._raw):
            self._match = self._STATUS.match(self._raw)
            self._family = 'EVENT'
            self._type = 'STATUS'
        elif self._DIMENSION_REQUEST_REPLY.match(self._raw):
            self._match = self._DIMENSION_REQUEST_REPLY.match(self._raw)
            self._family = 'EVENT'
            self._type = 'DIMENSION_REQUEST_REPLY'
        elif self._DIMENSION_WRITING.match(self._raw):
            self._match = self._DIMENSION_WRITING.match(self._raw)
            self._family = 'COMMAND'
            self._type = 'DIMENSION_WRITING'

        self._who = self._match.group('who')
        self._where = self._match.group('where')

class OWNCommand(OWNMessage):
    """ This class is a subclass of messages. All messages sent during a command session are commands.
    Dividing this in a subclass provides better clarity """

    def __init__(self, data):
        self._raw = data

        if self._STATUS.match(self._raw):
            self._match = self._STATUS.match(self._raw)
            self._family = 'COMMAND'
            self._type = 'STATUS'
        elif self._STATUS_REQUEST.match(self._raw):
            self._match = self._STATUS_REQUEST.match(self._raw)
            self._family = 'REQUEST'
            self._type = 'STATUS_REQUEST'
        elif self._DIMENSION_WRITING.match(self._raw):
            self._match = self._DIMENSION_WRITING.match(self._raw)
            self._family = 'COMMAND'
            self._type = 'DIMENSION_WRITING'
        elif self._DIMENSION_REQUEST.match(self._raw):
            self._match = self._DIMENSION_REQUEST.match(self._raw)
            self._family = 'REQUEST'
            self._type = 'DIMENSION_REQUEST'

        self._who = self._match.group('who')
        self._where = self._match.group('where')

    @classmethod
    def switchON(cls, _where):
        return cls("*1*1*{}##".format(_where))

    @classmethod
    def switchOFF(cls, _where):
        return cls("*1*0*{}##".format(_where))

    @classmethod
    def setLightTo(cls, _where, _level=30):
        _level = round(_level/10)
        if _level == 1:
            _level = 2
        return cls("*1*{}*{}##".format(_level, _where))

    @classmethod
    def setLightToFine(cls, _where, _level=30):
        _level = int(_level)+100
        return cls("*#1*{}#1*{}*2##".format(_where, _level))

    @classmethod
    def raiseShutter(cls, _where):
        return cls("*2*1*{}##".format(_where))
    
    @classmethod
    def lowerShutter(cls, _where):
        return cls("*2*2*{}##".format(_where))

    @classmethod
    def stopShutter(cls, _where):
        return cls("*2*0*{}##".format(_where))

    @classmethod
    def setShutterTo(cls, _where, _level=30):
        return cls("*#2*{}#11#001*{}##".format(_where, _level))

class OWNSignaling(OWNMessage):
    """ This class is a subclass of messages. It is dedicated to signaling messages such as ACK or Authentication negotiation """

    def __init__(self, data):
        self._raw = data

        if self._ACK.match(self._raw):
            self._match = self._ACK.match(self._raw)
            self._family = 'SIGNALING'
            self._type = 'ACK'
        elif self._NACK.match(self._raw):
            self._match = self._NACK.match(self._raw)
            self._family = 'SIGNALING'
            self._type = 'NACK'
        elif self._NONCE.match(self._raw):
            self._match = self._NONCE.match(self._raw)
            self._family = 'SIGNALING'
            self._type = 'NONCE'
        elif self._SHA.match(self._raw):
            self._match = self._SHA.match(self._raw)
            self._family = 'SIGNALING'
            self._type = 'SHA'
        elif self._COMMAND_SESSION.match(self._raw):
            self._match = self._COMMAND_SESSION.match(self._raw)
            self._family = 'SIGNALING'
            self._type = 'COMMAND_SESSION'
        elif self._EVENT_SESSION.match(self._raw):
            self._match = self._EVENT_SESSION.match(self._raw)
            self._family = 'SIGNALING'
            self._type = 'EVENT_SESSION'

    @property
    def nonce(self):
        """ Return the authentication nonce IF the message is a nonce message """
        if self.isNonce:
            return self._match.group(1)
        else:
            return None

    @property
    def sha(self):
        """ Return the authentication SHA version IF the message is a SHA challenge message """
        if self.isSHA:
            return self._match.group(1)
        else:
            return None

    def isACK(self):
        return self._type == 'ACK'

    def isNACK(self):
        return self._type == 'NACK'

    def isNonce(self):
        return self._type == 'NONCE'

    def isSHA(self):
        return self._type == 'SHA'