"""
Notification service.

Handles user notifications via logging and Email.
"""

import logging
from uuid import UUID
from typing import Optional
from sqlmodel import Session, select

from app.models.document import Document, DocumentStatus
from app.models.project import Project
from app.models.user import User
from app.core.config import settings
from app.utils.email import send_email

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications to users.
    """

    def __init__(self, session: Optional[Session] = None):
        self.session = session

    def notify_document_status(
        self,
        document_id: UUID,
        status: DocumentStatus,
        message: Optional[str] = None,
    ) -> None:
        """
        Notify user about document status change.
        """
        log_msg = f"Notification: Document {document_id} is now {status.value}"
        if message:
            log_msg += f" - {message}"

        logger.info(log_msg)

        if status == DocumentStatus.FAILED and settings.EMAILS_ENABLED and self.session:
            self._send_email_alert(document_id, message)
        
        # Always send WebSocket notification if possible
        self._send_websocket_notification(document_id, status, message)

    def _send_websocket_notification(
        self, document_id: UUID, status: DocumentStatus, message: Optional[str] = None
    ) -> None:
        """
        Publish notification to Redis for WebSocket delivery.
        """
        try:
            import redis
            import json

            # Get user ID for this document
            user_id = None
            if self.session:
                statement = (
                    select(Project.owner_id)
                    .join(Document, Document.project_id == Project.id)
                    .where(Document.id == document_id)
                )
                user_id = self.session.execute(statement).scalar()

            if not user_id:
                logger.warning(f"Could not determine user for document {document_id}")
                return

            redis_url = settings.REDIS_URL or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
            r = redis.from_url(redis_url)
            
            payload = {
                "type": "document_status",
                "document_id": str(document_id),
                "status": status.value,
                "message": message,
            }
            
            notification = {
                "user_id": str(user_id),
                "payload": payload
            }
            
            r.publish("notifications", json.dumps(notification))
            logger.debug(f"Published notification to Redis for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to publish WebSocket notification: {e}")

    def _send_email_alert(self, document_id: UUID, message: Optional[str]) -> None:
        """
        Send email alert when document processing fails.
        """
        try:
            # Fetch document and project owner
            statement = (
                select(User.email, Document.filename)
                .join(Project, Project.owner_id == User.id)
                .join(Document, Document.project_id == Project.id)
                .where(Document.id == document_id)
            )
            result = self.session.execute(statement).first()
            if not result:
                logger.warning(f"Could not find owner for document {document_id}")
                return

            user_email, filename = result

            send_email(
                email_to=user_email,
                subject_template=f"Document Processing Failed: {filename}",
                html_template=f"""
                <h3>Processing Failed</h3>
                <p>We're sorry, but the processing for your document <b>{filename}</b> has failed.</p>
                <p><b>Error:</b> {message or 'Unknown error'}</p>
                <p>Please check the RAGify dashboard for more details.</p>
                """,
            )
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
