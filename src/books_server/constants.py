import pathlib

DATA_PATH = pathlib.Path(__file__).parent.parent.parent / "data"

BOOKS_PATH = DATA_PATH / "books"

BOOKS_PATH.mkdir(exist_ok=True)
