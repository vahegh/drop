from nicegui import ui
from helpers import parse_inputs
from api_models import VenueCreate, VenueUpdate
from elements import (primary_button, secondary_button, accented_button,
                      page_header, section_title, generate_form_from_model)
from routes.venue import create_venue, update_venue, delete_venue, get_all_venues, get_venue_info


async def venues_panel():
    async def create_dialog():
        with ui.dialog(value=True) as dialog:
            with ui.card():
                section_title('New Venue')
                form = generate_form_from_model(VenueCreate)

                async def submit():
                    data = await parse_inputs(form, VenueCreate)
                    try:
                        await create_venue(VenueCreate(**data))
                        ui.notify("Venue created")

                    except Exception as e:
                        ui.notify(f"Unable to create venue: {str(e)}", type='negative')
                accented_button('Save').on_click(submit)
                primary_button('Cancel').on_click(dialog.close)

    with ui.row():
        ui.element('div').classes('w-[38px]')
        page_header('Venues')
        ui.icon('add', size='lg', color='secondary').on('click', create_dialog)

    venues_container = ui.column().classes('w-full')
    with venues_container:
        venues = await get_all_venues()
        for v in venues:
            with ui.card().classes('w-full').props(remove='flat').on('click', lambda v=v: ui.navigate.to(f'/gagodzya/venue/{v.id}')):
                with ui.column().classes('items-center justify-center'):
                    section_title(v.name)
                    ui.label(v.address).classes('font-medium')


async def venue_details_panel(venue_id):
    venue = await get_venue_info(venue_id)

    async def delete():
        if await ui.run_javascript('confirm("Are you sure you want to delete this venue?")', timeout=10):
            try:
                await delete_venue(venue.id)
                ui.notify('Venue deleted successfully.')
                ui.navigate.to('/gagodzya/venues')

            except Exception as e:
                ui.notify(f'Error deleting venue: {str(e)}')

    async def create_dialog():
        with ui.dialog(value=True) as dialog:
            with ui.card():
                section_title('Edit Venue')
                form = generate_form_from_model(VenueUpdate, venue.__dict__)

                async def submit():
                    data = await parse_inputs(form, VenueUpdate)
                    try:
                        await update_venue(venue.id, VenueUpdate(**data))
                        ui.navigate.reload()
                    except Exception as e:
                        ui.notify(f"Unable to update venue: {str(e)}", type='negative')
                accented_button('Save').on_click(submit)
                primary_button('Cancel').on_click(dialog.close)

    page_header(venue.name)
    ui.label(f'Address: {venue.address}')
    ui.label(f'Coordinates: {venue.latitude}, {venue.longitude}')
    ui.link("Google Maps", venue.google_maps_link)
    ui.link("Yandex Maps", venue.yandex_maps_link)

    primary_button('Edit').on_click(create_dialog)
    secondary_button('Delete').on_click(delete)
