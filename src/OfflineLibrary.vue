<template>
    <Navigation active="local"/>
    <ContextMenu
      v-model="displayBookContextMenu"
      :x="contextMenuX"
      :y="contextMenuY"
      :title="displayBookContextMenu?.title"
    >
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
        <BookCoverThumbnail :book="book" :image="`url(${book.cover})`"/>
      </div>
    </div>
</template>

<style>
/* Context menu styles now live in components/ContextMenu.vue */
.context-menu-item svg { width:1.4em; height:1.4em; color: #000a; }

</style>

<script setup lang="ts">
import {onMounted, onBeforeUnmount, ref} from 'vue'
import {deleteFromIndexedDB, getValuesFromIndexedDB, loadFromIndexedDB} from './dbaccess'
import BookCoverThumbnail from "./BookCoverThumbnail.vue";
import Navigation from "./Navigation.vue";
import IconTrashBin from "../public/icons/trash-bin-minimalistic-svgrepo-com.svg"
import ContextMenu from "./components/ContextMenu.vue"
import ContextMenuItem from "./components/ContextMenuItem.vue";

const displayBookContextMenu = ref<any>(null)
const contextMenuX = ref(0)
const contextMenuY = ref(0)

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

