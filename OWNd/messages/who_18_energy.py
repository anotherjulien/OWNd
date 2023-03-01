"""OpenWebNet messages related to energy systems (WHO=18)"""
import datetime
from typing import Optional

from .base_message import OWNCommand, OWNEvent
from ..const import (
    MESSAGE_TYPE_ACTIVE_POWER,
    MESSAGE_TYPE_CURRENT_DAY_CONSUMPTION,
    MESSAGE_TYPE_CURRENT_MONTH_CONSUMPTION,
    MESSAGE_TYPE_DAILY_CONSUMPTION,
    MESSAGE_TYPE_ENERGY_TOTALIZER,
    MESSAGE_TYPE_HOURLY_CONSUMPTION,
    MESSAGE_TYPE_MONTHLY_CONSUMPTION,
)


class OWNEnergyEvent(OWNEvent):
    def __init__(self, data):
        super().__init__(data)

        if not self._where.startswith("5") and not self._where.startswith("7"):
            return None

        self._type = None
        self._sensor = self._where[1:]
        self._active_power = 0
        self._total_consumption = 0
        self._hourly_consumption = dict()
        self._daily_consumption = dict()
        self._current_day_partial_consumption = 0
        self._monthly_consumption = dict()
        self._current_month_partial_consumption = 0

        if self._dimension is not None:
            if self._dimension == 113:
                self._type = MESSAGE_TYPE_ACTIVE_POWER
                self._active_power = int(self._dimension_value[0])
                self._human_readable_log = f"Sensor {self._sensor} is reporting an active power draw of {self._active_power} W."  # pylint: disable=line-too-long
            elif self._dimension == 511:
                _now = datetime.date.today()
                _raw_message_date = datetime.date(
                    _now.year,
                    int(self._dimension_param[0]),
                    int(self._dimension_param[1]),
                )
                try:
                    if _raw_message_date > _now:
                        _message_date = datetime.date(
                            _now.year - 1,
                            int(self._dimension_param[0]),
                            int(self._dimension_param[1]),
                        )
                    else:
                        _message_date = datetime.date(
                            _now.year,
                            int(self._dimension_param[0]),
                            int(self._dimension_param[1]),
                        )
                except ValueError:
                    return None

                if int(self._dimension_value[0]) != 25:
                    self._type = MESSAGE_TYPE_HOURLY_CONSUMPTION
                    self._hourly_consumption["date"] = _message_date
                    self._hourly_consumption["hour"] = int(self._dimension_value[0]) - 1
                    self._hourly_consumption["value"] = int(self._dimension_value[1])
                    self._human_readable_log = f"Sensor {self._sensor} is reporting a power consumption of {self._hourly_consumption['value']} Wh for {self._hourly_consumption['date']} at {self._hourly_consumption['hour']}."  # pylint: disable=line-too-long
                else:
                    self._type = MESSAGE_TYPE_DAILY_CONSUMPTION
                    self._daily_consumption["date"] = _message_date
                    self._daily_consumption["value"] = int(self._dimension_value[1])
                    self._human_readable_log = f"Sensor {self._sensor} is reporting a power consumption of {self._daily_consumption['value']} Wh for {self._daily_consumption['date']}."  # pylint: disable=line-too-long
            elif self._dimension == 513 or self._dimension == 514:
                _now = datetime.date.today()
                _raw_message_date = datetime.date(
                    _now.year, int(self._dimension_param[0]), 1
                )
                try:
                    if self._dimension == 513 and _raw_message_date > _now:
                        _message_date = datetime.date(
                            _now.year - 1,
                            int(self._dimension_param[0]),
                            int(self._dimension_value[0]),
                        )
                    elif self._dimension == 514:
                        if _raw_message_date > _now:
                            _message_date = datetime.date(
                                _now.year - 2,
                                int(self._dimension_param[0]),
                                int(self._dimension_value[0]),
                            )
                        else:
                            _message_date = datetime.date(
                                _now.year - 1,
                                int(self._dimension_param[0]),
                                int(self._dimension_value[0]),
                            )
                    else:
                        _message_date = datetime.date(
                            _now.year,
                            int(self._dimension_param[0]),
                            int(self._dimension_value[0]),
                        )
                except ValueError:
                    return None
                self._type = MESSAGE_TYPE_DAILY_CONSUMPTION
                self._daily_consumption["date"] = _message_date
                self._daily_consumption["value"] = int(self._dimension_value[1])
                self._human_readable_log = f"Sensor {self._sensor} is reporting a power consumption of {self._daily_consumption['value']} Wh for {self._daily_consumption['date']}."  # pylint: disable=line-too-long
            elif self._dimension == 51:
                self._type = MESSAGE_TYPE_ENERGY_TOTALIZER
                self._total_consumption = int(self._dimension_value[0])
                self._human_readable_log = f"Sensor {self._sensor} is reporting a total power consumption of {self._total_consumption} Wh."  # pylint: disable=line-too-long
            elif self._dimension == 54:
                self._type = MESSAGE_TYPE_CURRENT_DAY_CONSUMPTION
                self._current_day_partial_consumption = int(self._dimension_value[0])
                self._human_readable_log = f"Sensor {self._sensor} is reporting a power consumption of {self._current_day_partial_consumption} Wh up to now today."  # pylint: disable=line-too-long
            elif self._dimension == 52:
                self._type = MESSAGE_TYPE_MONTHLY_CONSUMPTION
                _message_date = datetime.date(
                    int(f"20{self._dimension_param[0]}"), self._dimension_param[1], 1
                )
                self._monthly_consumption["date"] = _message_date
                self._monthly_consumption["value"] = int(self._dimension_value[0])
                self._human_readable_log = f"Sensor {self._sensor} is reporting a power consumption of {self._monthly_consumption['value']} Wh for {self._monthly_consumption['date'].strftime('%B %Y')}."  # pylint: disable=line-too-long
            elif self._dimension == 53:
                self._type = MESSAGE_TYPE_CURRENT_MONTH_CONSUMPTION
                self._current_month_partial_consumption = int(self._dimension_value[0])
                self._human_readable_log = f"Sensor {self._sensor} is reporting a power consumption of {self._current_month_partial_consumption} Wh up to now this month."  # pylint: disable=line-too-long

    @property
    def message_type(self):
        return self._type

    @property
    def entity(self) -> str:
        _message_type_mapping = {
            MESSAGE_TYPE_ACTIVE_POWER: "-power",
            MESSAGE_TYPE_ENERGY_TOTALIZER: "-total-energy",
            MESSAGE_TYPE_CURRENT_MONTH_CONSUMPTION: "-monthly-energy",
            MESSAGE_TYPE_CURRENT_DAY_CONSUMPTION: "-daily-energy",
        }
        return f"{self.unique_id}{_message_type_mapping.get(self._type, '')}"

    @property
    def active_power(self):
        return self._active_power

    @property
    def total_consumption(self):
        return self._total_consumption

    @property
    def hourly_consumption(self):
        return self._hourly_consumption

    @property
    def daily_consumption(self):
        return self._daily_consumption

    @property
    def current_day_partial_consumption(self):
        return self._current_day_partial_consumption

    @property
    def monthly_consumption(self):
        return self._monthly_consumption

    @property
    def current_month_partial_consumption(self):
        return self._current_month_partial_consumption

    @property
    def human_readable_log(self):
        return self._human_readable_log


