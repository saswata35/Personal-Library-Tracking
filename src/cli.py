"""Interactive command-line menu."""
import argparse
from pathlib import Path

from .library import Library
from .models import Book, LibraryError
from .storage import JSONStorage


def display(books: list[Book]) -> None:
    """Show full IDs for subsequent menu operations."""
    if not books:
        print("No books found.")
        return
    for book in books:
        print(f"\nID: {book.id}\n{book.title} — {book.author} | {book.genre}")
        print(f"{book.status} | Page {book.current_page}/{book.total_pages}")
        if book.finish_date:
            print(f"Finished: {book.finish_date}")


def main() -> int:
    """Load the collection, run the menu, and handle user-facing errors."""
    parser = argparse.ArgumentParser(
        description="Personal Library & Reading Tracker"
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data.json",
        help="JSON storage path (default: project data.json)",
    )
    args = parser.parse_args()

    try:
        library = Library(JSONStorage(args.data))
    except LibraryError as exc:
        print(f"Error: {exc}. Repair the data file before retrying.")
        return 1

    while True:
        try:
            print("\nPERSONAL LIBRARY & READING TRACKER")
            print("1. Add book\n2. View/filter books\n3. Start reading")
            print("4. Update progress\n5. Mark finished\n6. Remove book")
            print("7. Search\n8. Statistics\n9. Exit")
            choice = input("Enter choice (1–9): ").strip()

            if choice == "1":
                book = Book(
                    title=input("Title: "),
                    author=input("Author: "),
                    genre=input("Genre: "),
                    total_pages=int(input("Total pages: ")),
                    status=(
                        input("Status (to-read/reading/finished) [to-read]: ").strip()
                        or "to-read"
                    ),
                )
                library.add(book)
                print(f"Book added. ID: {book.id}")
            elif choice == "2":
                display(
                    library.books(
                        input("Status filter (blank = all): ").strip(),
                        input("Genre filter (blank = all): ").strip(),
                    )
                )
            elif choice in ("3", "4", "5"):
                book_id = input("Full book ID: ").strip()
                page = int(input("Current page: ")) if choice == "4" else 0
                action = {"3": "start", "4": "progress", "5": "finish"}[choice]
                library.update(book_id, action, page)
                print("Book updated and saved.")
            elif choice == "6":
                book_id = input("Full book ID: ").strip()
                if input("Remove this book? (yes/no): ").strip().casefold() == "yes":
                    library.remove(book_id)
                    print("Book removed.")
            elif choice == "7":
                display(library.search(input("Title or author: ")))
            elif choice == "8":
                stats = library.statistics()
                print(f"Total books: {stats['total_books']}")
                print(f"Finished this year: {stats['finished_this_year']}")
                print(
                    f"Average pages per finished book: {stats['average_pages_per_finished_book']:.2f}"
                )
                print(
                    "Favorite genre(s): "
                    + (", ".join(stats["favorite_genres"]) or "None yet")
                )
            elif choice == "9":
                print("Goodbye!")
                return 0
            else:
                print("Choose a number from 1 to 9.")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return 0
        except (LibraryError, ValueError) as exc:
            print(f"Error: {exc}")