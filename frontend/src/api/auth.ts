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
  | { status: 'new_user'; token: string; email: string; first_name: string; last_name: string }

export async function googleAuth(access_token: string): Promise<GoogleAuthResponse> {
  const res = await client.post<GoogleAuthResponse>('/auth/google', { access_token })
  return res.data
}

export type MagicLinkResponse =
  | { status: 'ok' }
  | { status: 'new_user'; token: string; email: string }

export async function sendMagicLink(email: string): Promise<MagicLinkResponse> {
  const res = await client.post<MagicLinkResponse>('/auth/magic-link', { email })
  return res.data
}

export async function signup(data: {
  token: string
  first_name: string
  last_name: string
  instagram_handle: string
}): Promise<{ status: 'ok' }> {
  const res = await client.post<{ status: 'ok' }>('/auth/signup', data)
  return res.data
}
