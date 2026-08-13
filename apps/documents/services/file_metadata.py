import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileMetadata:
    file_hash: str
    file_size: int


def calculate_file_metadata(
    file_path: str,
) -> FileMetadata:
    """
    Calculate SHA-256 hash and size for a stored file.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File does not exist: {file_path}"
        )

    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return FileMetadata(
        file_hash=sha256.hexdigest(),
        file_size=path.stat().st_size,
    )