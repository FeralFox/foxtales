<template>
  <Navigation active="local" />
  <ContextMenu
    v-model="displayBookContextMenu"
    :x="contextMenuX"
    :y="contextMenuY"
    :title="displayBookContextMenu?.title"
  >
    <ContextMenuItem @click="toggleIsRead()" :icon="IconBookRead">
      {{
        displayBookContextMenu.fxtl_status.includes('read')
          ? 'Mark as unread'
          : 'Mark as read'
      }}
    </ContextMenuItem>
    <ContextMenuItem @click="toggleIsFavorite()" :icon="IconFavorite">
      {{
        displayBookContextMenu.fxtl_status.includes('favorite')
          ? 'Remove from favorite'
          : 'Mark as favorite'
      }}
    </ContextMenuItem>
    <ContextMenuItem
      @click="deleteBook(displayBookContextMenu)"
      :icon="IconTrashBin"
      >Delete from Device</ContextMenuItem
    >
  </ContextMenu>

  <div
    style="
      position: relative;
      display: flex;
      flex-wrap: wrap;
      align-content: flex-start;
      overflow: auto;
    "
    @click="closeModal"
  >
    <div
      v-for="book in offlineBooks"
      :key="book.uuid"
      :title="book.title"
      @click.stop="goToBook(book.uuid!)"
      @contextmenu.prevent="openContextMenu($event, book)"
      style="cursor: pointer; position: relative"
    >
      <BookCoverThumbnail :book="book" :image="`url(${book.cover})`" />
    </div>
  </div>
</template>

<style scoped>
/* Context menu styles now live in components/ContextMenu.vue */
.context-menu-item svg {
  width: 1.4em;
  height: 1.4em;
  color: #000a;
}
</style>

<script setup lang="ts">
import { onMounted, ref, toRaw } from 'vue'
import {
  deleteFromIndexedDB,
  getValuesFromIndexedDB,
  loadFromIndexedDB,
  saveToBookDb,
} from './dbaccess'
import BookCoverThumbnail from './BookCoverThumbnail.vue'
import Navigation from './Navigation.vue'
import IconTrashBin from '../public/icons/trash-bin-minimalistic-svgrepo-com.svg'
import ContextMenu from './components/ContextMenu.vue'
import ContextMenuItem from './components/ContextMenuItem.vue'
import IconBookRead from '../public/icons/eye-svgrepo-com.svg'
import IconFavorite from '../public/icons/favorite-filled-svgrepo-com.svg'
import { syncedUpdate } from './sync'

const displayBookContextMenu = ref<any>(null)
const contextMenuX = ref(0)
const contextMenuY = ref(0)

async function toggleIsRead() {
  const book = displayBookContextMenu.value
  let isRead = book.fxtl_status.includes('read')
  if (isRead) {
    book.fxtl_status = book.fxtl_status.filter((s: string) => s !== 'read')
  } else {
    book.fxtl_status.push('read')
  }
  displayBookContextMenu.value = null
  await saveToBookDb('books', toRaw(book), book.uuid)
  syncedUpdate('update-read-status', book.uuid, { fxtl_is_read: !isRead })
}

async function toggleIsFavorite() {
  const book = displayBookContextMenu.value
  let isFavorite = book.fxtl_status.includes('favorite')
  if (isFavorite) {
    book.fxtl_status = book.fxtl_status.filter((s: string) => s !== 'favorite')
  } else {
    book.fxtl_status.push('favorite')
  }
  displayBookContextMenu.value = null
  await saveToBookDb('books', toRaw(book), book.uuid)
  syncedUpdate('update-favorite-status', book.uuid, {
    fxtl_status: isFavorite ? '' : 'favorite',
  })
}

function openContextMenu(event: MouseEvent, book: any) {
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  displayBookContextMenu.value = book
}

async function deleteBook(book: any) {
  displayBookContextMenu.value = null
  await deleteFromIndexedDB('books', 'books', book.uuid.toString())
  await deleteFromIndexedDB('data', 'data', book.uuid.toString())
  await loadOfflineBooks()
}

function closeModal() {
  displayBookContextMenu.value = null
}

// ContextMenu handles its own open/close lifecycle now

type BookEntry = {
  id?: string
  cover?: string
  fxtl_progress_update: string
  fxtl_progress: number
  fxtl_owner: string
  fxtl_is_read: string
  [k: string]: any
}

const LIST_SORT_UNREAD_BOOKS_FIRST = true

const offlineBooks = ref<BookEntry[]>([])

async function loadOfflineBooks() {
  try {
    const bks = (await getValuesFromIndexedDB('books', 'books')) as BookEntry[]
    bks.sort((a, b) => {
      let al = Date.parse(a?.fxtl_progress_update) ?? 0
      let bl = Date.parse(b?.fxtl_progress_update) ?? 0
      if (LIST_SORT_UNREAD_BOOKS_FIRST) {
        if (a.fxtl_status.includes('read')) {
          al -= 100000000000
        }
        if (b.fxtl_status.includes('read')) {
          bl -= 100000000000
        }
      }
      return bl - al
    })
    const own_books = []
    const current_user = localStorage.getItem('current_user')
    for (let book of bks) {
      if (!current_user || current_user === book.fxtl_owner) {
        // @ts-ignore
        book.cover = await loadFromIndexedDB('cover', 'cover', book.uuid!)
        // @ts-ignore
        own_books.push(book)
      }
    }
    offlineBooks.value = own_books
  } catch (e) {
    console.log(e)
  }
}

function goToBook(id: string) {
  window.location.href = `/#/book?id=${id}`
}

onMounted(() => {
  loadOfflineBooks()
})
</script>
