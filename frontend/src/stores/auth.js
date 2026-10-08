import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { login as apiLogin, register as apiRegister } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('access_token'))
  const refreshToken = ref(localStorage.getItem('refresh_token'))
  const username = ref(localStorage.getItem('username'))

  const isAuthenticated = computed(() => !!accessToken.value)

  function setTokens({ access, refresh }) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  async function login(credentials) {
    const data = await apiLogin(credentials)
    setTokens(data)
    username.value = credentials.username
    localStorage.setItem('username', credentials.username)
  }

  async function register(payload) {
    await apiRegister(payload)
    await login({ username: payload.username, password: payload.password })
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    username.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('username')
  }

  return { accessToken, refreshToken, username, isAuthenticated, login, register, logout }
})
