"""Collection operations and reading statistics."""
from collections import Counter
from copy import deepcopy
from datetime import date

from .models import Book, BookNotFoundError, ValidationError
from .storage import Storage


class Library:
    """Own books and compose a storage backend; save each successful change."""

    def __init__(self, storage: Storage) -> None:
        self._storage = storage
        self._books = storage.load()

    def books(self, status: str = "", genre: str = "") -> list[Book]:
        """Return copies so callers cannot bypass collection persistence."""
        return deepcopy(
            [
                b
                for b in self._books
                if (not status or b.status == status)
                and (not genre or b.genre.casefold() == genre.casefold())
            ]
        )

    def _commit(self, books: list[Book]) -> None:
        self._storage.save(books)
        self._books = books

    def add(self, book: Book) -> None:
        """Add a book with a unique ID."""
        if any(b.id == book.id for b in self._books):
            raise ValidationError("A book with this ID already exists.")
        self._commit(self._books + [deepcopy(book)])

    def _index(self, book_id: str) -> int:
        for index, book in enumerate(self._books):
            if book.id == book_id:
                return index
        raise BookNotFoundError(f"Book ID not found: {book_id}")

    def update(self, book_id: str, action: str, page: int = 0) -> None:
        """Apply a supported state change on a copy before persisting."""
        books = deepcopy(self._books)
        book = books[self._index(book_id)]
        if action == "start":
            book.start_reading()
        elif action == "progress":
            book.update_progress(page)
        elif action == "finish":
            book.mark_finished()
        else:
            raise ValidationError("Unknown update action.")
        self._commit(books)

    def remove(self, book_id: str) -> None:
        """Remove a book by its full ID."""
        books = deepcopy(self._books)
        del books[self._index(book_id)]
        self._commit(books)

    def search(self, query: str) -> list[Book]:
        """Match a case-insensitive substring in title or author."""
        query = query.casefold().strip()
        return deepcopy(
            [
                book
                for book in self._books
                if (query in book.title.casefold() or query in book.author.casefold())
            ]
        )

    def statistics(self) -> dict:
        """Count finished books and pages; genre ties return all winners."""
        finished = [book for book in self._books if book.status == "finished"]
        genres = Counter(book.genre.casefold() for book in finished)
        highest = max(genres.values(), default=0)
        return {
            "total_books": len(self._books),
            "finished_this_year": sum(
                date.fromisoformat(book.finish_date).year == date.today().year
                for book in finished
                if book.finish_date
            ),
            "average_pages_per_finished_book": (
                sum(book.total_pages for book in finished) / len(finished)
                if finished
                else 0
            ),
            "favorite_genres": sorted(
                g for g, count in genres.items() if count == highest
            ),
        }