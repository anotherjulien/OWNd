"""OpenWebNet messages related to the heating and cooling systems (WHO=4)"""

import re

from typing import Optional, Tuple, Union

from ..const import (
    CLIMATE_MODE_AUTO,
    CLIMATE_MODE_COOL,
    CLIMATE_MODE_HEAT,
    CLIMATE_MODE_OFF,
    MESSAGE_TYPE_ACTION,
    MESSAGE_TYPE_LOCAL_OFFSET,
    MESSAGE_TYPE_LOCAL_TARGET_TEMPERATURE,
    MESSAGE_TYPE_MAIN_HUMIDITY,
    MESSAGE_TYPE_MAIN_TEMPERATURE,
    MESSAGE_TYPE_MODE,
    MESSAGE_TYPE_MODE_TARGET,
    MESSAGE_TYPE_SECONDARY_TEMPERATURE,
    MESSAGE_TYPE_TARGET_TEMPERATURE,
)
from .base_message import OWNCommand, OWNEvent


class OWNHeatingEvent(OWNEvent):
    def __init__(self, data: Union[OWNEvent, str]):

        if isinstance(data, OWNEvent):
            for key, val in vars(data).items():
                setattr(self, key, val)
        else:
            super().__init__(data)

        self._type: Optional[str] = None

        self._zone: int = (
            int(self._where[1:]) if self._where.startswith("#") else int(self._where)
        )
        if self._zone == 0 and self._where_param:
            self._zone = int(self._where_param[0])
        self._sensor: Optional[int] = None
        if self._zone > 99:
            self._sensor = int(str(self._zone)[:1])
            self._zone = int(str(self._zone)[1:])
        self._actuator = None

        self._mode: Optional[int] = None
        self._mode_name: Optional[str] = None
        self._set_temperature: Optional[float] = None
        self._local_offset: Optional[int] = None
        self._local_set_temperature: Optional[float] = None
        self._measured_temperature: Optional[float] = None
        self._secondary_temperature: Optional[float] = None
        self._measured_humidity: Optional[float] = None

        self._is_active: Optional[bool] = None
        self._is_heating: Optional[bool] = None
        self._is_cooling: Optional[bool] = None

        self._fan_on: Optional[bool] = None
        self._fan_speed: Optional[int] = None
        self._cooling_fan_on: Optional[bool] = None
        self._cooling_fan_speed: Optional[int] = None

        _valve_active_states = ("1", "2", "6", "7", "8")
        _actuator_active_states = ("1", "2", "6", "7", "8", "9")

        if self._what is not None:
            self._mode = int(self._what)
            if self._mode in [103, 203, 303, 102, 202, 302]:
                self._type = MESSAGE_TYPE_MODE
                self._mode_name = CLIMATE_MODE_OFF
                self._human_readable_log = (
                    f"Zone {self._zone}'s mode is set to '{self._mode_name}'"
                )
            elif (
                self._mode in [0, 210, 211, 215]
                or (self._mode >= 2101 and self._mode <= 2103)
                or (self._mode >= 2201 and self._mode <= 2216)
            ):
                self._type = MESSAGE_TYPE_MODE
                self._mode_name = CLIMATE_MODE_COOL
                self._human_readable_log = (
                    f"Zone {self._zone}'s mode is set to '{self._mode_name}'"
                )
            elif (
                self._mode in [1, 110, 111, 115]
                or (self._mode >= 1101 and self._mode <= 1103)
                or (self._mode >= 1201 and self._mode <= 1216)
            ):
                self._type = MESSAGE_TYPE_MODE
                self._mode_name = CLIMATE_MODE_HEAT
                self._human_readable_log = (
                    f"Zone {self._zone}'s mode is set to '{self._mode_name}'"
                )
            elif (
                self._mode in [310, 311, 315]
                or (self._mode >= 23001 and self._mode <= 23255)
                or (self._mode >= 13001 and self._mode <= 13255)
            ):
                self._type = MESSAGE_TYPE_MODE
                self._mode_name = CLIMATE_MODE_AUTO
                self._human_readable_log = (
                    f"Zone {self._zone}'s mode is set to '{self._mode_name}'"
                )
            elif self._mode == 20:
                self._mode_name = None
                self._human_readable_log = (
                    f"Zone {self._zone}'s remote control is disabled"
                )
            elif self._mode == 21:
                self._mode_name = None
                self._human_readable_log = (
                    f"Zone {self._zone}'s remote control is enabled"
                )
            else:
                self._mode_name = None
                self._human_readable_log = f"Zone {self._zone}'s mode is unknown"

            if (
                self._type == MESSAGE_TYPE_MODE
                and self._what_param
                and self._what_param[0] is not None
            ):
                self._type = MESSAGE_TYPE_MODE_TARGET
                self._set_temperature = float(
                    f"{self._what_param[0][1:3]}.{self._what_param[0][-1]}"
                )
                self._human_readable_log += f" at {self._set_temperature}°C."
            else:
                self._human_readable_log += "."

        if self._dimension == 0 and self._dimension_value:  # Temperature
            if self._sensor is None:
                self._type = MESSAGE_TYPE_MAIN_TEMPERATURE
                self._measured_temperature = float(
                    f"{self._dimension_value[0][1:3]}.{self._dimension_value[0][-1]}"
                )
                self._human_readable_log = f"Zone {self._zone}'s main sensor is reporting a temperature of {self._measured_temperature}°C."  # pylint: disable=line-too-long
            else:
                self._type = MESSAGE_TYPE_SECONDARY_TEMPERATURE
                self._secondary_temperature = float(
                    f"{self._dimension_value[0][1:3]}.{self._dimension_value[0][-1]}"
                )
                self._human_readable_log = f"Zone {self._zone}'s secondary sensor {self._sensor} is reporting a temperature of {self._secondary_temperature}°C."  # pylint: disable=line-too-long

        elif self._dimension == 11 and self._dimension_value:  # Fan speed
            _fan_mode = int(self._dimension_value[0])
            if _fan_mode < 4:
                self._fan_on = True
                self._is_active = True
                if _fan_mode > 0:
                    self._fan_speed = _fan_mode
                    self._human_readable_log = (
                        f"Zone {self._zone}'s fan is on at speed {self._fan_speed}."
                    )
                else:
                    self._human_readable_log = (
                        f"Zone {self._zone}'s fan is on at 'Auto' speed."
                    )
            else:
                self._fan_on = False
                self._is_active = False
                self._human_readable_log = f"Zone {self._zone}'s fan is off."

        elif (
            self._dimension == 12 and self._dimension_value
        ):  # Local set temperature (set+offset)
            self._type = MESSAGE_TYPE_LOCAL_TARGET_TEMPERATURE
            self._local_set_temperature = float(
                f"{self._dimension_value[0][1:3]}.{self._dimension_value[0][-1]}"
            )
            self._human_readable_log = f"Zone {self._zone}'s local target temperature is set to {self._local_set_temperature}°C."  # pylint: disable=line-too-long

        elif self._dimension == 13 and self._dimension_value:  # Local offset
            self._type = MESSAGE_TYPE_LOCAL_OFFSET
            if (
                self._dimension_value[0] == "0"
                or self._dimension_value[0] == "00"
                or self._dimension_value[0] == "4"
                or self._dimension_value[0] == "5"
                or self._dimension_value[0] == "6"
                or self._dimension_value[0] == "7"
                or self._dimension_value[0] == "8"
            ):
                self._local_offset = 0
            elif self._dimension_value[0].startswith("0"):
                self._local_offset = int(f"{self._dimension_value[0][1:]}")
            else:
                self._local_offset = -int(f"{self._dimension_value[0][1:]}")
            self._human_readable_log = (
                f"Zone {self._zone}'s local offset is set to {self._local_offset}°C."
            )

        elif self._dimension == 14 and self._dimension_value:  # Set temperature
            self._type = MESSAGE_TYPE_TARGET_TEMPERATURE
            self._set_temperature = float(
                f"{self._dimension_value[0][1:3]}.{self._dimension_value[0][-1]}"
            )
            self._human_readable_log = f"Zone {self._zone}'s target temperature is set to {self._set_temperature}°C."  # pylint: disable=line-too-long

        elif self._dimension == 19 and self._dimension_value:  # Valves status
            self._type = MESSAGE_TYPE_ACTION
            self._is_cooling = self._dimension_value[0] in _valve_active_states
            self._is_heating = self._dimension_value[1] in _valve_active_states
            self._is_active = self._is_cooling | self._is_heating
            # Handle cooling valve status relative to fan speed/status
            _cooling_value = int(self._dimension_value[0])
            if _cooling_value == 0:
                self._human_readable_log = f"Zone {self._zone}'s cooling valve is off"
            elif _cooling_value == 1:
                self._human_readable_log = f"Zone {self._zone}'s cooling valve is on"
            elif _cooling_value == 2:
                self._human_readable_log = (
                    f"Zone {self._zone}'s cooling valve is opened"
                )
            elif _cooling_value == 3:
                self._human_readable_log = (
                    f"Zone {self._zone}'s cooling valve is closed"
                )
            elif _cooling_value == 4:
                self._human_readable_log = (
                    f"Zone {self._zone}'s cooling valve is stopped"
                )
            elif _cooling_value > 4:
                _fan_mode = _cooling_value - 5
                if _fan_mode > 0:
                    self._cooling_fan_on = True
                    self._is_active = True
                    self._cooling_fan_speed = _fan_mode
                    self._human_readable_log = f"Zone {self._zone}'s cooling fan is on at speed {self._fan_speed}"  # pylint: disable=line-too-long
                else:
                    self._cooling_fan_on = False
                    self._is_active = False
                    self._human_readable_log = f"Zone {self._zone}'s cooling fan is off"
            # Handle heating valve status relative to fan speed/status
            _heating_value = int(self._dimension_value[1])
            if _heating_value == 0:
                self._human_readable_log += "; heating valve is off."
            elif _heating_value == 1:
                self._human_readable_log += "; heating valve is on."
            elif _heating_value == 2:
                self._human_readable_log += "; heating valve is opened."
            elif _heating_value == 3:
                self._human_readable_log += "; heating valve is closed."
            elif _heating_value == 4:
                self._human_readable_log += "; heating valve is stopped."
            elif _heating_value > 4:
                _fan_mode = _heating_value - 5
                if _fan_mode > 0:
                    self._fan_on = True
                    self._is_active = True
                    self._fan_speed = _fan_mode
                    self._human_readable_log += (
                        f"; heating fan is on at speed {self._fan_speed}."
                    )
                else:
                    self._fan_on = False
                    self._is_active = False
                    self._human_readable_log += "; heating fan is off."

        elif self._dimension == 20 and self._dimension_value:  # Actuator status
            self._type = MESSAGE_TYPE_ACTION
            self._is_active = self._dimension_value[0] in _actuator_active_states
            self._actuator = (
                self._where_param[0] if self._where_param[0] is not None else 1
            )
            _value = int(self._dimension_value[0])
            if _value == 0:
                self._human_readable_log = (
                    f"Zone {self._zone}'s actuator {self._actuator} is off."
                )
            elif _value == 1:
                self._human_readable_log = (
                    f"Zone {self._zone}'s actuator {self._actuator} is on."
                )
            elif _value == 2:
                self._human_readable_log = (
                    f"Zone {self._zone}'s actuator {self._actuator} is opened."
                )
            elif _value == 3:
                self._human_readable_log = (
                    f"Zone {self._zone}'s actuator {self._actuator} is closed."
                )
            elif _value == 4:
                self._human_readable_log = (
                    f"Zone {self._zone}'s actuator {self._actuator} is stopped."
                )
            elif _value > 4:
                _fan_mode = _value - 5
                if _fan_mode > 0:
                    self._fan_on = True
                    self._is_active = True
                    if _fan_mode < 4:
                        self._fan_speed = _fan_mode
                        self._human_readable_log = (
                            f"Zone {self._zone}'s fan is on at speed {self._fan_speed}."
                        )
                    else:
                        self._human_readable_log = (
                            f"Zone {self._zone}'s fan is on at 'Auto' speed."
                        )
                else:
                    self._fan_on = False
                    self._is_active = False
                    self._human_readable_log = f"Zone {self._zone}'s fan is off."

        elif self._dimension == 60 and self._dimension_value:  # Humidity
            self._type = MESSAGE_TYPE_MAIN_HUMIDITY
            self._measured_humidity = float(self._dimension_value[0])
            self._human_readable_log = f"Zone {self._zone}'s main sensor is reporting a humidity of {self._measured_humidity}%."  # pylint: disable=line-too-long

    @property
    def unique_id(self) -> str:
        """The ID of the subject of this message"""
        if self._zone == 0:
            return f"{self._who}-#0"
        elif self._sensor is not None:
            return f"{self._who}-{self._where}"
        else:
            return f"{self._who}-{self._zone}"

    @property
    def message_type(self) -> Optional[str]:
        return self._type

    @property
    def zone(self) -> int:
        return self._zone

    @property
    def sensor(self) -> Optional[int]:
        return self._sensor

    @property
    def mode(self) -> Optional[str]:
        return self._mode_name

    def is_active(self) -> Optional[bool]:
        return self._is_active

    def is_heating(self) -> Optional[bool]:
        return self._is_heating

    def is_cooling(self) -> Optional[bool]:
        return self._is_cooling

    @property
    def main_temperature(self) -> Optional[float]:
        return self._measured_temperature

    @property
    def main_humidity(self) -> Optional[float]:
        return self._measured_humidity

    @property
    def secondary_temperature(self) -> Tuple[Optional[int], Optional[float]]:
        return (self._sensor, self._secondary_temperature)

    @property
    def set_temperature(self) -> Optional[float]:
        return self._set_temperature

    @property
    def local_offset(self) -> Optional[int]:
        return self._local_offset

    @property
    def local_set_temperature(self) -> Optional[float]:
        return self._local_set_temperature


