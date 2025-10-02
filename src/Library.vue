<template>
  <Navigation active="library"/>
  <div style="display: flex; flex-wrap: wrap;align-content: flex-start;overflow:auto">
    <div class="book_card">
      <div class="upload-book">
        <IconAddBook class="add-book-icon"/>
        Upload Book
        <input class="file-upload" type="file" accept="*" @change="uploadFile"/>
      </div>
    </div>
    <div v-for="book in books" :key="book.id" @click="downloadBook(book.id)" style="cursor: pointer">
      <BookCoverThumbnail
          :book="book"
          :image="covers[book.id] ? `url(${covers[book.id]})` : ''"
      />

    </div>
  </div>
</template>

<style>
.add-book-icon {
  height: 50%;
  width: 50%;
  padding-bottom: 1rem;
  color: #777;
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
import IconAddBook from "../public/icons/education-book-add-svgrepo-com.svg"
import {authHeaders, URL} from "./constants"


async function fetchAsync(url: string) {
  const response = await fetch(url, { headers: authHeaders() })
  return await response.json()
}

interface BookMeta {
  id: string
  title: string
}

const books = ref<BookMeta[]>([])
const covers = ref<Record<string, string>>({})

async function uploadFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input?.files?.[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)
  await fetch(`${URL}/add_book`, {
    method: 'PUT',
    headers: authHeaders(),
    body: formData,
  })
  await loadBooks()
  // clear the file input so the same file can be selected again if needed
  input.value = ''
}

async function downloadBook(identifier: string) {
  const bookMetaData = await fetchAsync(`${URL}/get_book_metadata?book_id=${identifier}`)
  const format = bookMetaData.formats[0]
  const book = await fetch(`${URL}/get_book?book_id=${identifier}&format=${format}`, { headers: authHeaders() })
  const blob = await book.blob()
  const cover = await fetch(`${URL}/get_book_cover?book_id=${identifier}&data_url=true`, { headers: authHeaders() })
  const coverBase64 = await cover.text()
  console.log(`Save`, identifier, bookMetaData)
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
  books.value = fetchedBooks
  // prefetch covers as data urls (requires auth header)
  const map: Record<string, string> = {}
  await Promise.all(fetchedBooks.map(async (b: any) => {
    try {
      const resp = await fetch(`${URL}/get_book_cover?book_id=${b.id}&data_url=true`, { headers: authHeaders() })
      if (resp.ok) {
        map[b.id] = await resp.text()
      }
    } catch {}
  }))
  covers.value = map
}

onMounted(() => {
  loadBooks()
})
</script>