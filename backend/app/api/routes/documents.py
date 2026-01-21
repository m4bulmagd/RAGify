from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Any
from uuid import UUID

from app.api import deps
from app.core.storage import s3_client
from app.models.document import Document, DocumentStatus
from app.models.user import User
from sqlmodel import select

from app.core.config import settings
import magic

router = APIRouter()


@router.post("/", response_model=Document, status_code=status.HTTP_201_CREATED)
async def upload_document(
    *,
    db: deps.SessionDep,
    current_user: deps.CurrentUser,
    project_id: UUID,
    file: UploadFile = File(...),
) -> Any:
    """
    Upload a document to S3 and register it in the database.
    """
    # Verify project access (TODO)

    # Validate file size
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File size exceeds the limit of {settings.MAX_UPLOAD_SIZE} bytes",
        )

    # Validate file type using magic
    await file.seek(0)
    file_head = await file.read(2048)
    mime_type = magic.from_buffer(file_head, mime=True)
    await file.seek(0)

    if mime_type not in settings.ALLOWED_UPLOAD_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {mime_type}. Allowed types: ({', '.join([ t.split('/')[-1].upper() for t in settings.ALLOWED_UPLOAD_CONTENT_TYPES] )})",
        )

    # Generate unique path
    file_ext = file.filename.split(".")[-1]
    s3_key = f"{project_id}/{file.filename}"

    # Upload to S3
    # Note: upload_fileobj is sync, so we wrap it or just run it.
    # For large files, better to run in threadpool or use aiobotocore.
    # FastAPI runs def endpoints in threadpool, async def in event loop.
    # Since we defined this as async def, we should ideally await s3 upload in threadpool
    # OR change s3_client to use aiobotocore.
    # For MVP simplicity, we'll assume blocking is okay-ish or rely on fast MinIO.
    # BETTER: Use run_in_executor

    import asyncio

    loop = asyncio.get_event_loop()

    try:
        await loop.run_in_executor(
            None, lambda: s3_client.upload_file(file.file, s3_key, file.content_type)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload file to storage: {str(e)}"
        )

    # Create Database Entry
    document = Document(
        filename=file.filename,
        file_type=file.content_type or "application/octet-stream",
        size=file.size or 0,
        status=DocumentStatus.PENDING,
        url=s3_key,
        project_id=project_id,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Trigger background document processing
    from app.workers.document_ingestion import process_document

    print(f"DEBUG: Celery Broker URL: {process_document.app.conf.broker_url}")
    process_document.delay(str(document.id))

    return document


@router.get("/", response_model=List[Document])
async def get_documents(
    *,
    db: deps.SessionDep,
    current_user: deps.CurrentUser,
    project_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    List documents for a project.
    """
    statement = (
        select(Document)
        .where(Document.project_id == project_id)
        .offset(skip)
        .limit(limit)
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(statement)
    return result.scalars().all()
