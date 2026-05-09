import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, mapped_column, Mapped

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://memos:vishnu%40memos%40rag@localhost:5432/memos")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="queued")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


def save_document(source: str, source_type: str) -> str:
    with Session() as session:
        doc = Document(id=str(uuid.uuid4()), source=source, source_type=source_type)
        session.add(doc)
        session.commit()
        return doc.id


def update_status(document_id: str, status: str) -> None:
    with Session() as session:
        doc = session.get(Document, document_id)
        if doc:
            doc.status = status
            session.commit()
