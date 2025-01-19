"""OpenWebNet messages related to CEN events (WHO=15)"""

from .base_message import OWNEvent


class OWNCENEvent(OWNEvent):
    def __init__(self, data):
        super().__init__(data)

        try:
            self._state = self._what_param[0]
        except IndexError:
            self._state = None
        self.push_button = self._what
        self.object = self._where

        if self._state is None:
            self._human_readable_log = f"Button {self.push_button} of CEN object {self.object}{self._interface_log_text} has been pressed."  # pylint: disable=line-too-long
        elif int(self._state) == 3:
            self._human_readable_log = f"Button {self.push_button} of CEN object {self.object}{self._interface_log_text} is being held pressed."  # pylint: disable=line-too-long
        elif int(self._state) == 1:
            self._human_readable_log = f"Button {self.push_button} of CEN object {self.object}{self._interface_log_text} has been released after a short press."  # pylint: disable=line-too-long
        elif int(self._state) == 2:
            self._human_readable_log = f"Button {self.push_button} of CEN object {self.object}{self._interface_log_text} has been released after a long press."  # pylint: disable=line-too-long

    @property
    def is_pressed(self):
        return self._state is None

    @property
    def is_held(self):
        return int(self._state) == 3

    @property
    def is_released_after_short_press(self):
        return int(self._state) == 1

    @property
    def is_released_after_long_press(self):
        return int(self._state) == 2
