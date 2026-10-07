# Personal Library & Reading Tracker

A menu-driven Python application for managing a personal book collection and tracking reading progress. Requires Python 3.10 or later and uses only the Python standard library.

## Working Features

- Add books with title, author, genre, total pages, and reading status.
- View the collection and filter by status, genre, or both.
- Start reading a book previously marked `to-read`.
- Update the current page of a book marked `reading`.
- Mark books as finished, setting progress to the total pages and recording today's local date.
- Remove books by ID after confirmation.
- Search titles and authors using case-insensitive partial matches.
- View total books, books finished this year, average pages per finished book, and favorite genres.
- Save every successful change and reload the collection automatically at startup.
- Handle invalid input, missing book IDs, and storage errors with custom exceptions.

## Tasks and Constraints

|   Menu   |                    Task                          |                     Input and behavior                           |

|    1     |                  Add book                        | Nonempty title, author, genre; positive integer page count; valid status. Default status is `to-read`.  |

|    2     |                  View/filter books               | Blank filters show all books. Status uses an exact match; genre uses a case-insensitive exact match. |

|    3     |                  Start reading                   | Requires an existing full book ID. Finished books cannot be restarted. |

|    4     |                  Update progress                 | Requires an existing full ID and `reading` status. Page must be an integer 
from zero to total pages.     |

|    5     |                  Mark finished                   | Requires an existing full ID. Sets all pages read and records a completion date. |

|    6     |                  Remove book                     | Requires an existing full ID and confirmation by typing `yes`. |

|    7     |                  Search                          | Case-insensitive substring search in title or author. An empty query matches all books. |

|    8     |                  Statistics                      | Calculates collection and completion statistics. |

|    9     |                  Exit                            | Changes are already saved after each successful operation. |


## Data Types and Validation

|      Field              |               Python type                   |                          Constraints                        |

|      `id`               |                `str`                        |        Automatically generated UUID hex string by default; nonempty and unique in the collection.                         |

|      `title`            |                `str`                        |        Nonempty after trimming surrounding whitespace.      |

|      `author`           |                `str`                        |        Nonempty after trimming surrounding whitespace.      |

|      `genre`            |                `str`                        |        Nonempty after trimming surrounding whitespace.      |

|      `total_pages`      |                `int`                        |        Greater than zero. Boolean values are rejected.      |

|      `status`           |                          `str`                        |        Exactly `to-read`, `reading`, or 
`finished`.                                           |

|      `current_page`     |                `int`                        |        Between zero and `total_pages`, inclusive. Boolean values are rejected. A `to-read` book must have zero progress.   |

|      `finish_date`      |                `str` or `None`              |        Only finished books have a finish date. It must be a valid, nonfuture ISO date; generated dates use `YYYY-MM-DD`. |

When a book is created as finished, its current page is set to the total pages and a missing finish date defaults to today.

The collection uses a `list[Book]`. Dictionaries represent serialized records and statistics. A set checks for duplicate IDs during loading, and `Counter` counts finished books by genre.

## Database and Data Persistence

This project uses ``JSON file storage``.

- Default storage: `data.json` beside `main.py`.
- Encoding: UTF-8, preserving Unicode titles and author names.
- Format: a JSON object containing `version: 1` and a `books` array.
- A missing file starts an empty collection; the first successful change creates it.
- Invalid saved data stops startup without overwriting the existing file.
- Saves write a temporary file, flush it to disk, and atomically replace the destination.
- If saving fails, the collection does not adopt the attempted change in memory.
- Use one running application instance per data file to avoid conflicting edits.
- Personal `data.json` is excluded from Git by `.gitignore`.

Example saved record:

```json
{
  "version": 1,
  "books": [
    {
      "id": "ab53017e89354639892e945d3e3d1820",
      "title": "Python Crash Course",
      "author": "Eric Matthes",
      "genre": "Programming",
      "total_pages": 544,
      "status": "reading",
      "current_page": 120,
      "finish_date": null
    }
  ]
}
```

## Statistics

|                    Statistic                       |                              Calculation                                    |

|                   Total books                      |                  Number of entries in the collection.                       |

|               Finished this year                   |                  Finished books whose finish date falls in the current local calendar year.                     |

|               Average pages per finished book      |                  Total pages of finished books divided by their count; zero if none are finished.                 |
 
|               Favorite genre(s)                    |                  Most frequent genre among finished books, ignoring case. All tied winners are displayed.    |

## Setup and Run

Clone the repository and enter its folder:

## Bash Presentation:-
```
git clone https://github.com/saswata35/Personal-Library-Tracking.git
cd Personal-Library-Tracking
```

## Windows powershell(Mandatory) :- 
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Note:- If activation is blocked, We can run the virtual environment interpreter directly:

## Windows powershell(Optional) :- 
```
.\.venv\Scripts\python.exe main.py
```

## Project Structure

```text
Personal_Library_Tracker/
    src/
        __init__.py
        __main__.py
        models.py
        library.py
        storage.py
        cli.py
    tests/
        test_library.py
    main.py
    requirements.txt
    README.md
    data.json
    .gitignore
```

## Python Concepts Used

|                    Concept                                       |                       Implementation                                     |

|              Classes and dataclasses                             |     `Book` stores book metadata and provides validation and progress methods. |

|                  Encapsulation                                   |     `Library` owns its collection and returns defensive copies.          |

|              Inheritance and abstraction                         |     `JSONStorage` implements the abstract `Storage` interface.           |

|                  Composition                                     |     `Library` receives and uses a storage backend.                       |

|              Custom exceptions                                   |     `LibraryError`, `ValidationError`, `BookNotFoundError`, and 
`StorageError`. |

|               Error handling                                     |     `try/except` handles expected input and persistence errors.          |

|          Type hints and docstrings                               |     Document expected types and method behavior.                         |

|           File handling and JSON                                 |     Save and load structured records using standard-library modules.     |

|           Command-line interface                                 |     `argparse` handles storage options; a menu handles user operations.  |

|                  Testing                                           |     `unittest`, temporary files, and mocked save failures.               |

## Tests

Run from the project root:

## Bash code(Mandatory):-
python -m unittest discover -s tests -v
```

The included six tests cover lifecycle and reload/removal, search and filtering, defensive copies, statistics, corrupt-file preservation, failed-save rollback, and validation.

## Optional Features Not Yet Implemented

- CSV or Markdown export.
- Ratings and review notes.
- Editable installation with `pip install -e .`.
- Internal event logging.

These are optional stretch goals. The separate assignment PDF and evaluation rubric were not included in the reviewed ZIP, so compliance with their additional requirements has not been verified.