class OWNHeatingCommand(OWNCommand):
    _human_readable_log: str  # Utterly useless but it makes pylint less grumpy

    @classmethod
    def status(cls, where: str):
        message = cls(f"*#4*{where}##")
        message._human_readable_log = f"Requesting climate status update for {message._where}{message._interface_log_text}."
        return message

    @classmethod
    def get_temperature(cls, where: str):
        message = cls(f"*#4*{where}*0##")
        message._human_readable_log = f"Requesting climate status update for {whmessage._where}{message._interface_log_textere}."
        return message

    @classmethod
    def set_mode(cls, where: str, mode: str, standalone: bool = False):
        central_local = re.compile(r"^#0#\d+$")
        if central_local.match(str(where)):
            zone = where
            zone_name = f"zone {int(where.split('#')[-1])}"
        else:
            zone = int(where.split("#")[-1]) if where.startswith("#") else int(where)
            zone_name = f"zone {zone}" if zone > 0 else "general"

            if standalone:
                zone = f"#{zone}" if zone == 0 else str(zone)
            else:
                zone = f"#{zone}"

        mode_name = mode
        if mode == CLIMATE_MODE_OFF:
            mode = "303"
        elif mode == CLIMATE_MODE_AUTO:
            mode = "311"
        else:
            return None

        message = cls(f"*4*{mode}*{zone}##")
        message._human_readable_log = f"Setting {zone_name} mode to '{mode_name}'."
        return message

    @classmethod
    def turn_off(cls, where: str, standalone: bool = False):
        return cls.set_mode(where=where, mode=CLIMATE_MODE_OFF, standalone=standalone)

    @classmethod
    def set_temperature(
        cls, where: str, temperature: float, mode: str, standalone: bool = False
    ):
        central_local = re.compile(r"^#0#\d+$")
        if central_local.match(str(where)):
            zone = where
            zone_name = f"zone {int(where.split('#')[-1])}"
        else:
            zone = int(where.split("#")[-1]) if where.startswith("#") else int(where)
            zone_name = f"zone {zone}" if zone > 0 else "general"

            if standalone:
                zone = f"#{zone}" if zone == 0 else str(zone)
            else:
                zone = f"#{zone}"

        temperature = round(temperature * 2) / 2
        if temperature < 5.0:
            temperature = 5.0
        elif temperature > 40.0:
            temperature = 40.0
        temperature_print = f"{temperature}"
        temperature = int(temperature * 10)

        mode_name = mode
        if mode == CLIMATE_MODE_HEAT:
            mode = "1"
        elif mode == CLIMATE_MODE_COOL:
            mode = "2"
        elif mode == CLIMATE_MODE_AUTO:
            mode = "3"

        message = cls(f"*#4*{zone}*#14*{temperature:04d}*{mode}##")
        message._human_readable_log = (
            f"Setting {zone_name} to {temperature_print}°C in mode '{mode_name}'."
        )
        return message
