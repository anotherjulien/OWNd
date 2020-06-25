""" This module contains OpenWebNet messages definition """

import re
import datetime


class OWNMessage():

    _ACK = re.compile("^\*#\*1##$") #  *#*1##
    _NACK = re.compile("^\*#\*0##$") #  *#*1##
    _COMMAND_SESSION = re.compile("^\*99\*0##$") #  *99*0##
    _EVENT_SESSION = re.compile("^\*99\*1##$") #  *99*1##
    _NONCE = re.compile("^\*#(\d+)##$") #  *#123456789##
    _SHA = re.compile("^\*98\*(\d)##$") #  *98*SHA##

    _WHO = re.compile("^\*#?(?P<who>\d+)\*.+##$")
    _STATUS = re.compile("^\*(?P<who>\d+)\*(?P<what>\d+)(?P<what_param>(?:#\d+)*)\*(?P<where>#?\d+)(?P<where_param>(?:#\d+)*)##$") #  *WHO*WHAT*WHERE##
    _STATUS_REQUEST = re.compile("^\*#(?P<who>\d+)\*(?P<where>#?\d+)(?P<where_param>(?:#\d+)*)##$") #  *#WHO*WHERE
    _DIMENSION_WRITING = re.compile("^\*#(?P<who>\d+)\*(?P<where>#?\d+)?(?P<where_param>(?:#\d+)*)?\*#(?P<dimension>\d*)(?P<dimension_param>(?:#\d+)*)?(?P<dimension_value>(?:\*\d+)+)##$") #  *#WHO*WHERE*#DIMENSION*VAL1*VALn##
    _DIMENSION_REQUEST = re.compile("^\*#(?P<who>\d+)\*(?P<where>#?\d+)?(?P<where_param>(?:#\d+)*)?\*(?P<dimension>\d+)##$") #  *#WHO*WHERE*DIMENSION##
    _DIMENSION_REQUEST_REPLY = re.compile("^\*#(?P<who>\d+)\*(?P<where>#?\d+)?(?P<where_param>(?:#\d+)*)?\*(?P<dimension>\d*)(?P<dimension_param>(?:#\d+)*)?(?P<dimension_value>(?:\*\d+)+)##$") #  *#WHO*WHERE*DIMENSION*VAL1*VALn##

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

    @classmethod
    def parse(cls, data):
        _WHO_REGEX = re.compile("^\*#?(?P<who>\d+)\*.+##$")
        _match = _WHO_REGEX.match(data)
        
        if _match:
            _who = int(_match.group('who'))
        
        if _who == 1:
            return OWNLightingEvent(data)
        elif _who == 2:
            return OWNAutomationEvent(data)
        elif _who == 18:
            return OWNEnergyEvent(data)

        return None

    def __init__(self, data):
        self._raw = data

        if self._STATUS.match(self._raw):
            self._match = self._STATUS.match(self._raw)
            self._family = 'EVENT'
            self._type = 'STATUS'
            self._who = int(self._match.group('who'))
            self._what = int(self._match.group('what'))
            self._whatParam = self._match.group('what_param').split('#')
            del self._whatParam[0]
            self._where = int(self._match.group('where'))
            self._whereParam = self._match.group('where_param').split('#')
            del self._whereParam[0]
            self._dimension = None
            self._dimensionParam = None
            self._dimensionValue = None

        elif self._DIMENSION_REQUEST_REPLY.match(self._raw):
            self._match = self._DIMENSION_REQUEST_REPLY.match(self._raw)
            self._family = 'EVENT'
            self._type = 'DIMENSION_REQUEST_REPLY'
            self._who = int(self._match.group('who'))
            self._what = None
            self._whatParam = None
            self._where = int(self._match.group('where'))
            self._whereParam = self._match.group('where_param').split('#')
            del self._whereParam[0]
            self._dimension = int(self._match.group('dimension'))
            self._dimensionParam = self._match.group('dimension_param').split('#')
            del self._dimensionParam[0]
            self._dimensionValue = self._match.group('dimension_value').split('*')
            del self._dimensionValue[0]

        elif self._DIMENSION_WRITING.match(self._raw):
            self._match = self._DIMENSION_WRITING.match(self._raw)
            self._family = 'COMMAND'
            self._type = 'DIMENSION_WRITING'
            self._who = int(self._match.group('who'))
            self._what = None
            self._whatParam = None
            self._where = int(self._match.group('where'))
            self._whereParam = self._match.group('where_param').split('#')
            del self._whereParam[0]
            self._dimension = int(self._match.group('dimension'))
            self._dimensionParam = self._match.group('dimension_param').split('#')
            del self._dimensionParam[0]
            self._dimensionValue = self._match.group('dimension_value').split('*')
            del self._dimensionValue[0]

