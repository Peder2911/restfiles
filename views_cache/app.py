import os
import base64
from environs import Env
from fastapi import FastAPI, UploadFile, File, Response
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

class FileCache():
    def __init__(self, dir: str, makedirs: bool = True):
        self.dir = dir
        if makedirs:
            self._ensure_dir()

    def _path(self, key):
        return os.path.join(self.dir, self._encode_key(key))

    def _encode_key(self, raw_key: str)-> str:
        return base64.b64encode(raw_key.encode()).decode()

    def _decode_key(self, key: str)-> str:
        return base64.b64decode(key.encode()).decode()

    def __getitem__(self, key):
        try:
            return open(self._path(key), "rb")
        except FileNotFoundError:
            raise KeyError(f"{key} not cached")

    def __setitem__(self, key: str, data: bytes):
        with open(self._path(key), "wb") as f:
            f.write(data)

    def __contains__(self, key):
        return os.path.exists(self._path(key))

    def __iter__(self):
        return (self._decode_key(k) for k in os.listdir(self.dir))

    def _ensure_dir(self):
        try:
            os.makedirs(self.dir)
        except FileExistsError:
            pass

    def delete(self, key):
        try:
            os.unlink(self._path(key))
        except FileNotFoundError:
            raise KeyError(f"{key} not cached")

env = Env()
env.read_env()
CACHE_DIR = env.str("CACHE_DIR", "./cache")

app = FastAPI()
cache = FileCache(CACHE_DIR)

@app.get("/files")
@app.get("/files/")
def list_files():
    return {"files": [*cache]}

@app.get("/files/{path:path}")
@app.get("/files/{path:path}/")
async def get_cached_file(path: str):
    try:
        return StreamingResponse(cache[path])
    except KeyError:
        return Response(status_code = 404)

@app.head("/files/{path:path}")
@app.head("/files/{path:path}/")
def check_cached_file(path: str):
    return Response(status_code = 204) if path in cache else Response(status_code = 404)

@app.post("/files/{path:path}")
@app.post("/files/{path:path}/")
async def upload_file_to_cache(
        path: str,
        file: UploadFile = File(None)):
    if not path in cache:
        cache[path] = await file.read()
        return Response(status_code = 201)
    else:
        return Response(status_code = 203)

@app.delete("/files/{path:path}")
@app.delete("/files/{path:path}/")
def delete_file(path: str):
    try:
        cache.delete(path)
    except KeyError:
        return Response(status_code = 404)
    else:
        return Response(status_code = 204)
