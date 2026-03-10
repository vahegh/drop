import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom'
import { confirmPayment } from '../api/payments'
import Layout from '../components/Layout'
import type { PaymentProvider, PaymentConfirmResponse } from '../types'
import { gtagEvent } from '../lib/analytics'

declare function fbq(...args: unknown[]): void

function providerFromPath(pathname: string): PaymentProvider {
  if (pathname.includes('ameria')) return 'MYAMERIA'
  if (pathname.includes('binding')) return 'BINDING'
  return 'VPOS'
}

export default function Callback() {
  const [params] = useSearchParams()
  const location = useLocation()
  const navigate = useNavigate()

  const [result, setResult] = useState<PaymentConfirmResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [alreadyProcessed, setAlreadyProcessed] = useState(false)

  useEffect(() => {
    // VPOS uses camelCase with capital ID (orderID, paymentID)
    // MyAmeria uses transactionId / paymentId
    // Binding payment uses order_id / payment_id
    const orderId =
      params.get('orderID') ??
      params.get('order_id') ??
      params.get('transactionId')
    const paymentId =
      params.get('paymentID') ??
      params.get('payment_id') ??
      params.get('paymentId') ??
      undefined
    const opaque = params.get('opaque') ?? undefined

    if (!orderId) {
      setError('Missing order ID.')
      return
    }

    confirmPayment({
      order_id: Number(orderId),
      provider: providerFromPath(location.pathname),
      payment_id: paymentId,
      opaque,
    })
      .then((res) => {
        setResult(res)
        if (res.status === 'CONFIRMED') {
          gtagEvent('purchase', {
            currency: 'AMD',
            value: res.amount,
            transaction_id: String(res.order_id),
            items: [{ item_id: res.event_id, price: res.amount }],
          })
          if (typeof fbq === 'function') {
            fbq('track', 'Purchase', { value: res.amount, currency: 'AMD' })
          }
        }
      })
      .catch((err) => {
        if (err?.response?.status === 409) {
          setAlreadyProcessed(true)
        } else {
          setError('Payment confirmation failed.')
        }
      })
  }, [])

  if (error) return (
    <Layout>
      <div className="flex flex-col items-center justify-center gap-6 min-h-[70vh] text-center">
        <div className="text-5xl">✗</div>
        <div>
          <p className="font-bold" style={{ color: 'var(--drop-negative)' }}>Payment failed</p>
          <p className="text-sm text-white/45 mt-1">{error}</p>
        </div>
        <button onClick={() => navigate('/')} className="btn-outline">Go home</button>
      </div>
    </Layout>
  )

  if (alreadyProcessed) return (
    <Layout>
      <div className="flex flex-col items-center justify-center gap-6 min-h-[70vh] text-center w-full max-w-96">
        <div
          className="text-6xl font-bold w-24 h-24 rounded-full flex items-center justify-center"
          style={{ background: 'rgba(0,201,81,0.15)', color: '#00c951' }}
        >
          ✓
        </div>
        <div>
          <h1 className="text-xl font-bold">Payment already processed</h1>
          <p className="text-sm text-white/55 mt-2">Your tickets have already been issued.</p>
        </div>
        <div className="flex flex-col gap-2 w-full">
          <button onClick={() => navigate('/profile')} className="btn-primary">View tickets</button>
          <button onClick={() => navigate('/')} className="btn-outline">Go home</button>
        </div>
      </div>
    </Layout>
  )

  if (!result) return (
    <Layout>
      <div className="flex items-center justify-center min-h-[70vh] text-white/45">
        Confirming payment…
      </div>
    </Layout>
  )

  const success = result.status === 'CONFIRMED'

  return (
    <Layout>
      <div className="flex flex-col items-center justify-center gap-6 min-h-[70vh] text-center w-full max-w-96">
        <div
          className="text-6xl font-bold w-24 h-24 rounded-full flex items-center justify-center"
          style={{
            background: success ? 'rgba(0,201,81,0.15)' : 'rgba(251,44,54,0.15)',
            color: success ? '#00c951' : '#fb2c36',
          }}
        >
          {success ? '✓' : '✗'}
        </div>
        <div>
          <h1 className="text-xl font-bold">{success ? 'Payment confirmed!' : 'Payment failed'}</h1>
          {success && (
            <p className="text-sm text-white/55 mt-2">
              {result.num_tickets} ticket{result.num_tickets !== 1 ? 's' : ''} issued · {result.amount.toLocaleString()} AMD
            </p>
          )}
          {!success && result.description && (
            <p className="text-sm text-white/45 mt-1">{result.description}</p>
          )}
        </div>
        <div className="flex flex-col gap-2 w-full">
          <button
            onClick={() => navigate('/profile')}
            className="btn-primary"
          >
            View tickets
          </button>
          <button onClick={() => navigate('/')} className="btn-outline">
            Go home
          </button>
        </div>
      </div>
    </Layout>
  )
}
