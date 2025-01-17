"""OpenWebNet messages related to external interface devices (WHO=13)"""

import datetime
from .base_message import OWNCommand, OWNEvent


class OWNGatewayEvent(OWNEvent):
    def __init__(self, data):
        super().__init__(data)

        self._year = None
        self._month = None
        self._day = None
        self._hour = None
        self._minute = None
        self._second = None
        self._timezone = None

        self._time = None
        self._date = None
        self._datetime = None

        self._ip_address = None
        self._netmask = None
        self._mac_address = None

        self._device_type = None
        self._firmware_version = None

        self._uptime = None

        self._kernel_version = None
        self._distribution_version = None

        if self._dimension == 0:
            self._hour = self._dimension_value[0]
            self._minute = self._dimension_value[1]
            self._second = self._dimension_value[2]
            self._timezone = (
                f"+{self._dimension_value[3][1:]}"
                if self._dimension_value[3][0] == "0"
                else f"-{self._dimension_value[3][1:]}"
            )
            self._time = datetime.time.fromisoformat(
                f"{self._hour}:{self._minute}:{self._second}{self._timezone}:00"
            )
            self._human_readable_log = f"Gateway's internal time is: {self._hour}:{self._minute}:{self._second} UTC {self._timezone}."  # pylint: disable=line-too-long

        elif self._dimension == 1:
            self._year = self._dimension_value[3]
            self._month = self._dimension_value[2]
            self._day = self._dimension_value[1]
            self._date = datetime.date(
                year=int(self._year), month=int(self._month), day=int(self._day)
            )
            self._human_readable_log = (
                f"Gateway's internal date is: {self._year}-{self._month}-{self._day}."
            )

        elif self._dimension == 10:
            self._ip_address = f"{self._dimension_value[0]}.{self._dimension_value[1]}.{self._dimension_value[2]}.{self._dimension_value[3]}"  # pylint: disable=line-too-long
            self._human_readable_log = f"Gateway's IP address is: {self._ip_address}."

        elif self._dimension == 11:
            self._netmask = f"{self._dimension_value[0]}.{self._dimension_value[1]}.{self._dimension_value[2]}.{self._dimension_value[3]}"  # pylint: disable=line-too-long
            self._human_readable_log = f"Gateway's netmask is: {self._netmask}."

        elif self._dimension == 12:
            self._mac_address = f"{int(self._dimension_value[0]):02x}:{int(self._dimension_value[1]):02x}:{int(self._dimension_value[2]):02x}:{int(self._dimension_value[3]):02x}:{int(self._dimension_value[4]):02x}:{int(self._dimension_value[5]):02x}"  # pylint: disable=line-too-long
            self._human_readable_log = f"Gateway's MAC address is: {self._mac_address}."

        elif self._dimension == 15:
            if self._dimension_value[0] == "2":
                self._device_type = "MHServer"
            elif self._dimension_value[0] == "4":
                self._device_type = "MH200"
            elif self._dimension_value[0] == "6":
                self._device_type = "F452"
            elif self._dimension_value[0] == "7":
                self._device_type = "F452V"
            elif self._dimension_value[0] == "11":
                self._device_type = "MHServer2"
            elif self._dimension_value[0] == "13":
                self._device_type = "H4684"
            elif self._dimension_value[0] == "200":
                self._device_type = "F454"
            else:
                self._device_type = f"Unknown ({self._dimension_value[0]})"
            self._human_readable_log = f"Gateway device type is: {self._device_type}."

        elif self._dimension == 16:
            self._firmware_version = f"{self._dimension_value[0]}.{self._dimension_value[1]}.{self._dimension_value[2]}"  # pylint: disable=line-too-long
            self._human_readable_log = (
                f"Gateway's firmware version is: {self._firmware_version}."
            )

        elif self._dimension == 19:
            self._uptime = datetime.timedelta(
                days=int(self._dimension_value[0]),
                hours=int(self._dimension_value[1]),
                minutes=int(self._dimension_value[2]),
                seconds=int(self._dimension_value[3]),
            )
            self._human_readable_log = f"Gateway's uptime is: {self._uptime}."

        elif self._dimension == 22:
            self._hour = self._dimension_value[0]
            self._minute = self._dimension_value[1]
            self._second = self._dimension_value[2]
            self._timezone = (
                f"+{self._dimension_value[3][1:]}"
                if self._dimension_value[3][0] == "0"
                else f"-{self._dimension_value[3][1:]}"
            )
            self._day = self._dimension_value[5]
            self._month = self._dimension_value[6]
            self._year = self._dimension_value[7]
            self._datetime = datetime.datetime.fromisoformat(
                f"{self._year}-{self._month}-{self._day}*{self._hour}:{self._minute}:{self._second}{self._timezone}:00"  # pylint: disable=line-too-long
            )
            self._human_readable_log = (
                f"Gateway's internal datetime is: {self._datetime}."
            )

        elif self._dimension == 23:
            self._kernel_version = f"{self._dimension_value[0]}.{self._dimension_value[1]}.{self._dimension_value[2]}"  # pylint: disable=line-too-long
            self._human_readable_log = (
                f"Gateway's kernel version is: {self._kernel_version}."
            )

        elif self._dimension == 24:
            self._distribution_version = f"{self._dimension_value[0]}.{self._dimension_value[1]}.{self._dimension_value[2]}"  # pylint: disable=line-too-long
            self._human_readable_log = (
                f"Gateway's distribution version is: {self._distribution_version}."
            )


