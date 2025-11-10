<script setup lang="ts">
import { ref, computed } from 'vue'
import Library from './Library.vue'
import Book from './Book.vue'
import OfflineLibrary from './OfflineLibrary.vue'
import Login from './Login.vue'
import Register from './Register.vue'

// Import all foliatejs assets for offline use.
import './modules/utils/foliatejs/fixed-layout.js'
import './modules/utils/foliatejs/paginator.js'
import './modules/utils/foliatejs/view.js'
import './modules/utils/foliatejs/overlayer.js'
import './modules/utils/foliatejs/progress.js'
import '/public/foliate/comic-book.js'
import '/public/foliate/epub.js'
import '/public/foliate/epubcfi.js'
import '/public/foliate/fb2.js'
import '/public/foliate/fflate.js'
import '/public/foliate/mobi.js'
import '/public/foliate/pdf.js'
import '/public/foliate/zip.js'

const offlineRoutes = ['/', '/book', '/register', '/login']

const routes: Record<string, any> = {
  '/': OfflineLibrary,
  '/lib': Library,
  '/login': Login,
  '/register': Register,
  '/book': Book,
}

const currentPath = ref(window.location.hash)

window.addEventListener('hashchange', () => {
  currentPath.value = window.location.hash
})

const isAuthenticated = () => !!localStorage.getItem('auth_token')

const currentView = computed(() => {
  const stem = (currentPath.value || '').slice(1)
  const route = stem.split('?')[0] || '/'
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

<style scoped>
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
