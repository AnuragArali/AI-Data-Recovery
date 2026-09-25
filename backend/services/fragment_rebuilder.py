from pathlib import Path


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


def read_file_data(
    file_path: Path
) -> bytes:

    try:

        with open(
            file_path,
            "rb"
        ) as file:

            return file.read()

    except OSError:

        return b""


def check_start_marker(
    data: bytes,
    file_type: str
) -> bool:

    markers = FILE_MARKERS.get(
        file_type
    )

    if not markers:
        return False

    return data.startswith(
        markers["start"]
    )


def check_end_marker(
    data: bytes,
    file_type: str
) -> bool:

    markers = FILE_MARKERS.get(
        file_type
    )

    if not markers:
        return False

    return data.endswith(
        markers["end"]
    )


def analyze_fragment(
    file_path: Path,
    file_type: str
) -> dict:

    data = read_file_data(
        file_path
    )

    if not data:

        return {
            "filename": file_path.name,
            "size_bytes": 0,
            "has_start_marker": False,
            "has_end_marker": False,
            "fragment_type": "UNREADABLE"
        }

    has_start = check_start_marker(
        data,
        file_type
    )

    has_end = check_end_marker(
        data,
        file_type
    )

    if has_start and has_end:

        fragment_type = "COMPLETE"

    elif has_start:

        fragment_type = "START_FRAGMENT"

    elif has_end:

        fragment_type = "END_FRAGMENT"

    else:

        fragment_type = "MIDDLE_FRAGMENT"

    return {
        "filename": file_path.name,
        "size_bytes": len(data),
        "has_start_marker": has_start,
        "has_end_marker": has_end,
        "fragment_type": fragment_type
    }


def remove_overlap(
    first_data: bytes,
    second_data: bytes,
    max_overlap: int = 64
) -> bytes:
    """
    Remove duplicated bytes when two fragments
    have an overlapping boundary.
    """

    if not first_data or not second_data:
        return second_data

    maximum = min(
        max_overlap,
        len(first_data),
        len(second_data)
    )

    best_overlap = 0

    for overlap_size in range(
        maximum,
        3,
        -1
    ):

        if (
            first_data[-overlap_size:]
            ==
            second_data[:overlap_size]
        ):

            best_overlap = overlap_size
            break

    return second_data[
        best_overlap:
    ]


def reconstruct_fragments(
    fragment_paths: list[Path],
    output_path: Path
) -> dict:
    """
    Reconstruct fragments in the supplied order.

    The function concatenates binary data while
    removing exact overlapping boundaries.
    """

    if not fragment_paths:

        return {
            "success": False,
            "message": "No fragments supplied",
            "output_file": None,
            "total_fragments": 0,
            "size_bytes": 0
        }

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    reconstructed_data = b""

    used_fragments = 0

    for index, fragment_path in enumerate(
        fragment_paths
    ):

        fragment_data = read_file_data(
            fragment_path
        )

        if not fragment_data:
            continue

        if index == 0:

            reconstructed_data = (
                fragment_data
            )

        else:

            fragment_to_add = remove_overlap(
                reconstructed_data,
                fragment_data
            )

            reconstructed_data += (
                fragment_to_add
            )

        used_fragments += 1

    if not reconstructed_data:

        return {
            "success": False,
            "message": "Unable to read fragment data",
            "output_file": None,
            "total_fragments": 0,
            "size_bytes": 0
        }

    try:

        with open(
            output_path,
            "wb"
        ) as output_file:

            output_file.write(
                reconstructed_data
            )

    except OSError as error:

        return {
            "success": False,
            "message": str(error),
            "output_file": None,
            "total_fragments": used_fragments,
            "size_bytes": 0
        }

    return {
        "success": True,
        "message": "Fragments reconstructed successfully",
        "output_file": str(output_path),
        "total_fragments": used_fragments,
        "size_bytes": len(
            reconstructed_data
        )
    }