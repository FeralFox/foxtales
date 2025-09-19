import pathlib

DATA_PATH = pathlib.Path(__file__).parent.parent.parent / "data"

CACHE_PATH = DATA_PATH / "cache"

CACHE_PATH.mkdir(exist_ok=True)