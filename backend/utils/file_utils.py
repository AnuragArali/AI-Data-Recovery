from pathlib import Path
import hashlib


UPLOAD_DIRECTORY = Path("temp/uploads")


def ensure_upload_directory():
    """
    Create the upload directory if it does not exist.
    """
    UPLOAD_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )


def save_uploaded_file(filename: str, content: bytes) -> Path:
    """
    Save uploaded evidence to the temporary upload directory.
    """

    ensure_upload_directory()

    file_path = UPLOAD_DIRECTORY / filename

    with open(file_path, "wb") as file:
        file.write(content)

    return file_path


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of an evidence file.
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        while chunk := file.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()