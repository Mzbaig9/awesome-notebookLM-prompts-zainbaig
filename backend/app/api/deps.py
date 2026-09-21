from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Order, OrderItem, User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user_id = decode_access_token(token)
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user


def load_order(db: Session, order_id: str) -> Order | None:
    return (
        db.query(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.artworks),
            selectinload(Order.items).joinedload(OrderItem.product),
            selectinload(Order.payments),
            selectinload(Order.events),
            joinedload(Order.user),
        )
        .filter(Order.id == order_id)
        .first()
    )


def get_owned_order(order_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Order:
    order = load_order(db, order_id)
    if order is None or (order.user_id != user.id and user.role != UserRole.admin):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


def get_any_order(order_id: str, _: User = Depends(require_admin), db: Session = Depends(get_db)) -> Order:
    order = load_order(db, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


def item_of(order: Order, item_id: str) -> OrderItem:
    item = next((i for i in order.items if i.id == item_id), None)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    return item
