<template>
  <div class="ovl" :class="{ on: open }" @click.self="close">
    <div class="modal" role="dialog" aria-label="staff">
      <div style="padding:24px 26px 0">
        <h3 style="font-size:19px">{{ lbl.title }}</h3>
        <p style="font-size:13px;color:var(--text-secondary);margin-top:8px;line-height:1.6">{{ lbl.body }}</p>
      </div>
      <form style="padding:16px 26px 22px;display:flex;flex-direction:column;gap:12px" @submit.prevent="submit">
        <div class="fld">
          <label>{{ lbl.username }}</label>
          <input class="sel" style="width:100%;background-image:none;padding-right:11px" v-model="username" autocomplete="username" />
        </div>
        <div class="fld">
          <label>{{ lbl.password }}</label>
          <input class="sel" type="password" style="width:100%;background-image:none;padding-right:11px" v-model="password" autocomplete="current-password" />
        </div>
        <p v-if="error" style="font-size:12px;color:var(--red-500,#c0392b)">{{ error }}</p>
        <div style="display:flex;gap:9px;margin-top:6px">
          <button type="button" class="btn btn-ghost" style="flex:1" @click="close">{{ lbl.cancel }}</button>
          <button type="submit" class="btn btn-teal" style="flex:1" :disabled="loading">{{ loading ? '…' : lbl.go }}</button>
        </div>
        <p style="font-size:11px;color:var(--text-tertiary);text-align:center">{{ lbl.note }}</p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAir } from '../../composables/useAir.js'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({ open: { type: Boolean, default: false } })
const emit = defineEmits(['close'])

const { t, tick } = useAir()
const router = useRouter()
const auth = useAuthStore()

const lbl = computed(() => {
  void tick.value
  return {
    title: t('login_t'),
    body: t('login_b'),
    username: t('username').toUpperCase(),
    password: t('password').toUpperCase(),
    cancel: t('cancel'),
    go: t('login_go'),
    note: t('demo_note'),
  }
})

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    password.value = ''
    error.value = ''
  }
})

function close() {
  emit('close')
}

async function submit() {
  if (loading.value) return
  error.value = ''
  loading.value = true
  try {
    await auth.login({ username: username.value, password: password.value })
    close()
    router.push('/monitorimi')
  } catch (e) {
    error.value = t('login_err')
  } finally {
    loading.value = false
  }
}
</script>
