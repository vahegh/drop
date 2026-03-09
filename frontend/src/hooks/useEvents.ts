import { useQuery } from '@tanstack/react-query'
import { getEvents, getNextEvent, getEvent, getEventPhotos, getAllPhotos } from '../api/events'

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

export function useEventPhotos(id: string, enabled: boolean) {
  return useQuery({
    queryKey: ['events', id, 'photos'],
    queryFn: () => getEventPhotos(id),
    enabled: !!id && enabled,
    staleTime: 1000 * 60 * 50, // 50 min — URLs expire in ~1h
  })
}

export function useAllPhotos() {
  return useQuery({
    queryKey: ['photos'],
    queryFn: getAllPhotos,
    staleTime: 1000 * 60 * 50,
  })
}
