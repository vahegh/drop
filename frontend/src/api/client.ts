import axios from 'axios'

const client = axios.create({
  baseURL: '/api/client',
  withCredentials: true,
})

export default client
