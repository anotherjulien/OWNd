"""OpenWebNet messages related to lighting systems (WHO=1)"""

import datetime
from typing import Optional, Union

from ..const import (
    MESSAGE_TYPE_ILLUMINANCE,
    MESSAGE_TYPE_MOTION,
    MESSAGE_TYPE_MOTION_TIMEOUT,
    MESSAGE_TYPE_PIR_SENSITIVITY,
    PIR_SENSITIVITY_MAPPING,
)
from .base_message import OWNCommand, OWNEvent


class OWNLightingEvent(OWNEvent):
    def __init__(self, data: Union[OWNEvent, str]):

        if isinstance(data, OWNEvent):
            for key, val in vars(data).items():
                setattr(self, key, val)
        else:
            super().__init__(data)

        self._type: str
        self._state: Optional[int] = None
        self._brightness = None
        self._brightness_preset = None
        self._transition = None
        self._timer = None
        self._blinker = None
        self._illuminance = None
        self._motion = False
        self._pir_sensitivity = None
        self._motion_timeout: Optional[datetime.timedelta] = None

        if self._what is not None and self._what != 1000:
            self._state = self._what

            if self._state == 0:  # Light off
                self._human_readable_log = (
                    f"Light {self._where}{self._interface_log_text} is switched off."
                )
            elif self._state == 1:  # Light on
                self._human_readable_log = (
                    f"Light {self._where}{self._interface_log_text} is switched on."
                )
            elif self._state > 1 and self._state < 11:  # Light dimmed to preset value
                self._brightness_preset = self._state
                # self._brightness = self._state * 10
                self._human_readable_log = f"Light {self._where}{self._interface_log_text} is switched on at brightness level {self._state}."  # pylint: disable=line-too-long
            elif self._state == 11:  # Timer at 1m
                self._timer = 60
                self._human_readable_log = f"Light {self._where}{self._interface_log_text} is switched on for {self._timer}s."
            elif self._state == 12:  # Timer at 2m
                self._timer = 120
                self._human_readable_log = f"Light {self._where}{self._interface_log_text} is switched on for {self._timer}s."
            elif self._state == 13:  # Timer at 3m
                self._timer = 180
                self._human_readable_log = f"Light {self._where}{self._interface_log_text} is switched on for {self._timer}s."
            elif self._state == 14:  # Timer at 4m
                self._timer = 240
                self._human_readable_log = f"Light {self._where}{self._interface_log_text} is switched on for {self._timer}s."
            elif self._state == 15:  # Timer at 5m
                self._timer = 300
                self._human_readable_log = f"Light {self._where}{self._interface_log_text} is switched on for {self._timer}s."
            elif self._state == 16:  # Timer at 15m
                self._timer = 900
                self._human_readable_log = f"Light {self._where}{self._interface_log_text} is switched on for {self._timer}s."
            elif self._state == 17:  # Timer at 30s
                self._timer = 30
                self._human_readable_log = f"Light {self._where}{self._interface_log_text} is switched on for {self._timer}s."
            elif self._state == 18:  # Timer at 0.5s
                self._timer = 0.5
                self._human_readable_log = f"Light {self._where}{self._interface_log_text} is switched on for {self._timer}s."
            elif self._state >= 20 and self._state <= 29:  # Light blinking
                self._blinker = 0.5 * (self._state - 19)
                self._human_readable_log = f"Light {self._where}{self._interface_log_text} is blinking every {self._blinker}s."
            elif self._state == 34:  # Motion detected
                self._type = MESSAGE_TYPE_MOTION
                self._motion = True
                self._human_readable_log = f"Light/motion sensor {self._where}{self._interface_log_text} detected motion"

        if self._dimension is not None:
            if (
                self._dimension == 1 or self._dimension == 4
            ) and self._dimension_value is not None:  # Brightness value
                self._brightness = int(self._dimension_value[0]) - 100
                self._transition = int(self._dimension_value[1])
                if self._brightness == 0:
                    self._state = 0
                    self._human_readable_log = f"Light {self._where}{self._interface_log_text} is switched off."
                else:
                    self._state = 1
                    self._human_readable_log = f"Light {self._where}{self._interface_log_text} is switched on at {self._brightness}%."
            elif (
                self._dimension == 2 and self._dimension_value is not None
            ):  # Time value
                self._timer = (
                    int(self._dimension_value[0]) * 3600
                    + int(self._dimension_value[1]) * 60
                    + int(self._dimension_value[2])
                )
                self._human_readable_log = f"Light {self._where}{self._interface_log_text} is switched on for {self._timer}s."
            elif (
                self._dimension == 5 and self._dimension_value is not None
            ):  # PIR sensitivity
                self._type = MESSAGE_TYPE_PIR_SENSITIVITY
                self._pir_sensitivity = int(self._dimension_value[0])
                self._human_readable_log = f"Light/motion sensor {self._where}{self._interface_log_text} PIR sesitivity is {PIR_SENSITIVITY_MAPPING[self._pir_sensitivity]}."  # pylint: disable=line-too-long
            elif (
                self._dimension == 6 and self._dimension_value is not None
            ):  # Illuminance value
                self._type = MESSAGE_TYPE_ILLUMINANCE
                self._illuminance = int(self._dimension_value[0])
                self._human_readable_log = f"Light/motion sensor {self._where}{self._interface_log_text} detected an illuminance value of {self._illuminance} lx."  # pylint: disable=line-too-long
            elif (
                self._dimension == 7 and self._dimension_value is not None
            ):  # Motion timeout value
                self._type = MESSAGE_TYPE_MOTION_TIMEOUT
                self._motion_timeout = datetime.timedelta(
                    hours=int(self._dimension_value[0]),
                    minutes=int(self._dimension_value[1]),
                    seconds=int(self._dimension_value[2]),
                )
                self._human_readable_log = f"Light/motion sensor {self._where}{self._interface_log_text} has timeout set to {self._motion_timeout}."  # pylint: disable=line-too-long
            elif self._dimension_value is not None:
                self._human_readable_log = f"Light/motion sensor {self._where}{self._interface_log_text} has sent an unknown dimension {self._dimension}."
            else:
                pass

    @property
    def message_type(self):
        return self._type

    @property
    def entity(self) -> str:
        _message_type_mapping = {
            MESSAGE_TYPE_ILLUMINANCE: "-illuminance",
            MESSAGE_TYPE_MOTION: "-motion",
            MESSAGE_TYPE_PIR_SENSITIVITY: "-motion",
            MESSAGE_TYPE_MOTION_TIMEOUT: "-motion",
        }
        return f"{self.unique_id}{_message_type_mapping.get(self._type, '')}"

    @property
    def brightness_preset(self):
        return self._brightness_preset

    @property
    def brightness(self):
        return self._brightness

    @property
    def transition(self):
        return self._transition

    @property
    def is_on(self) -> bool:
        return 0 < self._state < 32 if self._state is not None else False

    @property
    def timer(self):
        return self._timer

    @property
    def blinker(self):
        return self._blinker

    @property
    def illuminance(self):
        return self._illuminance

    @property
    def motion(self) -> bool:
        return self._motion

    @property
    def pir_sensitivity(self):
        return self._pir_sensitivity

    @property
    def motion_timeout(self) -> Optional[datetime.timedelta]:
        return self._motion_timeout


