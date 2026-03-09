import { apiClient } from './client';

export async function adminLogin(email: string, password: string) {
  const res = await apiClient.post('/api/admin/auth/login', { email, password });
  return res.data as { access_token: string };
}
