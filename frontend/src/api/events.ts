import client from './client'
import type { EventResponse } from '../types'

export async function getEvents(): Promise<EventResponse[]> {
  const res = await client.get<EventResponse[]>('/events')
  return res.data
}

export async function getNextEvent(): Promise<EventResponse | null> {
  const res = await client.get<EventResponse | null>('/events/next')
  return res.data
}

export async function getEvent(id: string): Promise<EventResponse> {
  const res = await client.get<EventResponse>(`/events/${id}`)
  return res.data
}

export async function getEventPhotos(id: string): Promise<string[]> {
  const res = await client.get<string[]>(`/events/${id}/photos`)
  return res.data
}

export async function getAllPhotos(): Promise<string[]> {
  const res = await client.get<string[]>('/events/photos')
  return res.data
}
