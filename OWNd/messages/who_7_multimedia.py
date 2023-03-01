"""OpenWebNet messages related to multimedia systems (WHO=7)"""

from .base_message import OWNCommand, OWNEvent


class OWNAVCommand(OWNCommand):
    @classmethod
    def receive_video(cls, where):
        camera_id = where
        if int(where) < 100:
            where = f"40{camera_id}"
        elif int(where) >= 4000 and int(where) < 5000:
            camera_id = where[2:]
        else:
            return None

        message = cls(f"*7*0*{where}##")
        message._human_readable_log = f"Opening video stream for camera {camera_id}."
        return message

    @classmethod
    def close_video(cls):
        message = cls("*7*9**##")
        message._human_readable_log = "Closing video stream."
        return message
