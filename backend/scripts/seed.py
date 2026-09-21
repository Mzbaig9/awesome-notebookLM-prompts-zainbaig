"""Create tables (dev), seed the starter catalog, and create an admin user.

Usage: python -m scripts.seed [--admin-email x --admin-password y]
"""

import argparse

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import User, UserRole
from app.services.seed import seed_catalog


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--admin-email")
    parser.add_argument("--admin-password")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        n = seed_catalog(db)
        print(f"Seeded {n} products")
        if args.admin_email and args.admin_password:
            email = args.admin_email.lower()
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                db.add(User(email=email, hashed_password=hash_password(args.admin_password), role=UserRole.admin, full_name="Admin"))
                print(f"Created admin {email}")
            else:
                user.role = UserRole.admin
                user.hashed_password = hash_password(args.admin_password)
                print(f"Updated admin {email}")
            db.commit()


if __name__ == "__main__":
    main()
