from pathlib import Path


# Known binary patterns used to identify common file formats.
FORMAT_PATTERNS = {
    "JPEG": [
        b"\xFF\xD8\xFF"
    ],
    "PNG": [
        b"\x89PNG\r\n\x1a\n"
    ],
    "PDF": [
        b"%PDF-"
    ],
    "ZIP": [
        b"PK\x03\x04",
        b"PK\x05\x06",
        b"PK\x07\x08"
    ],
}


def identify_format(file_path: Path) -> str:
    """
    Identify a file format using its binary header.
    """

    try:
        with open(file_path, "rb") as file:
            header = file.read(16)

    except OSError:
        return "UNREADABLE"

    for file_format, patterns in FORMAT_PATTERNS.items():

        for pattern in patterns:

            if header.startswith(pattern):
                return file_format

    return "UNKNOWN"