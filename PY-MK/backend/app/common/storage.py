from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


DOCUMENT_TYPES = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "text/plain": ".txt",
}
IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


@dataclass(frozen=True)
class StoredFile:
    key: str
    original_name: str
    content_type: str
    size: int


class LocalStorage:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or settings.storage_path).resolve()

    async def save(
        self,
        upload: UploadFile,
        folder: str,
        allowed_types: dict[str, str],
        max_size: int | None = None,
    ) -> StoredFile:
        content_type = (upload.content_type or "").lower()
        extension = allowed_types.get(content_type)
        if not upload.filename or extension is None:
            raise HTTPException(status_code=415, detail="Tipo de archivo no permitido")

        limit = max_size or settings.storage_max_file_size
        content = await upload.read(limit + 1)
        if not content:
            raise HTTPException(status_code=400, detail="El archivo está vacío")
        if len(content) > limit:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"El archivo excede el límite de {limit // (1024 * 1024)} MB",
            )

        key = f"{folder}/{uuid4().hex}{extension}"
        destination = self.resolve(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return StoredFile(key, Path(upload.filename).name, content_type, len(content))

    def resolve(self, key: str) -> Path:
        candidate = (self.root / key).resolve()
        if self.root not in candidate.parents:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        return candidate


storage = LocalStorage()
