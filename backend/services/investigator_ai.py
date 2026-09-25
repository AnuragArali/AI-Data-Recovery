import os
import json
import re

from google import genai


# ==================================================
# SYSTEM INSTRUCTIONS
# ==================================================

SYSTEM_PROMPT = """
You are an AI-assisted digital evidence investigator.

Your job is to explain structured forensic recovery
results to an investigator.

IMPORTANT RULES:

1. Use ONLY the supplied forensic analysis data.

2. Never invent evidence.

3. Never invent timestamps, filenames, users,
   locations, file contents, or events.

4. Do not modify or reconstruct binary data.

5. Do not override deterministic forensic results.

6. Do not claim that a file is authentic merely
   because it passed structural validation.

7. Clearly distinguish measured evidence
   from interpretation.

8. If information is unavailable, explicitly
   say that it is unavailable.

9. Explain technical results in simple,
   investigator-friendly language.

10. Recommendations must be suggested next
    investigative checks, not definitive conclusions.

11. Do not treat a prototype priority score as
    proof that an artifact is actually important
    to an investigation.

12. Do not claim that the recovered artifact
    came from a particular person or event unless
    the supplied evidence explicitly supports it.
"""


# ==================================================
# GEMINI CLIENT
# ==================================================

def get_gemini_client():

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured"
        )

    return genai.Client(
        api_key=api_key
    )


# ==================================================
# BUILD FORENSIC CONTEXT
# ==================================================

def build_investigation_context(
    fragment_order: dict,
    reconstruction: dict,
    integrity: dict,
    artifact: dict,
    priority: dict,
    fragment_details: list[dict] | None = None
) -> dict:

    reconstruction_details = reconstruction.get("reconstruction", {})

    return {

        "fragment_analysis": {

            "ordered_fragments":
                fragment_order.get(
                    "ordered_fragments",
                    []
                ),

            "remaining_fragments":
                fragment_order.get(
                    "remaining_fragments",
                    []
                ),

            "ordering_confidence":
                fragment_order.get(
                    "confidence",
                    0.0
                ),

            "status":
                fragment_order.get(
                    "status",
                    "UNKNOWN"
                ),

            "fragments": [
                {
                    "filename": fragment.get("filename", "UNKNOWN"),
                    "format": fragment.get("detected_format", "UNKNOWN"),
                    "role": fragment.get("fragment_type", "UNKNOWN"),
                    "has_start_marker": fragment.get("has_start_marker", False),
                    "has_end_marker": fragment.get("has_end_marker", False),
                }
                for fragment in (fragment_details or [])
                if isinstance(fragment, dict)
            ]
        },

        "reconstruction": {

            "success":
                reconstruction.get(
                    "success",
                    False
                ),

            "format":
                reconstruction.get(
                    "format",
                    "UNKNOWN"
                ),

            "size_bytes":
                reconstruction_details.get(
                    "size_bytes",
                    0
                ),

            "output_file":
                reconstruction_details.get(
                    "output_file",
                    None
                )
        },

        "integrity": {

            "status":
                integrity.get(
                    "integrity_status",
                    "UNKNOWN"
                ),

            "corruption":
                integrity.get(
                    "corruption_status",
                    "UNKNOWN"
                ),

            "file_readable":
                integrity.get(
                    "file_readable",
                    False
                ),

            "format_valid":
                integrity.get(
                    "format_valid",
                    False
                ),

            "start_marker_valid":
                integrity.get(
                    "start_marker_valid",
                    False
                ),

            "end_marker_valid":
                integrity.get(
                    "end_marker_valid",
                    False
                ),

            "sha256":
                integrity.get(
                    "sha256",
                    None
                )
        },

        "artifact": {

            "format":
                artifact.get(
                    "format",
                    "UNKNOWN"
                ),

            "category":
                artifact.get(
                    "category",
                    "UNKNOWN"
                ),

            "description":
                artifact.get(
                    "description",
                    ""
                ),

            "size_bytes":
                artifact.get(
                    "size_bytes",
                    0
                )
        },

        "priority": {

            "score":
                priority.get(
                    "priority_score",
                    0
                ),

            "level":
                priority.get(
                    "priority",
                    "UNKNOWN"
                ),

            "reasons":
                priority.get(
                    "reasons",
                    []
                )
        }
    }


# ==================================================
# BUILD AI PROMPT
# ==================================================

