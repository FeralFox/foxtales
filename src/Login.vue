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

      <p class="hint">
        Need an account?
        <a href="#/register">Sign up</a>
      </p>
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
    localStorage.setItem('current_user', username.value)
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
/* Background */
.login-container {
  width: 100%;
  min-height: 100svh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background:
    radial-gradient(
      40rem 40rem at 20% -10%,
      #e8f0ff 0%,
      rgba(232, 240, 255, 0) 60%
    ),
    radial-gradient(
      50rem 50rem at 120% 120%,
      #ffe9f0 0%,
      rgba(255, 233, 240, 0) 60%
    ),
    linear-gradient(180deg, #f8fafc 0%, #f3f4f6 100%);
}

/* Card */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
  max-width: 380px;
  padding: 2rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  background: #ffffff;
  box-shadow:
    0 20px 25px -5px rgba(0, 0, 0, 0.08),
    0 8px 10px -6px rgba(0, 0, 0, 0.06);
  animation: cardIn 360ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

.login-form h2 {
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

/* Labels & inputs */
label {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.92rem;
  color: #334155;
}

input {
  padding: 0.65rem 0.8rem;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  background: #ffffff;
  color: #0f172a;
  outline: none;
  transition:
    border-color 140ms ease,
    box-shadow 140ms ease,
    background 140ms ease;
}

input::placeholder {
  color: #9aa4b2;
}

input:hover {
  background: #fbfdff;
}

input:focus {
  border-color: #5b8cff;
  box-shadow: 0 0 0 4px rgba(45, 108, 223, 0.15);
}

/* Button */
button {
  margin-top: 0.25rem;
  padding: 0.8rem 1rem;
  border: 0;
  border-radius: 12px;
  background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  font-weight: 600;
  letter-spacing: 0.2px;
  cursor: pointer;
  transition:
    transform 120ms ease,
    filter 120ms ease,
    box-shadow 120ms ease;
  box-shadow: 0 10px 16px -8px rgba(37, 99, 235, 0.6);
}

button:hover {
  transform: translateY(-1px);
  filter: brightness(1.02);
}

button:active {
  transform: translateY(0);
  filter: brightness(0.98);
}

button[disabled] {
  filter: grayscale(0.1) brightness(0.92);
  cursor: not-allowed;
  box-shadow: none;
}

/* Error message */
.error {
  margin: 0.25rem 0 0;
  padding: 0.6rem 0.8rem;
  border: 1px solid rgba(220, 38, 38, 0.25);
  background: rgba(254, 242, 242, 0.9);
  color: #991b1b;
  border-radius: 10px;
}

@keyframes cardIn {
  from {
    transform: translateY(8px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
