import { useQuery } from '@tanstack/react-query'
import { getEvents, getNextEvent, getEvent } from '../api/events'

export function useEvents() {
  return useQuery({
    queryKey: ['events'],
    queryFn: getEvents,
  })
}

export function useNextEvent() {
  return useQuery({
    queryKey: ['events', 'next'],
    queryFn: getNextEvent,
  })
}

export function useEvent(id: string) {
  return useQuery({
    queryKey: ['events', id],
    queryFn: () => getEvent(id),
    enabled: !!id,
  })
}
