from pydantic import BaseModel, EmailStr, PositiveFloat
from datetime import datetime
from uuid import UUID
from typing import Optional
from enums import PersonStatus, PaymentStatus, PaymentProvider


class VenueCreate(BaseModel):
    name: str
    short_name: str
    area: str
    address: str
    latitude: float
    longitude: float
    google_maps_link: str
    yandex_maps_link: str


class VenueUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    area: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    google_maps_link: Optional[str] = None
    yandex_maps_link: Optional[str] = None


class VenueResponse(BaseModel):
    id: UUID
    name: str
    short_name: str
    area: str
    address: str
    latitude: float
    longitude: float
    google_maps_link: str
    yandex_maps_link: str

    class Config:
        from_attributes = True


class PersonCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    instagram_handle: str
    telegram_handle: Optional[str] = None
    avatar_url: Optional[str] = None
    referer_id: Optional[UUID] = None


class PersonUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    instagram_handle: Optional[str] = None
    telegram_handle: Optional[str] = None
    status: Optional[PersonStatus] = None
    avatar_url: Optional[str] = None
    album_url: Optional[str] = None
    referer_id: Optional[UUID] = None


class PersonResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    instagram_handle: str
    telegram_handle: Optional[str]
    status: PersonStatus
    avatar_url: Optional[str]
    album_url: Optional[str]
    referer_id: Optional[UUID]

    class Config:
        from_attributes = True


class MemberCardCreate(BaseModel):
    person_id: UUID


class MemberCardResponse(BaseModel):
    id: UUID
    serial_number: int
    person_id: UUID
    apple_pass_url: str
    google_pass_url: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TicketTierCreate(BaseModel):
    name: str
    price: int
    capacity: Optional[int] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    required_person_status: Optional[PersonStatus] = None
    sort_order: int = 0
    is_active: bool = True
    ecrm_good_code: Optional[str] = None
    ecrm_good_name: Optional[str] = None


class TicketTierUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    capacity: Optional[int] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    required_person_status: Optional[PersonStatus] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    ecrm_good_code: Optional[str] = None
    ecrm_good_name: Optional[str] = None


class TicketTierResponse(BaseModel):
    id: UUID
    event_id: UUID
    name: str
    price: int
    capacity: Optional[int]
    available_from: Optional[datetime]
    available_until: Optional[datetime]
    required_person_status: Optional[PersonStatus]
    sort_order: int
    is_active: bool
    ecrm_good_code: Optional[str]
    ecrm_good_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    name: str
    starts_at: datetime
    ends_at: datetime
    venue_id: UUID
    image_url: str
    video_url: Optional[str]
    album_url: Optional[str]
    track_url: Optional[str]
    description: str
    early_bird_date: Optional[datetime] = None
    early_bird_price: Optional[int] = None
    general_admission_price: int
    member_ticket_price: int
    max_capacity: int
    shared: bool


class EventResponse(BaseModel):
    id: UUID
    name: str
    starts_at: datetime
    ends_at: datetime
    venue_id: UUID
    image_url: str
    video_url: Optional[str]
    album_url: Optional[str]
    track_url: Optional[str]
    description: str
    early_bird_date: Optional[datetime] = None
    early_bird_price: Optional[int] = None
    general_admission_price: int
    member_ticket_price: int
    max_capacity: int
    shared: bool
    created_at: datetime
    tiers: list['TicketTierResponse'] = []

    class Config:
        from_attributes = True


class EventUpdate(BaseModel):
    name: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    venue_id: Optional[UUID] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    album_url: Optional[str] = None
    track_url: Optional[str] = None
    description: Optional[str] = None
    early_bird_date: Optional[datetime] = None
    early_bird_price: Optional[int] = None
    general_admission_price: Optional[int] = None
    member_ticket_price: Optional[int] = None
    max_capacity: Optional[int] = None
    shared: Optional[bool] = None


class EventTicketCreate(BaseModel):
    person_id: UUID
    event_id: UUID
    payment_order_id: Optional[int] = None


class EventTicketResponse(BaseModel):
    id: UUID
    person_id: UUID
    event_id: UUID
    payment_order_id: Optional[int] = None
    apple_pass_url: Optional[str] = None
    google_pass_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]
    attended_at: Optional[datetime]

    class Config:
        from_attributes = True


class RegistrationRequest(BaseModel):
    pushToken: str


class UpdatedPassesResponse(BaseModel):
    serialNumbers: list[UUID]
    lastUpdated: str


