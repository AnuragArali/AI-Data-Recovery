import os
import unittest
from unittest.mock import patch

from backend.services.investigator_ai import (
    ask_gemini,
    generate_fallback_answer,
)


CONTEXT = {
    "fragment_analysis": {
        "ordered_fragments": ["part-01.bin", "part-02.bin", "part-03.bin"],
        "remaining_fragments": [],
        "ordering_confidence": 0.82,
        "status": "ORDERED",
        "fragments": [
            {
                "filename": "part-01.bin",
                "format": "JPEG",
                "role": "START_FRAGMENT",
                "has_start_marker": True,
                "has_end_marker": False,
            },
            {
                "filename": "part-03.bin",
                "format": "JPEG",
                "role": "END_FRAGMENT",
                "has_start_marker": False,
                "has_end_marker": True,
            },
        ],
    },
    "reconstruction": {
        "success": True,
        "format": "PNG",
        "size_bytes": 2048,
        "output_file": "recovered/recovered_file.png",
    },
    "integrity": {
        "status": "VALID",
        "corruption": "LOW",
        "file_readable": True,
        "format_valid": True,
        "start_marker_valid": True,
        "end_marker_valid": True,
        "sha256": "test-hash",
    },
    "artifact": {
        "format": "PNG",
        "category": "IMAGE",
        "description": "Recovered image artifact",
        "size_bytes": 2048,
    },
    "priority": {
        "score": 85,
        "level": "HIGH",
        "reasons": ["IMAGE artifact", "Low corruption detected"],
    },
}


class FakeResponse:
    text = "Question-specific Gemini response"


class FakeModels:
    def __init__(self):
        self.request = None

    def generate_content(self, **kwargs):
        self.request = kwargs
        return FakeResponse()


class FakeClient:
    def __init__(self):
        self.models = FakeModels()


class InvestigatorAiTests(unittest.TestCase):
    def test_fallback_uses_the_question_to_select_relevant_evidence(self):
        ordering_answer = generate_fallback_answer(
            "Which fragments were selected for the ordering?", CONTEXT
        )["answer"]
        integrity_answer = generate_fallback_answer(
            "Is the recovered artifact structurally valid?", CONTEXT
        )["answer"]
        priority_answer = generate_fallback_answer(
            "Why was this given a high priority score?", CONTEXT
        )["answer"]
        end_answer = generate_fallback_answer(
            "Why is part 3 the final fragment?", CONTEXT
        )["answer"]

        self.assertIn("part-01.bin → part-02.bin", ordering_answer)
        self.assertIn("Integrity status: VALID", integrity_answer)
        self.assertIn("Priority classification: HIGH", priority_answer)
        self.assertIn("part-03.bin", end_answer)
        self.assertIn("FF D9", end_answer)
        self.assertNotEqual(ordering_answer, integrity_answer)
        self.assertNotEqual(integrity_answer, priority_answer)

    @patch("backend.services.investigator_ai.get_gemini_client")
    def test_gemini_call_uses_configured_model_and_returns_its_answer(self, get_client):
        client = FakeClient()
        get_client.return_value = client

        with patch.dict(
            os.environ,
            {"GEMINI_MODEL": "test-model", "GEMINI_FALLBACK_MODEL": "backup-model"},
        ):
            result = ask_gemini(
                "What is the artifact type?",
                CONTEXT,
                [{"role": "user", "content": "Tell me about the artifact."}],
            )

        self.assertEqual(result["answer"], "Question-specific Gemini response")
        self.assertTrue(result["ai_generated"])
        self.assertEqual(result["model"], "test-model")
        self.assertEqual(client.models.request["model"], "test-model")
        self.assertIn("What is the artifact type?", client.models.request["contents"])
        self.assertIn("Tell me about the artifact.", client.models.request["contents"])


if __name__ == "__main__":
    unittest.main()
