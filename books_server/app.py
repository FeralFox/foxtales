import base64
import dataclasses
import os
import pathlib
import subprocess
import tempfile
from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional

import functools
import google_books_api_wrapper.api
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

from calibredb import CalibreDb, CalibreListData, FullBookMetadata, FxtlData, UserData
from lib import is_correct_password, hash_new_password

BASE_PATH = pathlib.Path(__file__).parent.parent
CLIENT_DIR = pathlib.Path(os.getenv("FOXTALES_CLIENT_DIR", BASE_PATH / "dist"))
SECRET_KEY = os.environ.get("SECRET_KEY")
DEFAULT_USER = os.getenv("DEFAULT_USER")
DEFAULT_PASSWORD = os.getenv("DEFAULT_USER_PASSWORD")
DEFAULT_USER_EMAIL = os.getenv("DEFAULT_USER_EMAIL")
LIBRARY_PATH = pathlib.Path(os.getenv("FOXTALES_LIBRARY_PATH", BASE_PATH / "volume" / "library"))
COMMON_LIBRARY_PATH = LIBRARY_PATH / "common"
USER_LIBRARY_PATH = LIBRARY_PATH / "users"
DEFAULT_USER_LIBRARY_PATH = LIBRARY_PATH / "users" / DEFAULT_USER
DEFAULT_LIB_PATH = pathlib.Path("/home/nightowl/defaultLibrary")
assert SECRET_KEY, "No SECRET_KEY environment variable provided"
assert DEFAULT_USER, "No DEFAULT_USER environment variable provided"
assert DEFAULT_PASSWORD, "No DEFAULT_USER_PASSWORD environment variable provided"

USER_DB_PATH = "/config/libraries/users.sqlite"

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
    try:
        library_path = USER_LIBRARY_PATH / username
        if not library_path.exists():
            # User not found
            raise ValueError()
        library = CalibreDb(library_path)
        user_data = library.get_user_data().user
        if not is_correct_password(user_data.salt, user_data.password, password):
            # Incorrect password
            raise ValueError()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    try:
        library.get_custom_columns()  # Check if user is correctly authenticated.
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": username}, expires_delta=timedelta(minutes=60)
    )
    active_users[username] = ActiveUserData(username=username, library=library)
    return Token(access_token=access_token, token_type="bearer")

@app.post("/register")
async def register(username: str, password: str, email: str):
    forbidden_symbols = set("'\"")
    forbidden_symbols_user = forbidden_symbols.union(":.")
    if forbidden_symbols_user.intersection(username):
        raise HTTPException(400, f"The username must not contain any of these characters: {', '.join(forbidden_symbols_user)}")
    if forbidden_symbols.intersection(password):
        raise HTTPException(400, f"The password must not contain any of these characters: {', '.join(forbidden_symbols)}")
    create_user(username, password, email)
    return True

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
async def add_book(current_user: Annotated[ActiveUserData, Depends(get_current_user)], book_uuid: str) -> Status:
    library = current_user.library
    library.remove_book(library.get_book_id_by_uuid(book_uuid))
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
async def get_book_details(current_user: Annotated[ActiveUserData, Depends(get_current_user)], book_uuid: str) -> FullBookMetadata:
    lib = current_user.library
    book_id = lib.get_book_id_by_uuid(book_uuid)
    return lib.get_book_metadata(book_id)


@app.get("/get_book_cover")
async def get_book_cover(current_user: Annotated[ActiveUserData, Depends(get_current_user)], book_uuid: str, data_url: bool = False):
    lib = current_user.library
    mtype, data = lib.retrieve_cover(book_uuid)
    if data_url:
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{mtype};base64,{b64}"
    else:
        return Response(content=data, media_type=mtype)


class BookMetaData(BaseModel):
    book_uuid: str
    fxtl_progress: Optional[float] = None
    fxtl_progress_update: Optional[str] = None
    fxtl_is_read: Optional[bool] = None
    fxtl_tags: Optional[list[str]] = None


