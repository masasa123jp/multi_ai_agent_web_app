from __future__ import annotations

import logging
from io import BytesIO
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.dependencies_async import get_db, get_current_user
from backend.models.file_attachment import FileAttachment  # 修正後のモデル

router = APIRouter(prefix="", tags=["logs"])
logger = logging.getLogger(__name__)

@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="ログアーカイブをアップロード",
)
async def upload_log(
    project_name: str = Form(..., description="プロジェクト名"),
    attachment: UploadFile = File(..., description="ZIP ファイル"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    ログインユーザーが ZIP をアップロードし、DB に保存して ID を返す
    """
    data = await attachment.read()
    new = FileAttachment(
        project_user_email=current_user.email,
        project_name=project_name,
        filename=attachment.filename,
        file_type=attachment.content_type,
        file_size=len(data),
        file_data=data,
    )
    db.add(new)
    await db.commit()
    await db.refresh(new)

    logger.info("Attachment %d saved by %s", new.file_attachment_key, current_user.email)
    return {"archive_id": new.file_attachment_key}


@router.get(
    "/history",
    summary="ログインユーザーのアップロード履歴一覧",
)
async def list_history(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """
    認証ユーザーがアップロードしたファイルの一覧を返却
    """
    # DDL で定義された主キー file_attachment_key を参照
    stmt = select(FileAttachment).where(
        FileAttachment.project_user_email == current_user.email
    ).order_by(FileAttachment.upload_time.desc())

    result = await db.execute(stmt)
    items = result.scalars().all()

    # フロント側が期待するフィールド名にマッピングして返却
    return [
        {
            "id":         item.file_attachment_key,
            "filename":   item.filename,
            "created_at": item.upload_time.isoformat(),
        }
        for item in items
    ]


@router.get(
    "/download/{archive_id}",
    summary="ログアーカイブ ZIP ダウンロード",
)
async def download_archive(
    archive_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    指定の ID のファイルをストリーミングで返却
    """
    stmt = select(FileAttachment).where(
        FileAttachment.file_attachment_key == archive_id,
        FileAttachment.project_user_email == current_user.email
    )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if not item or not item.file_data:
        raise HTTPException(status_code=404, detail="File not found")

    buf = BytesIO(item.file_data)
    return StreamingResponse(
        buf,
        media_type=item.file_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{item.filename}"'},
    )
