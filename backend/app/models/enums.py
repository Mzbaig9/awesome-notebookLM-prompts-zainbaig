import enum


class UserRole(str, enum.Enum):
    customer = "customer"
    admin = "admin"


class OrderStatus(str, enum.Enum):
    cart = "cart"
    pending_payment = "pending_payment"
    paid = "paid"
    in_review = "in_review"
    awaiting_customer = "awaiting_customer"
    approved = "approved"
    in_production = "in_production"
    shipped = "shipped"
    completed = "completed"
    cancelled = "cancelled"
    refunded = "refunded"


class ArtworkStatus(str, enum.Enum):
    awaiting_artwork = "awaiting_artwork"
    submitted = "submitted"
    rejected = "rejected"
    proof_sent = "proof_sent"
    changes_requested = "changes_requested"
    approved = "approved"


class ArtworkKind(str, enum.Enum):
    customer_upload = "customer_upload"
    proof = "proof"


class DesignService(str, enum.Enum):
    upload = "upload"
    design_later = "design_later"
    hire_designer = "hire_designer"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    refunded = "refunded"
    failed = "failed"


class PriceType(str, enum.Enum):
    multiplier = "multiplier"
    flat = "flat"
    per_sqft = "per_sqft"
    per_unit = "per_unit"
