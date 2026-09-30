# Personal Library & Reading Tracker

A menu-driven Python application that saves a personal book collection between runs.
Requires Python 3.10 or later. No third-party packages are needed.

## Setup (Windows PowerShell)

Extract the ZIP, open a terminal in `Personal_Library_Tracker`, then run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

If PowerShell activation is blocked, run `.\.venv\Scripts\python.exe main.py`.

## Setup (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

## Using the app

1. Add a book with title, author, genre, positive page count and status.
2. View all books or enter a status and/or exact genre filter.
3. Copy the full book ID from the displayed collection and choose Start reading.
4. Update progress with an absolute page number between zero and total pages.
5. Mark finished to record today's local date and set progress to total pages.
6. Remove a book by ID after typing `yes`.
7. Search with a case-insensitive partial title or author.
8. View statistics.
9. Exit. Every successful mutation has already been saved.

A book added as `finished` receives today's date immediately. Repeated completion
preserves the original date. Reaching the last page through progress does not
change status automatically; choose Mark finished. Progress can be corrected
backward. Duplicate titles are allowed because different editions can share titles.

```bash
python main.py --data my_collection.json
python main.py --help
python -m unittest discover -s tests -v
```

The default file is `data.json` beside `main.py`, regardless of the current
working directory. A missing file starts an empty collection. Invalid existing
JSON stops startup without overwriting the file. Saves use a temporary file and
atomic replacement; failed saves do not update the in-memory collection.
Use one running instance per data file to avoid conflicting edits.

## Statistics definitions

- Total books: all collection entries.
- Finished this year: completion dates in the current local calendar year.
- Average pages per finished book: total pages of all finished books divided by
  finished count; zero when none are finished.
- Favorite genre: the most frequent genre among finished books, ignoring case;
  all tied genres are shown. Unfinished books do not count.

## Structure and concepts

```text
Personal_Library_Tracker/
    src/
        __init__.py
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

`Book` owns validation and progress behavior. `Library` encapsulates the collection
and returns defensive copies. It composes a `Storage` backend. `JSONStorage`
inherits from the abstract `Storage` class. Custom exceptions inherit from
`LibraryError`, separating domain and persistence errors. Type hints and
focused docstrings document public behavior. Storage uses UTF-8 and UUID book IDs.

## Git submission

The download includes a local repository with meaningful commits. After creating
an empty public or shared-access remote repository, run:

```bash
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

If a ZIP tool removes the included `.git` directory, initialize a new repository
with `git init -b main`, `git add .`, and `git commit -m "Implement personal library tracker"`
before adding the remote. Personal `data.json` is ignored; the application creates
it after the first change. Do not commit your virtual environment.

The technical requirements PDF and evaluation rubric were not supplied, so this
implementation follows the requirements in the project description. No remote
repository has been created or published.
