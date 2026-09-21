from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.session import get_db
from app.models import OptionGroup, Product
from app.schemas.catalog import ProductOut, ProductSummary, QuoteIn, QuoteOut
from app.services.pricing import PricingError, quote_item

router = APIRouter(prefix="/products", tags=["products"])


def get_product_by_slug(db: Session, slug: str, include_inactive: bool = False) -> Product:
    q = (
        db.query(Product)
        .options(selectinload(Product.option_groups).selectinload(OptionGroup.choices), selectinload(Product.quantity_tiers))
        .filter(Product.slug == slug)
    )
    if not include_inactive:
        q = q.filter(Product.active.is_(True))
    product = q.first()
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product


@router.get("", response_model=list[ProductSummary])
def list_products(category: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Product).filter(Product.active.is_(True))
    if category:
        q = q.filter(Product.category == category)
    return q.order_by(Product.category, Product.name).all()


@router.get("/{slug}", response_model=ProductOut)
def get_product(slug: str, db: Session = Depends(get_db)):
    return get_product_by_slug(db, slug)


@router.post("/{slug}/quote", response_model=QuoteOut)
def quote(slug: str, body: QuoteIn, db: Session = Depends(get_db)):
    """Instant price for a configuration, the same computation used at checkout."""
    product = get_product_by_slug(db, slug)
    try:
        q = quote_item(product, body.quantity, body.width_in, body.height_in, body.size_preset, body.options)
    except PricingError as exc:
        raise HTTPException(422, str(exc)) from exc
    return QuoteOut(**q.__dict__, currency=get_settings().currency)