class LogRequest(BaseModel):
    logs: list[str]


class SendLink(BaseModel):
    email: str
    event_id: UUID


class PaymentCreate(BaseModel):
    person_id: UUID
    event_id: Optional[UUID]
    amount: PositiveFloat
    provider: PaymentProvider
    ticket_holders: list[UUID]


class PaymentResponse(BaseModel):
    order_id: int
    person_id: UUID
    event_id: Optional[UUID] = None
    amount: float
    provider: PaymentProvider
    upstream_payment_id: Optional[UUID] = None
    status: PaymentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentUpdate(BaseModel):
    person_id: Optional[UUID] = None
    event_id: Optional[UUID] = None
    amount: Optional[float] = None
    provider: Optional[PaymentProvider] = None
    upstream_payment_id: Optional[UUID] = None
    status: Optional[PaymentStatus] = None


class CardBindingCreate(BaseModel):
    id: UUID
    person_id: UUID
    masked_card_number: str
    card_expiry_date: str
    is_active: bool


class CardBindingResponse(BaseModel):
    id: UUID
    person_id: UUID
    masked_card_number: str
    card_expiry_date: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CardBindingUpdate(BaseModel):
    person_id: Optional[UUID] = None
    masked_card_number: Optional[str] = None
    card_expiry_date: Optional[str] = None
    is_active: Optional[bool] = None


# payment providers
class VPOSInitPaymentRequest(BaseModel):
    ClientID: str
    Username: str
    Password: str
    Description: str
    OrderID: int
    Amount: float
    BackURL: Optional[str] = None
    Opaque: Optional[str | UUID] = None
    CardHolderID: Optional[str | UUID] = None


class VPOSMakeBindingPaymentRequest(BaseModel):
    ClientID: str
    Username: str
    Password: str
    Description: str
    OrderID: int
    Amount: float
    BackURL: Optional[str] = None
    Opaque: Optional[str | UUID] = None
    CardHolderID: Optional[str | UUID] = None
    PaymentType: int = 6


class VPOSMakeBindingPaymentResponse(BaseModel):
    PaymentID: str
    Amount: float
    ApprovedAmount: float
    ApprovalCode: str
    CardNumber: str
    ClientName: str
    Currency: str
    DateTime: str
    DepositedAmount: float
    Description: str
    MDOrderID: str
    ExpDate: str
    MerchantId: str
    Opaque: str
    OrderID: int
    PaymentState: str
    PaymentType: int
    PrimaryRC: str
    ResponseCode: str
    ProcessingIP: str
    rrn: str
    TerminalId: str
    TranDescription: Optional[str] = None
    OrderStatus: int
    RefundedAmount: float
    CardHolderID: str
    BindingID: str
    ActionCode: str


class VPOSBindingsRequest(BaseModel):
    ClientID: str
    Username: str
    Password: str
    PaymentType: int = 6


class VPOSCardBinding(BaseModel):
    CardHolderID: str | UUID
    CardPan: str
    ExpDate: str
    IsAvtive: bool


class VPOSBindingsResponse(BaseModel):
    ResponseCode: str
    ResponseMessage: str
    CardBindingFileds: list[VPOSCardBinding]


class VPOSDeactivateBindingRequest(BaseModel):
    ClientID: str
    Username: str
    Password: str
    PaymentType: int = 6
    CardHolderID: str | UUID


class VPOSPaymentDetailsRequest(BaseModel):
    Username: str
    Password: str
    PaymentID: UUID


class VPOSPaymentDetailsResponse(BaseModel):
    Amount: Optional[float] = None
    ApprovedAmount: Optional[float] = None
    ApprovalCode: Optional[str] = None
    CardNumber: Optional[str] = None
    ClientName: Optional[str] = None
    ClientEmail: Optional[str] = None
    Currency: Optional[str] = None
    DateTime: Optional[str] = None
    DepositedAmount: Optional[float] = None
    Description: Optional[str] = None
    MerchantId: Optional[str] = None
    Opaque: Optional[str] = None
    OrderID: Optional[int] = None
    PaymentState: Optional[str] = None
    PaymentType: Optional[int] = None
    ResponseCode: Optional[str] = None
    rrn: Optional[str] = None
    TerminalId: Optional[str] = None
    TrxnDescription: Optional[str] = None
    OrderStatus: Optional[int] = None
    RefundedAmount: Optional[float] = None
    CardHolderID: Optional[str] = None
    MDOrderID: Optional[str] = None
    PrimaryRC: Optional[str] = None
    ExpDate: Optional[str] = None
    ProcessingIP: Optional[str] = None
    BindingID: Optional[str] = None
    ActionCode: Optional[str] = None
    ExchangeRate: Optional[float] = None


