"""OpenWebNet messages related to scenes (WHO=17)"""

from .base_message import OWNCommand, OWNEvent


class OWNSceneEvent(OWNEvent):
    def __init__(self, data):
        super().__init__(data)

        self._scene = self._where
        self._state = self._what

        if self._state == 1:
            _status = "started"
        elif self._state == 2:
            _status = "stoped"
        elif self._state == 3:
            _status = "enabled"
        elif self._state == 4:
            _status = "disabled"
        else:
            _status = f"unknonwn ({self._state})"

        self._human_readable_log = f"Scene {self._scene} is {_status}."

    @property
    def scenario(self):
        return self._scene

    @property
    def state(self):
        return self._state

    @property
    def is_on(self):
        if self._state == 1:
            return True
        elif self._state == 2:
            return False
        else:
            return None

    @property
    def is_enabled(self):
        if self._state == 3:
            return True
        elif self._state == 4:
            return False
        else:
            return None


class OWNSceneCommand(OWNCommand):
    @classmethod
    def status(cls, where):
        message = cls(f"*#17*{where}##")
        message._human_readable_log = f"Requesting scene {where} status."
        return message

    @classmethod
    def start(cls, where):
        message = cls(f"*17*1*{where}##")
        message._human_readable_log = f"Starting scene {where}."
        return message

    @classmethod
    def stop(cls, where):
        message = cls(f"*17*2*{where}##")
        message._human_readable_log = f"Stoping scene {where}."
        return message

    @classmethod
    def enable(cls, where):
        message = cls(f"*17*3*{where}##")
        message._human_readable_log = f"Enabling scene {where}."
        return message

    @classmethod
    def disable(cls, where):
        message = cls(f"*17*4*{where}##")
        message._human_readable_log = f"Disabling scene {where}."
        return message