class OWNEnergyCommand(OWNCommand):
    @classmethod
    def start_sending_instant_power(cls, where, duration: int = 65):
        where = f"{where}#0" if str(where).startswith("7") else str(where)
        duration = 255 if duration > 255 else duration
        message = cls(f"*#18*{where}*#1200#1*{duration}##")
        message._human_readable_log = f"Requesting instant power draw update from sensor {where} for {duration} minutes."  # pylint: disable=line-too-long
        return message

    @classmethod
    def get_hourly_consumption(cls, where, date: datetime.date):
        where = f"{where}#0" if str(where).startswith("7") else str(where)
        today = datetime.date.today()
        one_year_ago = datetime.date(
            year=today.year - 1, month=today.month, day=today.day
        )
        if date < one_year_ago:
            return None
        message = cls(f"*#18*{where}*511#{date.month}#{date.day}##")
        message._human_readable_log = (
            f"Requesting hourly power consumption from sensor {where} for {date}."
        )
        return message

    @classmethod
    def get_partial_daily_consumption(cls, where):
        where = f"{where}#0" if str(where).startswith("7") else str(where)
        message = cls(f"*#18*{where}*54##")
        message._human_readable_log = (
            f"Requesting today's partial power consumption from sensor {where}."
        )
        return message

    @classmethod
    def get_daily_consumption(cls, where, year, month):
        where = f"{where}#0" if str(where).startswith("7") else str(where)
        today = datetime.date.today()
        one_year_ago = today - datetime.timedelta(years=1)
        two_year_ago = today - datetime.timedelta(years=2)
        target = datetime.date(year=year, month=month, day=1)
        if target > today:
            return None
        elif target > one_year_ago:
            message = cls(f"*18*59#{month}*{where}##")
        elif target > two_year_ago:
            message = cls(f"*18*510#{month}*{where}##")
        else:
            return None
        message._human_readable_log = f"Requesting daily power consumption for {year}-{month} from sensor {where}."  # pylint: disable=line-too-long
        return message

    @classmethod
    def get_partial_monthly_consumption(cls, where):
        where = f"{where}#0" if str(where).startswith("7") else str(where)
        message = cls(f"*#18*{where}*53##")
        message._human_readable_log = (
            f"Requesting this month's partial power consumption from sensor {where}."
        )
        return message

    @classmethod
    def get_monthly_consumption(cls, where, year, month):
        where = f"{where}#0" if str(where).startswith("7") else str(where)
        message = cls(f"*#18*{where}*52#{str(year)[2:]}#{month}##")
        message._human_readable_log = f"Requesting monthly power consumption for {year}-{month} from sensor {where}."  # pylint: disable=line-too-long
        return message

    @classmethod
    def get_total_consumption(cls, where):
        where = f"{where}#0" if str(where).startswith("7") else str(where)
        message = cls(f"*#18*{where}*51##")
        message._human_readable_log = (
            f"Requesting total power consumption from sensor {where}."
        )
        return message
