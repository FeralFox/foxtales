<template>
  <Navigation active="library"/>
  <ContextMenu
      v-model="displayBookContextMenu"
      :x="contextMenuX"
      :y="contextMenuY"
      :title="displayBookContextMenu?.title"
  >
    <ContextMenuItem @click="downloadBook(displayBookContextMenu.id)" :icon="IconDownload">
      Download to Device
    </ContextMenuItem>
    <ContextMenuItem @click="confirmRemoveBook(displayBookContextMenu.id)" :icon="IconRemove">
      Remove from Library
    </ContextMenuItem>
  </ContextMenu>
  <div style="display: flex; flex-wrap: wrap;align-content: flex-start;overflow:auto" @scroll="onScroll"
       ref="book-container">
    <div class="book_card" ref="upload-book">
      <div class="upload-book">
        <IconAddBook class="add-book-icon"/>
        <div v-if="!isUploading">Upload Book</div>
        <div v-else class="progress-container">
          <div class="progress-label">Uploading... {{ uploadProgress }}%</div>
          <div class="progress-bar">
            <div class="progress-bar-fill" :style="{ width: uploadProgress + '%' }"></div>
          </div>
        </div>
        <input :disabled="isUploading" class="file-upload" type="file" multiple accept="*" @change="uploadFile"/>
      </div>
      <div v-if="uploadError" class="upload-error">{{ uploadError }}</div>
    </div>
    <div v-for="book in books" :key="book.id" @click="downloadBook(book.id)"
         @contextmenu.prevent="openContextMenu($event, book)" style="cursor: pointer; position: relative">
      <div v-if="downloadingId === book.id"  class="download-overlay" @click.stop>
        <div class="spinner spinner-with-progress" :style="{ background: `conic-gradient(rgb(var(--primary-rgb)) 0deg, rgb(var(--primary-rgb)) ${Math.round(downloadProgress * 3.6)}deg, rgba(0,0,0,0) 0) border-box` }"></div>
      </div>
      <div v-if="downloadQueue.includes(book.id)" class="download-overlay" @click.stop>
        <div class="spinner"></div>
      </div>
      <BookCoverThumbnail
          :book="book"
          :image="covers[book.id] ? `url(${covers[book.id]})` : ''"
      />
    </div>
    
    <div v-if="showDeleteModal" class="modal" @click.stop>
      <div style="font-weight: 600">Remove from Library</div>
      <div>Are you sure you want to remove this book from your library?</div>
      <div style="display:flex; gap: 8px; justify-content: flex-end; margin-top: 8px">
        <button @click="cancelRemoveBook" :disabled="isDeleting" class="btn-ghost">Cancel</button>
        <button @click="removeBookConfirmed" :disabled="isDeleting" class="btn-danger">
          {{ isDeleting ? 'Removing…' : 'Remove' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {nextTick, onMounted, ref, useTemplateRef} from 'vue'
import {saveToIndexedDB} from './dbaccess'
import BookCoverThumbnail from "./BookCoverThumbnail.vue";
import Navigation from "./Navigation.vue";
import IconAddBook from "../public/icons/education-book-add-svgrepo-com.svg"
import {authHeaders, URL} from "./constants"
import ContextMenu from "./components/ContextMenu.vue"
import ContextMenuItem from "./components/ContextMenuItem.vue";
import IconDownload from "../public/icons/download-svgrepo-com.svg"
import IconRemove from "../public/icons/trash-bin-minimalistic-svgrepo-com.svg"


const bookContainer = useTemplateRef('book-container')


async function fetchAsync(url: string) {
  const response = await fetch(url, {headers: authHeaders()})
  if (response.status === 401) {
    window.location.hash = "#/login"
    throw "Authorization error - forward to login page."
  }
  return await response.json()
}

interface BookMeta {
  id: string
  title: string
}

const books = ref<BookMeta[]>([])
const covers = ref<Record<string, string>>({})
const downloadingId = ref<string>('')
const downloadQueue = ref<string[]>([])
const downloadProgress = ref(0)
const downloadError = ref('')
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadError = ref('')

const displayBookContextMenu = ref<any>(null)
const contextMenuX = ref(0)
const contextMenuY = ref(0)

function openContextMenu(event: MouseEvent, book: any) {
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  displayBookContextMenu.value = book
}

async function uploadFile(event: Event) {
  const input = event.target as HTMLInputElement
  const files = input?.files || []
  if (files.length === 0) return

  const totalBooks = files.length
  const progressOneBook = 1 / totalBooks
  let currentBook = 0;
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
            const progressCurrentFile = (e.loaded / e.total);
            const totalProgress = progressAllFiles + (progressCurrentFile * progressOneBook)
            uploadProgress.value = Math.min(100, Math.round((totalProgress) * 100));
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

      await loadBooks(0, true)
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
    const status_removed = await fetchAsync(`${URL}/remove_book?book_id=${identifier}`)
    if (status_removed.success) {
      const newBooks: BookMeta[] = []
      for (let book of books.value) {
        if (book.id !== identifier) newBooks.push(book)
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

async function downloadBook(identifier: string) {
  if (downloadingId.value) {
    downloadQueue.value.push(identifier)
    return
  }

  // reset and show overlay for this book
  displayBookContextMenu.value = null;
  downloadingId.value = identifier
  downloadProgress.value = 0
  downloadError.value = ''
  try {
    const bookMetaData = await fetchAsync(`${URL}/get_book_metadata?book_id=${identifier}`)
    const format = bookMetaData.formats?.[0]

    // Download book blob with progress using XHR
    const blob: Blob = await new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('GET', `${URL}/get_book?book_id=${identifier}&format=${format}`)

      // auth header
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
          downloadProgress.value = Math.min(100, Math.round((e.loaded / e.total) * 100))
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

    // Download cover (small) - no progress bar necessary
    const cover = await fetch(`${URL}/get_book_cover?book_id=${identifier}&data_url=true`, {headers: authHeaders()})
    const coverBase64 = await cover.text()

    // Save all to IndexedDB
    await saveToIndexedDB('books', 'books', bookMetaData, identifier)
    await saveToIndexedDB(`cover`, 'cover', coverBase64, identifier)
    await saveToIndexedDB(`data`, 'data', blob, identifier)
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

const BOOKS_TO_PREFETCH = 20;

async function loadBooks(start_from: number, initialFetch?: boolean) {
  const fetchedBooks = await fetchAsync(`${URL}/list_books?max_items=${BOOKS_TO_PREFETCH}&start_from=${start_from}`)
  if (fetchedBooks.length === 0) {
    return
  }
  // Immediately display all books as soon as they are available.
  if (start_from === 0) {
    covers.value = {}
    books.value = fetchedBooks
  } else {
    books.value = [...books.value, ...fetchedBooks]
  }

  // prefetch covers as data urls (requires auth header)
  await Promise.all(fetchedBooks.map(async (b: any) => {
    try {
      const resp = await fetch(`${URL}/get_book_cover?book_id=${b.id}&data_url=true`, {headers: authHeaders()})
      if (resp.ok) {
        covers.value[b.id] = await resp.text()
      }
    } catch {
    }
  }))

  // Wait for all books and covers to be displayed - then render everything - then check if there are scrollbars.
  // Then check if we need to fetch more books to fill the page.
  await nextTick()
  let hasScrollBars = bookContainer.value!.scrollHeight > bookContainer.value!.clientHeight;
  let mightHaveAdditionalBooks = fetchedBooks.length === BOOKS_TO_PREFETCH;
  if (initialFetch && !hasScrollBars && mightHaveAdditionalBooks) {
    await loadBooks(start_from + BOOKS_TO_PREFETCH, true)
  }
  scrollEventDisabled = false
}

let scrollEventDisabled = false;


function onScroll() {
  if (scrollEventDisabled) {
    return
  }
  let maxScrollHeight = bookContainer.value!.scrollHeight - bookContainer.value!.clientHeight;
  let scrollHeight = bookContainer.value!.scrollTop
  let scrollBottom = maxScrollHeight - scrollHeight
  if (scrollBottom < 200) {
    if (scrollEventDisabled) {
      return
    }
    scrollEventDisabled = true
    loadBooks(books.value.length, false)
  }
}


onMounted(() => {
  loadBooks(0, true)
})
</script>


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
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
