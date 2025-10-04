import dataclasses
import functools
import io
import json
import logging
import mimetypes
import os
import pathlib
import re
import subprocess
import tempfile
from typing import Optional

import PIL.Image
import time

LIBRARY_PATH = pathlib.Path("/config/Calibre Library")

@dataclasses.dataclass
class FxtlMetaData:
    progress: float
    progress_updated: float


class AuthenticationError(ValueError):
    pass


class CalibreDb:
    def __init__(self, host: str, user: str, password: str):
        self._host = host
        self._user = user
        self._password = password

    def _get_auth(self):
        return ['--with-library', LIBRARY_PATH.as_posix()]

    def _upgrade_library(self):
        try:
            columns = self.get_custom_columns()
        except Exception:
            raise AuthenticationError()
        if not "fxtl_owner" in columns.values():
            self._add_custom_column("fxtl_owner", "Added by", "text", False)
        if not "fxtl_users" in columns.values():
            self._add_custom_column("fxtl_users", "Users with Access", "text", True)


    def _add_custom_column(self, name: str, display_name: str, datatype: str, is_multiple: bool):
        print(f"Add custom column {name}")
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

    def list_books(self, filter_query: str = "", fields: str = "all"):
        filter_options = []
        if filter_query:
            filter_options = ["--search", filter_query]
        result = subprocess.check_output(['calibredb', 'list', *filter_options, '--fields', fields, '--for-machine', *self._get_auth()])
        results = []
        for res in json.loads(result):
            owner = res.get("*fxtl_owner")
            users_with_access = res.get("*fxtl_users", [])

            if "everybody" in users_with_access:
                users_with_access.append(self._user)

            all_users_with_access = [owner, *users_with_access]

            if self._user in all_users_with_access or not all_users_with_access:
                res["formats"] = [path.rsplit(".", 1)[-1].upper() for path in res.get("formats", [])]
                results.append(res)
        return results

    def add_book(self, book: pathlib.Path, users: Optional[list[str]] = None) -> int:
        result = subprocess.check_output(['calibredb', "add",  book.as_posix(), *self._get_auth()])
        try:
            book_id = int(re.findall(b"\d+", result)[0])
        except Exception as error:
            raise RuntimeError(f"Unexpected response when calling 'calibredb add': {result}") from error
        result = subprocess.check_output(['calibredb', "set_custom",  "fxtl_owner", str(book_id), ",".join(users or [self._user]), *self._get_auth()])
        result = subprocess.check_output(['calibredb', "set_custom",  "fxtl_users", str(book_id), "", *self._get_auth()])
        print("Calibredb set_custom output", result)
        return book_id

    def update_metadata(self, book_id: int, metadata: FxtlMetaData):
        with tempfile.TemporaryDirectory() as tmpdir_str:
            the_dir = pathlib.Path(tmpdir_str)
            tmp_file = the_dir / "metadata.fxtl"
            tmp_file.write_text(json.dumps({self._user: dataclasses.asdict(metadata)}))
            result = subprocess.check_output(["calibredb", "add_format", "--as-extra-data-file", str(book_id), tmp_file, *self._get_auth()])
        return result

    def retrieve_book(self, book_id: int, format: str) -> tuple[str, bytes]:
        with tempfile.TemporaryDirectory() as tmpdir_str:
            the_dir = pathlib.Path(tmpdir_str)
            result = subprocess.check_output(["calibredb", "export", "--dont-update-metadata", "--dont-save-extra-files", "--dont-write-opf", "--dont-save-cover", "--formats", format, "--template", "{id}", "--to-dir", the_dir.as_posix(), str(book_id), *self._get_auth()])
            the_book = next(the_dir.glob("*"))
            return mimetypes.guess_type(the_book)[0], the_book.read_bytes()

    @functools.lru_cache(maxsize=500)
    def retrieve_cover(self, book_id: int) -> tuple[str, bytes]:
        with tempfile.TemporaryDirectory() as tmpdir_str:
            the_dir = pathlib.Path(tmpdir_str)
            subprocess.check_output(["calibredb", "export", "--dont-save-extra-files", "--dont-update-metadata", "--dont-write-opf", "--formats", "jpg,jpeg,png,gif", "--template", "{id}", "--to-dir", the_dir.as_posix(), str(book_id), *self._get_auth()])
            the_book = next(the_dir.glob("*"))
            image = PIL.Image.open(the_book)
            buffer = io.BytesIO()
            image.thumbnail((400, 400))
            image.save(buffer, "jpeg", quality=80)
            return "image/jpeg", buffer.getvalue()

    def retrieve_fxtl_data(self, book_id: int) -> dict:
        with tempfile.TemporaryDirectory() as tmpdir_str:
            the_dir = pathlib.Path(tmpdir_str)
            subprocess.check_output(["calibredb", "export", "--dont-update-metadata", "--dont-write-opf", "--dont-save-cover", "--formats", "fxtl", "--template", "{id}", "--to-dir", the_dir.as_posix(), str(book_id), *self._get_auth()])
            try:
                the_book = next((the_dir / "data").glob("*"))
                return json.loads(the_book.read_text()).get(self._user, {})
            except Exception as exc:
                logging.warning(f"Suppressed error when retrieving fxtl data: {exc}")
                return {}

    def get_book_metadata(self, book_id: int) -> dict:
        data = self.list_books(f"id:{book_id}")[0]
        fxtl_data = self.retrieve_fxtl_data(book_id)
        progress = {
            "position": 0,
            "lastUpdated": time.time()
        }
        return {**data, "progress": progress, "fxtl": fxtl_data}
