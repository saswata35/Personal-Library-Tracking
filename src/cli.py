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
        print(
            f"\nID: {book.id}\n"
            f"{book.title} — {book.author} | {book.genre}"
        )
        print(
            f"{book.status} | "
            f"Page {book.current_page}/{book.total_pages}"
        )

        if getattr(book, "rating", None) is not None:
            print(f"Rating: {book.rating}/5")

        if getattr(book, "review", None):
            print(f"Review: {book.review}")

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
            print("1. Add book")
            print("2. View/filter books")
            print("3. Start reading")
            print("4. Update progress")
            print("5. Mark finished")
            print("6. Remove book")
            print("7. Search")
            print("8. Statistics")
            print("9. Update rating/review")
            print("10. Export CSV/Markdown report")
            print("11. Exit")

            choice = input("Enter choice (1–11): ").strip()

            # ---------------------------------------------------------
            # 1. Add book
            # ---------------------------------------------------------
            if choice == "1":
                book = Book(
                    title=input("Title: "),
                    author=input("Author: "),
                    genre=input("Genre: "),
                    total_pages=int(input("Total pages: ")),
                    status=(
                        input(
                            "Status "
                            "(to-read/reading/finished) [to-read]: "
                        ).strip()
                        or "to-read"
                    ),
                )

                library.add(book)
                print(f"Book added. ID: {book.id}")

            # ---------------------------------------------------------
            # 2. View/filter books
            # ---------------------------------------------------------
            elif choice == "2":
                status = input(
                    "Status filter (blank = all): "
                ).strip()

                genre = input(
                    "Genre filter (blank = all): "
                ).strip()

                display(library.books(status, genre))

            # ---------------------------------------------------------
            # 3, 4, 5. Reading actions
            # ---------------------------------------------------------
            elif choice in ("3", "4", "5"):
                book_id = input("Full book ID: ").strip()

                page = (
                    int(input("Current page: "))
                    if choice == "4"
                    else 0
                )

                action = {
                    "3": "start",
                    "4": "progress",
                    "5": "finish",
                }[choice]

                library.update(book_id, action, page)

                print("Book updated and saved.")

            # ---------------------------------------------------------
            # 6. Remove book
            # ---------------------------------------------------------
            elif choice == "6":
                book_id = input("Full book ID: ").strip()

                confirmation = input(
                    "Remove this book? (yes/no): "
                ).strip().casefold()

                if confirmation == "yes":
                    library.remove(book_id)
                    print("Book removed.")
                else:
                    print("Book was not removed.")

            # ---------------------------------------------------------
            # 7. Search
            # ---------------------------------------------------------
            elif choice == "7":
                query = input("Title or author: ").strip()
                display(library.search(query))

            # ---------------------------------------------------------
            # 8. Statistics
            # ---------------------------------------------------------
            elif choice == "8":
                stats = library.statistics()

                print(f"Total books: {stats['total_books']}")
                print(
                    f"Finished this year: "
                    f"{stats['finished_this_year']}"
                )
                print(
                    "Average pages per finished book: "
                    f"{stats['average_pages_per_finished_book']:.2f}"
                )
                print(
                    "Favorite genre(s): "
                    + (
                        ", ".join(stats["favorite_genres"])
                        or "None yet"
                    )
                )

            # ---------------------------------------------------------
            # 9. Update rating/review
            # ---------------------------------------------------------
            elif choice == "9":
                book_id = input("Full book ID: ").strip()

                rating_input = input(
                    "Rating (1–5, blank to keep unchanged): "
                ).strip()

                rating = (
                    int(rating_input)
                    if rating_input
                    else None
                )

                review = input(
                    "Review/notes (blank to keep unchanged): "
                ).strip()

                library.update_rating_review(
                    book_id,
                    rating=rating,
                    review=review if review else None,
                )

                print("Rating/review updated and saved.")

            # ---------------------------------------------------------
            # 10. Export CSV/Markdown report
            # ---------------------------------------------------------
            elif choice == "10":
                print("\nEXPORT REPORT")
                print("1. CSV")
                print("2. Markdown")

                export_choice = input(
                    "Choose export format (1–2): "
                ).strip()

                if export_choice == "1":
                    output_path = input(
                        "CSV file path [library_report.csv]: "
                    ).strip() or "library_report.csv"

                    library.export_report(
                        Path(output_path),
                        format="csv",
                    )

                    print(
                        f"CSV report exported to: {output_path}"
                    )

                elif export_choice == "2":
                    output_path = input(
                        "Markdown file path "
                        "[library_report.md]: "
                    ).strip() or "library_report.md"

                    library.export_report(
                        Path(output_path),
                        format="markdown",
                    )

                    print(
                        f"Markdown report exported to: "
                        f"{output_path}"
                    )

                else:
                    print("Choose either 1 or 2.")

            # ---------------------------------------------------------
            # 11. Exit
            # ---------------------------------------------------------
            elif choice == "11":
                print("Goodbye!")
                return 0

            else:
                print("Choose a number from 1 to 11.")

        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return 0

        except (LibraryError, ValueError) as exc:
            print(f"Error: {exc}")

