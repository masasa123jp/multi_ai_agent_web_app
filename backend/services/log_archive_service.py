# backend/services/log_archive_service.py

# 非同期 AsyncSession を用いてログアーカイブを保存・取得するサービスモジュール
# - AsyncSession に対応し、select/execute を用いたクエリ実行
# - CRUD 処理をすべて async/await ベースで実装

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.log_archive import LogArchive

async def save_log_archive(
    db: AsyncSession,
    user_email: str,
    project_name: str,
    filename: str,
    zip_data: bytes
) -> LogArchive:
    """
    新しいログアーカイブをデータベースに保存
    - db: AsyncSession (非同期セッション)
    - user_email: アーカイブ所有者のメールアドレス
    - project_name: 対象プロジェクト名
    - filename: アーカイブファイル名
    - zip_data: バイナリ形式の ZIP データ
    成功時に DB 保存済みの LogArchive インスタンスを返却
    """
    # 1) モデルインスタンスを生成してセッションに追加
    arch = LogArchive(
        user_email=user_email,
        project_name=project_name,
        filename=filename,
        zip_data=zip_data
    )
    db.add(arch)

    # 2) コミットして永続化
    await db.commit()

    # 3) リフレッシュして更新されたフィールドを取得
    await db.refresh(arch)
    return arch

async def list_log_archives_by_project(
    db: AsyncSession,
    user_email: Optional[str],
    project_name: Optional[str]
) -> List[LogArchive]:
    """
    指定されたユーザ(email)およびプロジェクト名に紐づくアーカイブ一覧を取得
    - user_email または project_name が None の場合はそのフィルタをスキップ
    - 作成日時の降順でソート
    """
    # 1) ベースとなる SELECT 文を組み立て
    stmt = select(LogArchive)

    # 2) フィルタ条件を動的に追加
    if user_email is not None:
        stmt = stmt.where(LogArchive.user_email == user_email)
    if project_name is not None:
        stmt = stmt.where(LogArchive.project_name == project_name)

    # 3) 作成日時降順でソート
    stmt = stmt.order_by(LogArchive.created_at.desc())

    # 4) クエリを実行して結果を取得
    result = await db.execute(stmt)
    # 5) ORM スカラーをリスト化して返却
    return result.scalars().all()

async def get_log_archive(
    db: AsyncSession,
    archive_id: int
) -> Optional[LogArchive]:
    """
    指定 ID のアーカイブを取得
    - 存在しなければ None を返却
    """
    # AsyncSession.get により単一エンティティを取得
    return await db.get(LogArchive, archive_id)

# public re-exports
__all__ = [
    'save_log_archive',
    'list_log_archives_by_project',
    'get_log_archive',
]
