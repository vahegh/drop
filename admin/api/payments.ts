import { apiClient } from './client';

export async function getPayments() {
  const res = await apiClient.get('/api/admin/payments');
  return res.data;
}
