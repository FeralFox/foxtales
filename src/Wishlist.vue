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

  <div
    style="width: 100%; display: flex; flex-direction: column; overflow: hidden"
  >
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
          @click="displayFilterRow = !displayFilterRow"
          class="filter-btn"
          :class="{
            'filter-btn-active': displayFilterRow,
            'filter-btn-colored': showOnlyUnread,
          }"
          title="Show filter options"
        >
          <span
            v-if="displayFilterRow"
            style="
              font-size: 1rem;
              line-height: 1;
              font-weight: 900;
              color: #555;
              transform: scale(1.3);
            "
          >
            ×
          </span>
          <template v-else>
            <IconFilterFilled v-if="showOnlyUnread" />
            <IconFilter v-else />
          </template>
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
      <div v-if="displayFilterRow" class="filter-row">
        <div class="option-left">
          <IconEye class="icon" />
          <span>Only Unread</span>
        </div>
        <div
          class="toggle-switch"
          :class="{ 'is-active': showOnlyUnread }"
          @click="toggleUnreadFilter"
        >
          <div class="toggle-handle"></div>
        </div>
        <div class="option-left">
          <IconTag class="icon" />
          <span>Tag:</span>
        </div>
        <div class="tag-input-container">
          <input
            v-model="tagSearch"
            @focus="showTagSuggestions = true"
            @blur="handleTagBlur"
            @keyup.enter="
              filteredTags.length > 0 ? selectTag(filteredTags[0]) : null
            "
            placeholder="Filter by tag..."
            class="tag-filter-input"
          />
          <button
            v-if="tagSearch"
            @click="clearTagFilter"
            class="clear-tag-btn"
          >
            ×
          </button>
          <div
            v-if="showTagSuggestions && filteredTags.length > 0"
            class="tag-suggestions"
          >
            <div
              v-for="tag in filteredTags"
              :key="tag"
              @mousedown.prevent="selectTag(tag)"
              class="tag-suggestion-item"
            >
              {{ tag }}
            </div>
          </div>
        </div>
        <div class="option-left">
          <IconAuthor class="icon" />
          <span>Author:</span>
        </div>
        <div class="tag-input-container">
          <input
            v-model="authorSearch"
            @focus="showAuthorSuggestions = true"
            @blur="handleAuthorBlur"
            @keyup.enter="
              filteredAuthors.length > 0
                ? selectAuthor(filteredAuthors[0])
                : null
            "
            placeholder="Filter by author..."
            class="tag-filter-input"
          />
          <button
            v-if="authorSearch"
            @click="clearAuthorFilter"
            class="clear-tag-btn"
          >
            ×
          </button>
          <div
            v-if="showAuthorSuggestions && filteredAuthors.length > 0"
            class="tag-suggestions"
          >
            <div
              v-for="author in filteredAuthors"
              :key="author"
              @mousedown.prevent="selectAuthor(author)"
              class="tag-suggestion-item"
            >
              {{ author }}
            </div>
          </div>
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
import { computed, nextTick, onMounted, ref, useTemplateRef } from 'vue'
import { getKeysFromIndexedDb } from '@/dbaccess'
import BookCoverThumbnail from '@/BookCoverThumbnail.vue'
import Navigation from '@/Navigation.vue'
import { URL } from '@/constants'
import ContextMenu from '@/components/ContextMenu.vue'
import ContextMenuItem from '@/components/ContextMenuItem.vue'
import { BookMeta } from '@/interfaces'
import BookDetailsSidebar from '@/components/BookDetailsSidebar.vue'
import SidebarButton from '@/components/SidebarButton.vue'
import { authHeaders, computeInitialFetchCount, fetchAsync } from '@/lib'
import IconShowDetails from '../public/icons/details-svgrepo-com.svg'
import IconList from '../public/icons/list-svgrepo-com.svg'
import IconGrid from '../public/icons/grid-svgrepo-com.svg'
import IconRemove from '../public/icons/remove-from-wishlist-svgrepo-com.svg'
import IconSearch from '../public/icons/magnifier-svgrepo-com.svg'
import IconFilter from '../public/icons/filter-svgrepo-com.svg'
import IconFilterFilled from '../public/icons/filter-filled-svgrepo-com.svg'
import IconEye from '../public/icons/eye-svgrepo-com.svg'
import IconTag from '../public/icons/tag-svgrepo-com.svg'
import IconAuthor from '../public/icons/author-svgrepo-com.svg'

const bookContainer = useTemplateRef('book-container')
const searchField = useTemplateRef('search-field')
const hiddenBookTile = useTemplateRef('book-size-reference')
const selectedBook = ref<BookMeta | null>(null)
const showOnlyUnread = ref(false)
const isListView = ref(localStorage.getItem('isListView') === 'true')
const displayFilterRow = ref(false)

const tagSearch = ref('')
const selectedTag = ref('')
const existingTags = ref<string[]>([])
const showTagSuggestions = ref(false)
const existingAuthors = ref<string[]>([])
const authorSearch = ref('')
const selectedAuthor = ref('')
const showAuthorSuggestions = ref(false)

