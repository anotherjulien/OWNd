"""OpenWebNet messages related to CEN+ events (WHO=25)"""

from .base_message import OWNEvent


class OWNCENPlusEvent(OWNEvent):
    def __init__(self, data):
        super().__init__(data)

        self._state = self._what
        self.push_button = int(self._what_param[0])
        self.object = self._where[1:]

        if self._state == 21:
            self._human_readable_log = f"Button {self.push_button} of CEN+ object {self.object} has been pressed"  # pylint: disable=line-too-long
        elif self._state == 22:
            self._human_readable_log = f"Button {self.push_button} of CEN+ object {self.object} is being held pressed"  # pylint: disable=line-too-long
        elif self._state == 23:
            self._human_readable_log = f"Button {self.push_button} of CEN+ object {self.object} is still being held pressed"  # pylint: disable=line-too-long
        elif self._state == 24:
            self._human_readable_log = f"Button {self.push_button} of CEN+ object {self.object} has been released"  # pylint: disable=line-too-long
        elif self._state == 25:
            self._human_readable_log = f"Button {self.push_button} of CEN+ object {self.object} has been slowly rotated clockwise"  # pylint: disable=line-too-long
        elif self._state == 26:
            self._human_readable_log = f"Button {self.push_button} of CEN+ object {self.object} has been quickly rotated clockwise"  # pylint: disable=line-too-long
        elif self._state == 27:
            self._human_readable_log = f"Button {self.push_button} of CEN+ object {self.object} has been slowly rotated counter-clockwise"  # pylint: disable=line-too-long
        elif self._state == 28:
            self._human_readable_log = f"Button {self.push_button} of CEN+ object {self.object} has been quickly rotated counter-clockwise"  # pylint: disable=line-too-long

    @property
    def is_short_pressed(self):
        return self._state == 21

    @property
    def is_held(self):
        return self._state == 22

    @property
    def is_still_held(self):
        return self._state == 23

    @property
    def is_released(self):
        return self._state == 24

    @property
    def is_slowly_turned_cw(self):
        return self._state == 25

    @property
    def is_quickly_turned_cw(self):
        return self._state == 26

    @property
    def is_slowly_turned_ccw(self):
        return self._state == 27

    @property
    def is_quickly_turned_ccw(self):
        return self._state == 28

    @property
    def human_readable_log(self):
        return self._human_readable_log
