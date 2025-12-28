<template>
  <div class="details-overlay" @click.self="props.onClose">
    <div class="details-panel" v-if="book">
      <div class="details-header">
        <a class="close-btn" @click="props.onClose" aria-label="Close"> × </a>
        <div
          class="cover"
          :style="{ backgroundImage: `url(${book.cover_url})` }"
        ></div>
        <div class="meta">
          <h2 class="title">{{ book.title }}</h2>
          <div class="authors" v-if="book.authors?.length">
            {{ book.authors }}
          </div>
          <div class="pub" v-if="year">{{ year }}</div>
          <div class="buttons">
            <slot></slot>
          </div>
        </div>
      </div>
      <div class="description" v-if="book.description">
        {{ book.description }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SearchedBook } from '../interfaces'

const props = defineProps<{
  book: SearchedBook | null | undefined
  onClose?: () => void
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

.close-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.9rem;
  background: transparent;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: inherit;
}

.details-panel {
  width: 28rem;
  max-width: 100vw;
  height: 100%;
  background: #fffc;
  color: #111;
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.15);
  padding: 1rem;
  position: relative;
  overflow: auto;
  backdrop-filter: blur(10px);
  animation: slidein 0.1s linear forwards;
}

.description {
  margin-top: 1rem;
  white-space: pre-wrap;
}

/* Mobile full-screen behavior */
@media (max-width: 640px) {
  .details-overlay {
    justify-content: center;
  }
  .details-panel {
    width: 100%;
    height: 100%;
    border-radius: 0;
  }
}

/* Sidebar / overlay styles */
.details-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: flex-end;
  z-index: 10;
}

@keyframes slidein {
  from {
    transform: translate(100%);
  }
  to {
    transform: translate(0);
  }
}
</style>
