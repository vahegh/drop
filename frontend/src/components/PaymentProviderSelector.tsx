import type { PaymentProvider, CardBindingResponse } from '../types'
import { isIOS, isAndroid } from '../lib/ua'

const BASE_PROVIDERS: { label: string; icon: string; value: PaymentProvider }[] = [
  { label: 'Card', icon: '/static/images/visa.svg', value: 'VPOS' },
  { label: 'MyAmeria', icon: '/static/images/myameria.png', value: 'MYAMERIA' },
  ...(isIOS ? [{ label: 'Apple Pay', icon: '/static/images/applePay.svg', value: 'APPLEPAY' as PaymentProvider }] : []),
  ...(isAndroid ? [{ label: 'Google Pay', icon: '/static/images/google_pay.svg', value: 'GOOGLEPAY' as PaymentProvider }] : []),
]

interface Props {
  provider: PaymentProvider
  setProvider: (p: PaymentProvider) => void
  saveCard: boolean
  setSaveCard: (v: boolean) => void
  cardBinding?: CardBindingResponse | null
}

export default function PaymentProviderSelector({ provider, setProvider, saveCard, setSaveCard, cardBinding }: Props) {
  const providers: { label: string; sublabel?: string; icon: string; value: PaymentProvider }[] = [
    ...(cardBinding ? [{
      label: cardBinding.masked_card_number,
      sublabel: `exp. ${cardBinding.card_expiry_date}`,
      icon: '/static/images/visa.svg',
      value: 'BINDING' as PaymentProvider,
    }] : []),
    ...BASE_PROVIDERS,
  ]

  return (
    <>
      <div className="flex flex-col gap-2 w-full max-w-96">
        {providers.map((p) => (
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
            <span className="flex flex-col items-start">
              <span>{p.label}</span>
              {p.sublabel && <span className="text-xs text-white/40 font-normal">{p.sublabel}</span>}
            </span>
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
