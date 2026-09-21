from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_order, item_of, load_order
from app.db.session import get_db
from app.models import Artwork, Order, OrderStatus, User
from app.schemas.orders import ArtworkOut, NoteIn, OrderItemOut, OrderOut, OrderSummary
from app.services import orders as order_service
from app.services.artwork import ArtworkError
from app.services.orders import OrderError
from app.services.storage import get_storage

router = APIRouter(prefix="/orders", tags=["orders"])


def serialize_order(order: Order) -> OrderOut:
    out = OrderOut.model_validate(order, from_attributes=True)
    out.item_count = len(order.items)
    for item_out, item in zip(out.items, order.items):
        for art_out, art in zip(item_out.artworks, item.artworks):
            art_out.has_preview = art.preview_key is not None
    return out


def _raise(exc: Exception):
    if isinstance(exc, OrderError):
        raise HTTPException(exc.status_code, str(exc)) from exc
    if isinstance(exc, ArtworkError):
        raise HTTPException(422, str(exc)) from exc
    raise exc


@router.get("", response_model=list[OrderSummary])
def list_my_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = (
        db.query(Order)
        .filter(Order.user_id == user.id, Order.status != OrderStatus.cart)
        .order_by(Order.created_at.desc())
        .all()
    )
    result = []
    for o in orders:
        s = OrderSummary.model_validate(o, from_attributes=True)
        s.item_count = len(o.items)
        result.append(s)
    return result


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order: Order = Depends(get_owned_order)):
    return serialize_order(order)


@router.post("/{order_id}/reopen", response_model=OrderOut)
def reopen(order: Order = Depends(get_owned_order), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Abandon a pending checkout and go back to editing the cart."""
    try:
        order_service.reopen_cart(db, order, user)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    db.commit()
    return serialize_order(load_order(db, order.id))


@router.post("/{order_id}/items/{item_id}/artwork", response_model=ArtworkOut, status_code=status.HTTP_201_CREATED)
async def reupload_artwork(item_id: str, file: UploadFile = File(...), order: Order = Depends(get_owned_order),
                           user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Upload corrected artwork after a rejection, or supply artwork for a 'design later' item."""
    item = item_of(order, item_id)
    data = await file.read()
    try:
        art = order_service.customer_upload(db, order, item, data, file.filename or "artwork", user)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    db.commit()
    return ArtworkOut.model_validate(art, from_attributes=True).model_copy(update={"has_preview": art.preview_key is not None})


@router.post("/{order_id}/items/{item_id}/proof/approve", response_model=OrderItemOut)
def approve_proof(item_id: str, background: BackgroundTasks, order: Order = Depends(get_owned_order),
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = item_of(order, item_id)
    try:
        order_service.customer_approve_proof(db, order, item, user, background)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    db.commit()
    return serialize_order(load_order(db, order.id)).items[[i.id for i in order.items].index(item_id)]


@router.post("/{order_id}/items/{item_id}/proof/request-changes", response_model=OrderItemOut)
def request_changes(item_id: str, body: NoteIn, order: Order = Depends(get_owned_order),
                    user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = item_of(order, item_id)
    if not body.note:
        raise HTTPException(422, "Describe the changes you need")
    try:
        order_service.customer_request_changes(db, order, item, user, body.note)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    db.commit()
    return serialize_order(load_order(db, order.id)).items[[i.id for i in order.items].index(item_id)]


@router.get("/{order_id}/artworks/{artwork_id}/download")
def download_artwork(artwork_id: str, preview: bool = False, order: Order = Depends(get_owned_order), db: Session = Depends(get_db)):
    art = db.get(Artwork, artwork_id)
    if art is None or art.item.order_id != order.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Artwork not found")
    key = art.preview_key if preview else art.storage_key
    if key is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No preview available")
    storage = get_storage()
    url = storage.url(key)
    if url:
        return RedirectResponse(url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    content_type = "image/jpeg" if preview else art.content_type
    filename = "preview.jpg" if preview else art.original_filename
    return StreamingResponse(storage.open(key), media_type=content_type,
                             headers={"Content-Disposition": f'inline; filename="{filename}"'})