class VPOSCancelPaymentRequest(BaseModel):
    Username: str
    Password: str
    PaymentID: UUID


class VPOSCancelPaymentResponse(BaseModel):
    ResponseCode: str
    ResponseMessage: str
    Opaque: Optional[str]


# myameria
class MyAmeriaCreateRequest(BaseModel):
    transactionAmount: float
    transactionId: Optional[str] = None
    merchantId: Optional[str] = None
    isBindingEnabled: bool = False
    userId: Optional[str] = None


class MyAmeriaPaymentDetailsRequest(BaseModel):
    transactionId: str
    paymentId: UUID
    merchantId: str


class MyAmeriaPaymentRefundRequest(BaseModel):
    transactionId: str
    amount: Optional[float] = None


class MyAmeriaPaymentDetailsResponse(BaseModel):
    isSuccessful: bool
    amount: float
    transactionId: str
    paymentId: UUID
    merchantId: str
    createdDate: datetime
    paymentDate: datetime
    isRefunded: bool
    refundedAmount: float
    refundedDate: Optional[datetime] = None
    bindId: Optional[UUID] = None
    labels: Optional[dict] = None


class PaymentConfirmRequest(BaseModel):
    order_id: int
    provider: PaymentProvider
    payment_id: Optional[UUID] = None
    opaque: Optional[str] = None


class PaymentConfirmResponse(BaseModel):
    order_id: int
    provider: PaymentProvider
    payment_id: Optional[UUID] = None
    status: PaymentStatus
    description: Optional[str] = None
    person_id: UUID
    event_id: UUID
    amount: int
    num_tickets: int


class ECRMItem(BaseModel):
    quantity: int
    price: int
    adgCode: Optional[str] = None
    dep: int = 1
    goodCode: str = "0001"
    goodName: str = "Մուտքավճար"
    unit: str = "հատ"


class ECRMPrintRequest(BaseModel):
    crn: int
    cardAmount: int
    cashAmount: int = 0
    partialAmount: int = 0
    prePaymentAmount: int = 0
    cashierId: int = 1
    mode: int = 2
    items: list[ECRMItem]


class ECRMCheckConnRequest(BaseModel):
    crn: int


class ECRMResult(BaseModel):
    receiptId: str
    crn: str
    sn: str
    tin: str
    taxpayer: str
    address: str
    time: int
    fiscal: str
    total: int
    change: int
    qr: str


class ECRMResponse(BaseModel):
    code: int
    message: str
    errorMessage: Optional[str] = None
    result: Optional[ECRMResult | str] = None


class TelegramMessage(BaseModel):
    chat_id: int
    text: str
    parse_mode: str = 'HTML'
    reply_markup: Optional[dict] = None


class VerifyPersonRequest(BaseModel):
    email: EmailStr
    event_id: UUID


class ValidateTokenRequest(BaseModel):
    token: str


class ValidateTokenResponse(BaseModel):
    person: PersonResponse
    event: EventResponse
    has_ticket: bool


class PersonResponseFull(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    full_name: str
    email: EmailStr
    instagram_handle: str
    telegram_handle: Optional[str] = None
    status: PersonStatus
    avatar_url: Optional[str] = None
    member_pass: MemberCardResponse | None = None
    event_tickets: list[EventTicketResponse] = []
    events_attended: int = 0
    referral_count: int = 0
    album_url: Optional[str] = None
    card_bindings: list[CardBindingResponse] = []
    is_admin: bool = False
    referer_id: Optional[UUID] = None
    payments: list[PaymentResponse] = []
    drink_vouchers: list['DrinkVoucherAdminResponse'] = []


class DrinkCreate(BaseModel):
    name: str
    price: int


class DrinkUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None


class DrinkVoucherAdminResponse(BaseModel):
    id: UUID
    drink_id: UUID
    drink_name: str
    payment_order_id: Optional[int] = None
    created_at: datetime
    used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DriveFolder(BaseModel):
    id: str
    name: str
    mime_type: str
    web_view_link: str
    person_id: Optional[UUID] = None
    member_name: Optional[str] = None
