import { apiClient } from './client';

export async function getEvents() {
  const res = await apiClient.get('/api/admin/events');
  return res.data;
}

export async function getEvent(id: string) {
  const res = await apiClient.get(`/api/admin/events/${id}`);
  return res.data;
}

export async function createEvent(body: Record<string, unknown>) {
  const res = await apiClient.post('/api/admin/events', body);
  return res.data;
}

export async function updateEvent(id: string, body: Record<string, unknown>) {
  const res = await apiClient.patch(`/api/admin/events/${id}`, body);
  return res.data;
}
