<template>
  <Navigation active="library"/>
  <ContextMenu
      v-model="displayBookContextMenu"
      :x="contextMenuX"
      :y="contextMenuY"
      :title="displayBookContextMenu?.title"
  >
    <ContextMenuItem @click="downloadBook(displayBookContextMenu.id)" :icon="IconDownload">Download to Device</ContextMenuItem>
  </ContextMenu>
  <div style="display: flex; flex-wrap: wrap;align-content: flex-start;overflow:auto">
    <div class="book_card">
      <div class="upload-book">
        <IconAddBook class="add-book-icon"/>
        <div v-if="!isUploading">Upload Book</div>
        <div v-else class="progress-container">
          <div class="progress-label">Uploading... {{ uploadProgress }}%</div>
          <div class="progress-bar">
            <div class="progress-bar-fill" :style="{ width: uploadProgress + '%' }"></div>
          </div>
        </div>
        <input :disabled="isUploading" class="file-upload" type="file" accept="*" @change="uploadFile"/>
      </div>
      <div v-if="uploadError" class="upload-error">{{ uploadError }}</div>
    </div>
    <div v-for="book in books" :key="book.id" @click="downloadBook(book.id)"
         @contextmenu="openContextMenu($event, book)" style="cursor: pointer; position: relative">
      <div v-if="downloadingId === book.id" class="download-overlay" @click.stop>
        <div class="progress-container">
          <div class="progress-label">Download... {{ downloadProgress }}%</div>
          <div class="progress-bar">
            <div class="progress-bar-fill" :style="{ width: downloadProgress + '%' }"></div>
          </div>
        </div>
      </div>
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
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: #4caf50;
  width: 0%;
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
  background: rgba(255,255,255,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
  z-index: 1;
  text-align: center;
}
</style>

<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {saveToIndexedDB} from './dbaccess'
import BookCoverThumbnail from "./BookCoverThumbnail.vue";
import Navigation from "./Navigation.vue";
import IconAddBook from "../public/icons/education-book-add-svgrepo-com.svg"
import {authHeaders, URL} from "./constants"
import IconTrashBin from "../public/icons/trash-bin-minimalistic-svgrepo-com.svg";
import ContextMenu from "./components/ContextMenu.vue"
import ContextMenuItem from "./components/ContextMenuItem.vue";
import IconDownload from "../public/icons/download-svgrepo-com.svg"


async function fetchAsync(url: string) {
  const response = await fetch(url, {headers: authHeaders()})
  if (response.status === 401) {
    window.location.hash="#/login"
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
const downloadProgress = ref(0)
const downloadError = ref('')
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadError = ref('')

const displayBookContextMenu = ref<any>(null)
const contextMenuX = ref(0)
const contextMenuY = ref(0)

function openContextMenu(event: MouseEvent, book: any) {
  event.preventDefault()
  // position near click with simple viewport clamping
  const menuW = 200, menuH = 120
  contextMenuX.value = Math.max(0, Math.min(event.clientX, window.innerWidth - menuW))
  contextMenuY.value = Math.max(0, Math.min(event.clientY, window.innerHeight - menuH))
  displayBookContextMenu.value = book
}

async function uploadFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input?.files?.[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  // Reset state
  isUploading.value = true
  uploadProgress.value = 0
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
          if (typeof value === 'string') xhr.setRequestHeader(key, value)
        })
      }

      // Progress events
      xhr.upload.onprogress = (e: ProgressEvent) => {
        if (e.lengthComputable) {
          uploadProgress.value = Math.min(100, Math.round((e.loaded / e.total) * 100))
        }
      }

      xhr.onload = () => {
        // Accept 200-299 range
        if (xhr.status >= 200 && xhr.status < 300) {
          uploadProgress.value = 100
          resolve()
        } else {
          reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`))
        }
      }

      xhr.onerror = () => reject(new Error('Network error during upload'))
      xhr.onabort = () => reject(new Error('Upload aborted'))

      xhr.send(formData)
    })

    await loadBooks()
  } catch (e: any) {
    console.error(e)
    uploadError.value = e?.message || 'Upload failed'
  } finally {
    // clear the file input so the same file can be selected again if needed
    if (input) input.value = ''
    // small delay to let user see 100%
    setTimeout(() => {
      isUploading.value = false
      uploadProgress.value = 0
    }, 400)
  }
}

async function downloadBook(identifier: string) {
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
          if (typeof value === 'string') xhr.setRequestHeader(key, value)
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
    const cover = await fetch(`${URL}/get_book_cover?book_id=${identifier}&data_url=true`, { headers: authHeaders() })
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
    }, 400)
  }
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