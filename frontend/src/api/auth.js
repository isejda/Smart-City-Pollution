import client from './client'

export function register(payload) {
  return client.post('register/', payload).then((res) => res.data)
}

export function login(credentials) {
  return client.post('login/', credentials).then((res) => res.data)
}

export function refreshAccessToken(refresh) {
  return client.post('login/refresh/', { refresh }).then((res) => res.data)
}
