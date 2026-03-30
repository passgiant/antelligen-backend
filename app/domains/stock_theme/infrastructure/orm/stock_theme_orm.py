from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.database import Base


class StockThemeOrm(Base):
    __tablename__ = "stock_theme"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    themes: Mapped[list] = mapped_column(JSON, nullable=False)
