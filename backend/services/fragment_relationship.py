from pathlib import Path
import re

from backend.utils.binary_identifier import identify_format


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


def read_bytes(file_path: Path) -> bytes:
    try:
        with open(file_path, "rb") as file:
            return file.read()
    except OSError:
        return b""


def infer_format_from_data(data: bytes) -> str:
    if not data:
        return "UNKNOWN"

    for file_format, markers in FILE_MARKERS.items():
        if data.startswith(markers["start"]):
            return file_format

        if data.endswith(markers["end"]):
            return file_format

    return "UNKNOWN"


def find_format_from_directory(
    file_path: Path,
    directory: Path
) -> str:

    # First try direct identification
    detected_format = identify_format(file_path)

    if detected_format != "UNKNOWN":
        return detected_format

    # Try the fragment's own bytes
    data = read_bytes(file_path)

    inferred_format = infer_format_from_data(data)

    if inferred_format != "UNKNOWN":
        return inferred_format

    # Look at other fragments/files in the same evidence set
    for other_file in directory.iterdir():

        if not other_file.is_file():
            continue

        if other_file == file_path:
            continue

        other_format = identify_format(other_file)

        if other_format != "UNKNOWN":
            return other_format

        other_data = read_bytes(other_file)

        other_inferred_format = infer_format_from_data(
            other_data
        )

        if other_inferred_format != "UNKNOWN":
            return other_inferred_format

    return "UNKNOWN"


def find_best_overlap(
    first_data: bytes,
    second_data: bytes,
    max_overlap: int = 128
) -> int:

    if not first_data or not second_data:
        return 0

    maximum = min(
        max_overlap,
        len(first_data),
        len(second_data)
    )

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
            return overlap_size

    return 0


def calculate_boundary_similarity(
    first_data: bytes,
    second_data: bytes,
    sample_size: int = 64
) -> float:

    if not first_data or not second_data:
        return 0.0

    first_boundary = first_data[-sample_size:]
    second_boundary = second_data[:sample_size]

    comparison_length = min(
        len(first_boundary),
        len(second_boundary)
    )

    if comparison_length == 0:
        return 0.0

    matches = 0

    for i in range(comparison_length):
        if first_boundary[i] == second_boundary[i]:
            matches += 1

    return matches / comparison_length


def get_fragment_type(
    data: bytes,
    file_format: str
) -> str:

    if not data:
        return "UNREADABLE"

    markers = FILE_MARKERS.get(file_format)

    if not markers:
        return "MIDDLE_FRAGMENT"

    has_start = data.startswith(
        markers["start"]
    )

    has_end = data.endswith(
        markers["end"]
    )

    if has_start and has_end:
        return "COMPLETE"

    if has_start:
        return "START_FRAGMENT"

    if has_end:
        return "END_FRAGMENT"

    return "MIDDLE_FRAGMENT"


def extract_fragment_number(
    filename: str
):
    """
    Extracts a numeric fragment/part number.

    Examples:
    part1.bin -> 1
    part2.bin -> 2
    fragment_3.bin -> 3
    """

    patterns = [
        r"part[_-]?(\d+)",
        r"fragment[_-]?(\d+)",
        r"chunk[_-]?(\d+)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            filename.lower()
        )

        if match:
            return int(match.group(1))

    return None


def calculate_sequence_score(
    first_filename: str,
    second_filename: str
) -> float:

    first_number = extract_fragment_number(
        first_filename
    )

    second_number = extract_fragment_number(
        second_filename
    )

    if (
        first_number is None
        or
        second_number is None
    ):
        return 0.0

    if second_number == first_number + 1:
        return 1.0

    if second_number > first_number:
        return 0.5

    return 0.0


