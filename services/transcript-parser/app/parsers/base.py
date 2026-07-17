from abc import ABC, abstractmethod
from pathlib import Path

from app.models import ParsedDocument


class TranscriptParser(ABC):
    @abstractmethod
    def parse(self, path: Path) -> ParsedDocument:
        raise NotImplementedError
