import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, cart, orders, payments, products
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import User, UserRole

logging.basicConfig(level=logging.INFO)


def ensure_admin() -> None:
    s = get_settings()
    if not (s.admin_email and s.admin_password):
        return
    with SessionLocal() as db:
        email = s.admin_email.lower()
        if db.query(User).filter(User.email == email).first():
            return
        db.add(User(email=email, hashed_password=hash_password(s.admin_password), role=UserRole.admin, full_name="Admin"))
        db.commit()


def create_app() -> FastAPI:
    s = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if not s.is_production:
            Base.metadata.create_all(bind=engine)  # production uses alembic migrations
        ensure_admin()
        yield

    app = FastAPI(title=s.app_name, version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[s.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for r in (auth.router, products.router, cart.router, orders.router, payments.router, admin.router):
        app.include_router(r)

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok", "payment_provider": s.payment_provider, "storage": s.storage_backend}

    return app


app = create_app()
