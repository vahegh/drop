import axios from 'axios'

const client = axios.create({
  baseURL: '/api/client',
  withCredentials: true,
})

let isRefreshing = false
let refreshQueue: Array<(ok: boolean) => void> = []

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status !== 401 || original._retried || original.url === '/auth/refresh') {
      return Promise.reject(error)
    }

    original._retried = true

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push((ok) => {
          if (ok) resolve(client(original))
          else reject(error)
        })
      })
    }

    isRefreshing = true
    try {
      await client.post('/auth/refresh')
      refreshQueue.forEach((cb) => cb(true))
      return client(original)
    } catch {
      refreshQueue.forEach((cb) => cb(false))
      return Promise.reject(error)
    } finally {
      isRefreshing = false
      refreshQueue = []
    }
  }
)

export default client
