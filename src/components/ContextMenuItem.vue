<script setup lang="ts">
defineProps<{
  icon?: Object
}>()
</script>

<template>
  <button class="context-menu-item">
    <component :is="icon" /> <slot></slot>
  </button>
</template>

<style scoped>

</style>