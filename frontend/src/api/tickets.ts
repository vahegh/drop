import client from './client'
import type { EventTicketResponse } from '../types'

export async function getTickets(eventId?: string): Promise<EventTicketResponse[]> {
  const res = await client.get<EventTicketResponse[]>('/tickets', {
    params: eventId ? { event_id: eventId } : undefined,
  })
  return res.data
}
