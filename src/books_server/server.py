import base64
import dataclasses
import io
import json
import pathlib
import re
import tempfile
import time
import zipfile
from typing import Literal, Optional

import PIL.Image
import fastapi
import uuid
from fastapi import UploadFile
import uvicorn
from starlette.middleware.cors import CORSMiddleware

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
class Chapter:
    identifier: str
    title: str
    length: int
    file: Optional[pathlib.Path] = None

    def to_dict(self):
        return {
            "identifier": self.identifier,
            "title": self.title,
            "length": self.length
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Chapter":
        return cls(**data)


@dataclasses.dataclass
class ReadingProgress:
    chapter: int
    position: int
    lastUpdated: float

    def to_dict(self):
        return {
            "chapter": self.chapter,
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
    chapters: list[Chapter]
    format: FORMATS
    progress: ReadingProgress
    version: int = 0

    def to_dict(self):
        return {
            "version": self.version,
            "identifier": self.identifier,
            "title": self.title,
            "format": self.format,
            "chapters": [chapter.to_dict() for chapter in self.chapters],
            "progress": self.progress.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BookMetaData":
        return cls(
            version=data["version"],
            identifier=data["identifier"],
            title=data["title"],
            chapters=[Chapter.from_dict(chapter) for chapter in data["chapters"]],
            format=data["format"],
            progress=ReadingProgress.from_dict(data["progress"])
        )


@dataclasses.dataclass
class Base64CoverData:
    cover: str


class Cbz:
    def __init__(self, identifier: str, file_path: pathlib.Path):
        self._file = file_path
        self._identifier = identifier

    def iter_chapters(self):
        with tempfile.TemporaryDirectory() as tmpdir_str:
            the_dir = pathlib.Path(tmpdir_str)
            pages = []

            with zipfile.ZipFile(self._file, 'r') as zip_ref:
                zip_ref.extractall(tmpdir_str)

            for file in the_dir.iterdir():
                if file.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                    pages.append(file)

            def natural_sort_key(s: pathlib.Path, _nsre=re.compile(r'(\d+)')):
                return [int(text) if text.isdigit() else text.lower()
                        for text in _nsre.split(s.name)]

            pages.sort(key=natural_sort_key)

            for i, page_path in enumerate(pages):
                yield Chapter(f"{self._identifier}_{str(i).zfill(5)}",
                              page_path.stem,
                              1, file=page_path)


def _load_metadata_from_cbz(identifier: str, cbz_path: pathlib.Path, filename: str):
    cbz = Cbz(identifier, file_path=cbz_path)

    the_cover = b""
    chapters = []
    for chapter in cbz.iter_chapters():
        if not the_cover or "cover" in chapter.title.lower():
            the_cover = chapter.file.read_bytes()
        chapters.append(chapter)

    metadata = BookMetaData(identifier=identifier,
                            title=filename.rsplit(".", 1)[0],
                            format="cbz",
                            chapters=chapters,
                            progress=ReadingProgress(
                                0,
                                0,
                                time.time()
                            ))
    return metadata, the_cover


@app.get("/", include_in_schema=False)
def forward_to_docs():
    return fastapi.responses.RedirectResponse("/docs")


@app.post("/add_book")
async def add_book(file: UploadFile):
    identifier = uuid.uuid4().hex
    book_dir = BOOKS_PATH / identifier
    book_dir.mkdir()
    output_file = book_dir / "book.cbz"
    output_file.write_bytes(await file.read())
    metadata, cover = _load_metadata_from_cbz(identifier, output_file, file.filename)
    (book_dir / "meta.json").write_text(json.dumps(metadata.to_dict(), indent=2))
    buffer = io.BytesIO()
    buffer.write(cover)
    buffer.seek(0)
    img = PIL.Image.open(buffer)
    img.thumbnail((600, 400))
    buffer = io.BytesIO()
    img.save(buffer, format="jpeg", quality=80)
    (book_dir / "cover.jpg").write_bytes(buffer.getvalue())


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


@app.get("/get_cover_b64")
def get_cover_b64(identifier: str) -> Base64CoverData:
    return Base64CoverData(base64.b64encode((BOOKS_PATH / identifier / "cover.jpg").read_bytes()).decode("utf-8"))


@app.get("/get_book")
def get_book_metadata(identifier: str) -> BookMetaData:
    data_path = BOOKS_PATH / identifier / "meta.json"
    return BookMetaData.from_dict(json.loads((data_path).read_text()))


@app.get("/get_book_content")
def get_book(identifier: str):
    base_path = BOOKS_PATH / identifier
    cbz = Cbz(identifier, base_path / "book.cbz")
    output = {}
    for chapter in cbz.iter_chapters():
        output[chapter.identifier] = base64.b64encode(chapter.file.read_bytes())
    return output


uvicorn.run(app, host="192.168.178.21")