class OWNGatewayCommand(OWNCommand):
    def __init__(self, data):
        super().__init__(data)

        self._year = None
        self._month = None
        self._day = None
        self._hour = None
        self._minute = None
        self._second = None
        self._timezone = None

        self._time = None
        self._date = None
        self._datetime = None

        if self._dimension == 0:
            self._hour = self._dimension_value[0]
            self._minute = self._dimension_value[1]
            self._second = self._dimension_value[2]
            self._timezone = (
                f"+{self._dimension_value[3][1:]}"
                if self._dimension_value[3][0] == "0"
                else f"-{self._dimension_value[3][1:]}"
            )
            self._time = datetime.time.fromisoformat(
                f"{self._hour}:{self._minute}:{self._second}{self._timezone}:00"
            )
            self._human_readable_log = (
                f"Gateway broadcasting internal time: {self._time}."
            )

        elif self._dimension == 1:
            self._year = self._dimension_value[3]
            self._month = self._dimension_value[2]
            self._day = self._dimension_value[1]
            self._date = datetime.date(
                year=int(self._year), month=int(self._month), day=int(self._day)
            )
            self._human_readable_log = (
                f"Gateway broadcasting internal date: {self._date}."
            )

        elif self._dimension == 22:
            self._hour = self._dimension_value[0]
            self._minute = self._dimension_value[1]
            self._second = self._dimension_value[2]
            self._timezone = (
                f"+{self._dimension_value[3][1:]}"
                if self._dimension_value[3][0] == "0"
                else f"-{self._dimension_value[3][1:]}"
            )
            self._day = self._dimension_value[5]
            self._month = self._dimension_value[6]
            self._year = self._dimension_value[7]
            self._datetime = datetime.datetime.fromisoformat(
                f"{self._year}-{self._month}-{self._day}*{self._hour}:{self._minute}:{self._second}{self._timezone}:00"  # pylint: disable=line-too-long
            )
            self._human_readable_log = (
                f"Gateway broadcasting internal datetime: {self._datetime}."
            )

    @classmethod
    def set_datetime_to_now(cls, time_zone: str):
        timezone = pytz.timezone(time_zone)
        now = timezone.localize(datetime.datetime.now())
        timezone_offset = (
            f"0{now.strftime('%z')[1:3]}"
            if now.strftime("%z")[0] == "+"
            else f"1{now.strftime('%z')[1:3]}"
        )
        message = cls(
            f"*#13**#22*{now.strftime('%H*%M*%S')}*{timezone_offset}*0{now.strftime('%w*%d*%m*%Y##')}"  # pylint: disable=line-too-long
        )
        message._human_readable_log = f"Setting gateway time to: {message._datetime}."
        return message

    @classmethod
    def set_date_to_today(cls, time_zone: str):
        timezone = pytz.timezone(time_zone)
        now = timezone.localize(datetime.datetime.now())
        message = cls(f"*#13**#1*0{now.strftime('%w*%d*%m*%Y##')}")
        message._human_readable_log = f"Setting gateway date to: {message._date}."
        return message

    @classmethod
    def set_time_to_now(cls, time_zone: str):
        timezone = pytz.timezone(time_zone)
        now = timezone.localize(datetime.datetime.now())
        timezone_offset = (
            f"0{now.strftime('%z')[1:3]}"
            if now.strftime("%z")[0] == "+"
            else f"1{now.strftime('%z')[1:3]}"
        )
        message = cls(f"*#13**#0*{now.strftime('%H*%M*%S')}*{timezone_offset}*##")
        message._human_readable_log = f"Setting gateway time to: {message._time}."
        return message
