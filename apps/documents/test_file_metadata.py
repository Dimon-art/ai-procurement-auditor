import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from apps.documents.services.file_metadata import (
    calculate_file_metadata,
)


class FileMetadataTests(SimpleTestCase):
    def test_calculate_file_metadata_returns_sha256_and_size(self):
        content = b"test file content"

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.pdf"
            file_path.write_bytes(content)

            metadata = calculate_file_metadata(
                str(file_path)
            )

        self.assertEqual(
            metadata.file_hash,
            hashlib.sha256(content).hexdigest(),
        )

        self.assertEqual(
            metadata.file_size,
            len(content),
        )