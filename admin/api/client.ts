import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

export const BASE_URL = 'https://dropdeadisco.com';
export const TOKEN_KEY = 'admin_token';

export const apiClient = axios.create({
  baseURL: BASE_URL,
});

apiClient.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
