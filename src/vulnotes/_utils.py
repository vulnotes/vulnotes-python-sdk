"""Internal helpers shared by the resource modules."""

from __future__ import annotations

import datetime as _dt
import io
import mimetypes
import os
from typing import Any, Union

# A file argument may be a filesystem path, raw bytes, an open file object,
# or a (filename, fileobj_or_bytes) / (filename, fileobj_or_bytes, content_type) tuple.
FileTypes = Union[str, "os.PathLike[str]", bytes, io.IOBase, tuple]


def omit_none(mapping: dict[str, Any]) -> dict[str, Any]:
    """Drop keys whose value is ``None`` (the API treats absent fields as unchanged)."""
    return {k: v for k, v in mapping.items() if v is not None}


def iso(value: str | _dt.date | _dt.datetime | None) -> str | None:
    """Convert a date/datetime to an ISO-8601 string; pass strings and None through."""
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, _dt.datetime):
        return value.isoformat()
    if isinstance(value, _dt.date):
        return value.isoformat()
    raise TypeError(f"expected str, date or datetime, got {type(value).__name__}")


def _with_content_type(filename: str, payload: Any) -> tuple:
    """Attach a guessed Content-Type so server-side upload filters (which
    check the part's MIME type, not the filename) accept the file."""
    content_type = mimetypes.guess_type(filename)[0]
    if content_type:
        return (filename, payload, content_type)
    return (filename, payload)


def prepare_file(file: FileTypes, default_name: str = "upload") -> tuple:
    """Normalize a user-supplied file argument into a (filename, payload[, type]) tuple
    suitable for the ``files=`` parameter of requests."""
    if isinstance(file, tuple):
        if len(file) == 2:
            return _with_content_type(file[0], file[1])
        return file  # already (filename, fileobj, content_type)
    if isinstance(file, bytes):
        return _with_content_type(default_name, file)
    if isinstance(file, (str, os.PathLike)):
        path = os.fspath(file)
        return _with_content_type(os.path.basename(path), open(path, "rb"))
    # file-like object
    name = getattr(file, "name", None)
    if isinstance(name, str) and name and not name.startswith("<"):
        return _with_content_type(os.path.basename(name), file)
    return _with_content_type(default_name, file)


def write_bytes(content: bytes, path: str | os.PathLike[str]) -> str:
    """Write binary content to *path* and return the path as a string."""
    path = os.fspath(path)
    with open(path, "wb") as fh:
        fh.write(content)
    return path
