<template>
  <div id="reader-content" v-if="url" :class="initialized ? '' : 'hidden'" style="position: relative;width:100%;height:100%">
    <vue-reader
        :location="initialPosition"
        :url="url"
        :getRendition="getRendition"
        @update:location="locationChange"
    >
    </vue-reader>

    <div class="progress">
      <input
          type="range"
          :value="current"
          :min="0"
          :max="100"
          :step="1"
          @change="change"
      />
    </div>
  </div>
</template>

<script setup>
import VueReader from './modules/VueReader/VueReader.vue'
import {onMounted, ref, toRaw} from 'vue'
import {loadFromBookDb, loadFromIndexedDB, saveToBookDb} from './dbaccess'
import {syncedUpdate} from "./sync";

const url = ref('')
const book_metadata = ref('')
const initialPosition = ref(0)
const initialized = ref(false)

const loadBook = async () => {
  const book_id = window.location.hash.split("?")[1].slice(3)
  const bmm =  await loadFromBookDb("books", book_id)
  book_metadata.value = bmm
  initialPosition.value = book_metadata.value.fxtl_progress
  const blob = await loadFromIndexedDB("data", "data", book_id)
  const format = bmm.formats[0].toLowerCase()
  url.value = new File([blob], `${book_metadata.value.title}.${format}`); //dataURLtoFile(`data:${book_metadata.value.data.mimetype};base64,${book.data}`, `${book_metadata.value.data.title}.cbz`)
}
onMounted(() => {
  loadBook()
})

let view = null
const current = ref(0)
const change = (e) => {
  const value = e.target.value
  current.value = value
  view.goToFraction(parseFloat(value / 100))
}

const getRendition = async (val) => {
  view = val
  setTimeout(async () => {
    view.renderer.prev();
    setTimeout(() => initialized.value = true, 200)
  }, 100)
}


const locationChange = async (detail) => {
  let { fraction } = detail
  current.value = Math.floor(fraction * 100)
  if (fraction === 1) {
    const book = book_metadata.value.fxtl_is_read = true
    await saveToBookDb("books", toRaw(book), book.id)
    syncedUpdate("update-read-status", book.id, {fxtl_is_read: true})
  }
  if (fraction !== book_metadata.value.fxtl_progress) {
    const dateUpdate = new Date().toISOString()
    book_metadata.value.fxtl_progress = fraction
    book_metadata.value.fxtl_progress_update = dateUpdate
    await saveToBookDb("books", toRaw(book_metadata.value), book_metadata.value.id)

    // Need to store explicitly as the user might delete the book from local books before the
    // latest progress is synced.
    await syncedUpdate("update-progress", book_metadata.value.id, {fxtl_progress: fraction, fxtl_progress_update: dateUpdate});
  }
}
</script>
<style>
.hidden {
  visibility: hidden;
}
.progress {
  position: absolute;
  bottom: 0;
  right: 0;
  left: 0;
  z-index: 1;
  color: #000;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  cursor: pointer;
}

.progress > input[type='number'] {
  text-align: center;
}

.progress > input[type='range'] {
  width: 100%;
  height: 5px;
  accent-color: #000;
  opacity: 0.5;
}
</style>