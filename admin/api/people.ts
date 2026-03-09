import { apiClient } from './client';

export async function getPeople(status?: string) {
  const res = await apiClient.get('/api/admin/people', { params: status ? { status } : undefined });
  return res.data;
}

export async function updatePersonStatus(id: string, status: string) {
  const res = await apiClient.patch(`/api/admin/people/${id}/status`, { status });
  return res.data;
}
