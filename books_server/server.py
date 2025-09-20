import base64
import dataclasses
import io
import json
import pathlib
import re
import tempfile
import time
import zipfile
from typing import Literal

import PIL.Image
import fastapi
import uuid
from fastapi import UploadFile
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse

from books_server.constants import BOOKS_PATH

app = fastapi.FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FORMATS = Literal["cbz"]


@dataclasses.dataclass
class ReadingProgress:
    position: float
    lastUpdated: float

    def to_dict(self):
        return {
            "position": self.position,
            "lastUpdated": self.lastUpdated
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReadingProgress":
        return cls(**data)


@dataclasses.dataclass
class BookMetaData:
    identifier: str
    title: str
    format: str
    mimetype: str
    progress: ReadingProgress
    version: int = 0

    def to_dict(self):
        return {
            "version": self.version,
            "identifier": self.identifier,
            "title": self.title,
            "format": self.format,
            "mimetype": self.mimetype,
            "progress": self.progress.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BookMetaData":
        return cls(
            version=data["version"],
            identifier=data["identifier"],
            title=data["title"],
            format=data["format"],
            mimetype=data["mimetype"],
            progress=ReadingProgress.from_dict(data["progress"])
        )


@dataclasses.dataclass
class FullBookMetaData(BookMetaData):
    cover: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "FullBookMetaData":
        return cls(
            version=data["version"],
            identifier=data["identifier"],
            title=data["title"],
            format=data["format"],
            mimetype=data["mimetype"],
            progress=ReadingProgress.from_dict(data["progress"]),
            cover=data["cover"]
        )


class BookInterface:
    def __init__(self, file: UploadFile):
        self._identifier = uuid.uuid4().hex
        self._file = file

    def get_id(self):
        return self._identifier

    def get_ext(self) -> str:
        return self._file.filename.rsplit(".", 1)[-1].lower().lstrip(".")

    def get_metadata(self) -> BookMetaData:
        return BookMetaData(identifier=self.get_id(),
                            mimetype=self.get_mimetype(),
                            title=self.get_title(),
                            format=self.get_ext(),
                            progress=ReadingProgress(
                                0,
                                time.time()
                            ))

    def get_mimetype(self) -> str:
        raise NotImplementedError()

    def get_title(self) -> str:
        raise NotImplementedError()

    def get_cover(self, book_file: pathlib.Path) -> bytes:
        raise NotImplementedError()


class Cbz(BookInterface):
    def __init__(self, file: UploadFile):
        super().__init__(file)

    def get_mimetype(self) -> str:
        return "application/x-cbz"

    def get_title(self):
        return self._file.filename.rsplit(".", 1)[0]

    def get_cover(self, book_file: pathlib.Path) -> bytes:
        """Retrieve the cover image."""
        # TODO: Sort when saving using natural_sort_key
        with tempfile.TemporaryDirectory() as tmpdir_str:
            the_dir = pathlib.Path(tmpdir_str)
            pages = []

            with zipfile.ZipFile(book_file, 'r') as zip_ref:
                zip_ref.extractall(tmpdir_str)

            for cover in the_dir.rglob("*cover*"):
                if cover.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                    return cover.read_bytes()

            for file in the_dir.iterdir():
                if file.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                    pages.append(file)

            def natural_sort_key(s: pathlib.Path, _nsre=re.compile(r'(\d+)')):
                return [int(text) if text.isdigit() else text.lower()
                        for text in _nsre.split(s.name)]

            pages.sort(key=natural_sort_key)

            return pages[0].read_bytes()


class Epub(BookInterface):
    pass


@app.get("/", include_in_schema=False)
def forward_to_docs():
    return fastapi.responses.RedirectResponse("/docs")


@app.post("/add_book")
async def add_book(file: UploadFile):
    ext = file.filename.rsplit(".", 1)[-1].lower()

    if ext.lower() == "cbz":
        book = Cbz(file)
    elif ext.lower() == "epub":
        book = Epub(file)
    else:
        raise NotImplementedError(f"Unknown format for {file.filename}")

    ext = book.get_ext()
    base_path = (BOOKS_PATH / book.get_id())
    base_path.mkdir(exist_ok=True)
    book_file = (base_path / f"book.{ext}")
    book_file.write_bytes(await file.read())

    (base_path / "meta.json").write_text(json.dumps(book.get_metadata().to_dict(), indent=2))

    buffer = io.BytesIO()
    buffer.write(book.get_cover(book_file))
    img = PIL.Image.open(buffer)
    img.thumbnail((600, 400))
    buffer = io.BytesIO()
    img.save(buffer, format="jpeg", quality=80)
    (base_path / "cover.jpg").write_bytes(buffer.getvalue())

    print(f"Added new book {book.get_id(), book.get_title()}")
    return book.get_id()


@app.get("/list_books")
def list_books() -> list[BookMetaData]:
    books: list[BookMetaData] = []
    for path in BOOKS_PATH.iterdir():
        books.append(BookMetaData.from_dict(json.loads((path / "meta.json").read_text())))
    books.sort(key=lambda v: v.title.lower())
    return books


@app.get("/get_cover")
def get_cover(identifier: str):
    return fastapi.responses.Response((BOOKS_PATH / identifier / "cover.jpg").read_bytes(),
                                      media_type="image/jpg")


@app.get("/get_book")
def get_book_metadata(identifier: str) -> FullBookMetaData:
    data_path = BOOKS_PATH / identifier / "meta.json"
    cover = BOOKS_PATH / identifier / "cover.jpg"
    return FullBookMetaData.from_dict(
        {
            **json.loads((data_path).read_text()),
            "cover": base64.b64encode(cover.read_bytes())
        }
    )


@app.get("/get_book_content")
def get_book_content(identifier: str):
    base_path = BOOKS_PATH / identifier

    book_path = next(base_path.glob("book*"))
    return FileResponse(book_path, media_type="application/x-cbz")


uvicorn.run(app, host="localhost")
