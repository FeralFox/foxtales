from pathlib import Path

from books_server.run import CalibreDb

db = CalibreDb("http://localhost:8000", "abc", "123")
print(db.add_book(Path(r"C:\Users\Kitsunebi\Downloads\Das Herz der Zwerge 1 - Markus Heitz.epub")))