def calculate_relationship(
    first_file: Path,
    second_file: Path,
    directory: Path
) -> dict:

    first_data = read_bytes(first_file)
    second_data = read_bytes(second_file)

    first_format = find_format_from_directory(
        first_file,
        directory
    )

    second_format = find_format_from_directory(
        second_file,
        directory
    )

    same_format = (
        first_format != "UNKNOWN"
        and
        first_format == second_format
    )

    first_type = get_fragment_type(
        first_data,
        first_format
    )

    second_type = get_fragment_type(
        second_data,
        second_format
    )

    overlap_size = find_best_overlap(
        first_data,
        second_data
    )

    if overlap_size > 0:
        overlap_similarity = min(
            overlap_size / 64,
            1.0
        )
    else:
        overlap_similarity = 0.0

    boundary_similarity = calculate_boundary_similarity(
        first_data,
        second_data
    )

    sequence_score = calculate_sequence_score(
        first_file.name,
        second_file.name
    )

    score = 0.0

    # Same file format
    if same_format:
        score += 0.20

    # Boundary similarity
    score += boundary_similarity * 0.15

    # Actual byte overlap
    score += overlap_similarity * 0.20

    # Fragment type compatibility
    if (
        first_type == "START_FRAGMENT"
        and
        second_type == "MIDDLE_FRAGMENT"
    ):
        score += 0.15

    elif (
        first_type == "MIDDLE_FRAGMENT"
        and
        second_type == "MIDDLE_FRAGMENT"
    ):
        score += 0.05

    elif (
        first_type == "MIDDLE_FRAGMENT"
        and
        second_type == "END_FRAGMENT"
    ):
        score += 0.15

    # Filename sequence
    score += sequence_score * 0.30

    # Complete files are not normally fragments
    if (
        first_type == "COMPLETE"
        or
        second_type == "COMPLETE"
    ):
        score *= 0.5

    score = round(
        min(score, 1.0),
        3
    )

    if score >= 0.70:
        relationship = "STRONG"

    elif score >= 0.45:
        relationship = "POSSIBLE"

    else:
        relationship = "WEAK"

    return {
        "first_fragment": first_file.name,
        "second_fragment": second_file.name,
        "score": score,
        "same_format": same_format,
        "boundary_similarity": round(
            boundary_similarity,
            3
        ),
        "overlap_size": overlap_size,
        "overlap_similarity": round(
            overlap_similarity,
            3
        ),
        "sequence_score": round(
            sequence_score,
            3
        ),
        "first_type": first_type,
        "second_type": second_type,
        "relationship": relationship
    }


def analyze_fragment_relationships(
    directory: Path
) -> list[dict]:

    files = [
        file_path
        for file_path in directory.iterdir()
        if file_path.is_file()
    ]

    relationships = []

    for first_file in files:

        for second_file in files:

            if first_file == second_file:
                continue

            relationship = calculate_relationship(
                first_file,
                second_file,
                directory
            )

            relationships.append(
                relationship
            )

    return relationships


def determine_fragment_order(
    directory: Path
) -> dict:

    files = [
        file_path
        for file_path in directory.iterdir()
        if file_path.is_file()
    ]

    if not files:
        return {
            "ordered_fragments": [],
            "remaining_fragments": [],
            "confidence": 0.0,
            "status": "NO_FRAGMENTS"
        }

    relationships = analyze_fragment_relationships(
        directory
    )

    # Find START fragment
    start_candidates = []

    for file_path in files:

        data = read_bytes(file_path)

        file_format = find_format_from_directory(
            file_path,
            directory
        )

        fragment_type = get_fragment_type(
            data,
            file_format
        )

        if fragment_type == "START_FRAGMENT":
            start_candidates.append(
                file_path
            )

    # Prefer the lowest numbered START fragment
    if start_candidates:

        start_candidates.sort(
            key=lambda path:
            extract_fragment_number(path.name)
            if extract_fragment_number(path.name)
            is not None
            else 999999
        )

        current = start_candidates[0]

    else:

        # Fall back to fragment with lowest number
        files.sort(
            key=lambda path:
            extract_fragment_number(path.name)
            if extract_fragment_number(path.name)
            is not None
            else 999999
        )

        current = files[0]

    ordered = [
        current.name
    ]

    used = {
        current.name
    }

    confidence_values = []

    while True:

        candidates = [
            relationship
            for relationship in relationships
            if (
                relationship["first_fragment"]
                ==
                current.name
                and
                relationship["second_fragment"]
                not in used
            )
        ]

        if not candidates:
            break

        candidates.sort(
            key=lambda item:
            (
                item["score"],
                item["sequence_score"]
            ),
            reverse=True
        )

        best = candidates[0]

        if best["score"] < 0.45:
            break

        next_fragment = best[
            "second_fragment"
        ]

        ordered.append(
            next_fragment
        )

        used.add(
            next_fragment
        )

        confidence_values.append(
            best["score"]
        )

        current = Path(
            next_fragment
        )

    remaining = [
        file_path.name
        for file_path in files
        if file_path.name not in used
    ]

    if not remaining:
        status = "ORDERED"
    else:
        status = "PARTIAL_ORDER"

    if confidence_values:

        confidence = sum(
            confidence_values
        ) / len(confidence_values)

    else:
        confidence = 0.0

    return {
        "ordered_fragments": ordered,
        "remaining_fragments": remaining,
        "confidence": round(
            confidence,
            3
        ),
        "status": status
    }