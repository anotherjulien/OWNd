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

    _STATUS = re.compile("^\*(?P<who>\d+)\*(?P<what>\d+)(?P<what_param>(?:#\d+)*)\*(?P<where>#?\*|\d+)(?P<where_param>(?:#\d+)*)##$") #  *WHO*WHAT*WHERE##
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
        _match = re.match("^\*#?(?P<who>\d+)\*.+##$", data)
        
        if _match:
            _who = int(_match.group('who'))
        
            if _who == 1:
                return OWNLightingEvent(data)
            elif _who == 2:
                return OWNAutomationEvent(data)
            elif _who == 5:
                return OWNBurglarAlarmEvent(data)
            elif _who == 15:
                return OWNCENEvent(data)
            elif _who == 18:
                return OWNEnergyEvent(data)
            elif _who == 25:
                _where = re.match("^\*.+\*(?P<where>\d+)##$", data).group('where')
                if _where.startswith('2'):
                    return OWNCENPlusEvent(data)
                elif _where.startswith('3'):
                    return OWNDryContactEvent(data)

        return None

    def __init__(self, data):
        self._raw = data

        if self._STATUS.match(self._raw):
            self._match = self._STATUS.match(self._raw)
            self._family = 'EVENT'
            self._type = 'STATUS'
            self._who = int(self._match.group('who'))
            self._what = int(self._match.group('what'))
            if self._what == 1000:
                self._family = 'COMMAND_TRANSLATION'
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

class OWNSceneEvent(OWNEvent):

    def __init__(self, data):
        super().__init__(data)

        self._scenario = self._what
        self._controlPanel = self._where

    @property
    def scenario(self):
        return self._scenario

    @property
    def controlPanel(self):
        return self._controlPanel

    @property
    def humanReadableLog(self):
        return "Scenario {} from control panel {} has been launched.".format(self._scenario, self._controlPanel)

class OWNLightingEvent(OWNEvent):

    def __init__(self, data):
        super().__init__(data)

        self._state = None
        self._brightness = None
        self._timer = None
        self._humanReadableLog = self._raw

        if self._what is not None and self._what != 1000:
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
    def isOn(self):
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

        if self._what is not None and self._what != 1000:
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
            self._isOpening = False
            self._isClosing = False
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
    
    @property
    def state(self):
        return self._state
    
    @property
    def isOpening(self):
        return self._isOpening

    @property
    def isClosing(self):
        return self._isClosing

    @property
    def isClosed(self):
        return self._isClosed

    @property
    def currentPosition(self):
        return self._position
    
    @property
    def humanReadableLog(self):
        return self._humanReadableLog

class OWNBurglarAlarmEvent(OWNEvent):

    def __init__(self, data):
        super().__init__(data)

        self._stateCode = int(self._what)
        self._state = None
        self._system = False
        self._zone = None
        self._sensor = None
        self._humanReadableLog = self._raw

        if self._where == "*":
            self._system = True
            self._humanReadableLog = "System is reporting: "
        elif self._where.startswith('#'):
            self._zone = str(self._where)[1:]
            if self._zone == '12':
                self._zone = 'c'
            elif self._zone == '15':
                self._zone = 'f'
            else:
                self._sensor = int(self._zone[1:])
                self._zone = int(self._zone[0])
            self._humanReadableLog = "Zone {} is reporting: ".format(self._zone)
        else:
            self._zone = int(str(self._where)[0])
            self._sensor = int(str(self._where)[1:])
            if self._zone == 0 :
                self._humanReadableLog = "Device {} in input zone is reporting: ".format(self._sensor)
            else:
                self._humanReadableLog = "Sensor {} in zone {} is reporting: ".format(self._sensor, self._zone)

        if self._stateCode == 0:
            self._state = 'maintenance'
        elif self._stateCode == 1:
            self._state = 'activation'
        elif self._stateCode == 2:
            self._state = 'deactivation'
        elif self._stateCode == 3:
            self._state = 'delay end'
        elif self._stateCode == 4:
            self._state = 'system battery fault'
        elif self._stateCode == 5:
            self._state = 'battery ok'
        elif self._stateCode == 6:
            self._state = 'no network'
        elif self._stateCode == 7:
            self._state = 'network present'
        elif self._stateCode == 8:
            self._state = 'engage'
        elif self._stateCode == 9:
            self._state = 'disengage'
        elif self._stateCode == 10:
            self._state = 'battery unloads'
        elif self._stateCode == 11:
            self._state = 'active zone'
        elif self._stateCode == 12:
            self._state = 'technical alarm'
        elif self._stateCode == 13:
            self._state = 'reset technical alarm'
        elif self._stateCode == 14:
            self._state = 'no reception'
        elif self._stateCode == 15:
            self._state = 'intrusion alarm'
        elif self._stateCode == 16:
            self._state = 'tampering'
        elif self._stateCode == 17:
            self._state = 'anti-panic alarm'
        elif self._stateCode == 18:
            self._state = 'non-active zone'
        elif self._stateCode == 26:
            self._state = 'start programming'
        elif self._stateCode == 27:
            self._state = 'stop programming'
        elif self._stateCode == 31:
            self._state = 'silent alarm'

        self._humanReadableLog = self._humanReadableLog + "'{}'.".format(self._state)

    @property
    def general(self):
        return self._system
    
    @property
    def zone(self):
        return self._zone

    @property
    def sensor(self):
        return self._sensor

    @property
    def isActive(self):
        return self._stateCode == 1 or self._stateCode == 11

    @property
    def isEngaged(self):
        return self._stateCode == 8

    @property
    def isAlarm(self):
        return self._stateCode == 12 or self._stateCode == 15 or self._stateCode == 16 or self._stateCode == 17 or self._stateCode == 31

    @property
    def humanReadableLog(self):
        return self._humanReadableLog
            


