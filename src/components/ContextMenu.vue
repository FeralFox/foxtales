<template>
  <div
    v-if="model"
    class="context-menu"
    :style="{ left: x + 'px', top: y + 'px', transform: `translate(${transformX}px, ${transformY}px)` }"
    @click.stop
    @contextmenu.prevent
    ref="context-menu"
  >
    <div v-if="title" class="context-menu-title">{{ title }}</div>
        <slot />
  </div>
</template>

<script setup lang="ts">
// Expose a MenuItem sub-component via named export and also as a property on default export using defineExpose is not possible.
// Consumers can import { MenuItem } from this file or use ContextMenu.MenuItem after Vue resolves component options.
import {onMounted, onBeforeUnmount, useTemplateRef, watch, nextTick, ref} from 'vue'


const props = defineProps<{ 
  x: number,
  y: number,
  title?: string
}>()

const transformX = ref(0)
const transformY = ref(0)

const model = defineModel<boolean | any>()

watch(model, async (newValue, old) => {
  await nextTick()
  if (newValue) {
    let rightEdge = props.x + input.value!.clientWidth + 20;
    transformX.value = Math.min(0, document.body.clientWidth - rightEdge)
    let bottomEdge = props.y + input.value!.clientHeight + 10;
    transformY.value = Math.min(0, document.body.clientHeight - bottomEdge)
    console.log("d", bottomEdge, transformY.value)
  }
})

const input = useTemplateRef('context-menu')

function close() { model.value = null }

let onKey: any, onWinClick: any
onMounted(() => {
  onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') close() }
  onWinClick = () => close()
  window.addEventListener('keydown', onKey)
  window.addEventListener('click', onWinClick)
  window.addEventListener('scroll', onWinClick, true)
  window.addEventListener('resize', onWinClick)
})
onBeforeUnmount(() => {
  if (onKey) window.removeEventListener('keydown', onKey)
  if (onWinClick) {
    window.removeEventListener('click', onWinClick)
    window.removeEventListener('scroll', onWinClick, true)
    window.removeEventListener('resize', onWinClick)
  }
})
</script>

<style scoped>
.context-menu {
  position: fixed;
  z-index: 1000;
  background: #fff9;
  border: 1px solid rgba(0,0,0,0.08);
  box-shadow: 0 12px 24px rgba(0,0,0,0.18), 0 2px 4px rgba(0,0,0,0.12);
  border-radius: 10px;
  padding: 0.35rem;
  min-width: 220px;
  animation: fade-in 120ms var(--transition-default, ease-in-out) both;
  backdrop-filter: blur(20px) saturate(140%);
}
.context-menu::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 10px;
  pointer-events: none;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.6);
}
.context-menu-title {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid rgba(0,0,0,0.2);
  margin-bottom: 0.25rem;
  color: #333;
  font-weight: 600;
  pointer-events: none;
}
</style>
