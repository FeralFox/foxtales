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
.context-menu-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  text-align: left;
  padding: 0.55rem 0.75rem;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  color: #222;
  transition: background 120ms ease, transform 60ms ease;
}
.context-menu-item:hover { background: rgba(0,0,0,0.04); }
.context-menu-item:active { transform: translateY(1px); }
.context-menu-item svg { width:1.4em; height:1.4em; color: #000a; }
</style>