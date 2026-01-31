<template>
  <div
    id="reader-content"
    v-if="url"
    :class="initialized ? '' : 'hidden'"
    style="position: relative; width: 100%; height: 100%"
  >
    <vue-reader
      :location="initialPosition"
      :url="url"
      :getRendition="getRendition"
      @update:location="locationChange"
      :on-btn-next="onBtnNext"
      :annotations="annotations"
      :on-annotation-updated="onAnnotationUpdate"
    >
    </vue-reader>
  </div>
</template>

<script setup>
import VueReader from './modules/VueReader/VueReader.vue'
import { onMounted, ref, toRaw } from 'vue'
import { loadFromBookDb, loadFromIndexedDB, saveToBookDb } from './dbaccess'
import { syncedUpdate } from './sync'

const url = ref('')
const book_metadata = ref('')
const annotations = ref({})
const initialPosition = ref(0)
const initialized = ref(false)
let isLastPage = false

const loadBook = async () => {
  const book_id = window.location.hash.split('?')[1].slice(3)
  const bmm = await loadFromBookDb('books', book_id)
  book_metadata.value = bmm
  const anno = await loadFromBookDb('annotations', book_id, {})
  annotations.value = anno
  initialPosition.value = book_metadata.value.fxtl_progress
  const blob = await loadFromIndexedDB('data', 'data', book_id)
  const format = bmm.formats[0].toLowerCase()
  url.value = new File([blob], `${book_metadata.value.title}.${format}`) //dataURLtoFile(`data:${book_metadata.value.data.mimetype};base64,${book.data}`, `${book_metadata.value.data.title}.cbz`)
}
onMounted(() => {
  loadBook()
})

let view = null

const getRendition = async (val) => {
  view = val
  setTimeout(async () => {
    view.renderer.prev()
    setTimeout(() => (initialized.value = true), 200)
  }, 100)
}

async function onBtnNext() {
  if (isLastPage) {
    book_metadata.value.fxtl_is_read = true
    await saveToBookDb(
      'books',
      toRaw(book_metadata.value),
      book_metadata.value.uuid,
    )
    syncedUpdate('update-read-status', book_metadata.value.uuid, {
      fxtl_is_read: true,
    })
    window.location.hash = '/'
  }
}

const onAnnotationUpdate = async (modified_highlight, allHighlights) => {
  await saveToBookDb(
    'annotations',
    toRaw(allHighlights),
    book_metadata.value.uuid,
  )
  syncedUpdate(
    'update-annotations',
    book_metadata.value.uuid,
    modified_highlight,
    true,
  )
}

const locationChange = async (detail) => {
  let { fraction } = detail
  isLastPage = fraction === 1
  if (fraction !== book_metadata.value.fxtl_progress) {
    const dateUpdate = new Date().toISOString()
    book_metadata.value.fxtl_progress = fraction
    book_metadata.value.fxtl_progress_update = dateUpdate
    await saveToBookDb(
      'books',
      toRaw(book_metadata.value),
      book_metadata.value.uuid,
    )

    // Need to store explicitly as the user might delete the book from local books before the
    // latest progress is synced.
    await syncedUpdate('update-progress', book_metadata.value.uuid, {
      fxtl_progress: fraction,
      fxtl_progress_update: dateUpdate,
    })
  }
}
</script>
<style scoped>
.hidden {
  visibility: hidden;
}
</style>
