import base64
import functools
import json
import os
import pathlib
import tempfile
import threading
import time
import fastapi
from fastapi import UploadFile
import uvicorn
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from calibredb import CalibreDb, FxtlMetaData

LIBRARY_PATH = pathlib.Path("/config/Calibre Library")

app = fastapi.FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@functools.lru_cache()
def get_db():
    return CalibreDb("http://localhost:8080", "abc", "123")


@app.put("/add_book")
async def add_book(file: UploadFile):
    with tempfile.TemporaryDirectory() as tmpdir_str:
        the_dir = pathlib.Path(tmpdir_str)
        the_file = the_dir / file.filename
        the_file.write_bytes(await file.read())
        book_id = get_db().add_book(the_file)
    return book_id


@app.get("/list_books")
async def list_books(search_query: str = "", fields: str = "all"):
    return list(reversed(get_db().list_books(search_query, fields)))


@app.get("/get_book_metadata")
async def get_book_details(book_id: int):
    return get_db().get_book_metadata(book_id)


@app.get("/get_book_cover")
async def get_book_cover(book_id: int, data_url: bool = False):
    mtype, data = get_db().retrieve_cover(book_id)
    if data_url:
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{mtype};base64,{b64}"
    else:
        return Response(content=data, media_type=mtype)


class BookMetaData(BaseModel):
    book_id: int
    fxtl: FxtlMetaData


@app.post("/set_book_metadata")
async def set_book_metadata(data: BookMetaData):
    return get_db().update_metadata(data.book_id, data.data)


@app.get("/get_book")
async def get_book(book_id: int, format: str):
    mtype, data = get_db().retrieve_book(book_id, format)
    return Response(content=data, media_type=mtype)

def create_user(username: str, password: str):
    os.system(f'''calibre-debug -c "from calibre.srv.users import *; m = UserManager('/config/Calibre Library/users.sqlite'); m.add_user('{username}', '{password}', readonly=False)"''')


def load_default_data():
    default_lib_path = pathlib.Path("/home/nightowl/defaultLibrary")

    for file in default_lib_path.rglob("*"):
        # Don't use shutil.copytree as it fails with a PermissionError for whatever reasons..
        if file.is_dir():
            continue
        relative_path = file.relative_to(default_lib_path)
        new_file = LIBRARY_PATH / relative_path
        new_file.parent.mkdir(parents=True, exist_ok=True)
        new_file.write_bytes(file.read_bytes())

if not LIBRARY_PATH.exists() or not (LIBRARY_PATH / "metadata.db").exists():
    print(f"Didn't find {LIBRARY_PATH}/metadata.db. Copy default library.")
    load_default_data()
    create_user("abc", "123")
    print("~~~ INITIAL SETUP DONE ~~~")


def run_calibre_server():
    os.system("calibre-server --userdb '/config/Calibre Library/users.sqlite' --enable-auth '/config/Calibre Library' --port 8080")


threading.Thread(target=run_calibre_server).start()
time.sleep(2)
print(json.dumps(get_db().list_books(), indent=2))
uvicorn.run(app, host="0.0.0.0", port=8000)