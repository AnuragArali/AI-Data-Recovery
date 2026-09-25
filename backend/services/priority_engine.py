# --------------------------------------------------
# PRIORITY ENGINE
# --------------------------------------------------

def calculate_priority(
    artifact: dict,
    integrity: dict
) -> dict:

    category = artifact.get(
        "category",
        "UNKNOWN"
    )

    integrity_status = integrity.get(
        "integrity_status",
        "INVALID"
    )

    corruption_status = integrity.get(
        "corruption_status",
        "HIGH"
    )


    # --------------------------------------------------
    # INITIAL SCORE
    # --------------------------------------------------

    priority_score = 0

    reasons = []


    # --------------------------------------------------
    # ARTIFACT CATEGORY SCORE
    # --------------------------------------------------

    category_scores = {

        "DOCUMENT": 35,

        "IMAGE": 30,

        "VIDEO": 30,

        "AUDIO": 25,

        "ARCHIVE": 25,

        "UNKNOWN": 10
    }


    type_score = category_scores.get(
        category,
        10
    )


    priority_score += type_score


    reasons.append(
        f"{category} artifact"
    )


    # --------------------------------------------------
    # INTEGRITY SCORE
    # --------------------------------------------------

    if integrity_status == "VALID":

        priority_score += 30

        reasons.append(
            "Artifact passed integrity validation"
        )

    elif integrity_status == "PARTIALLY_VALID":

        priority_score += 15

        reasons.append(
            "Artifact is partially valid"
        )

    else:

        reasons.append(
            "Artifact failed integrity validation"
        )


    # --------------------------------------------------
    # CORRUPTION SCORE
    # --------------------------------------------------

    if corruption_status == "LOW":

        priority_score += 25

        reasons.append(
            "Low corruption detected"
        )

    elif corruption_status == "MEDIUM":

        priority_score += 10

        reasons.append(
            "Moderate corruption detected"
        )

    else:

        reasons.append(
            "High corruption detected"
        )


    # --------------------------------------------------
    # LIMIT SCORE
    # --------------------------------------------------

    priority_score = min(
        priority_score,
        100
    )


    # --------------------------------------------------
    # DETERMINE PRIORITY LEVEL
    # --------------------------------------------------

    if priority_score >= 75:

        priority = "HIGH"

    elif priority_score >= 50:

        priority = "MEDIUM"

    else:

        priority = "LOW"


    # --------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------

    return {

        "priority_score":
            priority_score,

        "priority":
            priority,

        "reasons":
            reasons
    }