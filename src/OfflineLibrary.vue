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
        displayBookContextMenu.fxtl_is_read ? 'Mark as unread' : 'Mark as read'
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
import { onMounted, onBeforeUnmount, ref, toRaw } from 'vue'
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
import { syncedUpdate } from './sync'

const displayBookContextMenu = ref<any>(null)
const contextMenuX = ref(0)
const contextMenuY = ref(0)

async function toggleIsRead() {
  let new_value = !displayBookContextMenu.value.fxtl_is_read
  displayBookContextMenu.value.fxtl_is_read = new_value
  const book = displayBookContextMenu.value
  displayBookContextMenu.value = null
  await saveToBookDb('books', toRaw(book), book.uuid)
  syncedUpdate('update-read-status', book.uuid, { fxtl_is_read: new_value })
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
  [k: string]: any
}

const offlineBooks = ref<BookEntry[]>([])

async function loadOfflineBooks() {
  try {
    const bks = (await getValuesFromIndexedDB('books', 'books')) as BookEntry[]
    bks.sort((a, b) => {
      const al = Date.parse(a?.fxtl_progress_update) ?? 0
      const bl = Date.parse(b?.fxtl_progress_update) ?? 0
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
