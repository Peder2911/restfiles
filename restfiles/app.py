import hashlib
import logging
import os
import aiofiles
from environs import Env
from fastapi import FastAPI, UploadFile, File, Response

logger = logging.getLogger(__name__)

class FileCache():
    def __init__(self, dir: str, makedirs: bool = True):
        self.dir = dir
        if makedirs:
            self._ensure_dir()

    def _path(self, key):
        return os.path.join(self.dir, self._encode_key(key))

    def _encode_key(self, raw_key: str)-> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()

    async def get(self, key):
        try:
            async with aiofiles.open(self._path(key), "rb") as f:
                data = await f.read()
        except FileNotFoundError:
            raise KeyError(f"{key} not cached")
        return data

    async def set(self, key: str, data: bytes):
        async with aiofiles.open(self._path(key), "wb") as f:
            await f.write(data)

    def __contains__(self, key):
        return os.path.exists(self._path(key))

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

@app.get("/files/{path:path}")
@app.get("/files/{path:path}/")
async def get_cached_file(path: str):
    try:
        data = await cache.get(path)
        return Response(data, media_type = "application/octet-stream")
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
        data = await file.read()
        await cache.set(path, data)
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
