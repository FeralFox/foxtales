<script setup lang="ts">
import IconEye from '../../public/icons/eye-svgrepo-com.svg'
import IconFilter from '../../public/icons/filter-svgrepo-com.svg'

const props = defineProps<{
  show: boolean
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'close'): void
}>()

function toggle() {
  emit('update:modelValue', !props.modelValue)
}
</script>

<template>
  <div v-if="show" class="filter-popup-overlay" @click.self="emit('close')">
    <div class="filter-popup-panel">
      <div class="panel-header">
        <h3>Filter</h3>
        <a class="close-btn" @click="emit('close')" aria-label="Close"> × </a>
      </div>
      <div class="filter-option" @click="toggle">
        <div class="option-left">
          <IconEye class="icon" />
          <span>Only Unread</span>
        </div>
        <div class="toggle-switch" :class="{ 'is-active': modelValue }">
          <div class="toggle-handle"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.filter-popup-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  justify-content: flex-end;
  z-index: 20;
}

.filter-popup-panel {
  width: 20rem;
  max-width: 80vw;
  background: #fffc;
  color: #111;
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.15);
  padding: 1rem;
  position: relative;
  backdrop-filter: blur(10px);
  animation: expand 0.2s ease-out forwards;
  height: fit-content;
  align-self: flex-start;
  border-bottom-left-radius: 8px;
  transform-origin: top right;
}

@keyframes expand {
  from {
    transform: scale(0.5) translate(0%, -20%);
    opacity: 0;
  }
  to {
    transform: scale(1) translate(0, 0);
    opacity: 1;
  }
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.panel-header h3 {
  margin: 0;
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: #777;
  padding: 0.25rem 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 5px;
  border: 1px solid transparent;
  width: 2.2rem;
  height: 2.2rem;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #111;
}

.filter-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 0.5rem;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s;
}

.filter-option:hover {
  background: rgba(0, 0, 0, 0.05);
}

.option-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 500;
}

.icon {
  width: 1.25rem;
  height: 1.25rem;
  color: #555;
}

.toggle-switch {
  width: 2.5rem;
  height: 1.25rem;
  background-color: #939393; /* Red for disabled */
  border-radius: 1rem;
  position: relative;
  transition: background-color 0.2s;
}

.toggle-switch.is-active {
  background-color: #4caf50; /* Green for enabled */
}

.toggle-handle {
  width: 1rem;
  height: 1rem;
  background-color: white;
  border-radius: 50%;
  position: absolute;
  top: 0.125rem;
  left: 0.125rem;
  transition: transform 0.2s;
}

.toggle-switch.is-active .toggle-handle {
  transform: translateX(1.25rem);
}
</style>
