<template>
  <Navigation active="wishlist" />
  <ContextMenu
    v-model="displayBookContextMenu"
    :x="contextMenuX"
    :y="contextMenuY"
    :title="displayBookContextMenu?.title"
  >
    <ContextMenuItem
      @click="openDetails(displayBookContextMenu!)"
      :icon="IconShowDetails"
    >
      Display Details
    </ContextMenuItem>
    <ContextMenuItem
      @click="confirmRemoveBook(displayBookContextMenu!.uuid)"
      :icon="IconRemove"
    >
      Remove from Wishlist
    </ContextMenuItem>
  </ContextMenu>

  <div style="width: 100%; display: flex; flex-direction: column">
    <div
      style="
        display: flex;
        padding: 1rem 1rem 0;
        align-items: stretch;
        position: relative;
        flex-direction: column;
      "
    >
      <div style="display: flex; flex-grow: 1">
        <div style="flex-grow: 1; position: relative; display: flex">
          <input
            ref="search-field"
            v-on:keyup.enter="applyFilter"
            class="search-field"
            type="text"
            placeholder="Filter..."
          />
          <div @click="applyFilter" class="search-field-btn">
            <IconSearch />
          </div>
        </div>
        <div
          @click="toggleListView"
          class="filter-btn"
          :class="{ 'filter-btn-active': isListView }"
          title="Toggle list/grid view"
          style="margin-left: 0.5rem"
        >
          <IconList v-if="!isListView" />
          <IconGrid v-if="isListView" />
        </div>
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
      <div
        style="overflow: auto; flex-grow: 1"
        @scroll="onScroll"
        ref="book-container"
      >
        <div
          style="display: flex; flex-wrap: wrap; align-content: flex-start"
          :class="{ 'list-view': isListView }"
        >
          <div
            class="book_card"
            ref="book-size-reference"
            v-if="!isListView"
          ></div>
          <div
            v-for="book in books"
            :key="book.uuid"
            @contextmenu.prevent="openContextMenu($event, book)"
            style="cursor: pointer; position: relative"
            :class="{ 'list-item': isListView }"
          >
            <BookCoverThumbnail
              :book="book"
              @click="openDetails(book)"
              :display-book-downloaded-icon="
                localBooks.includes(book.uuid.toString())
              "
              :image="covers[book.uuid] ? `url(${covers[book.uuid]})` : ''"
              :is-list-view="isListView"
            />
          </div>
        </div>
      </div>
      <div v-if="booksLoading" class="libraries-loading-spinner">
        <div class="spinner"></div>
      </div>
    </div>
  </div>

  <div v-if="showDeleteModal" class="modal" @click.stop>
    <div style="font-weight: 600">Remove from Wishlist</div>
    <div>Are you sure you want to remove this book from your wishlist?</div>
    <div
      style="
        display: flex;
        gap: 8px;
        justify-content: flex-end;
        margin-top: 8px;
      "
    >
      <button
        @click="cancelRemoveBook"
        :disabled="isDeleting"
        class="btn-ghost"
      >
        Cancel
      </button>
      <button
        @click="removeBookConfirmed"
        :disabled="isDeleting"
        class="btn-danger"
      >
        {{ isDeleting ? 'Removing…' : 'Remove' }}
      </button>
    </div>
  </div>
  <BookDetailsSidebar
    v-if="selectedBook"
    :book="selectedBook"
    :buttons="[]"
    @action="() => {}"
    :onClose="closeDetails"
    @update="(newTags) => handleBookUpdate(selectedBook, newTags)"
  >
    <SidebarButton
      :icon="IconRemove"
      @click="confirmRemoveBook(selectedBook!.uuid)"
      title="Remove from Wishlist"
    >
    </SidebarButton>
  </BookDetailsSidebar>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref, useTemplateRef } from 'vue'
