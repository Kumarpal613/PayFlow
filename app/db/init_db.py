from app.db.database import engine
from app.models.account import Account


def init_db() -> None:
    Account.__table__.create(bind=engine, checkfirst=True)


if __name__ == "__main__":
    init_db()
