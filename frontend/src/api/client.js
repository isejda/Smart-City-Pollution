import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshing = null

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error
    const refreshToken = localStorage.getItem('refresh_token')

    if (response?.status !== 401 || config._retried || !refreshToken) {
      return Promise.reject(error)
    }
    config._retried = true

    refreshing ??= axios
      .post('/api/login/refresh/', { refresh: refreshToken })
      .then((res) => {
        localStorage.setItem('access_token', res.data.access)
        return res.data.access
      })
      .finally(() => {
        refreshing = null
      })

    try {
      const access = await refreshing
      config.headers.Authorization = `Bearer ${access}`
      return client(config)
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('username')
      return Promise.reject(error)
    }
  },
)

export default client
