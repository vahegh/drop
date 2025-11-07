from api_models import EventResponse, VenueResponse, PersonResponse, EventTicketResponse, MemberCardResponse, PaymentResponse
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from routes.event import get_event_info, get_all_events
from routes.venue import get_venue_info, get_all_venues
from routes.person import get_all_persons, get_person
from routes.payment import get_all_payments
from routes.event_ticket import get_all_tickets


class CacheManager:
    _events: dict[UUID, EventResponse] = {}
    _venues: dict[UUID, VenueResponse] = {}
    _persons: dict[UUID, VenueResponse] = {}
    _event_tickets: dict[UUID, list[EventTicketResponse]] = {}
    _member_passes: dict[UUID, MemberCardResponse] = {}
    _payments: dict[int, PaymentResponse] = {}

    _events_last_refresh: Optional[datetime] = None
    _venues_last_refresh: Optional[datetime] = None
    _persons_last_refresh: Optional[datetime] = None
    _event_tickets_last_refresh: Optional[datetime] = None
    _member_passes_last_refresh: Optional[datetime] = None
    _payments_last_refresh: Optional[datetime] = None
    _ttl: timedelta = timedelta(minutes=120)

    async def fetch_event(self, event_id: UUID) -> EventResponse:
        if event_id not in self._events:
            self._events[event_id] = await get_event_info(event_id)
        return self._events[event_id]

    async def fetch_venue(self, venue_id: UUID) -> VenueResponse:
        if venue_id not in self._venues:
            self._venues[venue_id] = await get_venue_info(venue_id)
        return self._venues[venue_id]

    async def fetch_all_events(self, force_refresh: bool = False) -> list[EventResponse]:
        now = datetime.now()
        cache_expired = (
            self._events_last_refresh is None or
            (now - self._events_last_refresh) > self._ttl
        )

        if not self._events or force_refresh or cache_expired:
            events = await get_all_events()
            self._events = {event.id: event for event in events}
            self._events_last_refresh = now

        return list(self._events.values())

    async def fetch_all_venues(self, force_refresh: bool = False) -> list[VenueResponse]:
        now = datetime.now()
        cache_expired = (
            self._venues_last_refresh is None or
            (now - self._venues_last_refresh) > self._ttl
        )

        if not self._venues or force_refresh or cache_expired:
            venues = await get_all_venues()
            self._venues = {venue.id: venue for venue in venues}
            self._venues_last_refresh = now

        return list(self._venues.values())

    async def fetch_next_event(self) -> Optional[EventResponse]:
        if not self._events:
            await self.get_all_events()

        if not self._events:
            return None

        now = datetime.now().astimezone()
        future_events = [e for e in self._events.values() if e.ends_at > now]

        if not future_events:
            return None

        return min(future_events, key=lambda e: e.starts_at)

    async def fetch_all_persons(self, force_refresh: bool = False) -> list[PersonResponse]:
        now = datetime.now()
        cache_expired = (
            self._persons_last_refresh is None or
            (now - self._persons_last_refresh) > self._ttl
        )

        if not self._persons or force_refresh or cache_expired:
            persons = await get_all_persons()
            self._persons = {person.id: person for person in persons}
            self._persons_last_refresh = now

        return list(self._persons.values())

    async def fetch_all_payments(self, force_refresh: bool = False):
        if not self._payments or force_refresh:
            payments = await get_all_payments()
            self._payments = {payment.order_id: payment for payment in payments}

        return list(self._payments.values())

    async def fetch_event_tickets(self, event_id: UUID, force_refresh: bool = False):
        """Get tickets for a specific event"""
        if force_refresh or event_id not in self._event_tickets:
            tickets = await get_all_tickets(event_id=event_id)
            self._event_tickets[event_id] = tickets
            return tickets

        return self._event_tickets.get(event_id, [])

    async def fetch_person(self, person_id: UUID) -> PersonResponse:
        """Get a single person by ID, fetching from API if not cached"""
        if person_id not in self._persons:
            self._persons[person_id] = await get_person(person_id)
        return self._persons[person_id]

    async def fetch_all_event_tickets(self, force_refresh: bool = False) -> list[EventTicketResponse]:
        """Get all event tickets, using cache if available and not expired"""
        now = datetime.now()
        cache_expired = (
            self._event_tickets_last_refresh is None or
            (now - self._event_tickets_last_refresh) > self._ttl
        )

        if not self._event_tickets or force_refresh or cache_expired:
            self._event_tickets = {}
            all_tickets = await get_all_tickets()
            for ticket in all_tickets:
                if ticket.event_id not in self._event_tickets:
                    self._event_tickets[ticket.event_id] = []
                self._event_tickets[ticket.event_id].append(ticket)
            self._event_tickets_last_refresh = now

        return [ticket for tickets in self._event_tickets.values() for ticket in tickets]

    @classmethod
    def clear_cache(cls):
        cls._events.clear()
        cls._venues.clear()
        cls._events_last_refresh = None
        cls._venues_last_refresh = None

    @classmethod
    def clear_events_cache(cls):
        cls._events.clear()
        cls._events_last_refresh = None

    @classmethod
    def clear_venues_cache(cls):
        cls._venues.clear()
        cls._venues_last_refresh = None

    @classmethod
    def set_ttl(cls, minutes: int):
        cls._ttl = timedelta(minutes=minutes)

    @classmethod
    def get_cache_stats(cls) -> dict:
        now = datetime.now()
        return {
            'events_count': len(cls._events),
            'venues_count': len(cls._venues),
            'events_age_seconds': (
                (now - cls._events_last_refresh).total_seconds()
                if cls._events_last_refresh else None
            ),
            'venues_age_seconds': (
                (now - cls._venues_last_refresh).total_seconds()
                if cls._venues_last_refresh else None
            ),
            'ttl_seconds': cls._ttl.total_seconds(),
        }


_cache_instance = CacheManager()


def get_cache() -> CacheManager:
    return _cache_instance
