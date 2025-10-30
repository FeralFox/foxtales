<template>
  <div class="login-container">
    <form class="login-form" @submit.prevent="onSubmit">
      <h2>Login</h2>
      <label>
        Username
        <input v-model="username" autocomplete="username" autofocus />
      </label>
      <label>
        Password
        <input
          v-model="password"
          type="password"
          autocomplete="current-password"
        />
      </label>
      <button type="submit" :disabled="loading">
        {{ loading ? 'Signing in…' : 'Sign in' }}
      </button>
      <p class="error" v-if="error">{{ error }}</p>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { URL } from './constants'

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    const body = new URLSearchParams()
    body.set('username', username.value)
    body.set('password', password.value)
    body.set('grant_type', 'password')

    const res = await fetch(`${URL}/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
    })

    if (!res.ok) {
      const msg = await res.text()
      throw new Error(msg || 'Login failed')
    }
    const data = await res.json()
    // Save token for subsequent requests
    localStorage.setItem('auth_token', data.access_token)
    // Navigate to library view
    window.location.hash = '/lib'
  } catch (e: any) {
    error.value = e?.message ?? 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 320px;
  padding: 1.5rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #fff;
}
label {
  display: flex;
  flex-direction: column;
  font-size: 0.9rem;
}
input {
  padding: 0.5rem 0.6rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}
button {
  padding: 0.6rem 0.8rem;
  background: #2d6cdf;
  color: white;
  border: 0;
  border-radius: 4px;
  cursor: pointer;
}
.error {
  color: #c00;
}
</style>
