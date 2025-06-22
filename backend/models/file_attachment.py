from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Integer,
    LargeBinary,
    TIMESTAMP,
    func,
    ForeignKeyConstraint
)
from sqlalchemy.orm import relationship
from backend.db.base import Base
from backend.models.project import Project  # Project モデルをインポート

class FileAttachment(Base):
    """
    agentbased.file_attachments テーブルの ORM モデル
    - プロジェクトに紐づくファイルバイナリを保存
    """
    __tablename__ = "file_attachments"
    __table_args__ = (
        # スキーマ名と複合外部キー制約を指定
        ForeignKeyConstraint(
            ["project_user_email", "project_name"],
            ["agentbased.projects.user_email", "agentbased.projects.name"],
            ondelete="CASCADE"
        ),
        {"schema": "agentbased"}
    )

    # ── 主キー ───────────────────────────────────
    file_attachment_key = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="プライマリキー"
    )

    # ── 外部キー（Project の複合主キーを参照） ───────────────
    project_user_email = Column(
        String(255),
        nullable=False,
        comment="紐づくプロジェクトのユーザメールアドレス"
    )
    project_name = Column(
        String(255),
        nullable=False,
        comment="紐づくプロジェクト名"
    )

    # ── ファイル情報 ─────────────────────────────
    filename    = Column(String(255), nullable=False, comment="ファイル名")
    file_type   = Column(String(100), nullable=True,  comment="MIME タイプ")
    file_size   = Column(Integer,     nullable=True,  comment="ファイルサイズ (バイト)")
    file_data   = Column(LargeBinary, nullable=True,  comment="ファイルバイナリデータ")
    upload_time = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
        comment="アップロード日時"
    )

    # ── リレーション: Project への双方向リレーション ───────
    project = relationship(
        Project,
        back_populates="file_attachments",
        lazy="joined",
        doc="このファイルが属するプロジェクトへの参照"
    )
