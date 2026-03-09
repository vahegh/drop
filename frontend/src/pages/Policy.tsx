import { Link } from 'react-router-dom'
import Layout from '../components/Layout'
import Section from '../components/Section'

export default function Policy() {
  return (
    <Layout showFooter>
      <Section className="pt-6">
        <h1 className="text-3xl font-bold text-center">Return Policy</h1>
      </Section>

      <Section sep>
        <div className="text-sm text-white/80 leading-relaxed w-full flex flex-col gap-4">
          <p>
            Any ticket purchased from{' '}
            <Link to="/" className="underline hover:text-white transition-colors">
              our website
            </Link>{' '}
            may be refunded until the previous day (included) of the event it is designated for.
          </p>
          <p>The return process consists of the following steps:</p>
          <ol className="list-decimal list-inside flex flex-col gap-2 text-white/70 pl-1">
            <li>
              Contact support via{' '}
              <a href="mailto:dropdeadisco@gmail.com" className="underline hover:text-white transition-colors">
                email
              </a>
            </li>
            <li>Your refund will be completed within 2–3 business days</li>
            <li>You'll receive your funds on the same card or account you made the purchase with</li>
          </ol>
        </div>
      </Section>

      <Section sep className="pb-4">
        <Link to="/" className="btn-outline">← Home</Link>
      </Section>
    </Layout>
  )
}
