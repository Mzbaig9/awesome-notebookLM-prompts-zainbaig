"""File storage abstraction. Local disk for development, S3 compatible storage in production."""

import re
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO, Protocol

from app.core.config import get_settings

_SAFE_KEY = re.compile(r"[^A-Za-z0-9._/-]")


def safe_key(key: str) -> str:
    key = _SAFE_KEY.sub("_", key).lstrip("/")
    if ".." in key:
        raise ValueError("Invalid storage key")
    return key


class Storage(Protocol):
    def save(self, key: str, data: bytes, content_type: str) -> str: ...
    def open(self, key: str) -> BinaryIO: ...
    def delete(self, key: str) -> None: ...
    def url(self, key: str, expires_seconds: int = 900) -> str | None: ...


class LocalStorage:
    def __init__(self, base_dir: str):
        self.base = Path(base_dir).resolve()
        self.base.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        p = (self.base / safe_key(key)).resolve()
        if self.base not in p.parents and p != self.base:
            raise ValueError("Invalid storage key")
        return p

    def save(self, key: str, data: bytes, content_type: str) -> str:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return key

    def open(self, key: str) -> BinaryIO:
        return self._path(key).open("rb")

    def delete(self, key: str) -> None:
        p = self._path(key)
        if p.exists():
            p.unlink()

    def url(self, key: str, expires_seconds: int = 900) -> str | None:
        return None


class S3Storage:
    def __init__(self, bucket: str, region: str | None, endpoint_url: str | None):
        import boto3

        self.bucket = bucket
        self.client = boto3.client("s3", region_name=region, endpoint_url=endpoint_url)

    def save(self, key: str, data: bytes, content_type: str) -> str:
        key = safe_key(key)
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return key

    def open(self, key: str) -> BinaryIO:
        return self.client.get_object(Bucket=self.bucket, Key=safe_key(key))["Body"]

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=safe_key(key))

    def url(self, key: str, expires_seconds: int = 900) -> str | None:
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": safe_key(key)}, ExpiresIn=expires_seconds
        )


@lru_cache
def get_storage() -> Storage:
    s = get_settings()
    if s.storage_backend == "s3":
        if not s.s3_bucket:
            raise RuntimeError("S3_BUCKET must be set when STORAGE_BACKEND=s3")
        return S3Storage(s.s3_bucket, s.s3_region, s.s3_endpoint_url)
    return LocalStorage(s.local_storage_dir)
