<template>
  <Navigation active="shelf" />
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
      @click="downloadBook(displayBookContextMenu!.uuid)"
      :icon="IconDownload"
      :disabled="localBooks.includes(displayBookContextMenu!.uuid.toString())"
    >
      Download to Device
    </ContextMenuItem>
    <ContextMenuItem
      @click="toggleIsRead(displayBookContextMenu)"
      :icon="IconBookRead"
    >
      {{
        displayBookContextMenu!.fxtl_is_read ? 'Mark as unread' : 'Mark as read'
      }}
    </ContextMenuItem>
    <ContextMenuItem
      @click="confirmRemoveBook(displayBookContextMenu!.uuid)"
      :icon="IconRemove"
    >
      Remove from Shelf
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
    <div style="overflow: hidden; position: relative; display: flex">
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
            ref="upload-book"
            :class="{ 'list-item': isListView }"
            v-if="!isListView"
          >
            <div class="upload-book">
              <IconAddBook class="add-book-icon" />
              <div v-if="!isUploading">Upload Book</div>
              <div v-else class="progress-container">
                <div class="progress-label">
                  Uploading... {{ uploadProgress }}%
                </div>
                <div class="progress-bar">
                  <div
                    class="progress-bar-fill"
                    :style="{ width: uploadProgress + '%' }"
                  ></div>
                </div>
              </div>
              <input
                :disabled="isUploading"
                class="file-upload"
                type="file"
                multiple
                accept="*"
                @change="uploadFile"
              />
            </div>
            <div v-if="uploadError" class="upload-error">{{ uploadError }}</div>
          </div>
          <div
            v-for="book in books"
            :key="book.uuid"
            @click="openDetails(book)"
            @contextmenu.prevent="openContextMenu($event, book)"
            style="cursor: pointer; position: relative"
            :class="{ 'list-item': isListView }"
          >
            <div
              v-if="downloadingId === book.uuid"
              class="download-overlay"
              @click.stop
            >
              <div
                class="spinner spinner-with-progress"
                :style="{
                  background: `conic-gradient(rgb(var(--primary-rgb)) 0deg, rgb(var(--primary-rgb)) ${Math.round(downloadProgress * 3.6)}deg, rgba(0,0,0,0) 0) border-box`,
                }"
              ></div>
            </div>
            <div
              v-if="downloadQueue.includes(book.uuid)"
              class="download-overlay"
              @click.stop
            >
              <div class="spinner"></div>
            </div>
            <BookCoverThumbnail
              :book="book"
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
    <div style="font-weight: 600">Remove from Shelf</div>
    <div>Are you sure you want to remove this book from your Shelf?</div>
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
      :icon="IconDownload"
      @click="downloadBook(selectedBook.uuid)"
      title="Download to Device"
      :loading="
        downloadQueue.includes(selectedBook.uuid.toString()) ||
        downloadingId === selectedBook.uuid.toString()
      "
      :disabled="
        downloadQueue.includes(selectedBook.uuid.toString()) ||
        downloadingId === selectedBook.uuid.toString() ||
        localBooks.includes(selectedBook.uuid.toString())
      "
    >
    </SidebarButton>
    <SidebarButton
      :icon="selectedBook.fxtl_is_read ? IconBookRead : IconBookUnread"
      @click="toggleIsRead(selectedBook)"
      :title="selectedBook.fxtl_is_read ? 'Mark as unread' : 'Mark as read'"
    >
    </SidebarButton>
    <SidebarButton
      :icon="IconRemove"
      @click="confirmRemoveBook(selectedBook!.uuid)"
      title="Remove from Shelf"
    >
    </SidebarButton>
  </BookDetailsSidebar>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, toRaw, useTemplateRef } from 'vue'
import {
  getKeysFromIndexedDb,
  loadFromBookDb,
  saveToBookDb,
  saveToIndexedDB,
} from '@/dbaccess'
import BookCoverThumbnail from '@/BookCoverThumbnail.vue'
import Navigation from '@/Navigation.vue'
import { URL } from '@/constants'
import ContextMenu from '@/components/ContextMenu.vue'
import { syncedUpdate } from '@/sync'
import { BookMeta } from '@/interfaces'
import SidebarButton from '@/components/SidebarButton.vue'
import BookDetailsSidebar from '@/components/BookDetailsSidebar.vue'
import ContextMenuItem from '@/components/ContextMenuItem.vue'
import { authHeaders, computeInitialFetchCount, fetchAsync } from '@/lib'
import IconAddBook from '../public/icons/education-book-add-svgrepo-com.svg'
import IconDownload from '../public/icons/download-svgrepo-com.svg'
import IconRemove from '../public/icons/trash-bin-minimalistic-svgrepo-com.svg'
import IconSearch from '../public/icons/magnifier-svgrepo-com.svg'
import IconBookRead from '../public/icons/eye-svgrepo-com.svg'
import IconBookUnread from '../public/icons/eye-filled-svgrepo-com.svg'
import IconShowDetails from '../public/icons/details-svgrepo-com.svg'
import IconFilter from '../public/icons/filter-svgrepo-com.svg'
import IconFilterFilled from '../public/icons/filter-filled-svgrepo-com.svg'
import IconEye from '../public/icons/eye-svgrepo-com.svg'
import IconTag from '../public/icons/tag-svgrepo-com.svg'
import IconAuthor from '../public/icons/author-svgrepo-com.svg'
import IconList from '../public/icons/list-svgrepo-com.svg'
import IconGrid from '../public/icons/grid-svgrepo-com.svg'

