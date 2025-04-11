from datetime import datetime
from typing import Protocol


class GenerateCurrentDT(Protocol):
    def __call__(self) -> datetime: ...
