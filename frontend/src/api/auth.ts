import client from './client'
import type { PersonResponseFull } from '../types'

export async function getMe(): Promise<PersonResponseFull> {
  const res = await client.get<PersonResponseFull>('/auth/me')
  return res.data
}

export async function logout(): Promise<void> {
  await client.post('/auth/logout')
}

export type GoogleAuthResponse =
  | { status: 'ok' }
  | { status: 'new_user'; email: string; first_name: string; last_name: string; avatar_url: string | null }

export async function googleAuth(credential: string): Promise<GoogleAuthResponse> {
  const res = await client.post<GoogleAuthResponse>('/auth/google', { credential })
  return res.data
}

export async function signupWithGoogle(data: {
  credential: string
  first_name: string
  last_name: string
  instagram_handle: string
}): Promise<{ status: 'ok' }> {
  const res = await client.post<{ status: 'ok' }>('/auth/signup', data)
  return res.data
}
