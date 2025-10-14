import base64
import dataclasses
import os
import pathlib
import subprocess
import tempfile
import threading
from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional

import jwt
import fastapi
from fastapi import UploadFile, Depends, HTTPException
import uvicorn
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import InvalidTokenError
from pydantic import BaseModel
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response, FileResponse
from starlette.staticfiles import StaticFiles

from calibredb import CalibreDb, FxtlMetaData, AuthenticationError, CalibreListData, FullBookMetadata

BASE_PATH = pathlib.Path(__file__).parent.parent
LIBRARY_PATH = pathlib.Path(os.getenv("FOXTALES_LIBRARY_PATH", BASE_PATH / "volume" / "library"))
CLIENT_DIR = pathlib.Path(os.getenv("FOXTALES_CLIENT_DIR", BASE_PATH / "dist"))
SECRET_KEY = os.environ.get("SECRET_KEY")
DEFAULT_USER = os.getenv("DEFAULT_USER")
DEFAULT_PASSWORD = os.getenv("DEFAULT_USER_PASSWORD")
assert SECRET_KEY, "No SECRET_KEY environment variable provided"
assert DEFAULT_USER, "No DEFAULT_USER environment variable provided"
assert DEFAULT_PASSWORD, "No DEFAULT_USER_PASSWORD environment variable provided"

app = fastapi.FastAPI()
origins = ["*"]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
ALGORITHM = "HS256"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Mount static assets
app.mount("/assets", StaticFiles(directory=CLIENT_DIR / "assets"), name="assets")
app.mount("/icons", StaticFiles(directory=CLIENT_DIR / "icons"), name="icons")


@dataclasses.dataclass
class Status:
    success: bool


@dataclasses.dataclass
class AddBookStatus:
    book_id: int
    success: bool


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = active_users.get(username)
    if user is None:
        raise credentials_exception
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class Token(BaseModel):
    access_token: str
    token_type: str


@dataclasses.dataclass
class ActiveUserData:
    username: str
    library: CalibreDb


active_users: dict[str, ActiveUserData] = {}

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    username = form_data.username
    password = form_data.password
    library = CalibreDb("http://localhost:8080", username, password)
    try:
        library.get_custom_columns()  # Check if user is correctly authenticated.
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": username}, expires_delta=timedelta(minutes=60)
    )
    active_users[username] = ActiveUserData(username=username, library=library)
    return Token(access_token=access_token, token_type="bearer")


# Serve index.html for the root
@app.get("/")
async def read_index():
    return FileResponse(os.path.join(CLIENT_DIR, "index.html"))


@app.put("/add_book")
async def add_book(current_user: Annotated[ActiveUserData, Depends(get_current_user)], file: UploadFile) -> AddBookStatus:
    with tempfile.TemporaryDirectory() as tmpdir_str:
        the_dir = pathlib.Path(tmpdir_str)
        the_file = the_dir / file.filename
        the_file.write_bytes(await file.read())
        book_id = current_user.library.add_book(the_file)
    return AddBookStatus(book_id=book_id, success=True)


@app.get("/remove_book")
async def add_book(current_user: Annotated[ActiveUserData, Depends(get_current_user)], book_id: int) -> Status:
    current_user.library.remove_book(book_id)
    return Status(success=True)


@app.get("/list_books")
async def list_books(current_user: Annotated[ActiveUserData, Depends(get_current_user)],
                     search_query: str = "",
                     fields: str = "all",
                     max_items: int = -1,
                     start_from: int = 0) -> list[CalibreListData]:
    book_list = list(reversed(current_user.library.list_books(search_query, fields)))
    if start_from:
        book_list = book_list[start_from:]
    if max_items:
        book_list = book_list[:max_items]
    return book_list

@app.get("/get_book_metadata")
async def get_book_details(current_user: Annotated[ActiveUserData, Depends(get_current_user)], book_id: int) -> FullBookMetadata:
    return current_user.library.get_book_metadata(book_id)


@app.get("/get_book_cover")
async def get_book_cover(current_user: Annotated[ActiveUserData, Depends(get_current_user)], book_id: int, data_url: bool = False):
    mtype, data = current_user.library.retrieve_cover(book_id)
    if data_url:
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{mtype};base64,{b64}"
    else:
        return Response(content=data, media_type=mtype)


class BookMetaData(BaseModel):
    book_id: int
    fxtl: FxtlMetaData


@app.post("/set_book_metadata")
async def set_book_metadata(current_user: Annotated[ActiveUserData, Depends(get_current_user)], data: BookMetaData):
    return current_user.library.update_fxtl_data(data.book_id, data.fxtl)


@app.get("/get_book")
async def get_book(current_user: Annotated[ActiveUserData, Depends(get_current_user)], book_id: int, format: str):
    mtype, data = current_user.library.retrieve_book(book_id, format)
    return Response(content=data, media_type=mtype)

# Serve index.html for all other routes (SPA support)
@app.get("/{path:path}", include_in_schema=False)
async def serve_spa(path: str):
    if (CLIENT_DIR / path).exists():
        return FileResponse(CLIENT_DIR / path)
    return FileResponse(CLIENT_DIR / "index.html")

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
    create_user(DEFAULT_USER, DEFAULT_PASSWORD)
    print("~~~ INITIAL SETUP DONE ~~~")


def run_calibre_server():
    os.system("calibre-server --userdb '/config/Calibre Library/users.sqlite' --enable-auth '/config/Calibre Library' --port 8080")

CalibreDb(LIBRARY_PATH.as_posix(), None, None).upgrade_library()  # noqa
threading.Thread(target=run_calibre_server).start()

uvicorn.run(app, host="0.0.0.0", port=8000)
