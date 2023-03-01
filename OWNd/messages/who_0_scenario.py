"""OpenWebNet messages related to scenario (WHO=0)"""


from .base_message import OWNCommand, OWNEvent


class OWNScenarioEvent(OWNEvent):
    def __init__(self, data: str):
        super().__init__(data)

        self._scenario = self._what
        self._control_panel = self._where
        self._human_readable_log = f"Scenario {self._scenario} from control panel {self._control_panel} has been launched."  # pylint: disable=line-too-long

    @property
    def scenario(self):
        return self._scenario

    @property
    def control_panel(self):
        return self._control_panel


class OWNScenarioCommand(OWNCommand):
    @classmethod
    def activate(cls, where: str, scenario: int):
        message = cls(f"*0*{scenario}*{where}##")
        message._human_readable_log = (
            f"Activating scenario {scenario} on controler {where}."
        )
        return message
