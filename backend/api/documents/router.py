"""Documents router."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.api.documents import schemas as doc_schemas
from backend.api.documents import service as doc_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/resume", response_model=doc_schemas.ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload a resume (PDF or DOCX)."""
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    try:
        return await doc_service.upload_resume(current_user["id"], file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/job-description/file", response_model=doc_schemas.JobDescriptionResponse)
async def upload_job_description_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload a job description file (PDF or DOCX)."""
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    try:
        return await doc_service.upload_job_description_file(current_user["id"], file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/job-description/text", response_model=doc_schemas.JobDescriptionResponse)
async def upload_job_description_text(
    data: doc_schemas.JobDescriptionTextRequest,
    current_user: dict = Depends(get_current_user),
):
    """Persist pasted job description text."""
    try:
        return await doc_service.upload_job_description_text(current_user["id"], data.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/job-description/url", response_model=doc_schemas.JobDescriptionResponse)
async def upload_job_description_url(
    data: doc_schemas.JobDescriptionUrlRequest,
    current_user: dict = Depends(get_current_user),
):
    """Persist a job description fetched from a URL."""
    try:
        return await doc_service.upload_job_description_url(current_user["id"], str(data.url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=list[doc_schemas.DocumentListItem])
async def list_documents(current_user: dict = Depends(get_current_user)):
    """List all documents for the current user."""
    return await doc_service.list_documents(current_user["id"])


@router.delete("/{document_id}", response_model=doc_schemas.DeleteResponse)
async def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a document."""
    success = await doc_service.delete_document(document_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"success": True}
