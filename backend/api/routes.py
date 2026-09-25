import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, UploadFile, File

from backend.utils.file_utils import save_uploaded_file

from backend.services.evidence_analyzer import (
    analyze_file,
    analyze_directory,
    analyze_relationships,
    determine_order,
    reconstruct_evidence
)

from backend.services.investigator_ai import (
    build_investigation_context,
    ask_gemini,
    generate_fallback_answer
)


router = APIRouter(
    prefix="/api/evidence",
    tags=["Evidence"]
)


UPLOAD_DIRECTORY = Path("temp/uploads")


# ============================================================
# UPLOAD EVIDENCE
# ============================================================

@router.post(
    "/upload",
    summary="Upload Evidence",
    description="Upload one or more digital evidence files."
)
async def upload_evidence(
    files: Annotated[
        list[UploadFile],
        File(
            ...,
            description="Select one or more digital evidence files"
        )
    ]
):

    if not files:
        raise HTTPException(
            status_code=400,
            detail="No evidence files were uploaded."
        )

    UPLOAD_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    saved_file_paths = []

    # --------------------------------------------------------
    # SAVE AND ANALYZE FILES
    # --------------------------------------------------------

    for uploaded_file in files:

        if not uploaded_file.filename:
            continue

        content = await uploaded_file.read()

        if not content:
            continue

        file_path = save_uploaded_file(
            uploaded_file.filename,
            content
        )

        saved_file_paths.append(file_path)

    if not saved_file_paths:
        raise HTTPException(
            status_code=400,
            detail="No valid evidence files were uploaded."
        )

    # A middle or end fragment normally lacks a format header.  Classifying
    # only after the complete set has been saved lets it use a matching start
    # fragment to identify its format and role.
    analyzed_files = [
        analyze_file(file_path, UPLOAD_DIRECTORY)
        for file_path in saved_file_paths
    ]

    # --------------------------------------------------------
    # ANALYZE RELATIONSHIPS
    # --------------------------------------------------------

    relationships = analyze_relationships(
        UPLOAD_DIRECTORY
    )

    # --------------------------------------------------------
    # DETERMINE FRAGMENT ORDER
    # --------------------------------------------------------

    fragment_order = determine_order(
        UPLOAD_DIRECTORY
    )

    # --------------------------------------------------------
    # RECONSTRUCT
    # --------------------------------------------------------

    reconstruction = reconstruct_evidence(
        UPLOAD_DIRECTORY
    )

    # --------------------------------------------------------
    # EXTRACT RESULTS
    # --------------------------------------------------------

    integrity = reconstruction.get(
        "integrity",
        {}
    )

    artifact = reconstruction.get(
        "artifact",
        {}
    )

    priority = reconstruction.get(
        "priority",
        {}
    )

    explanation = reconstruction.get(
        "explanation",
        {}
    )

    # --------------------------------------------------------
    # INVESTIGATION SUMMARY
    # --------------------------------------------------------

    investigation = {
        "status": explanation.get(
            "recovery_status",
            "UNKNOWN"
        ),

        "file_type": artifact.get(
            "format",
            "UNKNOWN"
        ),

        "artifact_category": artifact.get(
            "category",
            "UNKNOWN"
        ),

        "fragments_used": len(
            fragment_order.get(
                "ordered_fragments",
                []
            )
        ),

        "fragment_order": fragment_order.get(
            "ordered_fragments",
            []
        ),

        "ordering_confidence": fragment_order.get(
            "confidence",
            0
        ),

        "reconstruction_status": (
            "SUCCESS"
            if reconstruction.get("success", False)
            else "FAILED"
        ),

        "integrity_status": integrity.get(
            "integrity_status",
            "UNKNOWN"
        ),

        "corruption_status": integrity.get(
            "corruption_status",
            "UNKNOWN"
        ),

        "priority": priority.get(
            "priority",
            "UNKNOWN"
        ),

        "priority_score": priority.get(
            "priority_score",
            0
        ),

        "recovered_file": reconstruction.get(
            "output_file"
        ),

        "explanation": explanation.get(
            "summary",
            ""
        )
    }

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "message": "Evidence uploaded and analyzed successfully.",

        "total_files": len(
            analyzed_files
        ),

        "files": analyzed_files,

        "relationships": relationships,

        "fragment_order": fragment_order,

        "reconstruction": reconstruction,

        "investigation": investigation
    }


# ============================================================
# ASK AI INVESTIGATOR
# ============================================================

@router.post(
    "/ask",
    summary="Ask Investigator",
    description="Ask the AI investigator a question about the uploaded evidence."
)
async def ask_investigator(
    question: str,
    history: str | None = None
):

    try:
        conversation_history = json.loads(history) if history else []
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Chat history must be valid JSON."
        )

    if not isinstance(conversation_history, list):
        raise HTTPException(
            status_code=400,
            detail="Chat history must be a list of messages."
        )

    # --------------------------------------------------------
    # CHECK UPLOAD DIRECTORY
    # --------------------------------------------------------

    if not UPLOAD_DIRECTORY.exists():

        raise HTTPException(
            status_code=400,
            detail="No evidence has been uploaded yet."
        )

    evidence_files = [
        file_path
        for file_path in UPLOAD_DIRECTORY.iterdir()
        if file_path.is_file()
    ]

    if not evidence_files:

        raise HTTPException(
            status_code=400,
            detail="No evidence files are available."
        )

    # --------------------------------------------------------
    # CHECK QUESTION
    # --------------------------------------------------------

    if not question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    # --------------------------------------------------------
    # DETERMINE ORDER
    # --------------------------------------------------------

    fragment_order = determine_order(
        UPLOAD_DIRECTORY
    )

    # --------------------------------------------------------
    # RECONSTRUCT
    # --------------------------------------------------------

    reconstruction = reconstruct_evidence(
        UPLOAD_DIRECTORY
    )

    # --------------------------------------------------------
    # FORENSIC RESULTS
    # --------------------------------------------------------

    integrity = reconstruction.get(
        "integrity",
        {}
    )

    artifact = reconstruction.get(
        "artifact",
        {}
    )

    priority = reconstruction.get(
        "priority",
        {}
    )

    fragment_details = analyze_directory(
        UPLOAD_DIRECTORY
    )

    # --------------------------------------------------------
    # BUILD AI CONTEXT
    # --------------------------------------------------------

    context = build_investigation_context(
        fragment_order=fragment_order,
        reconstruction=reconstruction,
        integrity=integrity,
        artifact=artifact,
        priority=priority,
        fragment_details=fragment_details
    )

    # --------------------------------------------------------
    # ANSWER THE QUESTION
    # --------------------------------------------------------

    # The assistant receives a normalized context even when reconstruction did
    # not complete.  That lets it answer questions about the failed step or
    # fragment ordering instead of returning a fixed sentence for every input.

    try:

        ai_result = ask_gemini(
            question,
            context,
            conversation_history
        )

        return {
            **ai_result,
            "context": context
        }

    except Exception as error:

        fallback_result = generate_fallback_answer(
            question,
            context
        )

        return {
            **fallback_result,
            "ai_error": str(error),
            "context": context
        }