class OWNLightingStatusEvent(OWNLightingEvent):
    """Modeling status impacting events"""

    _state: int

    @property
    def is_on(self) -> bool:
        return 0 < self._state < 32


class OWNLightingCommand(OWNCommand):
    _human_readable_log: str  # Utterly useless but it makes pylint less grumpy

    @classmethod
    def status(cls, where: str):
        message = cls(f"*#1*{where}##")
        message._human_readable_log = f"Requesting light or switch {message._where}{message._interface_log_text} status."
        return message

    @classmethod
    def get_brightness(cls, where: str):
        message = cls(f"*#1*{where}*1##")
        message._human_readable_log = f"Requesting light {message._where}{message._interface_log_text} brightness."
        return message

    @classmethod
    def get_pir_sensitivity(cls, where: str):
        message = cls(f"*#1*{where}*5##")
        message._human_readable_log = f"Requesting light/motion sensor {message._where}{message._interface_log_text} PIR sensitivity."
        return message

    @classmethod
    def get_illuminance(cls, where: str):
        message = cls(f"*#1*{where}*6##")
        message._human_readable_log = f"Requesting light/motion sensor {message._where}{message._interface_log_text} illuminance."
        return message

    @classmethod
    def get_motion_timeout(cls, where: str):
        message = cls(f"*#1*{where}*7##")
        message._human_readable_log = f"Requesting light/motion sensor {message._where}{message._interface_log_text} motion timeout."
        return message

    @classmethod
    def flash(cls, where: str, _freqency: float = 0.5):
        if _freqency is not None and _freqency >= 0.5 and _freqency <= 5:
            _freqency = round(_freqency * 2) / 2
        else:
            _freqency = 0.5
        _what = int((_freqency / 0.5) + 19)
        message = cls(f"*1*{_what}*{where}##")
        message._human_readable_log = f"Flashing light {message._where}{message._interface_log_text} every {_freqency}s."
        return message

    @classmethod
    def switch_on(cls, where: str, _transition: Optional[int] = None):
        if _transition is not None:
            _transition_speed = normalize_transition_speed(_transition)
            message = cls(f"*1*1#{_transition_speed}*{where}##")
            message._human_readable_log = f"Switching ON light {message._where}{message._interface_log_text} with transition speed {_transition}."
        else:
            message = cls(f"*1*1*{where}##")
            message._human_readable_log = f"Switching ON light or switch {message._where}{message._interface_log_text}."
        return message

    @classmethod
    def switch_off(cls, where: str, _transition: Optional[int] = None):
        if _transition is not None:
            _transition_speed = normalize_transition_speed(_transition)
            message = cls(f"*1*0#{_transition_speed}*{where}##")
            message._human_readable_log = f"Switching OFF light {message._where}{message._interface_log_text} with transition speed {_transition}."
        else:
            message = cls(f"*1*0*{where}##")
            message._human_readable_log = f"Switching OFF light or switch {message._where}{message._interface_log_text}."
        return message

    @classmethod
    def set_brightness(
        cls, where: str, _level: int = 30, _transition: Optional[int] = None
    ):
        command_level = int(_level) + 100
        _transition_speed = normalize_transition_speed(_transition)
        message = cls(f"*#1*{where}*#1*{command_level}*{_transition_speed}##")
        message._human_readable_log = (
            f"Setting light {message._where}{message._interface_log_text} brightness to {_level}% with transition speed {transition_speed}."  # pylint: disable=line-too-long
            if transition_speed > 0
            else f"Setting light {message._where}{message._interface_log_text} brightness to {_level}%."
        )
        return message


def normalize_transition_speed(_transition: Optional[int] = None) -> int:
    if _transition is not None:
        if _transition >= 0 and _transition <= 255:
            return _transition
        elif _transition < 0:
            return 0
        elif _transition > 255:
            return 255
    return 0
