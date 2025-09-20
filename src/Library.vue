<template>
    <Navigation/>
    <div style="display: flex; flex-wrap: wrap;">
      <div
          style="padding: 5px; margin: 1rem; font-weight: bold; white-space: nowrap; text-overflow: ellipsis; overflow: hidden; width: 15em; height: 23em;">
        <div class="upload-book">
          <img class="add-book-icon" src="/public/icons/education-book-add-svgrepo-com.svg" />
          Upload Book
          <input class="file-upload" type="file" accept="*" @change="uploadFile" />
        </div>
      </div>
      <div v-for="book in books" :key="book.id" @click="downloadBook(book.id)" style="cursor: pointer">
        <BookCoverThumbnail
            :book="book"
            :image="`url(${URL}/get_book_cover?book_id=${book.id})`"
        />
      </div>
    </div>
</template>

<style>
.add-book-icon {
  width: 40%;
  padding-bottom:1rem;
}
.file-upload {
  height: 100%;
  width: 100%;
  opacity: 0;
  position: absolute;
  top: 0;
  left: 0;
  cursor: pointer;
}
.upload-book {
  position: relative;
  width: 100%;
  height: calc(100% - 2rem);
  border: 2px dashed #0009;
  border-radius: 5px;
  margin-bottom: 5px;
  color: #0009;
  display: flex;
  justify-content: center;
  flex-direction: column;
  font-size: 140%;
  align-items: center;
  font-weight: bold;
  cursor: pointer
}
</style>

<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {saveToIndexedDB} from './dbaccess'
import BookCoverThumbnail from "./BookCoverThumbnail.vue";
import Navigation from "./Navigation.vue";

const URL = 'http://localhost:8000'

async function fetchAsync(url: string) {
  const response = await fetch(url)
  return await response.json()
}

interface BookMeta {
  id: string
  title: string
}

const books = ref<BookMeta[]>([])

async function uploadFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input?.files?.[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)
  await fetch(`${URL}/add_book`, {
    method: 'PUT',
    body: formData,
  })
  await loadBooks()
  // clear the file input so the same file can be selected again if needed
  input.value = ''
}

async function downloadBook(identifier: string) {
  const bookMetaData = await fetchAsync(`${URL}/get_book_metadata?book_id=${identifier}`)
  const format = bookMetaData.formats[0]
  const book = await fetch(`${URL}/get_book?book_id=${identifier}&format=${format}`)
  const blob = await book.blob()
  const cover = await fetch(`${URL}/get_book_cover?book_id=${identifier}&data_url=true`)
  const coverBase64 = await cover.text()
  console.log(`Save`, identifier,  bookMetaData)
  await saveToIndexedDB(
      'books',
      'books',
      bookMetaData,
      identifier
  )
  await saveToIndexedDB(`cover`, 'cover', coverBase64, identifier)
  await saveToIndexedDB(`data`, 'data', blob, identifier)
}

async function loadBooks() {
  const fetchedBooks = await fetchAsync(`${URL}/list_books`)
  console.log(fetchedBooks)
  books.value = fetchedBooks
}

onMounted(() => {
  loadBooks()
})
</script>