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
      :icon="IconShowDetails"
    >
      Details
    </ContextMenuItem>
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
    <!-- Recent searches chips -->
    <div v-if="recentSearches.length" class="recent-searches">
      <button
        v-if="books.length === 0"
        v-for="term in recentSearches"
        :key="term"
        class="chip"
        @click="selectRecent(term)"
      >
        {{ term }}
      </button>
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
            @click="openDetails(book)"
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
    <!-- Book details sidebar / mobile overlay -->
    <div v-if="selectedBook" class="details-overlay" @click.self="closeDetails">
      <div class="details-panel">
        <a class="close-btn" @click="closeDetails" aria-label="Close"> × </a>
        <div class="details-header">
          <div
            class="cover"
            :style="{ backgroundImage: `url(${selectedBook.cover_url})` }"
          ></div>
          <div class="meta">
            <h2 class="title">{{ selectedBook.title }}</h2>
            <div v-if="selectedBook.subtitle" class="subtitle">
              {{ selectedBook.subtitle }}
            </div>
            <div class="authors" v-if="selectedBook.authors?.length">
              {{ selectedBook.authors }}
            </div>
            <div class="pub">{{ selectedBook.pubdate }}</div>
            <div class="isbn" v-if="selectedBook.isbn">
              ISBN: {{ selectedBook.isbn }}
            </div>
            <button
              v-if="!itemOnWishlist"
              class="wishlist-btn"
              @click="addToWishlist(selectedBook)"
            >
              <IconAddToWishlist class="icon" />
              <span>Add to Wishlist</span>
            </button>
            <button
              v-if="itemOnWishlist"
              disabled
              class="wishlist-btn"
              @click="addToWishlist(selectedBook)"
            >
              <IconChecked class="icon" />
              <span>On Wishlist</span>
            </button>
          </div>
        </div>
        <div class="description" v-if="selectedBook.description">
          {{ selectedBook.description }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, useTemplateRef, onMounted } from 'vue'
import { getKeysFromIndexedDb } from './dbaccess'
import BookCoverThumbnail from './BookCoverThumbnail.vue'
import Navigation from './Navigation.vue'
import { authHeaders, URL } from './constants'
import ContextMenu from './components/ContextMenu.vue'
import ContextMenuItem from './components/ContextMenuItem.vue'
import IconSearch from '../public/icons/magnifier-svgrepo-com.svg'
import { SearchedBook } from './interfaces'
import IconAddToWishlist from '../public/icons/add-to-wishlist-svgrepo-com.svg'
import IconShowDetails from '../public/icons/details-svgrepo-com.svg'
import IconChecked from '../public/icons/check-square-svgrepo-com.svg'

const searchField = useTemplateRef('search-field')

const RECENT_KEY = 'explore_recent_searches'
const MAX_RECENT = 10
const recentSearches = ref<string[]>([])

function loadRecentSearches() {
  try {
    const raw = localStorage.getItem(RECENT_KEY)
    recentSearches.value = raw ? (JSON.parse(raw) as string[]) : []
  } catch (_) {
    recentSearches.value = []
  }
}

function saveRecentSearch(term: string) {
  const t = term.trim()
  if (!t) return
  const filtered = recentSearches.value.filter(
    (x) => x.toLowerCase() !== t.toLowerCase(),
  )
  filtered.unshift(t)
  recentSearches.value = filtered.slice(0, MAX_RECENT)
  try {
    localStorage.setItem(RECENT_KEY, JSON.stringify(recentSearches.value))
  } catch (_) {
    // ignore quota errors
  }
}

function selectRecent(term: string) {
  if (searchField.value) {
    ;(searchField.value as HTMLInputElement).value = term
  }
  loadBooks(true, term)
}

async function addToWishlist(book: SearchedBook) {
  displayBookContextMenu.value = null
  itemOnWishlist.value = true
  const response = await fetch(`${URL}/wishlist_book`, {
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    method: 'POST',
    body: JSON.stringify(book),
  })
  console.log(response)
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
const itemOnWishlist = ref(false)

const selectedBook = ref<SearchedBook | null>(null)

function openDetails(book: SearchedBook) {
  itemOnWishlist.value = false
  selectedBook.value = book
}

function closeDetails() {
  selectedBook.value = null
}

function openContextMenu(event: MouseEvent, book: any) {
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  displayBookContextMenu.value = book
}

function applyFilter() {
  const searchValue =
    (searchField.value as HTMLInputElement | null)?.value ?? ''
  saveRecentSearch(searchValue)
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
onMounted(() => {
  loadRecentSearches()
})
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

.recent-searches {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1rem 0;
}

.recent-label {
  color: #666;
  font-size: 0.9rem;
}

.chip {
  border: 1px solid var(--book-border);
  background: #fff;
  color: #333;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  cursor: pointer;
  font-size: 0.85rem;
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

.subtitle {
  color: #666;
  font-size: 0.95rem;
}

.authors,
.pub,
.isbn {
  font-size: 0.9rem;
}

.wishlist-btn {
  margin-top: 0.5rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: rgb(var(--primary-rgb));
  color: #fff;
  border: none;
  padding: 0.4rem 0.6rem;
  border-radius: 4px;
  cursor: pointer;
}

.wishlist-btn .icon {
  width: 1em;
  height: 1em;
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
</style>
