from collections import defaultdict
from datetime import timedelta, datetime, timezone
from nicegui import ui
import plotly.graph_objs as go
from plotly.graph_objs import Layout
from enums import PaymentStatus
from api_models import EventUpdate, EventCreate
from helpers import parse_inputs
from components import (primary_button, secondary_button, accented_button,
                        page_header, section_title, event_datetime_col,
                        ticket_price_col, generate_form_from_model, ticket_indicator,
                        person_card)
from services.event import create_event, update_event, delete_event, get_all_events, get_event_info
from services.venue import get_all_venues
from services.payment import get_all_payments
from services.event_ticket import get_all_tickets
from services.person import get_all_persons, get_person


async def events_panel():
    venues = await get_all_venues()
    events = await get_all_events()

    async def create():
        with ui.dialog(value=True) as dialog:
            with ui.card():
                section_title('New Event')
                form = generate_form_from_model(EventCreate, venues=venues)

                async def submit():
                    data = await parse_inputs(form, EventCreate)
                    try:
                        await create_event(EventCreate(**data))
                        ui.notify("Event created")
                        ui.navigate.reload()

                    except Exception as e:
                        ui.notify(f"Unable to create event: {str(e)}", type='negative')

                accented_button('Save').on_click(submit)
                primary_button('Cancel').on_click(dialog.close)

    with ui.row():
        ui.element('div').classes('w-[38px]')
        page_header('Events')
        ui.icon('add', size='lg', color='secondary').on('click', create)

    section_title('Ticket Purchase Trends')

    all_payments = await get_all_payments()

    payment_map = {p.order_id: p for p in all_payments}

    now = datetime.now().astimezone()

    traces = []
    event_start_info = []

    for event in events:
        event_tickets = await get_all_tickets(event.id)

        if not event_tickets:
            continue

        event_start = event.starts_at.astimezone()
        end_date = min(event_start, now)

        days_range = (end_date.date() - event.created_at.date()).days + 1

        if days_range <= 0:
            continue

        daily_counts = [0] * days_range
        daily_revenue = [0] * days_range
        refunds = 0
        processed_payments = set()

        for ticket in event_tickets:
            if ticket.payment_order_id and ticket.payment_order_id in payment_map:
                payment = payment_map[ticket.payment_order_id]
                if payment.status == PaymentStatus.REFUNDED:
                    refunds += 1
                    continue

                purchase_date = payment.created_at

                days_from_creation = (purchase_date.date() - event.created_at.date()).days

                if 0 <= days_from_creation < days_range:
                    daily_counts[days_from_creation] += 1
                    if ticket.payment_order_id not in processed_payments:
                        daily_revenue[days_from_creation] += payment.amount
                        processed_payments.add(ticket.payment_order_id)
        cumulative = []
        cumulative_revenue = []
        total = 0
        total_revenue = 0
        for i in range(days_range):
            total += daily_counts[i]
            cumulative.append(total)
            total_revenue += daily_revenue[i]
            cumulative_revenue.append(total_revenue)

        if cumulative and cumulative[-1] > 0:
            trace = go.Scatter(
                x=list(range(days_range)),
                y=cumulative,
                mode='lines+markers',
                name=event.name,
                customdata=cumulative_revenue,
                hovertemplate='<b>%{fullData.name}</b><br>' +
                'Day %{x}<br>' +
                'Tickets sold: %{y}<br>' +
                'Total revenue: %{customdata} AMD<br>' +
                '<extra></extra>'
            )
            traces.append(trace)

            event_start_day = (event_start.date() - event.created_at.date()).days
            event_start_info.append({
                'day': event_start_day,
                'trace_index': len(traces) - 1
            })

    if traces:
        fig = go.Figure(
            data=traces,
            layout=Layout(
                xaxis=dict(
                    rangemode='tozero',
                    dtick=1
                ),
                yaxis=dict(
                    rangemode='tozero'
                ),
                hovermode='closest',
                margin=dict(l=60, r=20, t=40, b=100),
                autosize=True,
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                )
            )
        )

        for info in event_start_info:
            trace_color = fig.data[info['trace_index']].line.color if hasattr(
                fig.data[info['trace_index']], 'line') else None

            fig.add_vline(
                x=info['day'],
                line_dash="dash",
                line_color=trace_color,
                opacity=0.6
            )

        ui.plotly(fig).classes('w-full h-96')
    else:
        ui.label('No ticket data available yet').classes('text-gray-500 italic')

    for e in events:
        with ui.card().classes('w-80').on('click', lambda e=e: ui.navigate.to(f'/gagodzya/event/{e.id}')).classes('w-32 cursor-pointer'):
            with ui.column().classes('w-full justify-between'):
                section_title(e.name)
                ui.label(e.starts_at.astimezone().strftime("%d %B")).classes('font-medium')


