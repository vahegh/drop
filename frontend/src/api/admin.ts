import axios from 'axios'

const adminClient = axios.create({
  baseURL: '/api/admin',
  withCredentials: true,
})

export const adminGetMe = () => adminClient.get('/auth/me').then(r => r.data)

export const adminGetPeople = (status?: string) =>
  adminClient.get('/people', { params: status ? { status } : undefined }).then(r => r.data)

export const adminGetPerson = (id: string) =>
  adminClient.get(`/people/${id}`).then(r => r.data)

export const adminUpdatePersonStatus = (id: string, status: string) =>
  adminClient.patch(`/people/${id}/status`, { status }).then(r => r.data)

export const adminGetEvents = () =>
  adminClient.get('/events').then(r => r.data)

export const adminGetEvent = (id: string) =>
  adminClient.get(`/events/${id}`).then(r => r.data)

export const adminCreateEvent = (body: Record<string, unknown>) =>
  adminClient.post('/events', body).then(r => r.data)

export const adminUpdateEvent = (id: string, body: Record<string, unknown>) =>
  adminClient.patch(`/events/${id}`, body).then(r => r.data)

export const adminGetVenues = () =>
  adminClient.get('/venues').then(r => r.data)

export const adminGetVenue = (id: string) =>
  adminClient.get(`/venues/${id}`).then(r => r.data)

export const adminCreateVenue = (body: Record<string, unknown>) =>
  adminClient.post('/venues', body).then(r => r.data)

export const adminUpdateVenue = (id: string, body: Record<string, unknown>) =>
  adminClient.patch(`/venues/${id}`, body).then(r => r.data)

export const adminCreatePerson = (body: Record<string, unknown>) =>
  adminClient.post('/people', body).then(r => r.data)

export const adminGetPayments = () =>
  adminClient.get('/payments').then(r => r.data)

export const adminUpdatePerson = (id: string, body: Record<string, unknown>) =>
  adminClient.patch(`/people/${id}`, body).then(r => r.data)

export const adminGetDrinks = () =>
  adminClient.get('/drinks').then(r => r.data)

export const adminCreateDrink = (body: Record<string, unknown>) =>
  adminClient.post('/drinks', body).then(r => r.data)

export const adminUpdateDrink = (id: string, body: Record<string, unknown>) =>
  adminClient.patch(`/drinks/${id}`, body).then(r => r.data)

export const adminDeletePerson = (id: string) =>
  adminClient.delete(`/people/${id}`)

export const adminDeleteEvent = (id: string) =>
  adminClient.delete(`/events/${id}`)

export const adminDeleteVenue = (id: string) =>
  adminClient.delete(`/venues/${id}`)

export const adminDeleteDrink = (id: string) =>
  adminClient.delete(`/drinks/${id}`)

export const adminDeleteTicket = (id: string) =>
  adminClient.delete(`/tickets/${id}`)

export const adminDeletePayment = (orderId: number) =>
  adminClient.delete(`/payments/${orderId}`)

export const adminRefundPayment = (orderId: number) =>
  adminClient.post(`/payments/${orderId}/refund`).then(r => r.data)

export const adminGetTiers = (eventId: string) =>
  adminClient.get(`/events/${eventId}/tiers`).then(r => r.data)

export const adminCreateTier = (eventId: string, body: Record<string, unknown>) =>
  adminClient.post(`/events/${eventId}/tiers`, body).then(r => r.data)

export const adminUpdateTier = (eventId: string, tierId: string, body: Record<string, unknown>) =>
  adminClient.patch(`/events/${eventId}/tiers/${tierId}`, body).then(r => r.data)

export const adminDeleteTier = (eventId: string, tierId: string) =>
  adminClient.delete(`/events/${eventId}/tiers/${tierId}`)

export const adminGetStats = () =>
  adminClient.get('/stats').then(r => r.data)