class OWNCENEvent(OWNEvent):

    def __init__(self, data):
        super().__init__(data)

        self._state = self._whatParam[0]
        self._pushButton = self._what
        self._object = self._where

        if self._state == None:
            self._humanReadableLog = "Button {} of CEN object {} has been pressed.".format(self._pushButton, self._object)
        elif int(self._state) == 3:
            self._humanReadableLog = "Button {} of CEN object {} is being held pressed.".format(self._pushButton, self._object)
        elif int(self._state) == 1:
            self._humanReadableLog = "Button {} of CEN object {} has been released after a short press.".format(self._pushButton, self._object)
        elif int(self._state) == 2:
            self._humanReadableLog = "Button {} of CEN object {} has been released after a long press.".format(self._pushButton, self._object)

    @property
    def isPressed(self):
        return self._state == None

    @property
    def isHeld(self):
        return int(self._state) == 3

    @property
    def isReleasedAfterShortPress(self):
        return int(self._state) == 1

    @property
    def isReleasedAfterLongPress(self):
        return int(self._state) == 2

    @property
    def humanReadableLog(self):
        return self._humanReadableLog

class OWNEnergyEvent(OWNEvent):
    def __init__(self, data):
        super().__init__(data)

        if  not str(self._where).startswith('5'):
            return None
        
        self._sensor = str(self._where)[1:]
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
                self._humanReadableLog = "Sensor {} is reporting an active power draw of {} W.".format(self._sensor, self._activePower)
            elif self._dimension == 511:
                _now = datetime.date.today()
                _messageDate =  datetime.date(_now.year, int(self._dimensionParam[0]), int(self._dimensionParam[1]))
                if _messageDate > _now:
                    _messageDate.replace(year= _now.year - 1)

                if int(self._dimensionValue[0]) != 25:
                    self._hourlyConsumption['date'] = _messageDate
                    self._hourlyConsumption['hour'] = int(self._dimensionValue[0])
                    self._hourlyConsumption['value'] = int(self._dimensionValue[1])
                    self._humanReadableLog = "Sensor {} is reporting a power consumtion of {} Wh for {} at {}.".format(self._sensor, self._hourlyConsumption['value'], self._hourlyConsumption['date'], self._hourlyConsumption['hour'])
                else:
                    self._hourlyConsumption['date'] = _messageDate
                    self._dailyConsumption['value'] = int(self._dimensionValue[1])
                    self._humanReadableLog = "Sensor {} is reporting a power consumtion of {} Wh for {}.".format(self._sensor, self._hourlyConsumption['value'], self._hourlyConsumption['date'])
                    
            elif self._dimension == 54:
                self._currentDayPartialConsumption = int(self._dimensionValue[0])
                self._humanReadableLog = "Sensor {} is reporting a power consumtion of {} Wh up to now today.".format(self._sensor, self._hourlyConsumption['value'])
            elif self._dimension == 52:
                _messageDate =  datetime.date(int("20" + str(self._dimensionParam[0])), self._dimensionParam[1], 1)
                self._monthlyConsumption['date'] = _messageDate
                self._monthlyConsumption['value'] = int(self._dimensionValue[0])
                self._humanReadableLog = "Sensor {} is reporting a power consumtion of {} Wh for {}.".format(self._sensor, self._monthlyConsumption['value'], self._monthlyConsumption['date'].strftime("%B %Y"))
            elif self._dimension == 53:
                self._currentMonthPartialConsumption = int(self._dimensionValue[0])
                self._humanReadableLog = "Sensor {} is reporting a power consumtion of {} Wh up to now this month.".format(self._sensor, self._currentMonthPartialConsumption['value'])

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
        
