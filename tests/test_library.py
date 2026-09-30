"""Behavioral tests with isolated JSON files."""
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from src.library import Library
from src.models import Book, ValidationError, StorageError, BookNotFoundError
from src.storage import JSONStorage


class LibraryTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.storage = JSONStorage(Path(temp.name) / 'data.json')
        self.library = Library(self.storage)

    def test_lifecycle_reload_remove(self):
        book = Book('Python', 'Alice', 'Technology', 100)
        self.library.add(book)
        with self.assertRaises(ValidationError):
            self.library.update(book.id, 'progress', 20)
        self.library.update(book.id, 'start')
        self.library.update(book.id, 'progress', 40)
        self.assertEqual(Library(self.storage).books()[0].current_page, 40)
        self.library.update(book.id, 'finish')
        loaded = Library(self.storage).books()[0]
        self.assertEqual((loaded.status, loaded.current_page, loaded.finish_date),
                         ('finished', 100, date.today().isoformat()))
        self.library.remove(book.id)
        self.assertEqual(Library(self.storage).books(), [])

    def test_search_filter_copies(self):
        self.library.add(Book('Python Basics', 'ALICE', 'Technology', 200))
        self.assertEqual(len(self.library.search('ali')), 1)
        self.assertEqual(len(self.library.books(genre='TECHNOLOGY')), 1)
        self.library.books()[0].title = 'Changed'
        self.assertEqual(self.library.books()[0].title, 'Python Basics')

    def test_statistics(self):
        self.assertEqual(self.library.statistics()['favorite_genres'], [])
        self.library.add(Book('A', 'X', 'Fiction', 100, 'finished'))
        self.library.add(Book('B', 'Y', 'History', 300, 'finished'))
        self.library.add(Book('C', 'Z', 'History', 500))
        stats = self.library.statistics()
        self.assertEqual(stats['finished_this_year'], 2)
        self.assertEqual(stats['average_pages_per_finished_book'], 200)
        self.assertEqual(stats['favorite_genres'], ['fiction', 'history'])

    def test_corrupt_file_preserved(self):
        self.storage.path.write_text('{broken', encoding='utf-8')
        with self.assertRaises(StorageError):
            Library(self.storage)
        self.assertEqual(self.storage.path.read_text(), '{broken')

    def test_save_failure_rollback(self):
        book = Book('A', 'X', 'Fiction', 100, 'reading')
        self.library.add(book)
        with patch.object(self.storage, 'save', side_effect=StorageError('failed')):
            with self.assertRaises(StorageError):
                self.library.update(book.id, 'progress', 50)
        self.assertEqual(self.library.books()[0].current_page, 0)
        self.assertEqual(Library(self.storage).books()[0].current_page, 0)

    def test_validation(self):
        for pages in (0, -1, True):
            with self.assertRaises(ValidationError):
                Book('A', 'X', 'Fiction', pages)
        with self.assertRaises(BookNotFoundError):
            self.library.remove('missing')
        with self.assertRaises(ValidationError):
            Book('A', 'X', 'Fiction', 100, 'reading').update_progress(101)


if __name__ == '__main__':
    unittest.main()