class OWNLightingEvent(OWNEvent):

    def __init__(self, data):
        super().__init__(data)

        self._state = None
        self._brightness = None
        self._timer = None
        self._humanReadableLog = self._raw

        if self._what is not None:
            if self._what == 1000:
                self._family = 'COMMAND_TRANSLATION'
                return None
            self._state = self._what
            if self._state == 0:
                self._humanReadableLog = "Light {} is switched off.".format(self._where)
            elif self._state == 1:
                self._humanReadableLog = "Light {} is switched on.".format(self._where)
            elif self._state > 1 and self._state < 11:
                self._brightness = self._state * 10
                self._humanReadableLog = "Light {} is switched on at {}%.".format(self._where, self._bightness)
            elif self._state == 11:
                self._timer = 60
                self._humanReadableLog = "Light {} is switched on for {}s.".format(self._where, self._timer)
            elif self._state == 12:
                self._timer = 120
                self._humanReadableLog = "Light {} is switched on for {}s.".format(self._where, self._timer)
            elif self._state == 13:
                self._timer = 180
                self._humanReadableLog = "Light {} is switched on for {}s.".format(self._where, self._timer)
            elif self._state == 14:
                self._timer = 240
                self._humanReadableLog = "Light {} is switched on for {}s.".format(self._where, self._timer)
            elif self._state == 15:
                self._timer = 300
                self._humanReadableLog = "Light {} is switched on for {}s.".format(self._where, self._timer)
            elif self._state == 16:
                self._timer = 900
                self._humanReadableLog = "Light {} is switched on for {}s.".format(self._where, self._timer)
            elif self._state == 17:
                self._timer = 30
                self._humanReadableLog = "Light {} is switched on for {}s.".format(self._where, self._timer)
            elif self._state == 18:
                self._timer = 0.5
                self._humanReadableLog = "Light {} is switched on for {}s.".format(self._where, self._timer)
        
        if self._dimension is not None:
            if self._dimension == 1:
                self._brightness = int(self._dimensionValue[0]) - 100
                if self._brightness == 0:
                    self._state = 0
                    self._humanReadableLog = "Light {} is switched off.".format(self._where)
                else:
                    self._state = 1
                    self._humanReadableLog = "Light {} is switched on at {}%.".format(self._where, self._bightness)
            elif self._dimension == 2:
                self._timer = int(self._dimensionValue[0])*3600 + int(self._dimensionValue[1])*60 + int(self._dimensionValue[2])
                self._humanReadableLog = "Light {} is switched on for {}s.".format(self._where, self._timer)

    @property
    def brightness(self):
        return self._brightness

    @property
    def is_on(self):
        return self._state > 0
    
    @property
    def timer(self):
        return self._timer
    
    @property
    def humanReadableLog(self):
        return self._humanReadableLog

class OWNAutomationEvent(OWNEvent):
    def __init__(self, data):
        super().__init__(data)

        self._state = None
        self._position = None
        self._priority = None
        self._info = None
        self._isOpening = None
        self._isClosing = None
        self._isClosed = None
        self._humanReadableLog = self._raw

        if self._what is not None:
            if self._what == 1000:
                self._family = 'COMMAND_TRANSLATION'
                return None
            self._state = self._what
        if self._dimension is not None:
            if self._dimension == 10:
                self._state = int(self._dimensionValue[0])
                self._position = int(self._dimensionValue[1])
                self._priority = int(self._dimensionValue[2])
                self._info = int(self._dimensionValue[3])

        if self._state == 0:
            self._humanReadableLog = "Cover {} stopped.".format(self._where)
            self._isOpening = False
            self._isClosing = False
        elif self._state == 10:
            if self._position == 0:
                self._humanReadableLog = "Cover {} is closed.".format(self._where)
                self._isClosed = True
            else:
                self._humanReadableLog = "Cover {} is opened at {}%.".format(self._where, self._position)
                self._isClosed = False
        else:
            if self._state == 1:
                self._humanReadableLog = "Cover {} is opening.".format(self._where)
                self._isOpening = True
                self._isClosing = False
            elif self._state == 11 or  self._state == 13:
                self._humanReadableLog = "Cover {} is opening from intial position {}.".format(self._where, self._position)
                self._isOpening = True
                self._isClosing = False
                self._isClosed = False
            elif self._state == 2:
                self._humanReadableLog = "Cover {} is closing.".format(self._where)
                self._isClosing = True
                self._isOpening = False
            elif self._state == 12 or self._state == 14:
                self._humanReadableLog = "Cover {} is closing from intial position {}.".format(self._where, self._position)
                self._isClosing = True
                self._isOpening = False
                self._isClosed = False
            else:
                self._isOpening = False
                self._isClosing = False
    
    @property
    def is_opening(self):
        return self._isOpening

    @property
    def is_closing(self):
        return self._isClosing

    @property
    def is_closed(self):
        return self._isClosed

    @property
    def current_position(self):
        return self._position
    
    @property
    def humanReadableLog(self):
        return self._humanReadableLog

