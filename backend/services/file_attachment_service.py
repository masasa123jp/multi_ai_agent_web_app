# backend/src/services/file_attachment_service.py
from models.file_attachment import db, FileAttachment
from sqlalchemy.ext.asyncio import AsyncSession

def save_file_attachment(db:AsyncSession, project_id: int, filename: str, file_type: str, file_size: int, file_data: bytes) -> FileAttachment:
    new_attachment = FileAttachment(
        project_id=project_id,
        filename=filename,
        file_type=file_type,
        file_size=file_size,
        file_data=file_data
    )
    db.session.add(new_attachment)
    db.session.commit()
    return new_attachment

def get_attachments_by_project(project_id: int):
    return FileAttachment.query.filter_by(project_id=project_id).all()

def get_attachment_by_id(attachment_id: int) -> FileAttachment:
    return FileAttachment.query.get(attachment_id)