class OWNDryContactEvent(OWNEvent):

    def __init__(self, data):
        super().__init__(data)

        self._state = 1 if self._what == 31 else 0
        self._detection = int(self._whatParam[0])
        self._sensor = str(self._where)[1:]

        if self._detection == 1:
            self._humanReadableLog = "Sensor {} detected {}.".format(self._sensor, "ON" if self._state == 1 else "OFF")
        else:
            self._humanReadableLog = "Sensor {} reported {}.".format(self._sensor, "ON" if self._state == 1 else "OFF")

    @property
    def isOn(self):
        return self._state == 1
    
    @property
    def isDetection(self):
        return self._detection == 1

    @property
    def humanReadableLog(self):
        return self._humanReadableLog


class OWNCENPlusEvent(OWNEvent):

    def __init__(self, data):
        super().__init__(data)

        self._state = self._what
        self._pushButton = int(self._whatParam[0])
        self._object = str(self._where)[1:]

        if self._state == 21:
            self._humanReadableLog = "Button {} of CEN+ object {} has been pressed".format(self._pushButton, self._object)
        elif self._state == 22:
            self._humanReadableLog = "Button {} of CEN+ object {} is being held pressed".format(self._pushButton, self._object)
        elif self._state == 23:
            self._humanReadableLog = "Button {} of CEN+ object {} is still being held pressed".format(self._pushButton, self._object)
        elif self._state == 24:
            self._humanReadableLog = "Button {} of CEN+ object {} has been released".format(self._pushButton, self._object)
        elif self._state == 25:
            self._humanReadableLog = "Button {} of CEN+ object {} has been slowly rotated clockwise".format(self._pushButton, self._object)
        elif self._state == 26:
            self._humanReadableLog = "Button {} of CEN+ object {} has been quickly rotated clockwise".format(self._pushButton, self._object)
        elif self._state == 27:
            self._humanReadableLog = "Button {} of CEN+ object {} has been slowly rotated counter-clockwise".format(self._pushButton, self._object)
        elif self._state == 28:
            self._humanReadableLog = "Button {} of CEN+ object {} has been quickly rotated counter-clockwise".format(self._pushButton, self._object)
    
    @property
    def isShortPressed(self):
        return self._state == 21

    @property
    def isHeld(self):
        return self._state == 22
    
    @property
    def isStillHeld(self):
        return self._state == 23

    @property
    def isReleased(self):
        return self._state == 24

    @property
    def isSlowlyTurnedCW(self):
        return self._state == 25

    @property
    def isQuicklyTurnedCW(self):
        return self._state == 26

    @property
    def isSlowlyTurnedCCW(self):
        return self._state == 27

    @property
    def isQuicklyTurnedCCW(self):
        return self._state == 28

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

class OWNLightingCommand(OWNCommand):

    def __init__(self, data):
        super().__init__(data)

    @classmethod
    def switchON(cls, _where):
        return cls("*1*1*{}##".format(_where))

    @classmethod
    def switchOFF(cls, _where):
        return cls("*1*0*{}##".format(_where))

    # @classmethod
    # def setLightTo(cls, _where, _level=30):
    #     _level = round(_level/10)
    #     if _level == 1:
    #         _level = 2
    #     return cls("*1*{}*{}##".format(_level, _where))

    @classmethod
    def setBrightness(cls, _where, _level=30):
        _level = int(_level)+100
        return cls("*#1*{}#1*{}*2##".format(_where, _level))

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