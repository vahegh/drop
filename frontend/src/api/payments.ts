import client from './client'
import type {
  InitiatePaymentRequest,
  InitiatePaymentResponse,
  PaymentConfirmRequest,
  PaymentConfirmResponse,
  CardBindingResponse,
} from '../types'

export async function initiatePayment(data: InitiatePaymentRequest): Promise<InitiatePaymentResponse> {
  const res = await client.post<InitiatePaymentResponse>('/payments', data)
  return res.data
}

export async function confirmPayment(data: PaymentConfirmRequest): Promise<PaymentConfirmResponse> {
  const res = await client.post<PaymentConfirmResponse>('/payments/confirm', data)
  return res.data
}

export async function getPaymentMethods(): Promise<CardBindingResponse[]> {
  const res = await client.get<CardBindingResponse[]>('/payments/methods')
  return res.data
}

export async function addPaymentMethod(): Promise<{ redirect_url: string }> {
  const res = await client.post<{ redirect_url: string }>('/payments/methods')
  return res.data
}

export async function removePaymentMethod(id: string): Promise<void> {
  await client.delete(`/payments/methods/${id}`)
}
