from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint, Sequence, text, Boolean, DateTime, Enum, Float, BigInteger
from enums import PersonStatus, PaymentStatus, PaymentProvider

Base = declarative_base()


class Venue(Base):
    __tablename__ = 'venue'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                     server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String)
    short_name: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(String)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    google_maps_link: Mapped[str] = mapped_column(String)
    yandex_maps_link: Mapped[str] = mapped_column(String)


class Person(Base):
    __tablename__ = 'person'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                     server_default=text("gen_random_uuid()"))
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True)
    instagram_handle: Mapped[str] = mapped_column(String, nullable=True)
    telegram_handle: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[PersonStatus] = mapped_column(
        Enum(PersonStatus), default=PersonStatus.pending)
    avatar_url: Mapped[str] = mapped_column(String, nullable=True)
    album_url: Mapped[str] = mapped_column(String, nullable=True)
    referer_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('person.id'), nullable=True)


class Event(Base):
    __tablename__ = 'event'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                     server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    venue_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('venue.id'))
    image_url: Mapped[str] = mapped_column(String)
    video_url: Mapped[str] = mapped_column(String, nullable=True)
    album_url: Mapped[str] = mapped_column(String, nullable=True)
    track_url: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String(2000))
    early_bird_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    early_bird_price: Mapped[int] = mapped_column(Integer, nullable=True)
    general_admission_price: Mapped[int] = mapped_column(Integer)
    member_ticket_price: Mapped[int] = mapped_column(Integer)
    max_capacity: Mapped[int] = mapped_column(Integer)
    area: Mapped[str] = mapped_column(String, nullable=True)
    shared: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    tiers: Mapped[list['TicketTier']] = relationship('TicketTier', order_by='TicketTier.sort_order', lazy='selectin')


class TicketTier(Base):
    __tablename__ = 'ticket_tier'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    event_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('event.id'))
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[int] = mapped_column(Integer)
    capacity: Mapped[int] = mapped_column(Integer, nullable=True)
    available_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    available_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    required_person_status: Mapped[PersonStatus] = mapped_column(Enum(PersonStatus), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    ecrm_good_code: Mapped[str] = mapped_column(String(10), nullable=True)
    ecrm_good_name: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MemberPass(Base):
    __tablename__ = 'member_pass'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                     server_default=text("gen_random_uuid()"))
    serial_number: Mapped[int] = mapped_column(Integer, unique=True)
    person_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('person.id'), unique=True)
    apple_pass_url: Mapped[str] = mapped_column(String, nullable=True)
    google_pass_url: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now())


class EventTicket(Base):
    __tablename__ = 'event_ticket'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                     server_default=text("gen_random_uuid()"))
    person_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('person.id'))
    event_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('event.id'))
    payment_order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('payment.order_id'), nullable=True)
    apple_pass_url: Mapped[str] = mapped_column(String, nullable=True)
    google_pass_url: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now())
    attended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (UniqueConstraint('person_id', 'event_id'),)


class AppleDevices(Base):
    __tablename__ = 'apple_devices'
    device_id: Mapped[str] = mapped_column(String, primary_key=True)
    push_token: Mapped[str] = mapped_column(String)


class AppleDeviceRegistrations(Base):
    __tablename__ = 'apple_device_registrations'
    device_id: Mapped[str] = mapped_column(
        String, ForeignKey('apple_devices.device_id'), primary_key=True)
    pass_type_id: Mapped[str] = mapped_column(String, primary_key=True)
    serial_number: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)


class Payment(Base):
    __tablename__ = "payment"

    order_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    person_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('person.id'))
    event_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('event.id'), nullable=True)
    amount: Mapped[float] = mapped_column(Float)
    provider: Mapped[Enum] = mapped_column(Enum(PaymentProvider))
    upstream_payment_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.CREATED)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now())


class PaymentIntent(Base):
    __tablename__ = 'payment_intent'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                     server_default=text("gen_random_uuid()"))
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('payment.order_id'))
    recipient_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('person.id'))
    tier_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('ticket_tier.id'), nullable=True)
    tier_price: Mapped[int] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now(),
                                                 onupdate=func.now())

    __table_args__ = (UniqueConstraint('order_id', 'recipient_id'),)


class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    person_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id"), nullable=False)


class CardBinding(Base):
    __tablename__ = 'card_binding'

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    person_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('person.id'))
    masked_card_number: Mapped[str] = mapped_column(String, nullable=True)
    card_expiry_date: Mapped[str] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Drink(Base):
    __tablename__ = 'drink'

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                     server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String)
    price: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DrinkVoucher(Base):
    __tablename__ = 'drink_voucher'

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                     server_default=text("gen_random_uuid()"))
    person_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('person.id'))
    drink_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('drink.id'))
    payment_order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('payment.order_id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class DrinkPaymentIntent(Base):
    __tablename__ = 'drink_payment_intent'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                     server_default=text("gen_random_uuid()"))
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('payment.order_id'))
    drink_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('drink.id'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now(),
                                                 onupdate=func.now())
