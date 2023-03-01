"""OpenWebNet messages (events only) related to auxiliaries (WHO=9)"""

from .base_message import OWNEvent


class OWNAuxEvent(OWNEvent):
    def __init__(self, data):
        super().__init__(data)

        self._channel = self._where

        self._state = self._what
        if self._state == 0:
            self._human_readable_log = (
                f"Auxilliary channel {self._channel} is set to 'OFF'."
            )
        elif self._state == 1:
            self._human_readable_log = (
                f"Auxilliary channel {self._channel} is set to 'ON'."
            )
        elif self._state == 2:
            self._human_readable_log = (
                f"Auxilliary channel {self._channel} is set to 'TOGGLE'."
            )
        elif self._state == 3:
            self._human_readable_log = (
                f"Auxilliary channel {self._channel} is set to 'STOP'."
            )
        elif self._state == 4:
            self._human_readable_log = (
                f"Auxilliary channel {self._channel} is set to 'UP'."
            )
        elif self._state == 5:
            self._human_readable_log = (
                f"Auxilliary channel {self._channel} is set to 'DOWN'."
            )
        elif self._state == 6:
            self._human_readable_log = (
                f"Auxilliary channel {self._channel} is set to 'ENABLED'."
            )
        elif self._state == 7:
            self._human_readable_log = (
                f"Auxilliary channel {self._channel} is set to 'DISABLED'."
            )
        elif self._state == 8:
            self._human_readable_log = (
                f"Auxilliary channel {self._channel} is set to 'RESET_GEN'."
            )
        elif self._state == 9:
            self._human_readable_log = (
                f"Auxilliary channel {self._channel} is set to 'RESET_BI'."
            )
        elif self._state == 10:
            self._human_readable_log = (
                f"Auxilliary channel {self._channel} is set to 'RESET_TRI'."
            )

    @property
    def channel(self):
        return self._channel

    @property
    def state_code(self):
        return self._state

    @property
    def is_on(self):
        return self._state == 1
