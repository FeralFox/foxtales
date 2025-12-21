<template>
  <Navigation active="explore" />
  <ContextMenu
    v-model="displayBookContextMenu"
    :x="contextMenuX"
    :y="contextMenuY"
    :title="displayBookContextMenu?.title"
  >
    <ContextMenuItem
      @click="addToWishlist(displayBookContextMenu!)"
      :icon="IconAddToWishlist"
    >
      Add to Wishlist
    </ContextMenuItem>
  </ContextMenu>
  <div style="width: 100%; display: flex; flex-direction: column">
    <div
      style="
        display: flex;
        padding: 1rem 1rem 0;
        align-items: center;
        position: relative;
      "
    >
      <input
        ref="search-field"
        v-on:keyup.enter="applyFilter"
        class="search-field"
        type="text"
        placeholder="search title, author or ISBN..."
      />
      <div @click="applyFilter" class="search-field-btn">
        <IconSearch />
      </div>
    </div>
    <div
      style="
        overflow: hidden;
        position: relative;
        display: flex;
        min-height: 15rem;
      "
    >
      <div style="overflow: auto" ref="book-container">
        <div style="display: flex; flex-wrap: wrap; align-content: flex-start">
          <div
            v-for="book in books"
            :key="book.id"
            @contextmenu.prevent="openContextMenu($event, book)"
            style="cursor: pointer; position: relative"
          >
            <BookCoverThumbnail
              :book="book"
              :image="`url(${book.cover_url})`"
            />
          </div>
        </div>
      </div>
      <div v-if="booksLoading" class="libraries-loading-spinner">
        <div class="spinner"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, useTemplateRef } from 'vue'
import { getKeysFromIndexedDb } from './dbaccess'
import BookCoverThumbnail from './BookCoverThumbnail.vue'
import Navigation from './Navigation.vue'
import { authHeaders, URL } from './constants'
import ContextMenu from './components/ContextMenu.vue'
import ContextMenuItem from './components/ContextMenuItem.vue'
import IconSearch from '../public/icons/magnifier-svgrepo-com.svg'
import { SearchedBook } from './interfaces'
import IconAddToWishlist from '../public/icons/add-to-wishlist-svgrepo-com.svg'

const searchField = useTemplateRef('search-field')

async function addToWishlist(book: SearchedBook) {
  displayBookContextMenu.value = null
  const response = await fetch(`${URL}/wishlist_book`, {
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    method: 'POST',
    body: JSON.stringify(book),
  })
  console.log(response.json())
}

async function fetchAsync(url: string) {
  const response = await fetch(url, { headers: authHeaders() })
  if (response.status === 401) {
    window.location.hash = '#/login'
    throw 'Authorization error - forward to login page.'
  }
  return await response.json()
}

const books = ref<SearchedBook[]>([])
const localBooks = ref<string[]>([])

const displayBookContextMenu = ref<SearchedBook | null>(null)
const contextMenuX = ref(0)
const contextMenuY = ref(0)

function openContextMenu(event: MouseEvent, book: any) {
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  displayBookContextMenu.value = book
}

function applyFilter() {
  const searchValue = searchField.value!.value
  loadBooks(true, searchValue)
}

const booksLoading = ref(false)

async function preloadBooks(filter: string) {
  localBooks.value = (await getKeysFromIndexedDb('books', 'books')) as string[]
  const fetchedBooks = await fetchAsync(
    `${URL}/explore_books?search_query=${encodeURIComponent(filter)}`,
  )
  console.log(fetchedBooks)
  books.value = fetchedBooks.result
  return fetchedBooks
}

async function loadBooks(displayLoadingOverlay: boolean, filter: string) {
  if (displayLoadingOverlay) {
    booksLoading.value = true
  }
  await preloadBooks(filter)
  booksLoading.value = false
}

// onMounted(() => {
//   loadBooks(0, true, true, '#fxtl_tags:"=wishlist"')
// })
</script>

<style scoped>
.spinner {
  width: 40px;
  height: 40px;
  border: 5px solid rgba(var(--primary-rgb), 0.2); /* light ring */
  border-top-color: rgb(var(--primary-rgb)); /* solid segment */
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
  transition: 0.2s ease-in-out;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.search-field {
  flex-grow: 1;
  padding: 0.5rem;
  border-radius: 5px;
  border: 1px solid var(--book-border);
}

.search-field-btn {
  height: 100%;
  padding: 5px;
  position: absolute;
  right: 0;
  transform: translate(-75%, 0);
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #777;
}

.search-field-btn svg {
  width: 1em;
  height: 1em;
}

.libraries-loading-spinner {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #fffa;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

@media (max-width: 640px) {
  .libraries-loading-spinner {
    margin-left: 1rem;
  }
}
</style>
