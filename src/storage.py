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
        """Load books from JSON and validate the saved collection."""
        try:
            # -----------------------------------------------------
            # Handle an empty/non-existing data file
            # -----------------------------------------------------
            if not self.path.exists():
                return []

            raw = json.loads(
                self.path.read_text(encoding="utf-8")
            )

            # -----------------------------------------------------
            # Validate root JSON structure
            # -----------------------------------------------------
            if not isinstance(raw, dict):
                raise ValidationError(
                    "Data file must contain a JSON object."
                )

            if raw.get("version") != 1:
                raise ValidationError(
                    "Unsupported data format."
                )

            if not isinstance(raw.get("books"), list):
                raise ValidationError(
                    "Books must be a list."
                )

            # -----------------------------------------------------
            # Convert dictionaries into Book objects
            # -----------------------------------------------------
            books = [
                Book(**item)
                for item in raw["books"]
                if isinstance(item, dict)
            ]

            # Make sure every item was a dictionary.
            if len(books) != len(raw["books"]):
                raise ValidationError(
                    "Each book must be a JSON object."
                )

            # -----------------------------------------------------
            # Check for duplicate IDs
            # -----------------------------------------------------
            if len({book.id for book in books}) != len(books):
                raise ValidationError(
                    "Duplicate book IDs in saved data."
                )

            return books

        except FileNotFoundError:
            return []

        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            ValueError,
            TypeError,
            ValidationError,
        ) as exc:
            raise StorageError(
                f"Cannot load {self.path}: {exc}"
            ) from exc

    def save(self, books: list[Book]) -> None:
        """Save the complete collection using atomic replacement."""
        temporary = None

        try:
            # -----------------------------------------------------
            # Ensure parent directory exists
            # -----------------------------------------------------
            self.path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            # -----------------------------------------------------
            # Write to a temporary file first
            # -----------------------------------------------------
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=".library-",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary = stream.name

                json.dump(
                    {
                        "version": 1,
                        "books": [
                            book.to_dict()
                            for book in books
                        ],
                    },
                    stream,
                    ensure_ascii=False,
                    indent=2,
                )

                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())

            # -----------------------------------------------------
            # Replace the original file atomically
            # -----------------------------------------------------
            os.replace(
                temporary,
                self.path,
            )

        except OSError as exc:
            raise StorageError(
                f"Cannot save {self.path}: {exc}"
            ) from exc

        finally:
            # -----------------------------------------------------
            # Remove temporary file if it still exists
            # -----------------------------------------------------
            if (
                temporary
                and os.path.exists(temporary)
            ):
                try:
                    os.unlink(temporary)
                except OSError:
                    pass

