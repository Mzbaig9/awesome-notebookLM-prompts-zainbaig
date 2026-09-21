import io
import os
import tempfile

import pytest

_tmp = tempfile.mkdtemp(prefix="printshop-test-")
os.environ.update(
    {
        "DATABASE_URL": f"sqlite:///{_tmp}/test.db",
        "STORAGE_BACKEND": "local",
        "LOCAL_STORAGE_DIR": f"{_tmp}/storage",
        "PAYMENT_PROVIDER": "fake",
        "EMAIL_BACKEND": "console",
        "SECRET_KEY": "test-secret",
        "ENVIRONMENT": "test",
        "FRONTEND_URL": "http://front.test",
    }
)

from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User, UserRole  # noqa: E402
from app.services.seed import seed_catalog  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_catalog(db)
        db.add(User(email="admin@test.com", hashed_password=hash_password("adminpass1"), role=UserRole.admin))
        db.commit()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _login(client, email, password):
    r = client.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(client):
    return _login(client, "admin@test.com", "adminpass1")


_counter = {"n": 0}


@pytest.fixture
def customer(client):
    _counter["n"] += 1
    email = f"cust{_counter['n']}@test.com"
    r = client.post("/auth/register", json={"email": email, "password": "customerpass1", "full_name": "Test Customer"})
    assert r.status_code == 201, r.text
    return _login(client, email, "customerpass1")


def png_bytes(width: int, height: int, dpi: int = 72) -> bytes:
    img = Image.new("RGB", (width, height), (200, 30, 30))
    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(dpi, dpi))
    return buf.getvalue()


def pdf_bytes(width_in: float = 24, height_in: float = 68) -> bytes:
    from pypdf import PdfWriter

    w = PdfWriter()
    w.add_blank_page(width=width_in * 72, height=height_in * 72)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


ADDRESS = {"name": "Test Customer", "line1": "1 Main St", "city": "Montreal", "region": "QC", "postal_code": "H1H1H1", "country": "CA"}
