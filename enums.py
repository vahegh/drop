import enum


class PersonStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    member = "member"
    free = "free"


class PaymentStatus(enum.Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    REFUNDED = "REFUNDED"


class PaymentProvider(enum.Enum):
    VPOS = "VPOS"
    MYAMERIA = "MYAMERIA"
    IDRAM = "IDRAM"
    APPLEPAY = "APPLEPAY"
