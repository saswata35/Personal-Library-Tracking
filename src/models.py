"""Validated book model and domain exceptions."""
from dataclasses import asdict, dataclass, field
from datetime import date
from uuid import uuid4


class LibraryError(Exception):
    """Base class for expected application errors."""


class ValidationError(LibraryError):
    """Invalid book data or operation."""


class BookNotFoundError(LibraryError):
    """The requested book does not exist."""


class StorageError(LibraryError):
    """Collection could not be read or saved."""


@dataclass
class Book:
    """A book with validated progress and completion metadata."""

    title: str
    author: str
    genre: str
    total_pages: int
    status: str = "to-read"
    current_page: int = 0
    finish_date: str | None = None
    id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        for name in ("title", "author", "genre", "id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValidationError(f"{name} must be nonempty text.")
            setattr(self, name, value.strip())

        # Disallow bool (since bool is a subclass of int in Python)
        if type(self.total_pages) is not int or self.total_pages <= 0:
            raise ValidationError("Total pages must be a positive integer.")

        if (
            type(self.current_page) is not int
            or not (0 <= self.current_page <= self.total_pages)
        ):
            raise ValidationError("Current page must be between 0 and total pages.")

        if self.status not in ("to-read", "reading", "finished"):
            raise ValidationError("Status must be to-read, reading or finished.")

        if self.status == "finished":
            self.current_page = self.total_pages
            self.finish_date = self.finish_date or date.today().isoformat()
            try:
                if date.fromisoformat(self.finish_date) > date.today():
                    raise ValueError("future date")
            except (TypeError, ValueError) as exc:
                raise ValidationError(
                    "Finish date must be a valid nonfuture ISO date."
                ) from exc
        elif self.finish_date is not None:
            raise ValidationError("Only finished books can have a finish date.")

        if self.status == "to-read" and self.current_page != 0:
            raise ValidationError("A to-read book must have zero progress.")

    def start_reading(self) -> None:
        """Move a waiting book to reading."""
        if self.status == "finished":
            raise ValidationError("This book is already finished.")
        self.status = "reading"

    def update_progress(self, page: int) -> None:
        """Set an absolute page number for a book currently being read."""
        if self.status != "reading":
            raise ValidationError("Start reading the book before updating progress.")
        if type(page) is not int or not (0 <= page <= self.total_pages):
            raise ValidationError("Page must be between 0 and total pages.")
        self.current_page = page

    def mark_finished(self) -> None:
        """Complete the book, preserving its original completion date."""
        self.status = "finished"
        self.current_page = self.total_pages
        self.finish_date = self.finish_date or date.today().isoformat()

    def to_dict(self) -> dict:
        """Return JSON-compatible fields."""
        return asdict(self)