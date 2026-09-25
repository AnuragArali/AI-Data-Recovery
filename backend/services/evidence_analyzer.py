from pathlib import Path

from backend.utils.binary_identifier import identify_format
from backend.utils.file_utils import calculate_sha256

from backend.services.fragment_rebuilder import (
    analyze_fragment,
    reconstruct_fragments
)

from backend.services.fragment_relationship import (
    analyze_fragment_relationships,
    determine_fragment_order,
    find_format_from_directory
)

from backend.services.integrity_analyzer import (
    analyze_integrity
)

from backend.services.artifact_classifier import (
    classify_artifact
)

from backend.services.priority_engine import (
    calculate_priority
)

from backend.services.ai_explainer import (
    generate_explanation
)


# ==================================================
# ANALYZE SINGLE FILE
# ==================================================

def analyze_file(
    file_path: Path,
    directory: Path | None = None
) -> dict:

    filename = file_path.name
    extension = file_path.suffix.lower()

    # --------------------------------------------------
    # FILE SIZE
    # --------------------------------------------------

    try:
        size_bytes = file_path.stat().st_size
    except OSError:
        size_bytes = 0

    # --------------------------------------------------
    # SHA-256
    # --------------------------------------------------

    try:
        sha256 = calculate_sha256(
            file_path
        )
    except OSError:
        sha256 = None

    # --------------------------------------------------
    # FORMAT DETECTION
    # --------------------------------------------------

    if directory is not None:

        detected_format = find_format_from_directory(
            file_path,
            directory
        )

    else:

        detected_format = identify_format(
            file_path
        )

    # --------------------------------------------------
    # HEADER STATUS
    # --------------------------------------------------

    if detected_format in [
        "UNKNOWN",
        "UNREADABLE"
    ]:

        header_status = "UNKNOWN"

    else:

        header_status = "VALID"

    # --------------------------------------------------
    # FRAGMENT ANALYSIS
    # --------------------------------------------------

    fragment_info = analyze_fragment(
        file_path,
        detected_format
    )

    # --------------------------------------------------
    # RETURN FILE ANALYSIS
    # --------------------------------------------------

    return {

        "filename":
            filename,

        "extension":
            extension,

        "size_bytes":
            size_bytes,

        "sha256":
            sha256,

        "detected_format":
            detected_format,

        "header_status":
            header_status,

        "fragment_type":
            fragment_info[
                "fragment_type"
            ],

        "has_start_marker":
            fragment_info[
                "has_start_marker"
            ],

        "has_end_marker":
            fragment_info[
                "has_end_marker"
            ]
    }


# ==================================================
# ANALYZE DIRECTORY
# ==================================================

def analyze_directory(
    directory: Path
) -> list[dict]:

    results = []

    if not directory.exists():
        return results

    for file_path in directory.iterdir():

        if file_path.is_file():

            result = analyze_file(
                file_path,
                directory
            )

            results.append(
                result
            )

    return results


# ==================================================
# ANALYZE FRAGMENT RELATIONSHIPS
# ==================================================

def analyze_relationships(
    directory: Path
) -> list[dict]:

    if not directory.exists():
        return []

    return analyze_fragment_relationships(
        directory
    )


# ==================================================
# DETERMINE FRAGMENT ORDER
# ==================================================

def determine_order(
    directory: Path
) -> dict:

    if not directory.exists():

        return {

            "ordered_fragments": [],

            "remaining_fragments": [],

            "confidence": 0.0,

            "status":
                "NO_DIRECTORY"
        }

    return determine_fragment_order(
        directory
    )


# ==================================================
# RECONSTRUCT EVIDENCE
# ==================================================

