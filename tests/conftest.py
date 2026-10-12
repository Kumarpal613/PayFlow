from collections.abc import Iterator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.repositories.accounts import create_account
from app.main import app


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    try:
        yield factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def seeded_session_factory(
    session_factory: sessionmaker[Session],
) -> sessionmaker[Session]:
    with session_factory.begin() as session:
        create_account(session, "alice", Decimal("1000.00"))
        create_account(session, "bob", Decimal("500.00"))
    return session_factory


@pytest.fixture
def api_client(
    seeded_session_factory: sessionmaker[Session],
) -> Iterator[TestClient]:
    from app.db.database import get_session

    def override_get_session() -> Iterator[Session]:
        with seeded_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
