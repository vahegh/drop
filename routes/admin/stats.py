from fastapi import APIRouter
from decorators import with_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from db_models import Payment, EventTicket, Event
from enums import PaymentStatus

router = APIRouter(tags=["Admin Stats"], prefix="/stats")


@router.get("")
async def get_stats():
    return await _get_stats()


@with_db
async def _get_stats(db: AsyncSession):
    # Overall revenue & confirmed payment count
    revenue_result = await db.execute(
        select(
            func.coalesce(func.sum(Payment.amount), 0).label("total_revenue"),
            func.count(Payment.order_id).label("total_payments"),
        ).where(Payment.status == PaymentStatus.CONFIRMED)
    )
    revenue_row = revenue_result.one()

    # Revenue & count by provider (confirmed only)
    provider_result = await db.execute(
        select(
            Payment.provider,
            func.count(Payment.order_id).label("count"),
            func.coalesce(func.sum(Payment.amount), 0).label("revenue"),
        )
        .where(Payment.status == PaymentStatus.CONFIRMED)
        .group_by(Payment.provider)
        .order_by(func.sum(Payment.amount).desc())
    )
    by_provider = [
        {"provider": row.provider.value, "count": row.count, "revenue": float(row.revenue)}
        for row in provider_result.all()
    ]

    # Total tickets issued
    total_tickets_result = await db.execute(select(func.count(EventTicket.id)))
    total_tickets = total_tickets_result.scalar() or 0

    # Per-event stats
    events_result = await db.execute(
        select(Event).order_by(Event.starts_at.desc())
    )
    events = events_result.scalars().all()

    events_stats = []
    for event in events:
        # Daily ticket issuance for this event
        daily_result = await db.execute(
            select(
                func.date_trunc("day", EventTicket.created_at).label("day"),
                func.count(EventTicket.id).label("count"),
            )
            .where(EventTicket.event_id == event.id)
            .group_by(text("day"))
            .order_by(text("day"))
        )
        daily_rows = daily_result.all()

        # Revenue for this event (confirmed payments)
        event_revenue_result = await db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.event_id == event.id,
                Payment.status == PaymentStatus.CONFIRMED,
            )
        )
        event_revenue = float(event_revenue_result.scalar() or 0)

        # Build daily series with running cumulative
        cumulative = 0
        daily = []
        for row in daily_rows:
            cumulative += row.count
            daily.append(
                {
                    "date": row.day.date().isoformat(),
                    "count": row.count,
                    "cumulative": cumulative,
                }
            )

        events_stats.append(
            {
                "id": str(event.id),
                "name": event.name,
                "starts_at": event.starts_at.isoformat(),
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "max_capacity": event.max_capacity,
                "ticket_count": cumulative,
                "revenue": event_revenue,
                "daily_tickets": daily,
            }
        )

    return {
        "total_revenue": float(revenue_row.total_revenue),
        "total_confirmed_payments": revenue_row.total_payments,
        "total_tickets": total_tickets,
        "by_provider": by_provider,
        "events": events_stats,
    }
