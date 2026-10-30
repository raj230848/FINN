import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.database import Base, get_db
from app.main import app
from app.seed import seed
from app.services.alerts import evaluate_alerts

@pytest.fixture
def db(tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / "test.db"}',connect_args={'check_same_thread':False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine,expire_on_commit=False)
    with factory() as session:
        seed(session)
        evaluate_alerts(session,'demo')
        session.commit()
        yield session
    engine.dispose()

@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    # Deliberately do not invoke production lifespan or external networks.
    yield TestClient(app)
    app.dependency_overrides.clear()
