"""Collection operations and reading statistics."""

from collections import Counter
from copy import deepcopy
from datetime import date
from pathlib import Path

from .models import Book, BookNotFoundError, ValidationError
from .storage import Storage


class Library:
    """Own books and compose a storage backend."""

    def __init__(self, storage: Storage) -> None:
        self._storage = storage
        self._books = storage.load()

    def books(
        self,
        status: str = "",
        genre: str = "",
    ) -> list[Book]:
        """Return copies so callers cannot bypass collection persistence."""
        return deepcopy(
            [
                book
                for book in self._books
                if (not status or book.status == status)
                and (
                    not genre
                    or book.genre.casefold() == genre.casefold()
                )
            ]
        )

    def _commit(self, books: list[Book]) -> None:
        """Persist changes and update the in-memory collection."""
        self._storage.save(books)
        self._books = books

    def add(self, book: Book) -> None:
        """Add a book with a unique ID."""
        if any(book_item.id == book.id for book_item in self._books):
            raise ValidationError(
                "A book with this ID already exists."
            )

        self._commit(self._books + [deepcopy(book)])

    def _index(self, book_id: str) -> int:
        """Return the index of a book by its full ID."""
        for index, book in enumerate(self._books):
            if book.id == book_id:
                return index

        raise BookNotFoundError(
            f"Book ID not found: {book_id}"
        )

    def update(
        self,
        book_id: str,
        action: str,
        page: int = 0,
    ) -> None:
        """Apply a supported state change before persisting."""
        books = deepcopy(self._books)
        book = books[self._index(book_id)]

        if action == "start":
            book.start_reading()

        elif action == "progress":
            book.update_progress(page)

        elif action == "finish":
            book.mark_finished()

        else:
            raise ValidationError(
                "Unknown update action."
            )

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
                if (
                    query in book.title.casefold()
                    or query in book.author.casefold()
                )
            ]
        )

    def update_rating_review(
        self,
        book_id: str,
        rating: int | None = None,
        review: str | None = None,
    ) -> None:
        """
        Update a book's rating and/or review.

        Rating must be between 1 and 5.
        A value of None leaves the existing value unchanged.
        """
        books = deepcopy(self._books)
        book = books[self._index(book_id)]

        if rating is not None:
            if not 1 <= rating <= 5:
                raise ValidationError(
                    "Rating must be between 1 and 5."
                )

            book.rating = rating

        if review is not None:
            book.review = review

        self._commit(books)

    def export_report(
        self,
        output_path: Path,
        format: str,
    ) -> None:
        """Export the library as CSV or Markdown."""
        format = format.casefold().strip()

        if format == "csv":
            self._export_csv(output_path)

        elif format in ("markdown", "md"):
            self._export_markdown(output_path)

        else:
            raise ValidationError(
                "Export format must be CSV or Markdown."
            )

    def _export_csv(self, output_path: Path) -> None:
        """Export all books to a CSV file."""
        import csv

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)

            writer.writerow(
                [
                    "ID",
                    "Title",
                    "Author",
                    "Genre",
                    "Total Pages",
                    "Current Page",
                    "Status",
                    "Start Date",
                    "Finish Date",
                    "Rating",
                    "Review",
                ]
            )

            for book in self._books:
                writer.writerow(
                    [
                        book.id,
                        book.title,
                        book.author,
                        book.genre,
                        book.total_pages,
                        book.current_page,
                        book.status,
                        getattr(book, "start_date", ""),
                        getattr(book, "finish_date", ""),
                        getattr(book, "rating", ""),
                        getattr(book, "review", ""),
                    ]
                )

    def _export_markdown(self, output_path: Path) -> None:
        """Export all books to a Markdown report."""
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        lines = [
            "# Personal Library & Reading Tracker",
            "",
            "## Books",
            "",
            (
                "| ID | Title | Author | Genre | "
                "Pages | Progress | Status | Rating |"
            ),
            (
                "|---|---|---|---|---:|---:|---|---:|"
            ),
        ]

        for book in self._books:
            rating = getattr(book, "rating", "")
            progress = (
                f"{book.current_page}/{book.total_pages}"
            )

            lines.append(
                f"| {book.id} | "
                f"{book.title} | "
                f"{book.author} | "
                f"{book.genre} | "
                f"{book.total_pages} | "
                f"{progress} | "
                f"{book.status} | "
                f"{rating} |"
            )

        lines.extend(
            [
                "",
                "## Reviews",
                "",
            ]
        )

        for book in self._books:
            review = getattr(book, "review", "")

            if review:
                lines.extend(
                    [
                        f"### {book.title}",
                        "",
                        f"**Rating:** "
                        f"{getattr(book, 'rating', '')}/5",
                        "",
                        f"**Review:** {review}",
                        "",
                    ]
                )

        output_path.write_text(
            "\n".join(lines),
            encoding="utf-8",
        )

    def statistics(self) -> dict:
        """Count finished books and pages; genre ties return all winners."""
        finished = [
            book
            for book in self._books
            if book.status == "finished"
        ]

        genres = Counter(
            book.genre.casefold()
            for book in finished
        )

        highest = max(
            genres.values(),
            default=0,
        )

        return {
            "total_books": len(self._books),
            "finished_this_year": sum(
                date.fromisoformat(
                    book.finish_date
                ).year
                == date.today().year
                for book in finished
                if book.finish_date
            ),
            "average_pages_per_finished_book": (
                sum(
                    book.total_pages
                    for book in finished
                )
                / len(finished)
                if finished
                else 0
            ),
            "favorite_genres": sorted(
                genre
                for genre, count in genres.items()
                if count == highest
            ),
        }