def reconstruct_evidence(
    directory: Path
) -> dict:

    # --------------------------------------------------
    # 1. DETERMINE FRAGMENT ORDER
    # --------------------------------------------------

    order_result = determine_order(
        directory
    )

    ordered_fragments = (
        order_result.get(
            "ordered_fragments",
            []
        )
    )

    confidence = (
        order_result.get(
            "confidence",
            0.0
        )
    )

    status = (
        order_result.get(
            "status",
            "UNKNOWN"
        )
    )

    # --------------------------------------------------
    # 2. CHECK WHETHER ORDER EXISTS
    # --------------------------------------------------

    if not ordered_fragments:

        return {

            "success": False,

            "message":
                "No fragment order found",

            "order":
                order_result
        }

    # --------------------------------------------------
    # 3. CHECK WHETHER ORDER IS COMPLETE
    # --------------------------------------------------

    if status != "ORDERED":

        return {

            "success": False,

            "message": (
                "Reconstruction skipped because "
                "fragment ordering is incomplete"
            ),

            "order":
                order_result
        }

    # --------------------------------------------------
    # 4. CHECK CONFIDENCE
    # --------------------------------------------------

    if confidence < 0.45:

        return {

            "success": False,

            "message": (
                "Reconstruction skipped because "
                "confidence is too low"
            ),

            "order":
                order_result
        }

    # --------------------------------------------------
    # 5. CONVERT FILENAMES TO PATHS
    # --------------------------------------------------

    fragment_paths = []

    for filename in ordered_fragments:

        fragment_path = (
            directory /
            filename
        )

        if fragment_path.exists():

            fragment_paths.append(
                fragment_path
            )

    # --------------------------------------------------
    # 6. CHECK FRAGMENT PATHS
    # --------------------------------------------------

    if not fragment_paths:

        return {

            "success": False,

            "message": (
                "Ordered fragments could "
                "not be located"
            ),

            "order":
                order_result
        }

    # --------------------------------------------------
    # 7. DETERMINE FILE FORMAT
    # --------------------------------------------------

    first_fragment = (
        fragment_paths[0]
    )

    detected_format = (
        find_format_from_directory(
            first_fragment,
            directory
        )
    )

    # --------------------------------------------------
    # 8. DETERMINE OUTPUT EXTENSION
    # --------------------------------------------------

    extension_map = {

        "JPEG": ".jpg",

        "PNG": ".png",

        "PDF": ".pdf",

        "ZIP": ".zip"
    }

    extension = extension_map.get(
        detected_format,
        ".bin"
    )

    # --------------------------------------------------
    # 9. CREATE RECOVERED DIRECTORY
    # --------------------------------------------------

    recovered_directory = Path(
        "recovered"
    )

    recovered_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------
    # 10. OUTPUT FILE
    # --------------------------------------------------

    output_path = (
        recovered_directory /
        f"recovered_file{extension}"
    )

    # --------------------------------------------------
    # 11. RECONSTRUCT FRAGMENTS
    # --------------------------------------------------

    reconstruction_result = (
        reconstruct_fragments(
            fragment_paths,
            output_path
        )
    )

    # --------------------------------------------------
    # 12. CHECK RECONSTRUCTION RESULT
    # --------------------------------------------------

    if not reconstruction_result.get(
        "success",
        False
    ):

        return {

            "success": False,

            "order":
                order_result,

            "format":
                detected_format,

            "reconstruction":
                reconstruction_result
        }

    # ==================================================
    # 13. INTEGRITY ANALYSIS
    # ==================================================

    integrity_result = (
        analyze_integrity(
            output_path,
            detected_format
        )
    )

    # ==================================================
    # 14. ARTIFACT CLASSIFICATION
    # ==================================================

    artifact_result = (
        classify_artifact(
            output_path,
            detected_format
        )
    )

    # ==================================================
    # 15. PRIORITY ASSESSMENT
    # ==================================================

    priority_result = (
        calculate_priority(
            artifact_result,
            integrity_result
        )
    )

    # ==================================================
    # 16. INVESTIGATIVE EXPLANATION
    # ==================================================

    explanation_result = (
        generate_explanation(

            fragment_order=order_result,

            reconstruction=reconstruction_result,

            integrity=integrity_result,

            artifact=artifact_result,

            priority=priority_result
        )
    )

    # ==================================================
    # 17. FINAL RESULT
    # ==================================================

    return {

        "success":
            True,

        "order":
            order_result,

        "format":
            detected_format,

        "reconstruction":
            reconstruction_result,

        "integrity":
            integrity_result,

        "artifact":
            artifact_result,

        "priority":
            priority_result,

        "explanation":
            explanation_result
    }