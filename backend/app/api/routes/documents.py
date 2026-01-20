from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Any
from uuid import UUID

from app.api import deps
from app.core.storage import s3_client
from app.models.document import Document, DocumentStatus
from app.models.user import User
from sqlmodel import select

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

    success = await loop.run_in_executor(
        None, lambda: s3_client.upload_file(file.file, s3_key, file.content_type)
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload file to storage")

    # Create Database Entry
    document = Document(
        filename=file.filename,
        file_type=file.content_type or "application/octet-stream",
        size=file.size or 0,  # file.size might be none if streamed?
        status=DocumentStatus.COMPLETED,  # Mark ready immediately for now, usually PENDING then worker processes it
        url=s3_key,
        project_id=project_id,
        # created_by=current_user.id # Model doesn't have created_by yet?
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

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
