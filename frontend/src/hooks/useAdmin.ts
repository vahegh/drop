import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '../api/admin'

export function useAdminMe() {
  return useQuery({ queryKey: ['admin', 'me'], queryFn: api.adminGetMe, retry: false })
}

export function useAdminPeople(status?: string) {
  return useQuery({ queryKey: ['admin', 'people', status], queryFn: () => api.adminGetPeople(status) })
}

export function useAdminPerson(id: string) {
  return useQuery({ queryKey: ['admin', 'person', id], queryFn: () => api.adminGetPerson(id), enabled: !!id })
}

export function useAdminUpdatePersonStatus() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => api.adminUpdatePersonStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'people'] }),
  })
}

export function useAdminEvents() {
  return useQuery({ queryKey: ['admin', 'events'], queryFn: api.adminGetEvents })
}

export function useAdminEvent(id: string) {
  return useQuery({ queryKey: ['admin', 'event', id], queryFn: () => api.adminGetEvent(id), enabled: !!id })
}

export function useAdminCreateEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.adminCreateEvent,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'events'] }),
  })
}

export function useAdminUpdateEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: Record<string, unknown> }) => api.adminUpdateEvent(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'events'] }),
  })
}

export function useAdminVenues() {
  return useQuery({ queryKey: ['admin', 'venues'], queryFn: api.adminGetVenues })
}

export function useAdminVenue(id: string) {
  return useQuery({ queryKey: ['admin', 'venue', id], queryFn: () => api.adminGetVenue(id), enabled: !!id })
}

export function useAdminCreateVenue() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.adminCreateVenue,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'venues'] }),
  })
}

export function useAdminUpdateVenue() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: Record<string, unknown> }) => api.adminUpdateVenue(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'venues'] }),
  })
}

export function useAdminCreatePerson() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.adminCreatePerson,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'people'] }),
  })
}

export function useAdminPayments() {
  return useQuery({ queryKey: ['admin', 'payments'], queryFn: api.adminGetPayments })
}
