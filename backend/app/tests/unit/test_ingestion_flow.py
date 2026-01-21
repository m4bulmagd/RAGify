import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from app.services.ingestion.deduplicator import Deduplicator
from app.services.ingestion.ingestion_service import IngestionService
from app.models.document import Document
from app.services.notification import NotificationService
from app.models.document import DocumentStatus


class TestIngestionFlow:
    def test_deduplicator_content_hash(self):
        deduplicator = Deduplicator()
        text = "  Test Content  "
        # Calculate expected hash dynamically
        import hashlib

        expected_hash = hashlib.sha256(b"test content").hexdigest()
        assert deduplicator.generate_content_hash(text) == expected_hash

    @patch("app.services.ingestion.deduplicator.select")
    def test_deduplicator_check_duplicate(self, mock_select):
        deduplicator = Deduplicator()
        session = MagicMock()
        project_id = uuid4()

        # Mock result
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = Document(filename="existing.pdf")
        session.execute.return_value = mock_result

        duplicate = deduplicator.check_duplicate(session, "some_hash", project_id)
        assert duplicate is not None
        assert duplicate.filename == "existing.pdf"

    def test_notification_service_logging(self, caplog):
        with caplog.at_level("INFO"):
            service = NotificationService()
            doc_id = uuid4()
            service.notify_document_status(doc_id, DocumentStatus.COMPLETED, "Done")

            assert (
                f"Notification: Document {doc_id} is now completed - Done"
                in caplog.text
            )
