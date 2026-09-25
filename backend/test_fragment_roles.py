import tempfile
import unittest
from pathlib import Path

from backend.services.evidence_analyzer import analyze_file


class FragmentRoleTests(unittest.TestCase):
    def test_jpeg_end_marker_is_classified_as_an_end_fragment(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            (directory / "part1.bin").write_bytes(b"\xff\xd8\xff\xe0header")
            final_fragment = directory / "part3.bin"
            final_fragment.write_bytes(b"image-data\xff\xd9")

            analysis = analyze_file(final_fragment, directory)

        self.assertEqual(analysis["detected_format"], "JPEG")
        self.assertEqual(analysis["fragment_type"], "END_FRAGMENT")
        self.assertTrue(analysis["has_end_marker"])


if __name__ == "__main__":
    unittest.main()
