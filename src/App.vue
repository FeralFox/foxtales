<script setup lang="ts">
import { ref, computed } from 'vue'
import Library from './Library.vue'
import Book from './Book.vue'
import OfflineLibrary from './OfflineLibrary.vue'
import Login from './Login.vue'
import Register from './Register.vue'
import Wishlist from './Wishlist.vue'
import Explore from './Explore.vue'

// Import all foliatejs assets for offline use.
import './modules/utils/foliatejs/fixed-layout.js'
import './modules/utils/foliatejs/paginator.js'
import './modules/utils/foliatejs/view.js'
import './modules/utils/foliatejs/overlayer.js'
import './modules/utils/foliatejs/progress.js'
import './modules/utils/foliatejs/comic-book.js'
import './modules/utils/foliatejs/epub.js'
import './modules/utils/foliatejs/epubcfi.js'
import './modules/utils/foliatejs/fb2.js'
import './modules/utils/foliatejs/mobi.js'
import './modules/utils/foliatejs/pdf.js'
import './modules/utils/foliatejs/vendor/fflate.js'
import './modules/utils/foliatejs/vendor/zip.js'
import './modules/utils/foliatejs/vendor/pdfjs/pdf.mjs'
import './modules/utils/foliatejs/vendor/pdfjs/pdf.worker.mjs'
import '/public/text_layer_builder.css'
import '/public/annotation_layer_builder.css'

const offlineRoutes = ['/', '/book', '/register', '/login']

const routes: Record<string, any> = {
  '/': OfflineLibrary,
  '/lib': Library,
  '/login': Login,
  '/register': Register,
  '/wishlist': Wishlist,
  '/explore': Explore,
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
