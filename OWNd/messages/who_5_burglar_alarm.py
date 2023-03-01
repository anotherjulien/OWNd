"""OpenWebNet messages (events only) related to the burglar alarm (WHO=5)"""

from .base_message import OWNCommand, OWNEvent


class OWNAlarmEvent(OWNEvent):
    def __init__(self, data):
        super().__init__(data)

        self._state_code = int(self._what)
        self._state = None
        self._system = False
        self._zone = None
        self._sensor = None

        if self._where == "*":
            self._system = True
            self._human_readable_log = "System is reporting: "
        elif self._where.startswith("#"):
            self._zone = self._where[1:]
            if self._zone == "12":
                self._zone = "c"
            elif self._zone == "15":
                self._zone = "f"
            else:
                self._sensor = int(self._zone[1:])
                self._zone = int(self._zone[0])
            self._human_readable_log = f"Zone {self._zone} is reporting: "
        else:
            self._zone = int(self._where[0])
            self._sensor = int(self._where[1:])
            if self._zone == 0:
                self._human_readable_log = (
                    f"Device {self._sensor} in input zone is reporting: "
                )
            else:
                self._human_readable_log = (
                    f"Sensor {self._sensor} in zone {self._zone} is reporting: "
                )

        if self._state_code == 0:
            self._state = "maintenance"
        elif self._state_code == 1:
            self._state = "activation"
        elif self._state_code == 2:
            self._state = "deactivation"
        elif self._state_code == 3:
            self._state = "delay end"
        elif self._state_code == 4:
            self._state = "system battery fault"
        elif self._state_code == 5:
            self._state = "battery ok"
        elif self._state_code == 6:
            self._state = "no network"
        elif self._state_code == 7:
            self._state = "network present"
        elif self._state_code == 8:
            self._state = "engage"
        elif self._state_code == 9:
            self._state = "disengage"
        elif self._state_code == 10:
            self._state = "battery unloads"
        elif self._state_code == 11:
            self._state = "active zone"
        elif self._state_code == 12:
            self._state = "technical alarm"
        elif self._state_code == 13:
            self._state = "reset technical alarm"
        elif self._state_code == 14:
            self._state = "no reception"
        elif self._state_code == 15:
            self._state = "intrusion alarm"
        elif self._state_code == 16:
            self._state = "tampering"
        elif self._state_code == 17:
            self._state = "anti-panic alarm"
        elif self._state_code == 18:
            self._state = "non-active zone"
        elif self._state_code == 26:
            self._state = "start programming"
        elif self._state_code == 27:
            self._state = "stop programming"
        elif self._state_code == 31:
            self._state = "silent alarm"

        self._human_readable_log = f"{self._human_readable_log}'{self._state}'."

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
    def is_active(self):
        return self._state_code == 1 or self._state_code == 11

    @property
    def is_engaged(self):
        return self._state_code == 8

    @property
    def is_alarm(self):
        return (
            self._state_code == 12
            or self._state_code == 15
            or self._state_code == 16
            or self._state_code == 17
            or self._state_code == 31
        )
