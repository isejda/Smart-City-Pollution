<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const username = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.register({ username: username.value, email: email.value, password: password.value })
    router.push('/monitorimi')
  } catch (e) {
    const data = e.response?.data
    error.value = data ? Object.values(data).flat().join(' ') : 'Registration failed.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="auth">
    <h1>Register</h1>
    <form @submit.prevent="submit">
      <label>
        Username
        <input v-model="username" required autocomplete="username" />
      </label>
      <label>
        Email
        <input v-model="email" type="email" autocomplete="email" />
      </label>
      <label>
        Password
        <input v-model="password" type="password" required autocomplete="new-password" />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="loading">{{ loading ? 'Creating account…' : 'Register' }}</button>
    </form>
    <p>Already have an account? <RouterLink to="/?staff=1">Log in</RouterLink></p>
  </main>
</template>

<style scoped>
.auth {
  max-width: 360px;
  margin: 3rem auto;
}
form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.9rem;
}
.error {
  color: #c00;
}
</style>