async function fetchExistingTags() {
  try {
    const tags = await fetchAsync(`${URL}/get_tags`)
    existingTags.value = tags.sort((a, b) => a.localeCompare(b))
  } catch (e) {
    console.error('Failed to fetch existing tags:', e)
  }
}

async function fetchExistingAuthors() {
  try {
    const authors = await fetchAsync(`${URL}/get_authors`)
    existingAuthors.value = authors.sort((a, b) => a.localeCompare(b))
  } catch (e) {
    console.error('Failed to fetch existing tags:', e)
  }
}

const filteredTags = computed(() => {
  const query = tagSearch.value.toLowerCase().trim()
  if (!query) return existingTags.value
  return existingTags.value.filter((tag) => tag.toLowerCase().includes(query))
})

const filteredAuthors = computed(() => {
  const query = authorSearch.value.toLowerCase().trim()
  if (!query) return existingAuthors.value
  return existingAuthors.value.filter((tag) =>
    tag.toLowerCase().includes(query),
  )
})

function selectTag(tag: string) {
  selectedTag.value = tag
  tagSearch.value = tag
  showTagSuggestions.value = false
  applyFilter()
}

function selectAuthor(tag: string) {
  selectedAuthor.value = tag
  authorSearch.value = tag
  showAuthorSuggestions.value = false
  applyFilter()
}

function clearTagFilter() {
  selectedTag.value = ''
  tagSearch.value = ''
  showTagSuggestions.value = false
  applyFilter()
}

function clearAuthorFilter() {
  selectedAuthor.value = ''
  authorSearch.value = ''
  showAuthorSuggestions.value = false
  applyFilter()
}

function handleTagBlur() {
  setTimeout(() => (showTagSuggestions.value = false), 200)
}

function handleAuthorBlur() {
  setTimeout(() => (showAuthorSuggestions.value = false), 200)
}

function toggleUnreadFilter() {
  showOnlyUnread.value = !showOnlyUnread.value
  applyFilter()
}

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
  let filter = DEFAULT_FILTER
  if (searchValue) {
    filter = `${searchValue} and ${DEFAULT_FILTER}`
  }
  if (selectedTag.value) {
    filter = `${filter} and tags:"=${selectedTag.value}"`
  }
  if (selectedAuthor.value) {
    filter = `${filter} and authors:"=${selectedAuthor.value}"`
  }
  if (showOnlyUnread.value) {
    filter = `${filter} and #fxtl_is_read:"no"`
  }
  loadBooks(0, filter, true, true)
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
  fetchExistingTags()
  fetchExistingAuthors()
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

.list-view {
  flex-direction: column;
  width: 100%;
}

.search-field {
  flex-grow: 1;
  padding: 0.5rem;
  width: 100%;
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

.filter-btn-colored {
  color: var(--primary);
}

.filter-row {
  display: grid;
  grid-template-columns: repeat(3, auto auto) 1fr;
  padding: 0.5rem 0;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
}
@media (max-width: 640px) {
  .filter-row {
    grid-template-columns: auto 1fr;
  }
}

.filter-option {
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: background 0.2s;
}

.tag-filter-option {
  cursor: default;
}

.tag-filter-option:hover {
  background: transparent;
}

.tag-input-container {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.tag-filter-input {
  padding: 0.25rem 1.5rem 0.25rem 0.5rem;
  border-radius: 4px;
  border: 1px solid var(--book-border);
  font-size: 0.9rem;
  width: 100%;
}

.clear-tag-btn {
  position: absolute;
  padding: 0 0.4rem;
  box-shadow: none !important;
  right: 0.25rem;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.1rem;
  color: #777;
  line-height: 1;
}
.clear-tag-btn::after {
  content: none;
}

.tag-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid var(--book-border);
  border-top: none;
  border-radius: 0 0 4px 4px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 10;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.tag-suggestion-item {
  padding: 0.4rem 0.6rem;
  cursor: pointer;
  font-size: 0.9rem;
}

.tag-suggestion-item:hover {
  background: #f0f0f0;
}

.filter-option:hover {
  background: #f0f0f0;
}

.option-left {
  display: flex;
  min-width: fit-content;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.option-left .icon {
  width: 1.25rem;
  height: 1.25rem;
  color: #555;
}

.toggle-switch {
  width: 2.5rem;
  height: 1.25rem;
  background-color: #9f9f9f; /* Red for disabled */
  border-radius: 1rem;
  position: relative;
  transition: background-color 0.2s;
  justify-self: flex-end;
  cursor: pointer;
}

.toggle-switch.is-active {
  background-color: #4caf50; /* Green for enabled */
}

.toggle-handle {
  width: 1rem;
  height: 1rem;
  background-color: white;
  border-radius: 50%;
  position: absolute;
  top: 0.125rem;
  left: 0.125rem;
  transition: transform 0.2s;
}

.toggle-switch.is-active .toggle-handle {
  transform: translateX(1.25rem);
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