async def event_details_panel(event_id):
    event = await get_event_info(event_id)
    await get_all_persons()

    async def edit_event():
        with ui.dialog(value=True) as dialog:
            with ui.card():
                section_title('Edit Event')
                venues = await get_all_venues()
                form = generate_form_from_model(
                    EventUpdate, default_values=event.__dict__, venues=venues)

                async def submit():
                    data = await parse_inputs(form, EventUpdate)
                    try:
                        await update_event(event.id, EventUpdate(**data))
                        ui.navigate.reload()

                    except Exception as e:
                        ui.notify(f"Unable to update event: {str(e)}", type='negative')

                accented_button('Save').on_click(submit)
                primary_button('Cancel').on_click(dialog.close)

    async def delete():
        if await ui.run_javascript('confirm("Are you sure you want to delete this event?")', timeout=10):
            try:
                await delete_event(event.id)
                ui.notify('Event deleted successfully.')
                ui.navigate.to('/gagodzya/events')
            except Exception as e:
                ui.notify(f'Error deleting event: {str(e)}')

    start_datetime = event.starts_at.astimezone()
    end_datetime = event.ends_at.astimezone()

    tickets = await get_all_tickets(event.id)
    ticket_map = {t.person_id: t for t in tickets}

    total_tickets_no = len(tickets)

    persons = await get_all_persons()

    interval = timedelta(minutes=5)
    time_bins = []
    current = start_datetime

    while current <= end_datetime:
        time_bins.append(current)
        current += interval

    attendance_by_bin = defaultdict(list)
    person_map = {p.id: p for p in persons}

    people_attended = 0

    for t in tickets:
        if not t.attended_at:
            continue

        person = person_map[t.person_id]

        people_attended += 1

        delta = t.attended_at.astimezone() - start_datetime
        bin_index = int(delta.total_seconds() // (5 * 60))
        if 0 <= bin_index < len(time_bins):
            bin_time = start_datetime + timedelta(minutes=5*bin_index)
            attendance_by_bin[bin_time].append(f"{person.first_name} {person.last_name}")

    if attendance_by_bin:
        last_bin = max(attendance_by_bin)

        last_index = time_bins.index(last_bin)
        time_bins = time_bins[:last_index + 2]

    y_vals = []
    hover_texts = []

    for t in time_bins:
        y_vals.append(len(attendance_by_bin[t]))
        if attendance_by_bin[t]:
            hover_texts.append("<br>".join(attendance_by_bin[t]))
        else:
            hover_texts.append("No attendees")

    fig = go.Figure(
        data=go.Scatter(
            x=time_bins,
            y=y_vals,
            mode='lines+markers'
        ),
        layout=Layout(
            hovermode='closest',
            xaxis=dict(
                tickformat='%-I%p',
            ),
            yaxis=dict(
                rangemode='tozero',
                dtick=1,
                tick0=0
            ),
            margin=dict(l=40, r=20, t=40, b=40),
            autosize=True
        )
    )

    page_header(event.name)

    with ui.card():
        event_datetime_col(event)
        section_title('Tickets')
        ticket_price_col(event)

    primary_button('Edit').on_click(edit_event)
    secondary_button('Delete').on_click(delete)

    section_title('Attendance')

    with ui.column():
        progress = people_attended
        ui.circular_progress(value=progress, min=0, max=total_tickets_no,
                             show_value=False, color='green').classes('w-64 h-auto').props('rounded track-color="orange" thickness="0.15"')
        ui.label(f"{progress} / {total_tickets_no}").classes('text-lg')

    ui.plotly(fig).classes('w-full h-96')

    with ui.grid().classes('flex justify-center gap-2 p-0'):
        for t in sorted(ticket_map.values(), key=lambda t: (t.attended_at or datetime.min.replace(tzinfo=timezone.utc))):
            p = await get_person(t.person_id)
            with person_card(p):
                with ui.row(wrap=False).classes('items-center'):
                    ui.label(f"{p.first_name} {p.last_name}").classes('text-center')
                    ui.label(t.attended_at.astimezone().strftime(
                        "%H:%M") if t.attended_at else "").classes('text-sm ml-auto')
                    ticket_indicator(True, bool(t.attended_at))
