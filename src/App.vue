<script setup lang="ts">
import { ref, computed } from 'vue'
import Library from './Library.vue'
import Book from './Book.vue'
import OfflineLibrary from "./OfflineLibrary.vue";
import Login from './Login.vue'

const offlineRoutes = ["/", "/book"]

const routes: Record<string, any> = {
  '/': OfflineLibrary,
  '/lib': Library,
  '/login': Login,
  '/book': Book
}

const currentPath = ref(window.location.hash)

window.addEventListener('hashchange', () => {
  currentPath.value = window.location.hash
})

const isAuthenticated = () => !!localStorage.getItem('auth_token')

const currentView = computed(() => {
  const stem = (currentPath.value || '').slice(1)
  const route = stem.split("?")[0] || '/'
  // Protect library and book routes
  console.log(offlineRoutes, route)
  if (!offlineRoutes.includes(route) && !isAuthenticated()) {
    if (window.location.hash !== '#/login') {
      window.location.hash = '/login'
    }
    return Login
  }
  return routes[route] || OfflineLibrary
})
</script>

<style>
.container {
  display: flex;
  height: 100vh;
}
</style>
<template>
  <div class="container">
    <component :is="currentView" />
  </div>
</template>