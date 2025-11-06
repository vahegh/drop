from nicegui import ui
from services.auth import verify_admin_token
from fastapi import HTTPException
from frame import frame
from pages.admin_pages.venues import venues_panel, venue_details_panel
from pages.admin_pages.events import events_panel, event_details_panel
from pages.admin_pages.people import persons_panel, person_details_panel


@ui.page('/gagodzya', response_timeout=10)
@ui.page('/gagodzya/{_:path}', response_timeout=10)
async def admin_page():
    try:
        await verify_admin_token(ui.context.client.request)
    except HTTPException:
        async with frame():
            ui.label("Not authorized").classes("text-red-500")
    else:
        ui.add_css('''
<style>
    .fixed-table table {
        table-layout: fixed !important;
    }
    .fixed-table th:first-child,
    .fixed-table td:first-child {
        width: 200px !important;
    }
    .fixed-table th:not(:first-child),
    .fixed-table td:not(:first-child) {
        width: 40px !important;
        text-align: center !important;
    }
    .fixed-table td:not(:first-child) {
        padding: 4px !important;
    }
    .fixed-table td:not(:first-child) > div {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        height: 100% !important;
    }
</style>
''')
        async with frame(show_footer=False) as (main_col, _):
            main_col.classes('p-4 gap-4')
            await ui.context.client.connected()
            with ui.footer().classes('p-0'):
                with ui.tabs().classes(f'w-full bg-white text-primary').props('left-icon="none" right-icon="none" active-color="secondary"'):
                    ui.tab('events').classes('text-black').on('click',
                                                              lambda: ui.navigate.to('/gagodzya'))
                    ui.tab('people').classes('text-black').on('click',
                                                              lambda: ui.navigate.to('/gagodzya/people'))
                    ui.tab('venues').classes('text-black').on('click',
                                                              lambda: ui.navigate.to('/gagodzya/venues'))

            ui.sub_pages({
                '/gagodzya': events_panel,
                '/gagodzya/people': persons_panel,
                '/gagodzya/venues': venues_panel,
                '/gagodzya/event/{event_id}': event_details_panel,
                '/gagodzya/person/{person_id}': person_details_panel,
                '/gagodzya/venue/{venue_id}': venue_details_panel
            }).classes('h-full w-full items-center gap-4')
