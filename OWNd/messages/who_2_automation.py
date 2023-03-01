"""OpenWebNet messages related to covers and orther automation systems (WHO=2)"""


from typing import Optional, Union

from .base_message import OWNCommand, OWNEvent


class OWNAutomationEvent(OWNEvent):
    def __init__(self, data: Union[OWNEvent, str]):

        if isinstance(data, OWNEvent):
            for key, val in vars(data).items():
                setattr(self, key, val)
        else:
            super().__init__(data)

        self._state: Optional[int] = None
        self._position: Optional[int] = None
        self._priority: Optional[str] = None
        self._info: Optional[int] = None
        self._is_opening: Optional[bool] = None
        self._is_closing: Optional[bool] = None
        self._is_closed: Optional[bool] = None

        if self._what is not None and self._what != 1000:
            self._state = self._what

        if self._dimension is not None:
            if self._dimension == 10 and self._dimension_value is not None:
                self._state = int(self._dimension_value[0])
                self._position = int(self._dimension_value[1])
                self._priority = self._dimension_value[2]
                self._info = int(self._dimension_value[3])

        if self._state == 0:
            self._human_readable_log = f"Cover {self._where} stopped."
            self._is_opening = False
            self._is_closing = False
        elif self._state == 10:
            self._is_opening = False
            self._is_closing = False
            if self._position == 0:
                self._human_readable_log = f"Cover {self._where} is closed."
                self._is_closed = True
            else:
                self._human_readable_log = (
                    f"Cover {self._where} is opened at {self._position}%."
                )
                self._is_closed = False
        else:
            if self._state == 1:
                self._human_readable_log = f"Cover {self._where} is opening."
                self._is_opening = True
                self._is_closing = False
            elif self._state == 11 or self._state == 13:
                self._human_readable_log = f"Cover {self._where} is opening from initial position {self._position}."  # pylint: disable=line-too-long
                self._is_opening = True
                self._is_closing = False
                self._is_closed = False
            elif self._state == 2:
                self._human_readable_log = f"Cover {self._where} is closing."
                self._is_closing = True
                self._is_opening = False
            elif self._state == 12 or self._state == 14:
                self._human_readable_log = f"Cover {self._where} is closing from initial position {self._position}."  # pylint: disable=line-too-long
                self._is_closing = True
                self._is_opening = False
                self._is_closed = False

    @property
    def state(self):
        return self._state

    @property
    def is_opening(self):
        return self._is_opening

    @property
    def is_closing(self):
        return self._is_closing

    @property
    def is_closed(self):
        return self._is_closed

    @property
    def current_position(self):
        return self._position


class OWNAutomationCommand(OWNCommand):
    _human_readable_log: str  # Utterly useless but it makes pylint less grumpy

    @classmethod
    def status(cls, where: str):
        message = cls(f"*#2*{where}##")
        message._human_readable_log = f"Requesting shutter {where} status."
        return message

    @classmethod
    def raise_shutter(cls, where: str):
        message = cls(f"*2*1*{where}##")
        message._human_readable_log = f"Raising shutter {where}."
        return message

    @classmethod
    def lower_shutter(cls, where: str):
        message = cls(f"*2*2*{where}##")
        message._human_readable_log = f"Lowering shutter {where}."
        return message

    @classmethod
    def stop_shutter(cls, where: str):
        message = cls(f"*2*0*{where}##")
        message._human_readable_log = f"Stoping shutter {where}."
        return message

    @classmethod
    def set_shutter_level(cls, where: str, level: int = 30):
        message = cls(f"*#2*{where}*#11#001*{level}##")
        message._human_readable_log = f"Setting shutter {where} position to {level}%."
        return message
