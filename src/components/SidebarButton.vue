<script setup lang="ts">
defineProps<{
  icon?: Object
  disabled?: boolean
  title?: string
}>()
</script>

<template>
  <button class="sidebar-btn" :disabled="disabled" :title="title">
    <component v-if="icon" :is="icon" class="icon" />
    <!--    <span><slot></slot></span>-->
  </button>
</template>

<style scoped>
.sidebar-btn {
  margin-top: 0.25rem;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.8rem;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 50%;
  background: linear-gradient(180deg, #ffffff, #f6f7f9);
  color: #222;
  cursor: pointer;
}

.icon {
  width: 1.5em;
  height: 1.5em;
}

.sidebar-btn:disabled {
  opacity: 0.7;
  cursor: default;
  color: #666;
}
</style>