@app.post("/set_book_metadata")
async def set_book_metadata(current_user: Annotated[ActiveUserData, Depends(get_current_user)], data: BookMetaData):
    book_id = current_user.library.get_book_id_by_uuid(data.book_uuid)
    if data.fxtl_progress is not None:
        current_user.library.set_custom_value(book_id, "fxtl_progress",
                                              str(data.fxtl_progress))
        current_user.library.set_custom_value(book_id, "fxtl_progress_update",
                                              data.fxtl_progress_update.replace("Z", "+00:00"))
    if data.fxtl_is_read is not None:
        current_user.library.set_custom_value(book_id, "fxtl_is_read", str(data.fxtl_is_read))


@app.get("/get_book")
async def get_book(current_user: Annotated[ActiveUserData, Depends(get_current_user)], book_uuid: str, format: str):
    lib = current_user.library
    book_id = lib.get_book_id_by_uuid(book_uuid)
    mtype, data = current_user.library.retrieve_book(book_id, format)
    return Response(content=data, media_type=mtype)


@dataclasses.dataclass
class SearchedBook:
    id: str
    title: str
    subtitle: str
    pubdate: str
    cover_url: str
    description: str
    authors: list[str]
    isbn: str


@dataclasses.dataclass
class SearchedBookResponse:
    result: list[SearchedBook]


@app.get("/explore_books")
async def search_book(current_user: Annotated[ActiveUserData, Depends(get_current_user)], search_query: str) -> SearchedBookResponse:
    return _search_book(search_query)

@functools.lru_cache(maxsize=10)
def _search_book(search_query: str) -> SearchedBookResponse:
    x = google_books_api_wrapper.api.GoogleBooksAPI().search_book(search_query)
    results = []
    for result in x:
        results.append(SearchedBook(
            id=result.id,
            title=result.title,
            subtitle=result.subtitle,
            pubdate=result.published_date,
            cover_url=result.large_thumbnail or result.small_thumbnail,
            description=result.description,
            authors=result.authors,
            isbn=result.ISBN_13 or result.ISBN_10,
        ))
    return SearchedBookResponse(results)

# Serve index.html for all other routes (SPA support)
@app.get("/{path:path}", include_in_schema=False)
async def serve_spa(path: str):
    if (CLIENT_DIR / path).exists():
        return FileResponse(CLIENT_DIR / path)
    return FileResponse(CLIENT_DIR / "index.html")

def create_user(username: str, password: str, email: str):
    # Assertions: Prevent users from getting access during registration by modifying the string below
    assert not "'" in username
    assert not '"' in username
    assert not "'" in password
    assert not '"' in password
    library_path = USER_LIBRARY_PATH / username
    load_default_data(library_path)
    salt, hashed_pw = hash_new_password(password)
    db = CalibreDb(library_path)
    db.store_user_data(FxtlData(UserData(
        username=username,
        password=hashed_pw,
        salt=salt,
        email=email
    )))

def load_default_data(library_path: pathlib.Path):
    for file in DEFAULT_LIB_PATH.rglob("*"):
        # Don't use shutil.copytree as it fails with a PermissionError for whatever reasons..
        if file.is_dir():
            continue
        relative_path = file.relative_to(DEFAULT_LIB_PATH)
        new_file = library_path / relative_path
        new_file.parent.mkdir(parents=True, exist_ok=True)
        new_file.write_bytes(file.read_bytes())

if not DEFAULT_USER_LIBRARY_PATH.exists() or not (DEFAULT_USER_LIBRARY_PATH / "metadata.db").exists():
    create_user(DEFAULT_USER, DEFAULT_PASSWORD, DEFAULT_USER_EMAIL)
    print("~~~ Created default user library. ~~~")

uvicorn.run(app, host="0.0.0.0", port=8000)
