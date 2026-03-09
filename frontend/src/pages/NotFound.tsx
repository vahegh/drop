import { Link } from 'react-router-dom'
import Layout from '../components/Layout'

export default function NotFound() {
  return (
    <Layout>
      <div className="flex flex-col items-center justify-center gap-6 min-h-[70vh] text-center">
        <img src="/static/images/404.gif" alt="404" className="w-48 rounded-3xl" />
        <div>
          <h1 className="text-3xl font-bold">404</h1>
          <p className="text-white/45 mt-1">Page not found.</p>
        </div>
        <Link to="/" className="btn-outline" style={{ width: 'auto', padding: '0 24px' }}>
          Go home
        </Link>
      </div>
    </Layout>
  )
}