import { getKeysFromIndexedDb } from './dbaccess'
import BookCoverThumbnail from './BookCoverThumbnail.vue'
import Navigation from './Navigation.vue'
import { authHeaders, URL } from './constants'
import ContextMenu from './components/ContextMenu.vue'
import ContextMenuItem from './components/ContextMenuItem.vue'
import IconRemove from '../public/icons/remove-from-wishlist-svgrepo-com.svg'
import IconSearch from '../public/icons/magnifier-svgrepo-com.svg'
import { BookMeta } from './interfaces'
import BookDetailsSidebar from './components/BookDetailsSidebar.vue'
import SidebarButton from './components/SidebarButton.vue'
import IconShowDetails from '../public/icons/details-svgrepo-com.svg'
import IconList from '../public/icons/list-svgrepo-com.svg'
import IconGrid from '../public/icons/grid-svgrepo-com.svg'
import { computeInitialFetchCount } from './lib'

const bookContainer = useTemplateRef('book-container')
const searchField = useTemplateRef('search-field')
const hiddenBookTile = useTemplateRef('book-size-reference')
const selectedBook = ref<BookMeta | null>(null)
const isListView = ref(localStorage.getItem('isListView') === 'true')

async function toggleListView() {
  isListView.value = !isListView.value
  localStorage.setItem('isListView', isListView.value.toString())
  await nextTick()
  hiddenBookTile.value!.style.display = 'none'
}

async function openDetails(book) {
  displayBookContextMenu.value = null
  selectedBook.value = book
}

function closeDetails() {
  selectedBook.value = null
}

function handleBookUpdate(book: BookMeta | null, newTags: string[]) {
  if (book) {
    book.tags = newTags
  }
}

async function postAsync(url: string, data: object) {
  const response = await fetch(`${URL}/set_book_metadata`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(data),
  })
  return await response.json()
}

async function fetchAsync(url: string) {
  const response = await fetch(url, { headers: authHeaders() })
  if (response.status === 401) {
    window.location.hash = '#/login'
    throw 'Authorization error - forward to login page.'
  }
  return await response.json()
}

const books = ref<BookMeta[]>([])
const localBooks = ref<string[]>([])
const covers = ref<Record<string, string>>({})

const displayBookContextMenu = ref<BookMeta | null>(null)
const contextMenuX = ref(0)
const contextMenuY = ref(0)

function openContextMenu(event: MouseEvent, book: any) {
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  displayBookContextMenu.value = book
}

const showDeleteModal = ref(false)
const bookIdPendingDelete = ref<string | null>(null)
const isDeleting = ref(false)

function confirmRemoveBook(identifier: string) {
  displayBookContextMenu.value = null
  bookIdPendingDelete.value = identifier
  showDeleteModal.value = true
}

async function removeBookConfirmed() {
  selectedBook.value = null
  if (!bookIdPendingDelete.value) return
  const identifier = bookIdPendingDelete.value
  isDeleting.value = true
  try {
    const status_removed = await fetchAsync(
      `${URL}/remove_book?book_uuid=${identifier}`,
    )
    if (status_removed.success) {
      const newBooks: BookMeta[] = []
      for (let book of books.value) {
        if (book.uuid !== identifier) newBooks.push(book)
      }
      books.value = newBooks
    }
  } finally {
    isDeleting.value = false
    showDeleteModal.value = false
    bookIdPendingDelete.value = null
  }
}

function cancelRemoveBook() {
  showDeleteModal.value = false
  bookIdPendingDelete.value = null
}

function applyFilter() {
  const searchValue = searchField.value!.value
  if (searchValue) {
    loadBooks(0, `#fxtl_tags:"=wishlist" and ${searchValue}`, true, true)
  } else {
    loadBooks(0, `#fxtl_tags:"=wishlist"`, true, true)
  }
}

const BOOKS_TO_PREFETCH = 10
const booksLoading = ref(false)

