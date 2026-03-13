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

export function useAdminUpdatePerson() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: Record<string, unknown> }) => api.adminUpdatePerson(id, body),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: ['admin', 'person', id] })
      qc.invalidateQueries({ queryKey: ['admin', 'people'] })
    },
  })
}

export function useAdminDrinks() {
  return useQuery({ queryKey: ['admin', 'drinks'], queryFn: api.adminGetDrinks })
}

export function useAdminCreateDrink() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.adminCreateDrink,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'drinks'] }),
  })
}

export function useAdminUpdateDrink() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: Record<string, unknown> }) => api.adminUpdateDrink(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'drinks'] }),
  })
}

export function useAdminDeletePerson() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.adminDeletePerson(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'people'] }),
  })
}

export function useAdminDeleteEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.adminDeleteEvent(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'events'] }),
  })
}

export function useAdminDeleteVenue() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.adminDeleteVenue(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'venues'] }),
  })
}

export function useAdminDeleteDrink() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.adminDeleteDrink(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'drinks'] }),
  })
}

export function useAdminDeleteTicket() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.adminDeleteTicket(id),
    onSuccess: (_data, _id, _ctx) => qc.invalidateQueries({ queryKey: ['admin', 'person'] }),
  })
}

export function useAdminDeletePayment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (orderId: number) => api.adminDeletePayment(orderId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'person'] }),
  })
}

export function useAdminRefundPayment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (orderId: number) => api.adminRefundPayment(orderId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'person'] }),
  })
}

export function useAdminTiers(eventId: string) {
  return useQuery({ queryKey: ['admin', 'tiers', eventId], queryFn: () => api.adminGetTiers(eventId), enabled: !!eventId })
}

export function useAdminCreateTier(eventId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => api.adminCreateTier(eventId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'tiers', eventId] }),
  })
}

export function useAdminUpdateTier(eventId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ tierId, body }: { tierId: string; body: Record<string, unknown> }) => api.adminUpdateTier(eventId, tierId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'tiers', eventId] }),
  })
}

export function useAdminStats() {
  return useQuery({ queryKey: ['admin', 'stats'], queryFn: api.adminGetStats })
}

export function useAdminDeleteTier(eventId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (tierId: string) => api.adminDeleteTier(eventId, tierId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'tiers', eventId] }),
  })
}
