"""Behavioral tests with isolated JSON files."""

import csv
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.library import Library
from src.models import (
    Book,
    BookNotFoundError,
    StorageError,
    ValidationError,
)
from src.storage import JSONStorage


class LibraryTests(unittest.TestCase):
    """Test Library behavior using isolated JSON storage."""

    def setUp(self):
        """Create a fresh temporary library for every test."""
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)

        self.storage = JSONStorage(
            Path(temp.name) / "data.json"
        )
        self.library = Library(self.storage)

        self.temp_dir = Path(temp.name)

    def test_lifecycle_reload_remove(self):
        """Test add, reading, progress, finish, reload and remove."""
        book = Book(
            "Python",
            "Alice",
            "Technology",
            100,
        )

        self.library.add(book)

        with self.assertRaises(ValidationError):
            self.library.update(
                book.id,
                "progress",
                20,
            )

        self.library.update(
            book.id,
            "start",
        )

        self.library.update(
            book.id,
            "progress",
            40,
        )

        self.assertEqual(
            Library(self.storage).books()[0].current_page,
            40,
        )

        self.library.update(
            book.id,
            "finish",
        )

        loaded = Library(self.storage).books()[0]

        self.assertEqual(
            (
                loaded.status,
                loaded.current_page,
                loaded.finish_date,
            ),
            (
                "finished",
                100,
                date.today().isoformat(),
            ),
        )

        self.library.remove(book.id)

        self.assertEqual(
            Library(self.storage).books(),
            [],
        )

    def test_search_filter_copies(self):
        """Test search, genre filtering and defensive copies."""
        self.library.add(
            Book(
                "Python Basics",
                "ALICE",
                "Technology",
                200,
            )
        )

        self.assertEqual(
            len(self.library.search("ali")),
            1,
        )

        self.assertEqual(
            len(
                self.library.books(
                    genre="TECHNOLOGY"
                )
            ),
            1,
        )

        self.library.books()[0].title = "Changed"

        self.assertEqual(
            self.library.books()[0].title,
            "Python Basics",
        )

    def test_statistics(self):
        """Test finished count, average pages and favorite genres."""
        self.assertEqual(
            self.library.statistics()["favorite_genres"],
            [],
        )

        self.library.add(
            Book(
                "A",
                "X",
                "Fiction",
                100,
                "finished",
            )
        )

        self.library.add(
            Book(
                "B",
                "Y",
                "History",
                300,
                "finished",
            )
        )

        self.library.add(
            Book(
                "C",
                "Z",
                "History",
                500,
            )
        )

        stats = self.library.statistics()

        self.assertEqual(
            stats["finished_this_year"],
            2,
        )

        self.assertEqual(
            stats["average_pages_per_finished_book"],
            200,
        )

        self.assertEqual(
            stats["favorite_genres"],
            ["fiction", "history"],
        )

    def test_corrupt_file_preserved(self):
        """Test that corrupted data raises an error without replacing it."""
        self.storage.path.write_text(
            "{broken",
            encoding="utf-8",
        )

        with self.assertRaises(StorageError):
            Library(self.storage)

        self.assertEqual(
            self.storage.path.read_text(
                encoding="utf-8"
            ),
            "{broken",
        )

    def test_save_failure_rollback(self):
        """Test that failed saves do not modify in-memory state."""
        book = Book(
            "A",
            "X",
            "Fiction",
            100,
            "reading",
        )

        self.library.add(book)

        with patch.object(
            self.storage,
            "save",
            side_effect=StorageError("failed"),
        ):
            with self.assertRaises(StorageError):
                self.library.update(
                    book.id,
                    "progress",
                    50,
                )

        self.assertEqual(
            self.library.books()[0].current_page,
            0,
        )

        self.assertEqual(
            Library(self.storage).books()[0].current_page,
            0,
        )

    def test_rating_and_review(self):
        """Test adding a rating and review to a book."""
        book = Book(
            "Clean Code",
            "Robert Martin",
            "Technology",
            400,
        )

        self.library.add(book)

        self.library.update_rating_review(
            book.id,
            rating=5,
            review="Excellent programming book.",
        )

        loaded = self.library.books()[0]

        self.assertEqual(
            loaded.rating,
            5,
        )

        self.assertEqual(
            loaded.review,
            "Excellent programming book.",
        )

    def test_rating_and_review_persistence(self):
        """Test rating and review survive JSON reload."""
        book = Book(
            "Python",
            "Alice",
            "Technology",
            200,
        )

        self.library.add(book)

        self.library.update_rating_review(
            book.id,
            rating=4,
            review="Very useful.",
        )

        reloaded = Library(
            self.storage
        ).books()[0]

        self.assertEqual(
            reloaded.rating,
            4,
        )

        self.assertEqual(
            reloaded.review,
            "Very useful.",
        )

    def test_invalid_rating(self):
        """Test that ratings outside 1-5 are rejected."""
        book = Book(
            "Python",
            "Alice",
            "Technology",
            200,
        )

        self.library.add(book)

        for rating in (0, 6, -1, True):
            with self.assertRaises(ValidationError):
                self.library.update_rating_review(
                    book.id,
                    rating=rating,
                )

    def test_rating_can_be_set_on_book(self):
        """Test direct Book rating validation."""
        book = Book(
            "Python",
            "Alice",
            "Technology",
            200,
            rating=5,
            review="Excellent.",
        )

        self.assertEqual(
            book.rating,
            5,
        )

        self.assertEqual(
            book.review,
            "Excellent.",
        )

    def test_empty_review_is_allowed(self):
        """Test that a book can have a rating without a review."""
        book = Book(
            "Python",
            "Alice",
            "Technology",
            200,
            rating=4,
        )

        self.assertEqual(
            book.rating,
            4,
        )

        self.assertEqual(
            book.review,
            "",
        )

    def test_update_only_rating(self):
        """Test changing rating without replacing the existing review."""
        book = Book(
            "Python",
            "Alice",
            "Technology",
            200,
            rating=3,
            review="Good book.",
        )

        self.library.add(book)

        self.library.update_rating_review(
            book.id,
            rating=5,
        )

        loaded = self.library.books()[0]

        self.assertEqual(
            loaded.rating,
            5,
        )

        self.assertEqual(
            loaded.review,
            "Good book.",
        )

    def test_update_only_review(self):
        """Test changing review without replacing the existing rating."""
        book = Book(
            "Python",
            "Alice",
            "Technology",
            200,
            rating=4,
            review="Good book.",
        )

        self.library.add(book)

        self.library.update_rating_review(
            book.id,
            review="Updated review.",
        )

        loaded = self.library.books()[0]

        self.assertEqual(
            loaded.rating,
            4,
        )

        self.assertEqual(
            loaded.review,
            "Updated review.",
        )

    def test_rating_unknown_book(self):
        """Test rating update for a missing book."""
        with self.assertRaises(BookNotFoundError):
            self.library.update_rating_review(
                "missing",
                rating=5,
            )

    def test_csv_export(self):
        """Test CSV report generation."""
        book = Book(
            "Python",
            "Alice",
            "Technology",
            200,
            "finished",
            rating=5,
            review="Excellent.",
        )

        self.library.add(book)

        output = self.temp_dir / "library_report.csv"

        self.library.export_report(
            output,
            format="csv",
        )

        self.assertTrue(
            output.exists()
        )

        with output.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            rows = list(
                csv.reader(file)
            )

        self.assertEqual(
            rows[0][0],
            "ID",
        )

        self.assertEqual(
            rows[0][-2:],
            ["Rating", "Review"],
        )

        self.assertEqual(
            rows[1][1],
            "Python",
        )

        self.assertEqual(
            rows[1][-2:],
            ["5", "Excellent."],
        )

    def test_markdown_export(self):
        """Test Markdown report generation."""
        book = Book(
            "Python",
            "Alice",
            "Technology",
            200,
            "finished",
            rating=5,
            review="Excellent.",
        )

        self.library.add(book)

        output = (
            self.temp_dir
            / "library_report.md"
        )

        self.library.export_report(
            output,
            format="markdown",
        )

        self.assertTrue(
            output.exists()
        )

        content = output.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "# Personal Library & Reading Tracker",
            content,
        )

        self.assertIn(
            "Python",
            content,
        )

        self.assertIn(
            "Alice",
            content,
        )

        self.assertIn(
            "Technology",
            content,
        )

        self.assertIn(
            "5",
            content,
        )

        self.assertIn(
            "Excellent.",
            content,
        )

    def test_invalid_export_format(self):
        """Test that unsupported report formats are rejected."""
        output = (
            self.temp_dir
            / "library_report.txt"
        )

        with self.assertRaises(ValidationError):
            self.library.export_report(
                output,
                format="txt",
            )

        self.assertFalse(
            output.exists()
        )

    def test_validation(self):
        """Test general book and operation validation."""
        for pages in (0, -1, True):
            with self.assertRaises(ValidationError):
                Book(
                    "A",
                    "X",
                    "Fiction",
                    pages,
                )

        with self.assertRaises(BookNotFoundError):
            self.library.remove("missing")

        with self.assertRaises(ValidationError):
            Book(
                "A",
                "X",
                "Fiction",
                100,
                "reading",
            ).update_progress(101)


if __name__ == "__main__":
    unittest.main()