"""Documents router."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.api.documents import schemas as doc_schemas
from backend.api.documents import service as doc_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/resume", response_model=doc_schemas.ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a resume (PDF or DOCX)."""
    user_id = current_user["id"]

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    try:
        result = await doc_service.upload_resume(user_id, file.filename, content)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/job-description", response_model=doc_schemas.JobDescriptionResponse)
async def upload_job_description(
    data: doc_schemas.JobDescriptionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Upload a job description (text or URL)."""
    user_id = current_user["id"]

    try:
        result = await doc_service.upload_job_description(
            user_id,
            text=data.text,
            url=data.url
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[doc_schemas.DocumentListItem])
async def list_documents(current_user: dict = Depends(get_current_user)):
    """List all documents for the current user."""
    user_id = current_user["id"]
    return doc_service.list_documents(user_id)


@router.delete("/{document_id}", response_model=doc_schemas.DeleteResponse)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a document."""
    user_id = current_user["id"]

    success = doc_service.delete_document(document_id, user_id)
    if not success:
        # Check if it was a 404 vs 403
        doc = doc_service.get_document(document_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Document not found")
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")

    return {"success": True}