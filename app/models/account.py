from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_accounts_balance_nonnegative"),
        CheckConstraint("length(trim(name)) > 0", name="ck_accounts_name_nonempty"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
    )
