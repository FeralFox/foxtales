<script setup type="ts">
import { ref, computed } from 'vue'
import Library from './Library.vue'
import Book from './Book.vue'
import OfflineLibrary from "./OfflineLibrary.vue";

const routes = {
  '/': OfflineLibrary,
  '/lib': Library,
  'book': Book
}

const currentPath = ref(window.location.hash)

window.addEventListener('hashchange', () => {
  currentPath.value = window.location.hash
})

const currentView = computed(() => {
  const stem = currentPath.value.slice(1)
  return routes[stem.split("?")[0] || '/'] || NotFound
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