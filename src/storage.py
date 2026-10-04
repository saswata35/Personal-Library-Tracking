"""JSON persistence with atomic replacement."""
import json
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from .models import Book, StorageError, ValidationError


class Storage(ABC):
    """Persistence interface; implementations can use different formats."""

    @abstractmethod
    def load(self) -> list[Book]:
        """Load the saved collection."""

    @abstractmethod
    def save(self, books: list[Book]) -> None:
        """Save the entire collection."""


class JSONStorage(Storage):
    """UTF-8 JSON storage implementing the abstract storage interface."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> list[Book]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or raw.get("version") != 1:
                raise ValidationError("Unsupported data format.")
            if not isinstance(raw.get("books"), list):
                raise ValidationError("Books must be a list.")
            books = [Book(**item) for item in raw["books"]]
            if len({book.id for book in books}) != len(books):
                raise ValidationError("Duplicate book IDs in saved data.")
            return books
        except FileNotFoundError:
            return []
        except (
            OSError, UnicodeError, ValueError, TypeError, ValidationError
        ) as exc:
            raise StorageError(
                f"Cannot load {self.path}: {exc}"
            ) from exc

    def save(self, books: list[Book]) -> None:
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent,
                prefix=".library-", suffix=".tmp", delete=False,
            ) as stream:
                temporary = stream.name
                json.dump(
                    {"version": 1, "books": [b.to_dict() for b in books]
                     },
                    stream,
                    ensure_ascii=False,
                    indent=2
                )
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except OSError as exc:
            raise StorageError(f"Cannot save {self.path}: {exc}") from exc
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