async function preloadBooks(
  filter: string | undefined,
  start_from: number,
  initialFetch: boolean | undefined,
  booksToFetch?: number,
) {
  booksToFetch = booksToFetch || BOOKS_TO_PREFETCH
  localBooks.value = (await getKeysFromIndexedDb('books', 'books')) as string[]
  let filterUrl = ''
  if (filter) {
    filterUrl = `&search_query=${encodeURIComponent(filter)}`
  }
  const fetchedBooks = await fetchAsync(
    `${URL}/list_books?max_items=${booksToFetch}
    &start_from=${start_from}${filterUrl}`,
  )
  // Immediately display all books as soon as they are available.
  if (start_from === 0) {
    covers.value = {}
    books.value = fetchedBooks
  } else {
    books.value = [...books.value, ...fetchedBooks]
  }

  // Wait for all books and covers to be displayed - then render everything
  // - then check if there are scrollbars.
  // Then check if we need to fetch more books to fill the page.
  await nextTick()
  let hasScrollBars =
    bookContainer.value!.scrollHeight > bookContainer.value!.clientHeight + 150
  let mightHaveAdditionalBooks = fetchedBooks.length === booksToFetch
  if (initialFetch && !hasScrollBars && mightHaveAdditionalBooks) {
    return [
      ...fetchedBooks,
      ...(await preloadBooks(filter, start_from + booksToFetch, true)),
    ]
  } else {
    return fetchedBooks
  }
}

async function loadBooks(
  start_from: number,
  filter: string,
  displayLoadingOverlay?: boolean,
  initialFetch?: boolean,
  booksToFetch?: number,
) {
  current_filter = filter
  if (displayLoadingOverlay) {
    booksLoading.value = true
  }
  const fetchedBooks = await preloadBooks(
    filter,
    start_from,
    initialFetch,
    booksToFetch,
  )
  booksLoading.value = false

  // Fetch covers as data urls
  await Promise.all(
    fetchedBooks.map(async (b: any) => {
      try {
        const resp = await fetch(
          `${URL}/get_book_cover?book_uuid=${b.uuid}&data_url=true`,
          { headers: authHeaders() },
        )
        if (resp.ok) {
          const cover = await resp.text()
          covers.value[b.uuid] = cover
          b.cover_url = cover
        }
      } catch {}
    }),
  )

  scrollEventDisabled = false
}

let scrollEventDisabled = false

function onScroll() {
  if (scrollEventDisabled) {
    return
  }
  let maxScrollHeight =
    bookContainer.value!.scrollHeight - bookContainer.value!.clientHeight
  let scrollHeight = bookContainer.value!.scrollTop
  let scrollBottom = maxScrollHeight - scrollHeight
  if (scrollBottom < 200) {
    if (scrollEventDisabled) {
      return
    }
    scrollEventDisabled = true
    loadBooks(books.value.length, current_filter, false, false)
  }
}

const DEFAULT_FILTER = '#fxtl_tags:"=wishlist"'
let current_filter = DEFAULT_FILTER
onMounted(async () => {
  // Ensure DOM is ready to measure tile and container sizes
  await nextTick()
  let booksToDisplay
  try {
    booksToDisplay = computeInitialFetchCount(
      hiddenBookTile.value,
      bookContainer.value,
      BOOKS_TO_PREFETCH,
    )
    hiddenBookTile.value!.style.display = 'none'
  } catch (e) {
    booksToDisplay = 30
  }
  loadBooks(0, DEFAULT_FILTER, true, true, booksToDisplay)
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

.book_card.list-item {
  width: 100%;
  margin: 0;
  height: auto;
}

.list-view {
  flex-direction: column;
  width: 100%;
}

.search-field {
  flex-grow: 1;
  padding: 0.5rem;
  border-radius: 5px;
  border: 1px solid var(--book-border);
}

.search-field-btn {
  height: 100%;
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

.filter-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
  margin-left: 0.5rem;
  cursor: pointer;
  color: #777;
  border: 1px solid var(--book-border);
  border-radius: 5px;
  background: white;
  transition: all 0.2s ease;
  min-width: 1.2rem;
}

.filter-btn:hover {
  background: #f5f5f5;
  color: var(--primary);
}

.filter-btn-active {
  color: var(--primary);
  border-color: var(--primary);
  background: rgba(var(--primary-rgb), 0.1);
}

.filter-btn svg {
  width: 1.2em;
  height: 1.2em;
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
.list-item {
  width: calc(100% - 1rem);
  transition: 0.2s ease-in-out;
  border-radius: 5px;
  margin: 0.5rem;
}
.list-item:hover {
  background-color: var(--list-item-bg);
}

.search-field-btn svg {
  width: 1em;
  height: 1em;
}
</style>
