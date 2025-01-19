""" This module contains OpenWebNet messages definition """

from typing import Match, Optional

from ..const import (
    PATTERN_ACK,
    PATTERN_NACK,
    PATTERN_COMMAND_SESSION,
    PATTERN_EVENT_SESSION,
    PATTERN_NONCE,
    PATTERN_SHA,
    PATTERN_STATUS,
    PATTERN_STATUS_REQUEST,
    PATTERN_DIMENSION_REQUEST,
    PATTERN_DIMENSION_REQUEST_REPLY,
    PATTERN_DIMENSION_WRITING,
)


class OWNMessage:
    """Base class for all OWN messages"""

    def __init__(self, data: str):
        self._raw = data
        self._match: Match[str]
        self._human_readable_log = self._raw
        self._family = ""
        self._who: int
        self._where = ""
        self._is_valid_message = False

        if status_match := PATTERN_STATUS.match(self._raw):
            self._is_valid_message = True
            self._match = status_match
            self._family = "EVENT"
            self._message_type = "STATUS"
            self._who = int(self._match.group("who"))
            self._what = int(self._match.group("what"))
            if self._what == 1000:
                self._family = "COMMAND_TRANSLATION"
            self._what_param = self._match.group("what_param").split("#")
            del self._what_param[0]
            self._where = self._match.group("where")
            self._where_param = self._match.group("where_param").split("#")
            del self._where_param[0]
            self._dimension = None
            self._dimension_param = None
            self._dimension_value = None

        elif status_request_match := PATTERN_STATUS_REQUEST.match(self._raw):
            self._is_valid_message = True
            self._match = status_request_match
            self._family = "REQUEST"
            self._message_type = "STATUS_REQUEST"
            self._who = int(self._match.group("who"))
            self._what = None
            self._what_param = None
            self._where = self._match.group("where")
            self._where_param = self._match.group("where_param").split("#")
            del self._where_param[0]
            self._dimension = None
            self._dimension_param = None
            self._dimension_value = None

        elif dimension_request_match := PATTERN_DIMENSION_REQUEST.match(self._raw):
            self._is_valid_message = True
            self._match = dimension_request_match
            self._family = "REQUEST"
            self._message_type = "DIMENSION_REQUEST"
            self._who = int(self._match.group("who"))
            self._what = None
            self._what_param = None
            self._where = self._match.group("where")
            self._where_param = self._match.group("where_param").split("#")
            del self._where_param[0]
            self._dimension = int(self._match.group("dimension"))
            self._dimension_param = None
            self._dimension_value = None

        elif dimension_reply_match := PATTERN_DIMENSION_REQUEST_REPLY.match(self._raw):
            self._is_valid_message = True
            self._match = dimension_reply_match
            self._family = "EVENT"
            self._message_type = "DIMENSION_REQUEST_REPLY"
            self._who = int(self._match.group("who"))
            self._what = None
            self._what_param = None
            self._where = self._match.group("where")
            self._where_param = self._match.group("where_param").split("#")
            del self._where_param[0]
            self._dimension = int(self._match.group("dimension"))
            self._dimension_param = self._match.group("dimension_param").split("#")
            del self._dimension_param[0]
            self._dimension_value = self._match.group("dimension_value").split("*")
            del self._dimension_value[0]

        elif dimension_writing_match := PATTERN_DIMENSION_WRITING.match(self._raw):
            self._is_valid_message = True
            self._match = dimension_writing_match
            self._family = "COMMAND"
            self._message_type = "DIMENSION_WRITING"
            self._who = int(self._match.group("who"))
            self._what = None
            self._what_param = None
            self._where = self._match.group("where")
            self._where_param = self._match.group("where_param").split("#")
            del self._where_param[0]
            self._dimension = int(self._match.group("dimension"))
            self._dimension_param = self._match.group("dimension_param").split("#")
            del self._dimension_param[0]
            self._dimension_value = self._match.group("dimension_value").split("*")
            del self._dimension_value[0]

    @property
    def is_event(self) -> bool:
        return self._family == "EVENT"

    @property
    def is_command(self) -> bool:
        return self._family == "COMMAND"

    @property
    def is_request(self) -> bool:
        return self._family == "REQUEST"

    @property
    def is_translation(self) -> bool:
        return self._family == "COMMAND_TRANSLATION"

    @property
    def is_valid(self) -> bool:
        return self._is_valid_message

    @property
    def who(self) -> int:
        """The 'who' ID of the subject of this message"""
        return self._who

    @property
    def where(self) -> str:
        """The 'where' ID of the subject of this message"""
        return self._where  # [1:] if self._where.startswith('#') else self._where

    @property
    def interface(self) -> str:
        """The 'where' parameter corresponding to the bus interface of the subject of this message"""
        return (
            self._where_param[1]
            if self._who in [1, 2, 15]
            and len(self._where_param) > 0
            and self._where_param[0] == "4"
            else None
        )

    @property
    def dimension(self) -> Optional[int]:
        """The 'where' ID of the subject of this message"""
        return self._dimension

    @property
    def entity(self) -> str:
        """The ID of the subject of this message"""
        return self.unique_id

    @property
    def unique_id(self) -> str:
        """The ID of the subject of this message"""
        return (
            f"{self.who}-{self.where}#4#{self.interface}"
            if self.interface is not None
            else f"{self.who}-{self.where}"
        )

    @property
    def event_content(self) -> dict:
        _event = {
            "message": self._raw,
            "family": self._family.replace("_", " ").capitalize(),
            "type": self._message_type.replace("_", " ").capitalize(),
            "who": self._who,
        }
        if self._where:
            _event.update({"where": self._where})
        if self.interface:
            _event.update({"interface": self.interface})
            if self._where_param and len(self._where_param) > 2:
                _event.update({"where parameters": self._where_param[2:]})
        elif self._where_param:
            _event.update({"where parameters": self._where_param})
        if self._what:
            _event.update({"what": self._what})
        if self._what_param:
            _event.update({"what parameters": self._what_param})
        if self._dimension:
            _event.update({"dimension": self._dimension})
        if self._dimension_param:
            _event.update({"dimension parameters": self._dimension_param})
        if self._dimension_value:
            _event.update({"dimension values": self._dimension_value})

        return _event

    @property
    def human_readable_log(self) -> str:
        """A human readable log of the event"""
        return self._human_readable_log

    @human_readable_log.setter
    def human_readable_log(self, human_readable_log: str) -> None:
        self._human_readable_log = human_readable_log

    @property
    def _interface_log_text(self) -> str:
        return f" on interface {self.interface}" if self.interface is not None else ""

    @property
    def is_general(self) -> bool:
        if self.who in [1, 2]:
            if self._where == "0":
                return True
            else:
                return False
        else:
            return False

    @property
    def is_group(self) -> bool:
        if self.who == 1 or self.who == 2:
            if self._where.startswith("#"):
                return True
            else:
                return False
        else:
            return False

    @property
    def is_area(self) -> bool:
        if self.who == 1 or self.who == 2:
            try:
                if (
                    self._where == "00"
                    or self._where == "100"
                    or (
                        len(self._where) == 1
                        and int(self._where) > 0
                        and int(self._where) < 10
                    )
                ):
                    return True
                else:
                    return False
            except ValueError:
                return False
        else:
            return False

    @property
    def group(self) -> Optional[int]:
        if self.is_group:
            return int(self._where[1:])
        else:
            return None

    @property
    def area(self) -> Optional[int]:
        if self.is_area:
            return 10 if self._where == "100" else int(self._where)
        else:
            return None

    def __repr__(self) -> str:
        return self._raw

    def __str__(self) -> str:
        return self._raw


