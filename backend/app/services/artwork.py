"""Artwork validation, metadata extraction, preflight warnings and preview generation."""

import io
from dataclasses import dataclass, field

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader

DEFAULT_ALLOWED = ["pdf", "jpg", "jpeg", "png", "tif", "tiff", "ai", "eps", "psd", "svg"]
RASTER_EXT = {"jpg", "jpeg", "png", "tif", "tiff"}
CONTENT_TYPES = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "tif": "image/tiff",
    "tiff": "image/tiff",
    "ai": "application/postscript",
    "eps": "application/postscript",
    "psd": "image/vnd.adobe.photoshop",
    "svg": "image/svg+xml",
}


class ArtworkError(ValueError):
    pass


@dataclass
class Inspection:
    extension: str
    content_type: str
    metadata: dict = field(default_factory=dict)
    preview: bytes | None = None


def extension_of(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def inspect(data: bytes, filename: str, allowed: list[str] | None = None, max_bytes: int | None = None) -> Inspection:
    allowed = [a.lower() for a in (allowed or DEFAULT_ALLOWED)]
    ext = extension_of(filename)
    if ext not in allowed:
        raise ArtworkError(f"File type '.{ext or '?'}' is not accepted. Allowed: {', '.join(allowed)}")
    if not data:
        raise ArtworkError("Uploaded file is empty")
    if max_bytes and len(data) > max_bytes:
        raise ArtworkError(f"File exceeds the maximum size of {max_bytes // (1024 * 1024)} MB")

    meta: dict = {"format": ext}
    preview = None

    if ext == "pdf":
        if not data.startswith(b"%PDF"):
            raise ArtworkError("File is not a valid PDF")
        try:
            reader = PdfReader(io.BytesIO(data))
            page = reader.pages[0]
            box = page.mediabox
            meta.update(
                {
                    "pages": len(reader.pages),
                    "page_width_in": round(float(box.width) / 72.0, 3),
                    "page_height_in": round(float(box.height) / 72.0, 3),
                    "encrypted": bool(reader.is_encrypted),
                }
            )
        except Exception as exc:  # pypdf raises many exception types
            raise ArtworkError(f"Could not read PDF: {exc}") from exc
    elif ext in RASTER_EXT:
        try:
            img = Image.open(io.BytesIO(data))
            img.load()
        except (UnidentifiedImageError, OSError) as exc:
            raise ArtworkError("File is not a valid image") from exc
        dpi = img.info.get("dpi")
        meta.update(
            {
                "pixel_width": img.width,
                "pixel_height": img.height,
                "mode": img.mode,
                "dpi": [round(float(dpi[0])), round(float(dpi[1]))] if dpi else None,
                "image_format": img.format,
            }
        )
        preview = _thumbnail(img)
    elif ext == "svg":
        if b"<svg" not in data[:4096].lower():
            raise ArtworkError("File is not a valid SVG")
    # ai / eps / psd are accepted on extension only; the reviewer opens them in a design tool

    return Inspection(extension=ext, content_type=CONTENT_TYPES.get(ext, "application/octet-stream"), metadata=meta, preview=preview)


def _thumbnail(img: Image.Image, max_px: int = 800) -> bytes:
    thumb = img.convert("RGB")
    thumb.thumbnail((max_px, max_px))
    buf = io.BytesIO()
    thumb.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


def preflight_warnings(metadata: dict, width_in: float | None, height_in: float | None, min_dpi: int | None) -> list[str]:
    """Human readable issues the reviewer and customer should see. They never block an upload."""
    warnings: list[str] = []
    fmt = metadata.get("format")
    if fmt in RASTER_EXT and width_in and height_in:
        pw, ph = metadata.get("pixel_width"), metadata.get("pixel_height")
        if pw and ph:
            effective = min(pw / width_in, ph / height_in)
            metadata["effective_dpi"] = round(effective, 1)
            if min_dpi and effective < min_dpi:
                warnings.append(
                    f"Low resolution: {effective:.0f} DPI at {width_in:.1f}x{height_in:.1f} in, minimum is {min_dpi} DPI"
                )
            ordered_ratio = width_in / height_in
            file_ratio = pw / ph
            if abs(ordered_ratio - file_ratio) / ordered_ratio > 0.03:
                warnings.append("Artwork aspect ratio does not match the ordered size; it will be cropped or distorted")
        if metadata.get("mode") not in (None, "RGB", "CMYK", "L"):
            warnings.append(f"Colour mode is {metadata.get('mode')}; RGB or CMYK is expected")
    if fmt == "pdf":
        if metadata.get("pages", 1) > 1:
            warnings.append("PDF has more than one page; only the first page will be printed")
        if metadata.get("encrypted"):
            warnings.append("PDF is encrypted and may not open in production")
        pw, ph = metadata.get("page_width_in"), metadata.get("page_height_in")
        if pw and ph and width_in and height_in:
            ordered_ratio = width_in / height_in
            file_ratio = pw / ph
            if abs(ordered_ratio - file_ratio) / ordered_ratio > 0.03:
                warnings.append("PDF page proportions do not match the ordered size")
    return warnings


def safe_filename(filename: str) -> str:
    import re

    name = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name).strip("._") or "file"
    return name[:120]
