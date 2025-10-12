import dataclasses
import functools
import io
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


@dataclasses.dataclass
class Progress:
    position: float
    last_update: float

    @classmethod
    def from_dict(cls, data: dict) -> "Progress":
        return cls(
            position=data.get("position", 0),
            last_update=data.get("last_update", 0),
        )


@dataclasses.dataclass
class FxtlMetaData:
    progress: Progress

    @classmethod
    def from_dict(cls, data: dict):
        return cls(progress=Progress.from_dict(data.get("progress", {})))


@dataclasses.dataclass
class FullFxtlMetaData:
    userdata: dict[str, FxtlMetaData]

    @classmethod
    def from_dict(cls, data: dict):
        userdata = data.get("userdata", {})
        for key, value in userdata.items():
            userdata[key] = FxtlMetaData.from_dict(value)
        return cls(userdata)


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
    fxtl_readers: list[str]

    @classmethod
    def from_dict(cls, data: dict) -> "CalibreListData":
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            uuid=data.get("uuid", ""),
            author_sort=data.get("author_sort", ""),
            authors=data.get("authors", ""),
            cover=data.get("cover", ""),
            formats=data.get("formats", []),
            identifiers=data.get("identifiers", {}),
            languages=data.get("languages", []),
            last_modified=data.get("last_modified", ""),
            pubdate=data.get("pubdate", ""),
            series_index=data.get("series_index", 0),
            size=data.get("size", 0),
            tags=data.get("tags", []),
            timestamp=data.get("timestamp", ""),
            fxtl_owner=data.get("*fxtl_owner", ""),
            fxtl_readers=data.get("*fxtl_readers", []),
        )


@dataclasses.dataclass
class FullBookMetadata(CalibreListData):
    fxtl: FxtlMetaData


class CalibreDb:
    def __init__(self, host: str, user: str, password: str):
        self._host = host
        self._user = user
        self._password = password

    def _get_auth(self):
        return ['--with-library', LIBRARY_PATH.as_posix()]

    def upgrade_library(self):
        """Add extra fields required by foxtales to Calibre library."""
        try:
            columns = self.get_custom_columns()
        except Exception:
            raise AuthenticationError()
        if not "fxtl_owner" in columns.values():
            self._add_custom_column("fxtl_owner", "Added by", "text", False)
        if not "fxtl_readers" in columns.values():
            self._add_custom_column("fxtl_readers", "Users with Access", "text", True)

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
            owner = res.get("*fxtl_owner")
            users_with_access = res.get("*fxtl_readers", [])

            if "*" in users_with_access:
                users_with_access.append(self._user)

            all_users_with_access = [owner, *users_with_access]

            if self._user in all_users_with_access or not all_users_with_access:
                res["formats"] = [path.rsplit(".", 1)[-1].upper() for path in res.get("formats", [])]
                results.append(CalibreListData.from_dict(res))
        return results

    def add_book(self, book: pathlib.Path, users: Optional[list[str]] = None) -> int:
        """Add a book to Calibre library."""
        result = subprocess.check_output(['calibredb', "add",  book.as_posix(), *self._get_auth()])
        try:
            book_id = int(re.findall(b"\d+", result)[0])
        except Exception as error:
            raise RuntimeError(f"Unexpected response when calling 'calibredb add': {result}") from error
        self.set_custom_value(book_id, "fxtl_owner", self._user)
        self.set_custom_value(book_id, "fxtl_readers", ",".join(users or [self._user]))
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

    def retrieve_book(self, book_id: int, format: str) -> tuple[str, bytes]:
        """Download the book. Returns a tuple of mimetype and byte data."""
        with tempfile.TemporaryDirectory() as tmpdir_str:
            the_dir = pathlib.Path(tmpdir_str)
            result = subprocess.check_output(["calibredb", "export", "--dont-update-metadata", "--dont-save-extra-files", "--dont-write-opf", "--dont-save-cover", "--formats", format, "--template", "{id}", "--to-dir", the_dir.as_posix(), str(book_id), *self._get_auth()])
            the_book = next(the_dir.glob("*"))
            return mimetypes.guess_type(the_book)[0], the_book.read_bytes()

    @functools.lru_cache(maxsize=500)
    def retrieve_cover(self, book_id: int) -> tuple[str, bytes]:
        """Retrieve the cover of the book. Returns a tuple of mimetype and byte data."""
        with tempfile.TemporaryDirectory() as tmpdir_str:
            the_dir = pathlib.Path(tmpdir_str)
            subprocess.check_output(["calibredb", "export", "--dont-save-extra-files", "--dont-update-metadata", "--dont-write-opf", "--formats", "jpg,jpeg,png,gif", "--template", "{id}", "--to-dir", the_dir.as_posix(), str(book_id), *self._get_auth()])
            the_book = next(the_dir.glob("*"))
            image = PIL.Image.open(the_book)
            buffer = io.BytesIO()
            image.thumbnail((400, 400))
            image.save(buffer, "jpeg", quality=80)
            return "image/jpeg", buffer.getvalue()

    def _retrieve_full_fxtl_data(self, book_id: int) -> FullFxtlMetaData:
        try:
            with tempfile.TemporaryDirectory() as tmpdir_str:
                the_dir = pathlib.Path(tmpdir_str)
                subprocess.check_output(["calibredb", "export", "--dont-update-metadata", "--dont-write-opf", "--dont-save-cover", "--formats", "fxtl", "--template", "{id}", "--to-dir", the_dir.as_posix(), str(book_id), *self._get_auth()])
                the_book = next((the_dir / "data").glob("*"))
                return FullFxtlMetaData.from_dict(json.loads(the_book.read_text()))
        except StopIteration:
            return FullFxtlMetaData({})

    def _retrieve_user_fxtl_data(self, book_id: int) -> FxtlMetaData:
        return self._retrieve_full_fxtl_data(book_id).userdata.get(self._user,
                                                                   FxtlMetaData(Progress(0, 0)))

    def update_fxtl_data(self, book_id: int, metadata: FxtlMetaData):
        """Update FxtlMetaData for the user."""
        full_fxtl_data = self._retrieve_full_fxtl_data(book_id)
        full_fxtl_data.userdata[self._user] = metadata
        with tempfile.TemporaryDirectory() as tmpdir_str:
            the_dir = pathlib.Path(tmpdir_str)
            tmp_file = the_dir / "metadata.fxtl"
            tmp_file.write_text(json.dumps(dataclasses.asdict(full_fxtl_data)))
            result = self.add_datafile(book_id, tmp_file)
        return result

    def get_book_metadata(self, book_id: int) -> FullBookMetadata:
        data = self.list_books(f"id:{book_id}")[0]
        fxtl_data = self._retrieve_user_fxtl_data(book_id)
        return FullBookMetadata(**data.__dict__, fxtl=fxtl_data)
