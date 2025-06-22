"""
backend/routers/log_archives.py
────────────────────────────────────────────────────────────────
ZIP 形式のビルド成果物（ワークフローログ）を管理するルーター。

エンドポイント
    POST   /api/logs/upload                 … アーカイブ保存
    GET    /api/logs/history                … 全履歴一覧
    GET    /api/logs/list/{user}/{project}  … プロジェクト別一覧
    GET    /api/logs/download/{archive_id}  … ZIP ダウンロード
依存
    • get_db()    : SQLAlchemy Session を DI
    • services.log_archive_service          : DB CRUD ラッパ
備考
    - 旧 Flask Blueprint + 個別 FastAPI 版を完全統合。
    - ファイル I/O は UploadFile.read() (async) を使用
      → スレッドブロッキングを回避 :contentReference[oaicite:3]{index=3}
    - ダウンロードは StreamingResponse でメモリ効率を確保
      （大容量でも chunk 配信可） :contentReference[oaicite:4]{index=4}
"""

from __future__ import annotations

from io import BytesIO
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session

from backend.db.dependencies_async import get_db
from backend.models.log_archive import LogArchive
from backend.services.log_archive_service import (
    save_log_archive,
    list_log_archives_by_project,
    get_log_archive,
)

# -------------------------------------------------------------
# APIRouter ―― prefix と tags を一元定義
#   ※ server.py で include_router(router, prefix="/api/logs")
# -------------------------------------------------------------
router = APIRouter(prefix="/api/logs", tags=["logs"])

# -------------------------------------------------------------
# POST /upload : ZIP を DB に保存
# -------------------------------------------------------------
@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="ZIP アーカイブを保存",
)
async def upload_archive(
    project_user_email: str = Form(..., description="ユーザ Email"),
    project_name: str = Form(..., description="プロジェクト名"),
    attachment: UploadFile = File(..., description="ZIP ファイル"),
    db: Session = Depends(get_db),
):
    """
    クライアントから送られた ZIP バイト列を DB (log_archives) に保存し
    `archive_id` を返す。

    * UploadFile は spooled file オブジェクト。`.read()` は非同期で
      実行されスレッドブロックを回避する :contentReference[oaicite:5]{index=5}。
    """
    data: bytes = await attachment.read()

    arch = save_log_archive(
        db=db,
        user_email=project_user_email,
        project_name=project_name,
        filename=attachment.filename,
        zip_data=data,
    )
    return {"archive_id": arch.id}

# -------------------------------------------------------------
# GET /history : 全ユーザ分を時系列で取得
# -------------------------------------------------------------
@router.get(
    "/history",
    response_model=List[dict],
    summary="全アーカイブの履歴一覧",
)
def history(db: Session = Depends(get_db)):
    """
    すべての LogArchive を作成日時降順で返却。
    ※ 管理者専用を想定、RBAC は別ミドルウェアで制御。
    """
    arches = (
        db.query(LogArchive)
        .order_by(LogArchive.created_at.desc())
        .all()
    )
    return [
        {
            "archive_id": a.id,
            "filename": a.filename,
            "created_at": a.created_at.isoformat(),
        }
        for a in arches
    ]

# -------------------------------------------------------------
# GET /list/{user}/{project} : プロジェクト単位の一覧
# -------------------------------------------------------------
@router.get(
    "/list/{project_user_email}/{project_name}",
    response_model=List[dict],
    summary="プロジェクト別アーカイブ一覧",
)
def list_by_project(
    project_user_email: str,
    project_name: str,
    db: Session = Depends(get_db),
):
    """
    user & project をキーに絞り込み。  
    log_archive_service へ処理を委譲し、SRP を維持。
    """
    arches = list_log_archives_by_project(
        db=db,
        user_email=project_user_email,
        project_name=project_name,
    )
    return [
        {
            "archive_id": a.id,
            "filename": a.filename,
            "created_at": a.created_at.isoformat(),
        }
        for a in arches
    ]

# -------------------------------------------------------------
# GET /download/{archive_id} : ZIP ストリーミング
# -------------------------------------------------------------
@router.get(
    "/download/{archive_id}",
    summary="ZIP をダウンロード",
)
def download_archive(
    archive_id: int,
    db: Session = Depends(get_db),
):
    """
    指定 ID の ZIP を StreamingResponse で返却。  
    メモリコピーを 1 度に抑えるため BytesIO を直接返す方式にした。
    """
    arch = get_log_archive(archive_id, db=db)
    if not arch or not arch.zip_data:
        raise HTTPException(status_code=404, detail="Archive not found")

    buf = BytesIO(arch.zip_data)
    # Content-Disposition で適切なファイル名を指定することにより
    # ブラウザの保存ダイアログに反映される。 :contentReference[oaicite:6]{index=6}
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{arch.filename}"'
        },
    )
