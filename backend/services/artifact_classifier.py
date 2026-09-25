from pathlib import Path


# --------------------------------------------------
# ARTIFACT FORMAT → CATEGORY
# --------------------------------------------------

ARTIFACT_CATEGORIES = {

    "JPEG": "IMAGE",
    "PNG": "IMAGE",

    "PDF": "DOCUMENT",

    "DOCX": "DOCUMENT",
    "XLSX": "DOCUMENT",
    "PPTX": "DOCUMENT",

    "ZIP": "ARCHIVE",

    "MP4": "VIDEO",
    "AVI": "VIDEO",
    "MKV": "VIDEO",

    "MP3": "AUDIO",
    "WAV": "AUDIO"
}


# --------------------------------------------------
# CATEGORY DESCRIPTIONS
# --------------------------------------------------

ARTIFACT_DESCRIPTIONS = {

    "IMAGE":
        "Recovered image artifact",

    "DOCUMENT":
        "Recovered document artifact",

    "ARCHIVE":
        "Recovered compressed/archive artifact",

    "VIDEO":
        "Recovered video artifact",

    "AUDIO":
        "Recovered audio artifact",

    "UNKNOWN":
        "Unknown or unsupported artifact"
}


# --------------------------------------------------
# CLASSIFY ARTIFACT
# --------------------------------------------------

def classify_artifact(
    file_path: Path,
    detected_format: str
) -> dict:

    # Determine category
    category = ARTIFACT_CATEGORIES.get(
        detected_format,
        "UNKNOWN"
    )

    # Determine description
    description = ARTIFACT_DESCRIPTIONS.get(
        category,
        "Unknown or unsupported artifact"
    )

    # Get file size
    try:

        size_bytes = file_path.stat().st_size

    except OSError:

        size_bytes = 0

    # Return classification
    return {

        "filename":
            file_path.name,

        "format":
            detected_format,

        "category":
            category,

        "description":
            description,

        "size_bytes":
            size_bytes
    }