class OWNEnergyEvent(OWNEvent):
    def __init__(self, data):
        super().__init__(data)

        if  not str(self._where).startswith('5'):
            return None

        self._activePower = None
        self._hourlyConsumption = None
        self._dailyConsumption = None
        self._currentDayPartialConsumption = None
        self._monthlyConsumption = None
        self._currentMonthPartialConsumption = None
        self._humanReadableLog = self._raw
        
        if self._dimension is not None:
            if self._dimension == 113:
                self._activePower = int(self._dimensionValue[0])
                self._humanReadableLog = "Sensor {} is reporting an active power draw of {} W.".format(self._where, self._activePower)
            elif self._dimension == 511:
                _now = datetime.date.today()
                _messageDate =  datetime.date(_now.year, int(self._dimensionParam[0]), int(self._dimensionParam[1]))
                if _messageDate > _now:
                    _messageDate.replace(year= _now.year - 1)

                if int(self._dimensionValue[0]) != 25:
                    self._hourlyConsumption['date'] = _messageDate
                    self._hourlyConsumption['hour'] = int(self._dimensionValue[0])
                    self._hourlyConsumption['value'] = int(self._dimensionValue[1])
                    self._humanReadableLog = "Sensor {} is reporting a power consumtion of {} Wh for {} at {}.".format(self._where, self._hourlyConsumption['value'], self._hourlyConsumption['date'], self._hourlyConsumption['hour'])
                else:
                    self._hourlyConsumption['date'] = _messageDate
                    self._dailyConsumption['value'] = int(self._dimensionValue[1])
                    self._humanReadableLog = "Sensor {} is reporting a power consumtion of {} Wh for {}.".format(self._where, self._hourlyConsumption['value'], self._hourlyConsumption['date'])
                    
            elif self._dimension == 54:
                self._currentDayPartialConsumption = int(self._dimensionValue[0])
                self._humanReadableLog = "Sensor {} is reporting a power consumtion of {} Wh up to now today.".format(self._where, self._hourlyConsumption['value'])
            elif self._dimension == 52:
                _messageDate =  datetime.date(int("20" + str(self._dimensionParam[0])), self._dimensionParam[1], 1)
                self._monthlyConsumption['date'] = _messageDate
                self._monthlyConsumption['value'] = int(self._dimensionValue[0])
                self._humanReadableLog = "Sensor {} is reporting a power consumtion of {} Wh for {}.".format(self._where, self._monthlyConsumption['value'], self._monthlyConsumption['date'].strftime("%B %Y"))
            elif self._dimension == 53:
                self._currentMonthPartialConsumption = int(self._dimensionValue[0])
                self._humanReadableLog = "Sensor {} is reporting a power consumtion of {} Wh up to now this month.".format(self._where, self._currentMonthPartialConsumption['value'])

    @property
    def activePower(self):
        return self._activePower
    
    @property
    def hourlyConsumption(self):
        return self._hourlyConsumption
    
    @property
    def dailyConsumption(self):
        return self._dailyConsumption
    
    @property
    def currentDayPartialConsumption(self):
        return self._currentDayPartialConsumption
    
    @property
    def monthlyConsumption(self):
        return self._monthlyConsumption

    @property
    def currentMonthParitalConsumption(self):
        return self._currentMonthPartialConsumption

    @property
    def humanReadableLog(self):
        return self._humanReadableLog

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