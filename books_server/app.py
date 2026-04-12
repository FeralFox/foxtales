import base64
import dataclasses
import hashlib
import os
import pathlib
import re
import subprocess
import tempfile
import threading
import traceback
from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional, Callable, Union

import functools

import bs4
import google_books_api_wrapper.api
import json
import jwt
import fastapi
import requests
import time
import uuid
from fastapi import UploadFile, Depends, HTTPException
import uvicorn
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from google_books_api_wrapper.exceptions import GoogleBooksAPIException
from jwt import InvalidTokenError
from pydantic import BaseModel
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response, FileResponse
from starlette.staticfiles import StaticFiles

from calibredb import CalibreDb, CalibreListData, FullBookMetadata, FxtlData, UserData, SearchedBook, _Annotation
from lib import is_correct_password, hash_new_password

BASE_PATH = pathlib.Path(__file__).parent.parent
CLIENT_DIR = pathlib.Path(os.getenv("FOXTALES_CLIENT_DIR", BASE_PATH / "dist"))
SECRET_KEY = os.environ.get("SECRET_KEY")
DEFAULT_USER = os.getenv("DEFAULT_USER")
DEFAULT_PASSWORD = os.getenv("DEFAULT_USER_PASSWORD")
DEFAULT_USER_EMAIL = os.getenv("DEFAULT_USER_EMAIL")
LIBRARY_PATH = pathlib.Path(os.getenv("FOXTALES_LIBRARY_PATH", BASE_PATH / "volume" / "libraries"))
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


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
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
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
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
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    try:
        library.get_custom_columns()  # Check if user is correctly authenticated.
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": username}, expires_delta=timedelta(days=30)
    )
    active_users[username] = ActiveUserData(username=username, library=library)
    return Token(access_token=access_token, token_type="bearer")

@app.post("/register")
def register(username: str, password: str, email: str):
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
def read_index():
    return FileResponse(os.path.join(CLIENT_DIR, "index.html"))


@app.put("/add_book")
async def add_book(current_user: Annotated[ActiveUserData, Depends(get_current_user)], file: UploadFile) -> AddBookStatus:
    with tempfile.TemporaryDirectory() as tmpdir_str:
        the_dir = pathlib.Path(tmpdir_str)
        the_file = the_dir / file.filename
        the_file.write_bytes(await file.read())
        book_id = current_user.library.add_book_from_file(the_file)
    return AddBookStatus(book_id=book_id, success=True)


@app.post("/wishlist_book")
def add_book(current_user: Annotated[ActiveUserData, Depends(get_current_user)], data: SearchedBook) -> AddBookStatus:
    book_id = current_user.library.wishlist_book(data)
    return AddBookStatus(book_id=book_id, success=True)


@app.get("/remove_book")
def add_book(current_user: Annotated[ActiveUserData, Depends(get_current_user)], book_uuid: str) -> Status:
    library = current_user.library
    library.remove_book(library.get_book_id_by_uuid(book_uuid))
    return Status(success=True)


