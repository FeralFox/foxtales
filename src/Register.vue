<template>
  <div class="register-container">
    <form class="register-form" @submit.prevent="onSubmit">
      <h2>Create account</h2>

      <label>
        Username
        <input v-model.trim="username" autocomplete="username" autofocus />
      </label>

      <label>
        Email
        <input v-model.trim="email" type="email" autocomplete="email" />
      </label>

      <label>
        Password
        <input v-model="password" type="password" autocomplete="new-password" />
      </label>

      <button type="submit" :disabled="loading">
        {{ loading ? 'Creating…' : 'Create account' }}
      </button>

      <p class="hint">
        Already have an account?
        <a href="#/login">Sign in</a>
      </p>

      <p class="error" v-if="error">{{ error }}</p>
      <p class="success" v-if="success">{{ success }}</p>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { URL } from './constants'

const username = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')

const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

async function onSubmit() {
  error.value = ''
  success.value = ''

  // Basic client-side validation
  if (!username.value || !email.value || !password.value) {
    error.value = 'Please fill out username, email, and password.'
    return
  }
  if (!emailRe.test(email.value)) {
    error.value = 'Please enter a valid email address.'
    return
  }

  loading.value = true
  try {
    const params = new URLSearchParams({
      username: username.value,
      password: password.value,
      email: email.value,
    })

    const res = await fetch(`${URL}/register?${params.toString()}`, {
      method: 'POST',
    })

    if (!res.ok) {
      // backend may return text/json with error
      const msg = await res.text()
      throw new Error(msg || 'Registration failed')
    }

    // Expecting boolean true from backend on success
    const text = await res.text()
    const ok =
      text === 'true' ||
      text === 'True' ||
      text === '1' ||
      (() => {
        try {
          return Boolean(JSON.parse(text))
        } catch {
          return false
        }
      })()
    if (!ok) {
      throw new Error('Registration failed')
    }

    success.value = 'Account created! Redirecting to sign in…'
    // small delay to let user see message
    setTimeout(() => {
      window.location.hash = '/login'
    }, 900)
  } catch (e: any) {
    error.value = e?.message ?? 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* Background */
.register-container {
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
.register-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
  max-width: 420px;
  padding: 2rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  background: #ffffff;
  box-shadow:
    0 20px 25px -5px rgba(0, 0, 0, 0.08),
    0 8px 10px -6px rgba(0, 0, 0, 0.06);
  animation: cardIn 360ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

.register-form h2 {
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
  background: linear-gradient(180deg, #10b981 0%, #059669 100%);
  color: #ffffff;
  font-weight: 600;
  letter-spacing: 0.2px;
  cursor: pointer;
  transition:
    transform 120ms ease,
    filter 120ms ease,
    box-shadow 120ms ease;
  box-shadow: 0 10px 16px -8px rgba(5, 150, 105, 0.5);
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

/* Error & success */
.error,
.success {
  margin: 0.25rem 0 0;
  padding: 0.6rem 0.8rem;
  border-radius: 10px;
}

.error {
  border: 1px solid rgba(220, 38, 38, 0.25);
  background: rgba(254, 242, 242, 0.9);
  color: #991b1b;
}

.success {
  border: 1px solid rgba(16, 185, 129, 0.25);
  background: rgba(236, 253, 245, 0.9);
  color: #065f46;
}

.hint {
  margin: 0.25rem 0 0;
  font-size: 0.9rem;
  color: #475569;
}

.hint a {
  color: #2563eb;
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
