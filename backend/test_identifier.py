from pathlib import Path

from backend.utils.binary_identifier import identify_format


test_file = Path("temp/uploads/test.bin")

result = identify_format(test_file)

print("Detected format:", result)