import { apiClient } from './client';

export async function checkIn(passId: string) {
  const res = await apiClient.post(`/api/attendance/?pass_id=${passId}`);
  return res.data;
}
