import dataclasses
import datetime
import functools
import json
import logging
import mimetypes
import pathlib
import re
import subprocess
import tempfile
from typing import Optional

import PIL.Image

LIBRARY_PATH = pathlib.Path("/config/Calibre Library")


class AuthenticationError(ValueError):
    pass


@dataclasses.dataclass
class CalibreListData:
    title: str
    uuid: str
    author_sort: str
    authors: str
    cover: str
    formats: list[str]
    id: int
    identifiers: dict[str, str]
    languages: list[str]
    last_modified: str
    pubdate: str
    series_index: float
    size: int
    tags: list[str]
    timestamp: str
    fxtl_owner: str
    fxtl_is_read: bool
    fxtl_progress: float
    fxtl_progress_update: str

    @classmethod
    def from_dict(cls, data: dict) -> "CalibreListData":
        # Calibre returns the full book path for local library. We only want to have the format.
        formats = [f.rsplit(".", 1)[-1] for f in data.get("formats", [])]
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            uuid=data.get("uuid", ""),
            author_sort=data.get("author_sort", ""),
            authors=data.get("authors", ""),
            cover=data.get("cover", ""),
            formats=formats,
            identifiers=data.get("identifiers", {}),
            languages=data.get("languages", []),
            last_modified=data.get("last_modified", ""),
            pubdate=data.get("pubdate", ""),
            series_index=data.get("series_index", 0),
            size=data.get("size", 0),
            tags=data.get("tags", []),
            timestamp=data.get("timestamp", ""),
            fxtl_owner=data.get("*fxtl_owner", ""),
            fxtl_is_read=data.get("*fxtl_is_read", False),
            fxtl_progress=data.get("*fxtl_progress", 0.0),
            fxtl_progress_update=data.get("*fxtl_progress_update", datetime.datetime.now().isoformat()),
        )


@dataclasses.dataclass
class FullBookMetadata(CalibreListData):
    pass


@dataclasses.dataclass
class UserData:
    username: str
    password: str
    salt: str
    email: str

    @classmethod
    def from_json(cls, data: dict) -> "UserData":
        return cls(**data)


@dataclasses.dataclass
class FxtlData:
    user: UserData

    @classmethod
    def load(cls, file: pathlib.Path) -> "FxtlData":
        data = json.loads(file.read_text())
        return cls(user=UserData.from_json(data["user"]))

    def save(self, file: pathlib.Path):
        file.write_text(json.dumps(dataclasses.asdict(self)))


@dataclasses.dataclass
class CachedBookMetadata:
    """Metadata that will (most likely) not change - used as cache."""
    book_id: int
    local_path: pathlib.Path


