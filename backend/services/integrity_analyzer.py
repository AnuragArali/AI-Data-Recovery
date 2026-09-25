from pathlib import Path
import hashlib
import zipfile

from PIL import Image

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


FILE_MARKERS = {
    "JPEG": {
        "start": b"\xFF\xD8\xFF",
        "end": b"\xFF\xD9"
    },
    "PNG": {
        "start": b"\x89PNG\r\n\x1a\n",
        "end": b"IEND\xAE\x42\x60\x82"
    },
    "PDF": {
        "start": b"%PDF-",
        "end": b"%%EOF"
    },
    "ZIP": {
        "start": b"PK\x03\x04",
        "end": b"PK\x05\x06"
    }
}


def calculate_sha256(file_path: Path) -> str | None:

    try:

        sha256 = hashlib.sha256()

        with open(file_path, "rb") as file:

            while chunk := file.read(8192):

                sha256.update(chunk)

        return sha256.hexdigest()

    except OSError:

        return None


def read_file_data(
    file_path: Path
) -> bytes:

    try:

        with open(file_path, "rb") as file:

            return file.read()

    except OSError:

        return b""


def check_markers(
    data: bytes,
    file_format: str
) -> tuple[bool, bool]:

    markers = FILE_MARKERS.get(
        file_format
    )

    if not markers:

        return False, False

    has_start_marker = data.startswith(
        markers["start"]
    )

    has_end_marker = data.endswith(
        markers["end"]
    )

    return (
        has_start_marker,
        has_end_marker
    )


def validate_jpeg(
    file_path: Path
) -> dict:

    try:

        with Image.open(file_path) as image:

            image.verify()

        return {
            "readable": True,
            "format_valid": True,
            "message": "JPEG image is readable and structurally valid"
        }

    except Exception as error:

        return {
            "readable": False,
            "format_valid": False,
            "message": f"JPEG validation failed: {error}"
        }


def validate_png(
    file_path: Path
) -> dict:

    try:

        with Image.open(file_path) as image:

            image.verify()

        return {
            "readable": True,
            "format_valid": True,
            "message": "PNG image is readable and structurally valid"
        }

    except Exception as error:

        return {
            "readable": False,
            "format_valid": False,
            "message": f"PNG validation failed: {error}"
        }


def validate_pdf(
    file_path: Path
) -> dict:

    if PdfReader is None:

        return {
            "readable": False,
            "format_valid": False,
            "message": "pypdf is not installed"
        }

    try:

        reader = PdfReader(
            str(file_path)
        )

        page_count = len(
            reader.pages
        )

        return {
            "readable": True,
            "format_valid": True,
            "page_count": page_count,
            "message": (
                f"PDF is readable with "
                f"{page_count} page(s)"
            )
        }

    except Exception as error:

        return {
            "readable": False,
            "format_valid": False,
            "message": f"PDF validation failed: {error}"
        }


def validate_zip(
    file_path: Path
) -> dict:

    try:

        with zipfile.ZipFile(
            file_path,
            "r"
        ) as archive:

            bad_file = archive.testzip()

            if bad_file is not None:

                return {
                    "readable": True,
                    "format_valid": False,
                    "message": (
                        f"ZIP corruption detected "
                        f"in {bad_file}"
                    )
                }

            return {
                "readable": True,
                "format_valid": True,
                "message": "ZIP archive is readable and valid"
            }

    except Exception as error:

        return {
            "readable": False,
            "format_valid": False,
            "message": f"ZIP validation failed: {error}"
        }


def validate_file(
    file_path: Path,
    file_format: str
) -> dict:

    if file_format == "JPEG":

        return validate_jpeg(
            file_path
        )

    if file_format == "PNG":

        return validate_png(
            file_path
        )

    if file_format == "PDF":

        return validate_pdf(
            file_path
        )

    if file_format == "ZIP":

        return validate_zip(
            file_path
        )

    return {
        "readable": False,
        "format_valid": False,
        "message": (
            "No validator available "
            "for this file format"
        )
    }


def analyze_integrity(
    file_path: Path,
    file_format: str
) -> dict:

    # -----------------------------------------
    # Check existence
    # -----------------------------------------

    if not file_path.exists():

        return {
            "success": False,
            "file": file_path.name,
            "message": "Recovered file does not exist"
        }


    # -----------------------------------------
    # File size
    # -----------------------------------------

    try:

        size_bytes = file_path.stat().st_size

    except OSError:

        size_bytes = 0


    if size_bytes == 0:

        return {
            "success": False,
            "file": file_path.name,
            "size_bytes": 0,
            "integrity_status": "INVALID",
            "corruption_status": "CORRUPTED",
            "message": "Recovered file is empty"
        }


    # -----------------------------------------
    # Read data
    # -----------------------------------------

    data = read_file_data(
        file_path
    )


    if not data:

        return {
            "success": False,
            "file": file_path.name,
            "size_bytes": size_bytes,
            "integrity_status": "INVALID",
            "corruption_status": "CORRUPTED",
            "message": "Recovered file cannot be read"
        }


    # -----------------------------------------
    # Markers
    # -----------------------------------------

    has_start_marker, has_end_marker = (
        check_markers(
            data,
            file_format
        )
    )


    # -----------------------------------------
    # Cryptographic hash
    # -----------------------------------------

    sha256 = calculate_sha256(
        file_path
    )


    # -----------------------------------------
    # Format-specific validation
    # -----------------------------------------

    validation = validate_file(
        file_path,
        file_format
    )


    readable = validation.get(
        "readable",
        False
    )

    format_valid = validation.get(
        "format_valid",
        False
    )


    # -----------------------------------------
    # Determine integrity status
    # -----------------------------------------

    if (
        has_start_marker
        and
        has_end_marker
        and
        readable
        and
        format_valid
    ):

        integrity_status = "VALID"

        corruption_status = "LOW"

        message = (
            "Recovered file passed "
            "format and integrity validation"
        )

    elif (
        readable
        and
        format_valid
    ):

        integrity_status = "PARTIALLY_VALID"

        corruption_status = "MEDIUM"

        message = (
            "Recovered file is readable, "
            "but one or more structural "
            "markers could not be verified"
        )

    else:

        integrity_status = "INVALID"

        corruption_status = "HIGH"

        message = validation.get(
            "message",
            "Recovered file failed validation"
        )


    # -----------------------------------------
    # Result
    # -----------------------------------------

    result = {

        "success": True,

        "file":
            file_path.name,

        "format":
            file_format,

        "size_bytes":
            size_bytes,

        "sha256":
            sha256,

        "start_marker_valid":
            has_start_marker,

        "end_marker_valid":
            has_end_marker,

        "file_readable":
            readable,

        "format_valid":
            format_valid,

        "integrity_status":
            integrity_status,

        "corruption_status":
            corruption_status,

        "message":
            message
    }


    # Add format-specific information
    result["validation"] = validation


    return result