const bookContainer = useTemplateRef('book-container')
const uploadBook = useTemplateRef('upload-book')
const searchField = useTemplateRef('search-field')
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

onMounted(() => {
  fetchExistingTags()
  fetchExistingAuthors()
})

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
  showTagSuggestions.value = false
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
const downloadingId = ref<string>('')
const downloadQueue = ref<string[]>([])
const downloadProgress = ref(0)
const downloadError = ref('')
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadError = ref('')

const displayBookContextMenu = ref<BookMeta | null>(null)
const contextMenuX = ref(0)
const contextMenuY = ref(0)

function openContextMenu(event: MouseEvent, book: any) {
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  displayBookContextMenu.value = book
}

function toggleUnreadFilter() {
  showOnlyUnread.value = !showOnlyUnread.value
  applyFilter()
}

function toggleListView() {
  isListView.value = !isListView.value
  localStorage.setItem('isListView', isListView.value.toString())
}

async function uploadFile(event: Event) {
  const input = event.target as HTMLInputElement
  const files = input?.files || []
  if (files.length === 0) return

  const totalBooks = files.length
  const progressOneBook = 1 / totalBooks
  let currentBook = 0
  uploadProgress.value = 0

  for (let file of Object.values(files)) {
    const formData = new FormData()
    formData.append('file', file)

    // Reset state
    isUploading.value = true
    uploadError.value = ''

    try {
      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhr.open('PUT', `${URL}/add_book`)

        // Set auth headers from authHeaders()
        const headers = authHeaders()
        if (headers instanceof Headers) {
          headers.forEach((value, key) => xhr.setRequestHeader(key, value))
        } else if (Array.isArray(headers)) {
          headers.forEach(([key, value]) => xhr.setRequestHeader(key, value))
        } else if (headers && typeof headers === 'object') {
          Object.entries(headers).forEach(([key, value]) => {
            xhr.setRequestHeader(key, value)
          })
        }

        // Progress events
        xhr.upload.onprogress = (e: ProgressEvent) => {
          if (e.lengthComputable) {
            const progressAllFiles = currentBook / totalBooks
            const progressCurrentFile = e.loaded / e.total
            const totalProgress =
              progressAllFiles + progressCurrentFile * progressOneBook
            uploadProgress.value = Math.min(
              100,
              Math.round(totalProgress * 100),
            )
          }
        }

        xhr.onload = () => {
          // Accept 200-299 range
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve()
          } else {
            reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`))
          }
        }

        xhr.onerror = () => reject(new Error('Network error during upload'))
        xhr.onabort = () => reject(new Error('Upload aborted'))

        xhr.send(formData)
      })

      await loadBooks(0, SHELF_DEFAULT_FILTER, false, true)
    } catch (e: any) {
      console.error(e)
      uploadError.value = e?.message || 'Upload failed'
    } finally {
      // clear the file input so the same file can be selected again if needed
      currentBook += 1
      if (input) input.value = ''
      // small delay to let user see 100%
      if (currentBook === totalBooks) {
        setTimeout(() => {
          isUploading.value = false
          uploadProgress.value = 0
        }, 400)
      }
    }
  }
}

const showDeleteModal = ref(false)
const bookIdPendingDelete = ref<string | null>(null)
const isDeleting = ref(false)

async function toggleIsRead(book) {
  let new_value = !book.fxtl_is_read
  book!.fxtl_is_read = new_value
  displayBookContextMenu.value = null

  if (await loadFromBookDb('books', book!.uuid, null)) {
    await saveToBookDb('books', toRaw(book), book!.uuid)
  }

  setTimeout(
    () =>
      syncedUpdate('update-read-status', book!.uuid, {
        fxtl_is_read: new_value,
      }),
    500,
  )
}

function confirmRemoveBook(identifier: string) {
  displayBookContextMenu.value = null
  bookIdPendingDelete.value = identifier
  showDeleteModal.value = true
}

async function removeBookConfirmed() {
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

async function downloadBook(uuid: string) {
  if (downloadingId.value) {
    downloadQueue.value.push(uuid)
    return
  }

  // reset and show overlay for this book
  displayBookContextMenu.value = null
  downloadingId.value = uuid
  downloadProgress.value = 0
  downloadError.value = ''
  try {
    const bookMetaData = await fetchAsync(
      `${URL}/get_book_metadata?book_uuid=${uuid}`,
    )
    const bookAnnotationsResponse = await fetchAsync(
      `${URL}/get_book_annotations?book_uuid=${uuid}`,
    )
    const format = bookMetaData.formats?.[0]

    // Download book blob with progress using XHR
    const blob: Blob = await new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('GET', `${URL}/get_book?book_uuid=${uuid}&format=${format}`)

      const headers = authHeaders()
      if (headers instanceof Headers) {
        headers.forEach((value, key) => xhr.setRequestHeader(key, value))
      } else if (Array.isArray(headers)) {
        headers.forEach(([key, value]) => xhr.setRequestHeader(key, value))
      } else if (headers && typeof headers === 'object') {
        Object.entries(headers).forEach(([key, value]) => {
          xhr.setRequestHeader(key, value)
        })
      }

      xhr.responseType = 'blob'
      xhr.onprogress = (e: ProgressEvent) => {
        if (e.lengthComputable) {
          downloadProgress.value = Math.min(
            100,
            Math.round((e.loaded / e.total) * 100),
          )
        }
      }
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          downloadProgress.value = 100
          resolve(xhr.response)
        } else {
          reject(new Error(`Download failed: ${xhr.status} ${xhr.statusText}`))
        }
      }
      xhr.onerror = () => reject(new Error('Network error during download'))
      xhr.onabort = () => reject(new Error('Download aborted'))
      xhr.send()
    })

    const cover = await fetch(
      `${URL}/get_book_cover?book_uuid=${uuid}&data_url=true`,
      { headers: authHeaders() },
    )
    const coverBase64 = await cover.text()
    bookMetaData.fxtl_owner =
      bookMetaData.fxtl_owner || localStorage.getItem('current_user')

    // Save all to IndexedDB
    await saveToIndexedDB('books', 'books', bookMetaData, uuid)
    await saveToIndexedDB(`cover`, 'cover', coverBase64, uuid)
    await saveToIndexedDB(`data`, 'data', blob, uuid)
    const annotations = {}
    for (let annotation of bookAnnotationsResponse.annotations) {
      if (!annotations[annotation.index]) {
        annotations[annotation.index] = []
      }
      annotations[annotation.index].push(annotation)
    }
    await saveToIndexedDB('books', 'annotations', annotations, uuid)
    localBooks.value.push(bookMetaData.uuid.toString())
  } catch (e: any) {
    console.error(e)
    downloadError.value = e?.message || 'Download failed'
  } finally {
    // allow the user to see 100% briefly
    setTimeout(() => {
      downloadingId.value = ''
      downloadProgress.value = 0
      if (downloadQueue.value.length > 0) {
        const nextBookToDownload = downloadQueue.value.shift()
        downloadBook(nextBookToDownload!)
      }
    }, 400)
  }
}

const SHELF_DEFAULT_FILTER = `not #fxtl_tags:"=wishlist"`

function applyFilter() {
  const searchValue = searchField.value!.value
  let filter = SHELF_DEFAULT_FILTER
  if (searchValue) {
    filter = `${searchValue} and ${SHELF_DEFAULT_FILTER}`
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
let current_filter = SHELF_DEFAULT_FILTER

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
    bookContainer.value!.scrollHeight > bookContainer.value!.clientHeight + 100
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

onMounted(async () => {
  // Ensure DOM is ready to measure tile and container sizes
  await nextTick()
  await loadBooks(
    0,
    SHELF_DEFAULT_FILTER,
    true,
    true,
    computeInitialFetchCount(
      uploadBook.value,
      bookContainer.value,
      BOOKS_TO_PREFETCH,
    ),
  )
})
</script>

<style scoped>
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
  height: calc(100% - 3.1rem);
  border: 2px dashed var(--book-border);
  border-radius: 5px;
  margin-bottom: 5px;
  color: #0009;
  display: flex;
  justify-content: center;
  flex-direction: column;
  align-items: center;
  font-weight: bold;
  cursor: pointer;
  box-sizing: border-box;
}

.progress-container {
  width: 80%;
}

.progress-label {
  font-weight: normal;
  color: #555;
  margin-bottom: 0.25rem;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(var(--primary-rgb), 0.2);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--primary);
  width: 0;
  transition: width 0.2s ease;
}

.upload-error {
  color: #b00020;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.download-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
  z-index: 1;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 5px solid rgba(var(--primary-rgb), 0.2); /* light ring */
  border-top-color: rgb(var(--primary-rgb)); /* solid segment */
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
  transition: 0.2s ease-in-out;
}

.spinner-with-progress {
  position: relative;
  animation: none;
  border-color: rgba(var(--primary-rgb), 0.2);
  transition: 0.2s ease-in-out;
  mask-image: radial-gradient(circle, transparent 55%, black 56%);
  mask-composite: exclude; /* for some browsers; harmless where unsupported */
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

.filter-btn-colored {
  color: var(--primary);
}

.filter-btn-active {
  color: var(--primary);
  border-color: var(--primary);
  background: rgba(var(--primary-rgb), 0.1);
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
.list-item {
  width: calc(100% - 1rem);
  transition: 0.2s ease-in-out;
  border-radius: 5px;
  margin: 0.5rem;
}
.list-item:hover {
  background-color: var(--list-item-bg);
}

@media (max-width: 640px) {
  .libraries-loading-spinner {
    margin-left: 1rem;
  }
}
</style>