class CalibreDb:
    def __init__(self, host: pathlib.Path):
        self._path = host
        self._user = host.name
        self._book_cache: dict[str, CachedBookMetadata] = {}
        self.upgrade_library()

    @functools.lru_cache(maxsize=1000)
    def get_book_id_by_uuid(self, uuid: str) -> Optional[int]:
        result = self.list_books(f"uuid:{uuid}", fields="")
        try:
            return result[0].id
        except (IndexError, AttributeError):
            raise FileNotFoundError(f"No book with uuid {uuid} found")

    def get_user_data(self) -> FxtlData:
        return FxtlData.load(self._path / "fxtl_data.json")

    def store_user_data(self, user_data: FxtlData):
        user_data.save(self._path / "fxtl_data.json")

    def _get_auth(self):
        return ['--with-library', self._path.as_posix()]

    def upgrade_library(self):
        """Add extra fields required by foxtales to Calibre library."""
        try:
            columns = self.get_custom_columns()
        except Exception:
            raise AuthenticationError()
        if not "fxtl_owner" in columns.values():
            self._add_custom_column("fxtl_owner", "Added by", "text", False)
        if not "fxtl_progress" in columns.values():
            self._add_custom_column("fxtl_progress", "Reading Progress", "float", False)
        if not "fxtl_progress_update" in columns.values():
            self._add_custom_column("fxtl_progress_update", "Last Reading Progress Update", "datetime", False)
        if not "fxtl_is_read" in columns.values():
            self._add_custom_column("fxtl_is_read", "Is Read", "bool", False)
        if not "fxtl_tags" in columns.values():
            self._add_custom_column("fxtl_tags", "Tags", "text", True)

    def _add_custom_column(self, name: str, display_name: str, datatype: str, is_multiple: bool):
        logging.info(f"Add custom column {name}")
        is_multiple = []
        if is_multiple:
            is_multiple = ["--is-multiple"]
        subprocess.check_output(["calibredb", "add_custom_column", *is_multiple, name, display_name, datatype, *self._get_auth()])

    def get_custom_columns(self) -> dict[int, str]:
        result = subprocess.check_output(['calibredb', 'custom_columns', *self._get_auth()])
        results = {}
        for line in result.decode("utf-8").splitlines():
            try:
                name, identifier = line.split(" ")
            except ValueError:
                continue
            results[int(identifier.strip("()"))] = name
        return results

    def list_books(self, filter_query: str = "", fields: str = "all") -> list[CalibreListData]:
        filter_options = []
        if filter_query:
            filter_options = ["--search", filter_query]
        result = subprocess.check_output(['calibredb', 'list', *filter_options, '--fields', fields, '--for-machine', *self._get_auth()])
        results = []
        for res in json.loads(result):
            data = CalibreListData.from_dict(res)
            self._book_cache[data.uuid] = CachedBookMetadata(
                data.id,
                pathlib.Path(data.cover).parent
            )
            results.append(data)
        return results

    def get_book_id(self, book_uuid: str) -> int:
        try:
            return self._book_cache[book_uuid].book_id
        except (KeyError, AssertionError):
            self.list_books(f"uuid:{book_uuid}")
            return self._book_cache[book_uuid].book_id

    def get_book_path(self, book_uuid: str) -> pathlib.Path:
        try:
            local_path = self._book_cache[book_uuid].local_path
            assert local_path.exists()
            return local_path
        except (KeyError, AssertionError):
            self.list_books(f"uuid:{book_uuid}")
            return self._book_cache[book_uuid].local_path

    def add_book(self, book: pathlib.Path, users: Optional[list[str]] = None) -> int:
        """Add a book to Calibre library."""
        result = subprocess.check_output(['calibredb', "add",  book.as_posix(), *self._get_auth()])
        try:
            book_id = int(re.findall(b"\d+", result)[0])
        except Exception as error:
            raise RuntimeError(f"Unexpected response when calling 'calibredb add': {result}") from error
        self.set_custom_value(book_id, "fxtl_owner", self._user)
        self.set_custom_value(book_id, "fxtl_progress", "0")
        self.set_custom_value(book_id, "fxtl_progress_update", datetime.datetime.now().isoformat())
        self.set_custom_value(book_id, "fxtl_is_read", "False")
        self.set_custom_value(book_id, "fxtl_tags", "")
        return book_id

    def remove_book(self, book_id: int):
        """Add a book to Calibre library."""
        result = subprocess.check_output(['calibredb', "remove",  str(book_id), *self._get_auth()])

    def set_custom_value(self, book_id: int, key: str, value: str) -> bytes:
        """Set custom value for a book."""
        return subprocess.check_output(
            ['calibredb', "set_custom", key, str(book_id), value, *self._get_auth()])

    def add_datafile(self, book_id: int, the_file: pathlib.Path) -> bytes:
        """Add a Calibre datafile."""
        return subprocess.check_output(
            ["calibredb", "add_format", "--as-extra-data-file", str(book_id), the_file, *self._get_auth()])

    def get_datafile(self, book_id: int, name: str) -> bytes:
        with tempfile.TemporaryDirectory() as tmpdir_str:
            the_dir = pathlib.Path(tmpdir_str)
            subprocess.check_output(["calibredb", "export", "--dont-update-metadata", "--dont-write-opf", "--formats", name, "--dont-save-cover", "--template", "{id}", "--to-dir", the_dir.as_posix(), str(book_id), *self._get_auth()])
            try:
                return next(the_dir.rglob(f"*{name}")).read_bytes()
            except StopIteration:
                return b""

    def retrieve_book(self, book_id: int, format: str) -> tuple[str, bytes]:
        """Download the book. Returns a tuple of mimetype and byte data."""
        with tempfile.TemporaryDirectory() as tmpdir_str:
            the_dir = pathlib.Path(tmpdir_str)
            result = subprocess.check_output(["calibredb", "export", "--dont-update-metadata", "--dont-save-extra-files", "--dont-write-opf", "--dont-save-cover", "--formats", format, "--template", "{id}", "--to-dir", the_dir.as_posix(), str(book_id), *self._get_auth()])
            the_book = next(the_dir.glob("*"))
            return mimetypes.guess_type(the_book)[0], the_book.read_bytes()

    @functools.lru_cache(maxsize=100)
    def retrieve_cover(self, book_uuid: str) -> tuple[str, bytes]:
        """Retrieve the cover of the book. Returns a tuple of mimetype and byte data."""
        local_path = self.get_book_path(book_uuid)
        preview = local_path / "data" / "cover.min.jpg"
        if preview.exists():
            b = preview.read_bytes()
            return "image/jpeg", b
        with tempfile.TemporaryDirectory() as tmpdir_str:
            the_dir = pathlib.Path(tmpdir_str)
            book_id = self.get_book_id(book_uuid)
            subprocess.check_output(["calibredb", "export", "--dont-save-extra-files", "--dont-update-metadata", "--dont-write-opf", "--formats", "jpg,jpeg,png,gif", "--template", "{id}", "--to-dir", the_dir.as_posix(), str(book_id), *self._get_auth()])
            the_book = next(the_dir.glob("*"))
            image = PIL.Image.open(the_book)
            preview.parent.mkdir(exist_ok=True)
            image.thumbnail((400, 400))
            image.save(preview, "jpeg", quality=80)
            return "image/jpeg", preview.read_bytes()

    def get_book_metadata(self, book_id: int) -> FullBookMetadata:
        data = self.list_books(f"id:{book_id}")[0]
        return FullBookMetadata(**data.__dict__)
