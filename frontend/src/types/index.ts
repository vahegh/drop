// Mirrors api_models.py Pydantic models

export type PersonStatus = 'pending' | 'verified' | 'rejected' | 'member'

export interface TicketTierResponse {
  id: string
  event_id: string
  name: string
  price: number
  capacity: number | null
  available_from: string | null
  available_until: string | null
  required_person_status: PersonStatus | null
  sort_order: number
  is_active: boolean
  ecrm_good_code: string | null
  ecrm_good_name: string | null
  created_at: string
}

export interface TicketTierCreate {
  name: string
  price: number
  capacity?: number
  available_from?: string
  available_until?: string
  required_person_status?: PersonStatus
  sort_order?: number
  is_active?: boolean
  ecrm_good_code?: string
  ecrm_good_name?: string
}

export interface CheckEmailResponse {
  exists: boolean
  status: PersonStatus | null
  id: string | null
  full_name: string | null
}
export type PaymentStatus = 'CREATED' | 'PENDING' | 'CONFIRMED' | 'REJECTED' | 'REFUNDED'
export type PaymentProvider = 'VPOS' | 'MYAMERIA' | 'APPLEPAY' | 'GOOGLEPAY' | 'BINDING'

export interface VenueResponse {
  id: string
  name: string
  short_name: string
  address: string
  latitude: number
  longitude: number
  google_maps_link: string
  yandex_maps_link: string
}

export interface MemberCardResponse {
  id: string
  serial_number: number
  person_id: string
  apple_pass_url: string
  google_pass_url: string
  created_at: string
  updated_at: string | null
}

export interface EventTicketResponse {
  id: string
  person_id: string
  event_id: string
  payment_order_id: number | null
  apple_pass_url: string | null
  google_pass_url: string | null
  created_at: string
  updated_at: string | null
  attended_at: string | null
}

export interface CardBindingResponse {
  id: string
  person_id: string
  masked_card_number: string
  card_expiry_date: string
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export interface PaymentResponse {
  order_id: number
  person_id: string
  event_id: string | null
  amount: number
  provider: PaymentProvider
  status: PaymentStatus
  created_at: string
  updated_at: string | null
}

export interface DrinkVoucherAdminResponse {
  id: string
  drink_id: string
  drink_name: string
  payment_order_id: number | null
  created_at: string
  used_at: string | null
}

export interface PersonRefResponse {
  id: string
  full_name: string
  status: PersonStatus
}

export interface PersonResponseFull {
  id: string
  first_name: string
  last_name: string
  full_name: string
  email: string
  instagram_handle: string
  telegram_handle: string | null
  status: PersonStatus
  avatar_url: string | null
  member_pass: MemberCardResponse | null
  event_tickets: EventTicketResponse[]
  events_attended: number
  referral_count: number
  album_url: string | null
  card_bindings: CardBindingResponse[]
  is_admin: boolean
  referer_id: string | null
  referer: PersonRefResponse | null
  referrals: PersonRefResponse[]
  payments: PaymentResponse[]
  drink_vouchers: DrinkVoucherAdminResponse[]
}

export interface EventResponse {
  id: string
  name: string
  starts_at: string
  ends_at: string
  venue_id: string
  image_url: string
  video_url: string | null
  album_url: string | null
  track_url: string | null
  description: string
  max_capacity: number
  area: string | null
  shared: boolean
  created_at: string
  tiers: TicketTierResponse[]
}

export interface PersonCreate {
  first_name: string
  last_name: string
  email: string
  instagram_handle: string
  telegram_handle?: string
  avatar_url?: string
  referer_id?: string
}

export interface PersonUpdate {
  first_name?: string
  last_name?: string
  email?: string
  instagram_handle?: string
  telegram_handle?: string
  avatar_url?: string
}

export interface DrinkResponse {
  id: string
  name: string
  price: number
  created_at: string
}

export interface PaymentConfirmRequest {
  order_id: number
  provider: PaymentProvider
  payment_id?: string
  opaque?: string
}

export interface PaymentConfirmResponse {
  order_id: number
  provider: PaymentProvider
  payment_id: string | null
  status: PaymentStatus
  description: string | null
  person_id: string
  event_id: string
  amount: number
  num_tickets: number
}

export interface InitiatePaymentRequest {
  event_id: string
  provider: PaymentProvider
  attendees: { person_id: string }[]
  drink_ids?: string[]
  save_card?: boolean
  card_id?: string
}

export interface InitiatePaymentResponse {
  order_id: number
  redirect_url: string
}

export interface PersonStats {
  [status: string]: number
}