class OWNEvent(OWNMessage):
    """
    This class is a subclass of messages.
    All messages received during an event session are events.
    Dividing this in a subclass provides better clarity
    """


class OWNCommand(OWNMessage):
    """
    This class is a subclass of messages.
    All messages sent during a command session are commands.
    Dividing this in a subclass provides better clarity
    """


class OWNSignaling(OWNMessage):
    """
    This class is a subclass of messages.
    It is dedicated to signaling messages such as ACK or Authentication negotiation
    """

    def __init__(self, data: str):  # pylint: disable=super-init-not-called
        self._raw = data
        self._match: Match[str]
        self._family = None
        self._type = "UNKNOWN"
        self._human_readable_log = data

        if ack_match := PATTERN_ACK.match(self._raw):
            self._match = ack_match
            self._family = "SIGNALING"
            self._type = "ACK"
            self._human_readable_log = "ACK."
        elif nack_match := PATTERN_NACK.match(self._raw):
            self._match = nack_match
            self._family = "SIGNALING"
            self._type = "NACK"
            self._human_readable_log = "NACK."
        elif nonce_match := PATTERN_NONCE.match(self._raw):
            self._match = nonce_match
            self._family = "SIGNALING"
            self._type = "NONCE"
            self._human_readable_log = (
                f"Nonce challenge received: {self._match.group(1)}."
            )
        elif sha_match := PATTERN_SHA.match(self._raw):
            self._match = sha_match
            self._family = "SIGNALING"
            self._type = f"SHA{'-1' if self._match.group(1) == '1' else '-256'}"
            self._human_readable_log = f"SHA{'-1' if self._match.group(1) == '1' else '-256'} challenge received."  # pylint: disable=line-too-long
        elif command_match := PATTERN_COMMAND_SESSION.match(self._raw):
            self._match = command_match
            self._family = "SIGNALING"
            self._type = "COMMAND_SESSION"
            self._human_readable_log = "Command session requested."
        elif event_match := PATTERN_EVENT_SESSION.match(self._raw):
            self._match = event_match
            self._family = "SIGNALING"
            self._type = "EVENT_SESSION"
            self._human_readable_log = "Event session requested."

    @property
    def nonce(self):
        """Return the authentication nonce IF the message is a nonce message"""
        if self.is_nonce:  # pylint: disable=using-constant-test
            return self._match.group(1)
        else:
            return None

    @property
    def sha_version(self):
        """Return the authentication SHA version IF the message is a SHA challenge message"""
        if self.is_sha:  # pylint: disable=using-constant-test
            return self._match.group(1)
        else:
            return None

    def is_ack(self) -> bool:
        return self._type == "ACK"

    def is_nack(self) -> bool:
        return self._type == "NACK"

    def is_nonce(self) -> bool:
        return self._type == "NONCE"

    def is_sha(self) -> bool:
        return self._type == "SHA-1" or self._type == "SHA-256"

    def is_sha_1(self) -> bool:
        return self._type == "SHA-1"

    def is_sha_256(self) -> bool:
        return self._type == "SHA-256"
