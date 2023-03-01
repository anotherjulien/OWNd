"""OpenWebNet messages related to dry contact and IR state (WHO=25)"""

from .base_message import OWNCommand, OWNEvent


class OWNDryContactEvent(OWNEvent):
    def __init__(self, data):
        super().__init__(data)

        self._state = 1 if self._what == 31 else 0
        self._detection = int(self._what_param[0])
        self._sensor = self._where[1:]

        if self._detection == 1:
            self._human_readable_log = (
                f"Sensor {self._sensor} detected {'ON' if self._state == 1 else 'OFF'}."
            )
        else:
            self._human_readable_log = (
                f"Sensor {self._sensor} reported {'ON' if self._state == 1 else 'OFF'}."
            )

    @property
    def is_on(self):
        return self._state == 1

    @property
    def is_detection(self):
        return self._detection == 1

    @property
    def human_readable_log(self):
        return self._human_readable_log


class OWNDryContactCommand(OWNCommand):
    @classmethod
    def status(cls, where):
        message = cls(f"*#25*{where}##")
        message._human_readable_log = f"Requesting dry contact {where} status."
        return message