@app.get("/list_books")
def list_books(current_user: Annotated[ActiveUserData, Depends(get_current_user)],
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
def get_book_details(current_user: Annotated[ActiveUserData, Depends(get_current_user)], book_uuid: str) -> FullBookMetadata:
    lib = current_user.library
    book_id = lib.get_book_id_by_uuid(book_uuid)
    return lib.get_book_metadata(book_id)


@dataclasses.dataclass
class BookAnnotationsResponse:
    annotations: list[_Annotation]


@app.get("/get_book_annotations")
def get_book_annotations(current_user: Annotated[ActiveUserData, Depends(get_current_user)], book_uuid: str) -> BookAnnotationsResponse:
    return BookAnnotationsResponse(current_user.library.get_book_annotations(book_uuid))


@app.get("/get_book_cover")
def get_book_cover(current_user: Annotated[ActiveUserData, Depends(get_current_user)], book_uuid: str, data_url: bool = False):
    lib = current_user.library
    mtype, data = lib.retrieve_cover(book_uuid)
    if data_url:
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{mtype};base64,{b64}"
    else:
        return Response(content=data, media_type=mtype)


class SetBookMetaDataParams(BaseModel):
    book_uuid: str
    update_type: str
    update_data: Union[list, dict]


@app.post("/set_book_metadata")
def set_book_metadata(current_user: Annotated[ActiveUserData, Depends(get_current_user)], data: SetBookMetaDataParams):
    book_id = current_user.library.get_book_id_by_uuid(data.book_uuid)
    if data.update_type == "update-progress":
        current_user.library.set_custom_value(book_id, "fxtl_progress",
                                              str(data.update_data["fxtl_progress"]))
        current_user.library.set_custom_value(book_id, "fxtl_progress_update",
                                              data.update_data["fxtl_progress_update"].replace("Z", "+00:00"))
    elif data.update_type == "update-read-status":
        current_user.library.set_custom_value(book_id, "fxtl_is_read", str(data["fxtl_is_read"]))
    elif data.update_type == "update-annotations":
        data_path = current_user.library.get_book_path(data.book_uuid)
        annotations_path = data_path / "data" / "annotations.json"
        try:
            annotations = json.loads(annotations_path.read_text())
        except FileNotFoundError:
            annotations = {}
        for operation, entry in data.update_data:
            if operation == "add":
                annotations[entry["uuid"]] = entry
            elif operation == "delete":
                try:
                    annotations.pop(entry["uuid"])
                except KeyError:
                    pass
        annotations_path.write_text(json.dumps(annotations))


@dataclasses.dataclass
class BookData:
    book_uuid: str
    title: str = ""
    description: str = ""
    tags: str = ""
    authors: str = ""


@app.post("/set_data")
def set_data(current_user: Annotated[ActiveUserData, Depends(get_current_user)], data: BookData):
    lib = current_user.library
    book_id = lib.get_book_id_by_uuid(data.book_uuid)
    if data.title:
        lib.set_metadata(book_id, "title", data.title)
    if data.description:
        lib.set_metadata(book_id, "comments", data.description)
    if data.tags:
        tags = sorted(data.tags.split(","))
        lib.set_metadata(book_id, "tags", ",".join(tags))
    if data.authors:
        lib.set_metadata(book_id, "authors", data.tags)


@app.get("/get_tags")
def get_tags(current_user: Annotated[ActiveUserData, Depends(get_current_user)]) -> list[str]:
    return current_user.library.get_all_tags()


@app.get("/get_book")
def get_book(current_user: Annotated[ActiveUserData, Depends(get_current_user)], book_uuid: str, format: str):
    lib = current_user.library
    book_id = lib.get_book_id_by_uuid(book_uuid)
    mtype, data = current_user.library.retrieve_book(book_id, format)
    return Response(content=data, media_type=mtype)


@dataclasses.dataclass
class SearchedBookResponse:
    result: list[SearchedBook]


@app.get("/explore_books")
def search_book(current_user: Annotated[ActiveUserData, Depends(get_current_user)], search_query: str) -> SearchedBookResponse:
    books = []
    threads = []
    for func in [_search_book_annas_archive, _search_book_on_google_books, _search_book_on_baka_updates]:
        threads.append(threading.Thread(target=_run_threaded, args=(func, search_query, books)))
    [t.start() for t in threads]
    [t.join() for t in threads]
    primary_results: list[SearchedBook] = []
    secondary_results: list[SearchedBook] = []
    for result in books:
        words = [*result.title.split(" "),
                 *result.authors.split(" ")]
        lc_query = {itm.lower().strip("\".,'-+") for itm in search_query.split(" ")}
        lc_words = {wrd.lower().strip("\".,'-+") for wrd in words}
        if search_query not in (result.identifiers or "") and not (lc_query.intersection(lc_words)):
            continue
        if result.title.rsplit(".", 1)[-1] in ["com", "zip", "rar", "pdf"]:
            continue
        if result.cover_url:
            primary_results.append(result)
        else:
            secondary_results.append(result)
    primary_results.sort(key=lambda book: (search_query.lower() in book.title.lower(), bool(book.description)), reverse=True)
    return SearchedBookResponse(result=[*primary_results, *secondary_results])


def _run_threaded(func: Callable, search_query: str, result_list: list[SearchedBook]):
    t0 = time.time()
    try:
        result_list += func(search_query)
    except Exception:
        traceback.print_exc()
    print(f"Calling {func.__name__} in {time.time() - t0:.2f} seconds")


@functools.lru_cache(maxsize=10)
def _search_book_annas_archive(search_query: str) -> list[SearchedBook]:
    query = search_query.replace(" ", "+")
    response = requests.get(f"https://annas-archive.gl/search?index=&page=1&sort=&display=&q={query}")
    b = bs4.BeautifulSoup(response.content, features="html.parser")
    results = [c for c in b.find_all(class_="js-aarecord-list-outer")[0].children if c.name == "div"]

    all_results = {}
    for result in results:
        try:
            image, info = [c for c in result.children if c.name in ["a", "div"]]
        except ValueError:
            continue
        image_url = image.find("img").attrs["src"]

        general_info, description_container, *_ = [c for c in info.children if c.name == "div"]
        general_data = [c for c in general_info.children if c.name == "a"]
        author = ""
        publisher = ""
        date = ""
        title = general_data[0].text.strip()
        author_identifier = general_info.find(class_="icon-[mdi--user-edit]")
        if author_identifier:
            author = author_identifier.parent.text.strip()
        publisher_identifier = general_info.find(class_="icon-[mdi--company]")
        if publisher_identifier:
            publisher = publisher_identifier.parent.text.strip()
            try:
                date = re.findall("\d{4}", publisher)[0]
            except IndexError:
                date = ""
        description = description_container.text.replace("Read more...", "").strip()
        all_results[f"{title},{author}"] = SearchedBook(
            uuid=uuid.uuid4().hex,
            title=title,
            pubdate=date,
            description=description.replace("Read more…", ""),
            authors=author,
            identifiers={},
            cover_url=image_url,
        )

    # Download book covers on server.
    # Pro: Ensuring that images can be loaded, no vanishing images in browser due to failed request.
    # Deduplication based on cover, "Add to wishlist" reliable.
    # Con: Half of the results cannot retrieve image, longer loading times.
    # pool = ThreadPool(processes=3)
    # pool.map(load_cover, list(all_results.values()))
    # pool.close()
    # pool.join()
    #
    # # Join books with the same image.
    # simplified_results = {(book._image_hash or id(book)): book for book in all_results.values()}

    return list(all_results.values())


def load_cover(item, timeout: int = 0.5):
    try:
        response = requests.get(item.cover_url, timeout=timeout)
        byte_data = response.content
        b64_data = base64.b64encode(byte_data)
        item._image_hash = hashlib.md5(byte_data).hexdigest()
        item.cover_url = f"data:image/jpeg;base64,{b64_data.decode()}"
    except:
        item.cover_url = ""


@functools.lru_cache(maxsize=10)
def _search_book_on_baka_updates(search_query: str) -> list[SearchedBook]:
    query = search_query.replace(" ", "+")
    query_items = search_query.split(" ")
    response = requests.get(f"https://www.mangaupdates.com/site/search/result?search={query}")
    soup = bs4.BeautifulSoup(response.text, features="html.parser")
    tags = [tag for tag in soup.find_all("h2") if tag.text == "Series"][0].next_sibling.find_all(title="Click for Series Info")
    results = []
    for result in tags:
        url = result.attrs["href"]
        title = result.text
        if not all(item.lower() in title.lower() for item in query_items):
            continue
        year = result.parent.next_sibling.next_sibling.text.strip()
        book = _analyze_baka_page(title, year, url)
        results.append(book)
        if len(results) >= 3:  # Accelerate listing results while reducing load on Baka.
            break
    return results


def _analyze_baka_page(title: str, year: str, url: str) -> SearchedBook:
    response =  requests.get(url)
    soup = bs4.BeautifulSoup(response.text, features="html.parser")
    description = [item for item in soup.find_all("b") if item.text == "Description"][0].parent.next_sibling.text
    genre_tags = [item for item in soup.find_all("b") if item.text == "Genre"][0].parent.next_sibling.find_all("a")
    genre = ", ".join(["Manga", *[tag.text for tag in genre_tags if not "Search for series" in tag.text]])
    try:
        image_url = soup.find_all(alt="Series Image")[0].attrs["src"]
    except IndexError:
        image_url = ""
    authors = [item for item in soup.find_all("b") if item.text == "Author(s)"][0].parent.next_sibling.text

    description = f"{description}\n\nGenre:\n{genre}"
    return SearchedBook(
        uuid=uuid.uuid4().hex,
        title=title,
        pubdate=year,
        cover_url=image_url,
        description=description,
        authors=authors,
        identifiers={}
    )


@functools.lru_cache(maxsize=10)
def _search_book_on_google_books(search_query: str) -> list[SearchedBook]:
    for _ in range(5):
        try:
            x = google_books_api_wrapper.api.GoogleBooksAPI().search_book(search_query)
            break
        except GoogleBooksAPIException as exc:
            time.sleep(1)
    else:
        raise exc
    results = []
    for result in x:
        authors = ", ".join(result.authors or [])
        results.append(SearchedBook(
            uuid=result.id,
            title=result.title,
            pubdate=result.published_date,
            cover_url=result.large_thumbnail or result.small_thumbnail,
            description=result.description or "",
            authors=authors,
            identifiers={},
        ))
    if not results and not '"' in search_query:
        # Seems Google is not good with searching... "exit black" is found, without " it isn't.
        return _search_book_on_google_books(f'"{search_query}"')
    return results

# Serve index.html for all other routes (SPA support)
@app.get("/{path:path}", include_in_schema=False)
def serve_spa(path: str):
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
