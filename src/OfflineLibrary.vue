<template>
    <Navigation active="local"/>
    <ContextMenu
      v-model="displayBookContextMenu"
      :x="contextMenuX"
      :y="contextMenuY"
      :title="displayBookContextMenu?.title"
    >
      <ContextMenuItem @click="toggleIsRead()" :icon="IconBookRead">
        Toggle Read Status
      </ContextMenuItem>
      <ContextMenuItem @click="deleteBook(displayBookContextMenu)" :icon="IconTrashBin">Delete from Device</ContextMenuItem>
    </ContextMenu>

    <div style="position: relative; display: flex; flex-wrap: wrap;align-content: flex-start;overflow:auto" @click="closeModal">
      <div
        v-for="book in offlineBooks"
        :key="book.id"
        :title="book.title"
        @click.stop="goToBook(book.id!)"
        @contextmenu.prevent="openContextMenu($event, book)"
        style="cursor: pointer; position: relative">
        <div v-if="book.fxtl_is_read" class="book-is-read" />
        <BookCoverThumbnail :book="book" :image="`url(${book.cover})`"/>
      </div>
    </div>
</template>

<style>
/* Context menu styles now live in components/ContextMenu.vue */
.context-menu-item svg { width:1.4em; height:1.4em; color: #000a; }

.book-is-read {
  position: absolute;
  top: 25px;
  right: 25px;
  width: 10px;
  height: 10px;
  background: green;
  border-radius: 50%;
}
</style>

<script setup lang="ts">
import {onMounted, onBeforeUnmount, ref, toRaw} from 'vue'
import {deleteFromIndexedDB, getValuesFromIndexedDB, loadFromIndexedDB, saveToBookDb} from './dbaccess'
import BookCoverThumbnail from "./BookCoverThumbnail.vue";
import Navigation from "./Navigation.vue";
import IconTrashBin from "../public/icons/trash-bin-minimalistic-svgrepo-com.svg"
import ContextMenu from "./components/ContextMenu.vue"
import ContextMenuItem from "./components/ContextMenuItem.vue";
import IconBookRead from "../public/icons/eye-svgrepo-com.svg";
import {syncedUpdate} from "./sync";

const displayBookContextMenu = ref<any>(null)
const contextMenuX = ref(0)
const contextMenuY = ref(0)

async function toggleIsRead() {
  let new_value = !displayBookContextMenu.value.fxtl_is_read;
  displayBookContextMenu.value.fxtl_is_read = new_value
  const book = displayBookContextMenu.value
  displayBookContextMenu.value = null
  await saveToBookDb("books", toRaw(book), book.id)
  syncedUpdate("update-read-status", book.id, {fxtl_is_read: new_value})
}

function openContextMenu(event: MouseEvent, book: any) {
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  displayBookContextMenu.value = book
}

async function deleteBook(book: any) {
  displayBookContextMenu.value = null
  await deleteFromIndexedDB("books", "books", book.id.toString())
  await deleteFromIndexedDB("data", "data", book.id.toString())
  await loadOfflineBooks();
}

function closeModal() {
  displayBookContextMenu.value = null
}

// ContextMenu handles its own open/close lifecycle now

type BookEntry = {
  id?: string
  cover?: string
  fxtl: {
    progress: {
      position: number,
      last_update: number
    },
  }
  [k: string]: any
}

const offlineBooks = ref<BookEntry[]>([])

async function loadOfflineBooks() {
  try {
    const bks = (await getValuesFromIndexedDB('books', 'books')) as BookEntry[]
    bks.sort((a, b) => {
      const al = a?.fxtl.progress.last_update ?? 0
      const bl = b?.fxtl.progress.last_update ?? 0
      return bl - al
    })
    for (let book of bks) {
      // @ts-ignore
      book.cover = await loadFromIndexedDB('cover', 'cover', book.id!)
    }
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

