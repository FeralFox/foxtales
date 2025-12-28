<template>
  <div class="details-header" v-if="book">
    <div class="cover" :style="{ backgroundImage: `url(${book.cover_url})` }"></div>
    <div class="meta">
      <h2 class="title">{{ book.title }}</h2>
      <div class="authors" v-if="book.authors?.length">{{ book.authors }}</div>
      <div class="pub" v-if="year">{{ year }}</div>

      <div class="buttons" v-if="buttons?.length">
        <button
          v-for="btn in buttons"
          :key="btn.key"
          class="wishlist-btn"
          :disabled="btn.disabled"
          @click.stop="$emit('action', btn.key)"
        >
          <component v-if="btn.icon" :is="btn.icon" class="icon" />
          <span>{{ btn.label }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SearchedBook } from '../interfaces'

export interface SidebarButton {
  key: string
  label: string
  icon?: any
  disabled?: boolean
}

const props = defineProps<{
  book: SearchedBook | null | undefined
  buttons?: SidebarButton[]
}>()

const year = computed(() => {
  const d = props.book?.pubdate
  if (!d) return ''
  // Try to extract 4-digit year
  const m = String(d).match(/(\d{4})/)
  return m ? m[1] : String(d)
})
</script>

<style scoped>
.details-header {
  display: flex;
  gap: 1rem;
}

.details-header .cover {
  width: 96px;
  height: 144px;
  background-size: cover;
  background-position: center;
  border: 1px solid var(--book-border);
  border-radius: 4px;
  flex-shrink: 0;
}

.details-header .meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.title {
  margin: 0;
  font-size: 1.25rem;
}

.authors,
.pub {
  color: #333;
  font-size: 0.95rem;
}

.buttons {
  margin-top: 0.5rem;
  display: flex;
  gap: 0.5rem;
}

.wishlist-btn {
  margin-top: 0.25rem;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.6rem;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 6px;
  background: linear-gradient(180deg, #ffffff, #f6f7f9);
  color: #222;
  cursor: pointer;
}

.wishlist-btn:disabled {
  opacity: 0.7;
  cursor: default;
}

.icon {
  width: 1em;
  height: 1em;
}
</style>