def build_ai_prompt(
    question: str,
    context: dict,
    conversation_history: list[dict] | None = None
) -> str:

    forensic_data = json.dumps(
        context,
        indent=2
    )

    recent_messages = []

    for message in (conversation_history or [])[-6:]:
        if not isinstance(message, dict):
            continue

        role = message.get("role")
        content = message.get("content")

        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue

        speaker = "INVESTIGATOR" if role == "user" else "ANALYST"
        recent_messages.append(
            f"{speaker}: {content.strip()[:600]}"
        )

    history_text = "\n".join(recent_messages) or "No earlier questions."

    return f"""
FORENSIC ANALYSIS DATA
======================

{forensic_data}


RECENT CONVERSATION
===================

{history_text}


INVESTIGATOR QUESTION
=====================

{question}


TASK
====

Answer the latest investigator question using ONLY
the forensic analysis data supplied above. Use the
recent conversation only to resolve references such
as "it", "that", or "why"; it is not evidence.

Use exactly these sections:

Answer:
Give a direct answer to the question.

Evidence:
List the relevant measured forensic findings.

Interpretation:
Explain what those findings mean.

Suggested Next Check:
Suggest useful additional investigative checks
if appropriate.

Remember:

- Do not invent facts.
- Do not invent file contents.
- Do not invent events or people.
- Do not claim authenticity.
- Do not change the forensic results.
- State uncertainty when appropriate.
- Keep the explanation concise.
"""


# ==================================================
# ASK GEMINI
# ==================================================

def ask_gemini(
    question: str,
    context: dict,
    conversation_history: list[dict] | None = None
) -> dict:

    client = get_gemini_client()

    prompt = build_ai_prompt(
        question,
        context,
        conversation_history
    )

    # Keeping the model configurable allows deployments with restricted model
    # access to select an available Gemini model without a code change.
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    fallback_model = os.getenv(
        "GEMINI_FALLBACK_MODEL",
        "gemini-3.5-flash"
    )
    last_resort_model = os.getenv(
        "GEMINI_LAST_RESORT_MODEL",
        "gemini-3.5-flash-lite"
    )
    models = [model]

    if fallback_model and fallback_model != model:
        models.append(fallback_model)

    if last_resort_model and last_resort_model not in models:
        models.append(last_resort_model)

    last_error = None

    for candidate_model in models:
        try:
            response = client.models.generate_content(

                model=candidate_model,

                contents=prompt,

                config={
                    "system_instruction":
                        SYSTEM_PROMPT,

                    "temperature":
                        0.2
                }
            )

            answer = (response.text or "").strip()

            if not answer:
                raise RuntimeError("Gemini returned an empty response")

            return {

                "question":
                    question,

                "answer":
                    answer,

                "ai_generated":
                    True,

                "provider":
                    "Google Gemini",

                "model":
                    candidate_model
            }

        except Exception as error:
            last_error = error

    raise RuntimeError(
        f"All configured Gemini models failed: {last_error}"
    ) from last_error


# ==================================================
# FALLBACK ANSWER
# ==================================================

