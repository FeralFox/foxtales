<template>
    <Navigation active="local"/>
    <div class="modal" v-if="displayBookContextMenu">
      <div><b>{{ displayBookContextMenu.title }}</b></div>
      <button @click="deleteBook(displayBookContextMenu)">Delete from device</button>
      <button @click="closeModal">Abort</button>
    </div>
    <div style="display: flex; flex-wrap: wrap;">
      <div
        v-for="book in offlineBooks"
        :key="book.id"
        :title="book.title"
        @click="goToBook(book.id!)"
        @contextmenu="openContextMenu($event, book)"
        style="cursor: pointer;">
        <BookCoverThumbnail :book="book" :image="`url(${book.cover})`"/>
      </div>
    </div>
</template>


<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {getValuesFromIndexedDB, loadFromIndexedDB} from './dbaccess'
import BookCoverThumbnail from "./BookCoverThumbnail.vue";
import Navigation from "./Navigation.vue";

const displayBookContextMenu = ref(null)

function openContextMenu(event, book) {
  event.preventDefault()
  displayBookContextMenu.value = book
}

function deleteBook(book) {
  // TODO: Delete from Device
  displayBookContextMenu.value = null
}

function closeModal() {
  displayBookContextMenu.value = null
}

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
    window.location.href = '/#lib'
  }
}

function goToBook(id: string) {
  window.location.href = `/#book?id=${id}`
}

onMounted(() => {
  loadOfflineBooks()
})
</script>

