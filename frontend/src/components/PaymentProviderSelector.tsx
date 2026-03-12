import type { PaymentProvider } from '../types'

export const PROVIDERS: { label: string; icon: string; value: PaymentProvider }[] = [
  { label: 'Card', icon: '/static/images/visa.svg', value: 'VPOS' },
  { label: 'MyAmeria', icon: '/static/images/myameria.png', value: 'MYAMERIA' },
  { label: 'Apple Pay', icon: '/static/images/applePay.svg', value: 'APPLEPAY' },
  { label: 'Google Pay', icon: '/static/images/google_pay.svg', value: 'GOOGLEPAY' },
]

interface Props {
  provider: PaymentProvider
  setProvider: (p: PaymentProvider) => void
  saveCard: boolean
  setSaveCard: (v: boolean) => void
}

export default function PaymentProviderSelector({ provider, setProvider, saveCard, setSaveCard }: Props) {
  return (
    <>
      <div className="flex flex-col gap-2 w-full max-w-96">
        {PROVIDERS.map((p) => (
          <button
            key={p.value}
            onClick={() => setProvider(p.value)}
            className="w-full rounded-3xl px-4 py-3 flex items-center gap-3 transition-all text-sm font-medium"
            style={{
              background: provider === p.value ? 'rgba(255,255,255,0.12)' : 'var(--drop-card)',
              border: provider === p.value ? '1px solid rgba(255,255,255,0.35)' : '1px solid rgba(255,255,255,0.18)',
            }}
          >
            <img src={p.icon} alt={p.label} className="w-8 h-5 object-contain" />
            <span>{p.label}</span>
            {provider === p.value && (
              <span className="ml-auto text-xs text-white/45">Selected</span>
            )}
          </button>
        ))}
      </div>
      {provider === 'VPOS' && (
        <label className="flex items-center gap-2 text-sm text-white/55 cursor-pointer w-full">
          <input
            type="checkbox"
            checked={saveCard}
            onChange={(e) => setSaveCard(e.target.checked)}
            className="rounded accent-white"
          />
          Save card for future payments
        </label>
      )}
    </>
  )
}
