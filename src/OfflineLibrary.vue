<template>
    <Navigation active="local"/>
    <!-- Context menu rendered at click position -->
    <div
      v-if="displayBookContextMenu"
      class="context-menu"
      :style="{ left: contextMenuX + 'px', top: contextMenuY + 'px' }"
      @click.stop
      @contextmenu.prevent
    >
      <div class="context-menu-title"><b>{{
          // @ts-ignore
          displayBookContextMenu.title!
        }}</b></div>
      <button class="context-menu-item" @click="deleteBook(displayBookContextMenu)">
        🗑️ Delete from device
      </button>
    </div>

    <div style="position: relative; display: flex; flex-wrap: wrap;align-content: flex-start;overflow:auto" @click="closeModal">
      <div
        v-for="book in offlineBooks"
        :key="book.id"
        :title="book.title"
        @click.stop="goToBook(book.id!)"
        @contextmenu="openContextMenu($event, book)"
        style="cursor: pointer; position: relative">
        <BookCoverThumbnail :book="book" :image="`url(${book.cover})`"/>
      </div>
    </div>
</template>

<style>
.context-menu {
  position: fixed;
  z-index: 1000;
  background: #fff9;
  border: 1px solid rgba(0,0,0,0.08);
  box-shadow: 0 12px 24px rgba(0,0,0,0.18), 0 2px 4px rgba(0,0,0,0.12);
  border-radius: 10px;
  padding: 0.35rem;
  min-width: 220px;
  animation: cm-fade-in 120ms var(--transition-default, ease-in-out) both;
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

@keyframes cm-fade-in {
  from { opacity: 0; transform: translateY(2px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
</style>

<script setup lang="ts">
import {onMounted, onBeforeUnmount, ref} from 'vue'
import {getValuesFromIndexedDB, loadFromIndexedDB} from './dbaccess'
import BookCoverThumbnail from "./BookCoverThumbnail.vue";
import Navigation from "./Navigation.vue";

const displayBookContextMenu = ref<any>(null)
const contextMenuX = ref(0)
const contextMenuY = ref(0)

function openContextMenu(event: MouseEvent, book: any) {
  event.preventDefault()
  // position near click with simple viewport clamping
  const menuW = 200, menuH = 120
  contextMenuX.value = Math.max(0, Math.min(event.clientX, window.innerWidth - menuW))
  contextMenuY.value = Math.max(0, Math.min(event.clientY, window.innerHeight - menuH))
  displayBookContextMenu.value = book
}

function deleteBook(book: any) {
  // TODO: Delete from Device
  displayBookContextMenu.value = null
}

function closeModal() {
  displayBookContextMenu.value = null
}

// Close on escape and on window right-click elsewhere
let onKey: any, onWinClick: any
onMounted(() => {
  onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') closeModal() }
  onWinClick = () => closeModal()
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

type BookEntry = {
  id?: string
  cover?: string
  data: {
    identifier: string
    title: string
    progress?: { lastUpdated?: number }
    [k: string]: any
  }
  [k: string]: any
}

const offlineBooks = ref<BookEntry[]>([])

async function loadOfflineBooks() {
  try {
    const bks = (await getValuesFromIndexedDB('books', 'books')) as BookEntry[]
    bks.sort((a, b) => {
      const al = a?.progress?.lastUpdated ?? 0
      const bl = b?.progress?.lastUpdated ?? 0
      return bl - al
    })
    for (let book of bks) {
      // @ts-ignore
      book.cover = await loadFromIndexedDB('cover', 'cover', book.id!)
    }
    console.log(bks)
    offlineBooks.value = bks
  } catch (e) {
    console.log(e)
    window.location.href = '/#/lib'
  }
}

function goToBook(id: string) {
  window.location.href = `/#/book?id=${id}`
}

onMounted(() => {
  loadOfflineBooks()
})
</script>

