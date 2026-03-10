import client from './client'
import type { PersonCreate, PersonUpdate, PersonResponseFull, PersonStats, CheckEmailResponse } from '../types'

export async function createPerson(data: PersonCreate): Promise<PersonResponseFull> {
  const res = await client.post<PersonResponseFull>('/people', data)
  return res.data
}

export async function getPersonStats(): Promise<PersonStats> {
  const res = await client.get<PersonStats>('/people/stats')
  return res.data
}

export async function checkEmail(email: string): Promise<CheckEmailResponse> {
  const res = await client.get<CheckEmailResponse>('/people/check-email', { params: { email } })
  return res.data
}

export async function checkInstagram(handle: string): Promise<{ found: boolean; username?: string; followers?: number; avatar_url?: string }> {
  const res = await client.post('/people/check-instagram', { handle })
  return res.data
}

export async function updateMe(data: PersonUpdate): Promise<PersonResponseFull> {
  const res = await client.patch<PersonResponseFull>('/people/me', data)
  return res.data
}

export async function uploadAvatar(file: File): Promise<{ avatar_url: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await client.post<{ avatar_url: string }>('/people/me/avatar', form)
  return res.data
}

export async function deleteAvatar(): Promise<void> {
  await client.delete('/people/me/avatar')
}

export async function referFriend(data: PersonCreate): Promise<PersonResponseFull> {
  const res = await client.post<PersonResponseFull>('/people/referral', data)
  return res.data
}
