from enum import Enum
from typing import BinaryIO, List, Tuple

class SenderType(Enum):
    KAKAO="kakao"
    GMAIL="gmail"

class Sender:
    def __init__(self, sender_type: SenderType):
        self.sender_type = sender_type

    def send(self, subject: str = "", content: str = "", attachments: List[Tuple[str, str, str, BinaryIO]] = [], receiver: List[str] = []):
        pass