def generate_fallback_answer(
    question: str,
    context: dict
) -> dict:

    integrity = context.get(
        "integrity",
        {}
    )

    reconstruction = context.get(
        "reconstruction",
        {}
    )

    fragments = context.get(
        "fragment_analysis",
        {}
    )

    artifact = context.get(
        "artifact",
        {}
    )

    priority = context.get(
        "priority",
        {}
    )

    reconstruction_success = reconstruction.get("success", False)
    order_status = fragments.get("status", "UNKNOWN")
    confidence = fragments.get("ordering_confidence", 0.0)
    ordered_fragments = fragments.get("ordered_fragments", [])
    remaining_fragments = fragments.get("remaining_fragments", [])
    integrity_status = integrity.get("status", "UNKNOWN")
    corruption_status = integrity.get("corruption", "UNKNOWN")
    artifact_format = artifact.get("format", reconstruction.get("format", "UNKNOWN"))
    artifact_category = artifact.get("category", "UNKNOWN")
    priority_level = priority.get("level", "UNKNOWN")
    priority_score = priority.get("score", 0)
    fragment_records = fragments.get("fragments", [])
    end_fragments = [
        fragment
        for fragment in fragment_records
        if fragment.get("role") == "END_FRAGMENT"
    ]
    lower_question = question.casefold()

    def has_any(*terms: str) -> bool:
        return any(re.search(rf"\b{re.escape(term)}\b", lower_question) for term in terms)

    if has_any("last", "final", "end", "ending") and end_fragments:
        end_fragment = end_fragments[0]
        end_filename = end_fragment.get("filename", "the final fragment")
        end_format = end_fragment.get("format", "UNKNOWN")
        marker_description = {
            "JPEG": "the JPEG end-of-image marker (FF D9)",
            "PNG": "the PNG IEND marker",
            "PDF": "the PDF %%EOF marker",
            "ZIP": "the ZIP end-of-central-directory marker",
        }.get(end_format, "a recognized file-end marker")
        direct_answer = (
            f"{end_filename} is the final fragment because it is classified as "
            f"END_FRAGMENT and contains {marker_description}."
        )
        evidence = [
            f"End fragment: {end_filename}",
            f"Detected format: {end_format}",
            f"End marker detected: {'yes' if end_fragment.get('has_end_marker') else 'no'}",
            f"Selected order: {' → '.join(ordered_fragments) or 'not established'}",
        ]
        interpretation = "An end marker strongly supports the final position, while the ordering confidence reflects the engine's support for the full sequence."
        next_check = "Inspect the final bytes of the reconstructed artifact and validate it with an independent format-aware tool."

    elif has_any("order", "ordering", "fragment", "sequence", "arranged"):
        if ordered_fragments:
            sequence = " → ".join(ordered_fragments)
            direct_answer = (
                f"The fragment ordering status is {order_status} with "
                f"{confidence:.0%} confidence. The selected sequence is: {sequence}."
            )
        else:
            direct_answer = (
                f"No fragment sequence was established. The ordering status is "
                f"{order_status} with {confidence:.0%} confidence."
            )
        evidence = [
            f"Ordering status: {order_status}",
            f"Ordering confidence: {confidence:.0%}",
        ]
        if remaining_fragments:
            evidence.append("Fragments not included: " + ", ".join(remaining_fragments))
        interpretation = "The confidence describes the ordering engine's support for the sequence; it is not proof of the original file order."
        next_check = "Review the boundary matches between adjacent fragments before relying on the sequence."

    elif has_any("integrity", "valid", "readable", "corrupt", "corruption", "hash", "sha"):
        direct_answer = (
            f"The recovered artifact has integrity status {integrity_status} and "
            f"corruption status {corruption_status}."
        )
        evidence = [
            f"Integrity status: {integrity_status}",
            f"Corruption status: {corruption_status}",
            f"File readable: {'yes' if integrity.get('file_readable', False) else 'no'}",
            f"Format valid: {'yes' if integrity.get('format_valid', False) else 'no'}",
        ]
        interpretation = "These are structural validation results. They do not by themselves establish authenticity or provenance."
        next_check = "Open the recovered file with an independent validator and preserve its SHA-256 value if one is available."

    elif has_any("priority", "important", "importance", "score", "urgent"):
        direct_answer = f"The prototype priority score is {priority_score}/100, classified as {priority_level}."
        evidence = [
            f"Priority classification: {priority_level}",
            f"Prototype score: {priority_score}/100",
        ]
        evidence.extend(f"Reason: {reason}" for reason in priority.get("reasons", []))
        interpretation = "This score helps triage work; it is not evidence that the artifact is important to an investigation."
        next_check = "Use the score alongside case context and chain-of-custody requirements when deciding what to examine next."

    elif has_any("type", "format", "file", "artifact", "category"):
        direct_answer = f"The recovered artifact is identified as {artifact_format} in the {artifact_category} category."
        evidence = [
            f"Detected format: {artifact_format}",
            f"Artifact category: {artifact_category}",
            f"Recovered size: {reconstruction.get('size_bytes', artifact.get('size_bytes', 0))} bytes",
        ]
        interpretation = "Format identification is based on the available binary structure and can be refined by further validation."
        next_check = "Inspect the recovered artifact with a format-aware viewer or parser."

    elif has_any(
        "recover", "recovered", "reconstruct", "reconstruction", "success",
        "output", "result", "failed", "failure", "complete", "completed",
    ):
        if reconstruction_success:
            direct_answer = "The reconstruction completed successfully."
        else:
            direct_answer = "The reconstruction did not complete successfully."
        evidence = [
            f"Reconstruction success: {'yes' if reconstruction_success else 'no'}",
            f"Recovered size: {reconstruction.get('size_bytes', 0)} bytes",
            f"Output file: {reconstruction.get('output_file') or 'not available'}",
        ]
        interpretation = "A successful reconstruction means bytes were assembled; it does not by itself prove that the recovered content is complete or authentic."
        next_check = "Validate the recovered output and compare it with the source fragments before drawing conclusions."

    else:
        direct_answer = (
            "I can answer questions about the uploaded evidence, such as fragment ordering, "
            "reconstruction, integrity, artifact type, or priority."
        )
        evidence = [
            f"Reconstruction success: {'yes' if reconstruction_success else 'no'}",
            f"Ordering status: {order_status} ({confidence:.0%} confidence)",
            f"Artifact type: {artifact_format}",
            f"Integrity status: {integrity_status}",
        ]
        interpretation = "The assistant only uses the available forensic analysis and will identify when the evidence cannot answer a question."
        next_check = "Ask a specific question about one of the listed findings."

    answer = "\n\n".join((
        f"Answer:\n{direct_answer}",
        "Evidence:\n" + "\n".join(f"- {item}" for item in evidence),
        f"Interpretation:\n{interpretation}",
        f"Suggested Next Check:\n{next_check}",
    ))

    return {

        "question":
            question,

        "answer": answer,

        "evidence": evidence,

        "interpretation": interpretation,

        "suggested_next_check": next_check,

        "ai_generated":
            False,

        "provider":
            "Fallback",

        "model":
            None
    }
