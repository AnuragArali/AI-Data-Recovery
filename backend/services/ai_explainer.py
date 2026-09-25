from typing import Any


def generate_explanation(
    fragment_order: dict,
    reconstruction: dict,
    integrity: dict,
    artifact: dict,
    priority: dict
) -> dict:

    # ==================================================
    # BASIC INFORMATION
    # ==================================================

    ordered_fragments = fragment_order.get(
        "ordered_fragments",
        []
    )

    confidence = fragment_order.get(
        "confidence",
        0.0
    )

    order_status = fragment_order.get(
        "status",
        "UNKNOWN"
    )

    file_format = artifact.get(
        "format",
        "UNKNOWN"
    )

    category = artifact.get(
        "category",
        "UNKNOWN"
    )

    size_bytes = reconstruction.get(
        "size_bytes",
        artifact.get(
            "size_bytes",
            0
        )
    )

    integrity_status = integrity.get(
        "integrity_status",
        "UNKNOWN"
    )

    corruption_status = integrity.get(
        "corruption_status",
        "UNKNOWN"
    )

    file_readable = integrity.get(
        "file_readable",
        False
    )

    format_valid = integrity.get(
        "format_valid",
        False
    )

    priority_level = priority.get(
        "priority",
        "UNKNOWN"
    )

    priority_score = priority.get(
        "priority_score",
        0
    )

    # ==================================================
    # RECOVERY STATUS
    # ==================================================

    if (
        order_status == "ORDERED"
        and reconstruction.get(
            "success",
            False
        )
    ):

        recovery_status = "SUCCESSFUL"

    elif ordered_fragments:

        recovery_status = "PARTIAL"

    else:

        recovery_status = "FAILED"

    # ==================================================
    # CONFIDENCE DESCRIPTION
    # ==================================================

    if confidence >= 0.75:

        confidence_description = (
            "high confidence"
        )

    elif confidence >= 0.45:

        confidence_description = (
            "moderate confidence"
        )

    else:

        confidence_description = (
            "low confidence"
        )

    # ==================================================
    # FINDINGS
    # ==================================================

    findings = []

    # Fragment finding
    if order_status == "ORDERED":

        findings.append(
            f"{len(ordered_fragments)} evidence "
            f"fragments were successfully arranged "
            f"into a complete sequence."
        )

        findings.append(
            "Fragment sequence: "
            + " → ".join(
                ordered_fragments
            )
        )

    elif ordered_fragments:

        findings.append(
            "Only part of the available "
            "fragment set could be ordered."
        )

    else:

        findings.append(
            "No reliable fragment sequence "
            "could be established."
        )

    # Format finding
    findings.append(
        f"The reconstructed artifact was "
        f"identified as a {file_format} "
        f"{category.lower()}."
    )

    # Reconstruction finding
    if reconstruction.get(
        "success",
        False
    ):

        findings.append(
            f"The reconstructed file contains "
            f"{size_bytes:,} bytes."
        )

    # Integrity finding
    if integrity_status == "VALID":

        findings.append(
            "The recovered file passed the "
            "available structural integrity "
            "checks and is readable."
        )

    elif integrity_status == "PARTIALLY_VALID":

        findings.append(
            "The recovered file is readable, "
            "but some structural checks "
            "could not be fully verified."
        )

    else:

        findings.append(
            "The recovered file failed one "
            "or more structural validation checks."
        )

    # Corruption finding
    if corruption_status == "LOW":

        findings.append(
            "The available validation checks "
            "indicate low detected corruption."
        )

    elif corruption_status == "MEDIUM":

        findings.append(
            "The available validation checks "
            "indicate moderate detected corruption."
        )

    elif corruption_status == "HIGH":

        findings.append(
            "The available validation checks "
            "indicate significant corruption "
            "or validation failure."
        )

    # ==================================================
    # RECOVERY REASONING
    # ==================================================

    recovery_reasoning = []

    if order_status == "ORDERED":

        recovery_reasoning.append(
            "The fragment ordering engine established "
            "a complete sequence."
        )

        recovery_reasoning.append(
            f"The ordering confidence was "
            f"{confidence:.2f}, representing "
            f"{confidence_description}."
        )

    else:

        recovery_reasoning.append(
            "The available evidence did not "
            "produce a fully reliable fragment sequence."
        )

    if file_format != "UNKNOWN":

        recovery_reasoning.append(
            f"File-format identification indicates "
            f"{file_format} based on the available "
            f"binary structure."
        )

    # ==================================================
    # INTEGRITY INTERPRETATION
    # ==================================================

    integrity_interpretation = (
        f"The recovered {file_format} artifact "
        f"has an integrity status of "
        f"{integrity_status}. "
    )

    if file_readable:

        integrity_interpretation += (
            "The file can be read by the available "
            "validation tools. "
        )

    else:

        integrity_interpretation += (
            "The file could not be fully read by "
            "the available validation tools. "
        )

    if format_valid:

        integrity_interpretation += (
            "Its recognized file structure passed "
            "the available format validation."
        )

    else:

        integrity_interpretation += (
            "Its recognized file structure did not "
            "pass all available format validation."
        )

    # ==================================================
    # PRIORITY EXPLANATION
    # ==================================================

    priority_explanation = (
        f"The prototype priority engine assigned "
        f"a score of {priority_score}/100 "
        f"and classified the artifact as "
        f"{priority_level}. "
    )

    if priority.get("reasons"):

        priority_explanation += (
            "Reasons: "
            + "; ".join(
                priority["reasons"]
            )
            + "."
        )

    # ==================================================
    # RECOMMENDATION
    # ==================================================

    if (
        integrity_status == "VALID"
        and
        file_readable
        and
        format_valid
        and
        order_status == "ORDERED"
    ):

        recommendation = (
            "The recovered artifact can be "
            "examined further because the "
            "fragment sequence was established "
            "and the recovered file passed "
            "the available structural checks."
        )

    elif integrity_status == "PARTIALLY_VALID":

        recommendation = (
            "The artifact should undergo "
            "additional examination because "
            "some structural information could "
            "not be fully verified."
        )

    else:

        recommendation = (
            "Additional recovery or validation "
            "should be performed before relying "
            "on the recovered artifact."
        )

    # ==================================================
    # SUMMARY
    # ==================================================

    if recovery_status == "SUCCESSFUL":

        summary = (
            f"A {file_format} artifact was successfully "
            f"reconstructed from "
            f"{len(ordered_fragments)} evidence fragments. "
            f"The fragment ordering had "
            f"{confidence_description} "
            f"({confidence:.2f}) confidence. "
            f"The recovered artifact is classified as "
            f"an {category.lower()} and has an integrity "
            f"status of {integrity_status}. "
            f"The prototype priority engine assigned "
            f"{priority_level} priority "
            f"({priority_score}/100)."
        )

    elif recovery_status == "PARTIAL":

        summary = (
            f"A {file_format} artifact was partially "
            f"reconstructed from the available evidence. "
            f"The fragment ordering confidence was "
            f"{confidence:.2f}. Additional recovery "
            f"may be required."
        )

    else:

        summary = (
            "The available evidence could not be "
            "reliably reconstructed into a complete "
            "artifact."
        )

    # ==================================================
    # FINAL RESULT
    # ==================================================

    return {

        "summary":
            summary,

        "recovery_status":
            recovery_status,

        "findings":
            findings,

        "recovery_reasoning":
            recovery_reasoning,

        "integrity_interpretation":
            integrity_interpretation,

        "priority_explanation":
            priority_explanation,

        "recommendation":
            recommendation,

        "fragment_order":
            ordered_fragments,

        "ordering_confidence":
            confidence,

        "integrity_status":
            integrity_status,

        "corruption_status":
            corruption_status,

        "artifact_category":
            category,

        "priority":
            priority_level,

        "priority_score":
            priority_score
    }