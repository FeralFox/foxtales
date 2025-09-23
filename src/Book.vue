<template>
  <div id="reader-content" v-if="url" style="position: relative;width:100%;height:100%">
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
import {getValuesFromIndexedDB, loadFromIndexedDB, saveToIndexedDB} from './dbaccess'

const url = ref('')
const book_metadata = ref('')
const initialPosition = ref(0)
let initialized = ref(false)

function dataURLtoFile(dataurl, filename) {
  var arr = dataurl.split(','),
      mime = arr[0].match(/:(.*?);/)[1],
      bstr = atob(arr[arr.length - 1]),
      n = bstr.length,
      u8arr = new Uint8Array(n);
  while(n--){
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new File([u8arr], filename, {type:mime});
}

const loadBook = async () => {
  const book_id = window.location.hash.split("?")[1].slice(3)
  const bmm =  await loadFromIndexedDB("books", "books", book_id)
  book_metadata.value = bmm
  initialPosition.value = book_metadata.value.progress.position
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
  let initialPosition = book_metadata.value.progress.position;
  console.log("load position", initialPosition)
}

const initLocation = async(position) => {
   let {fraction} = position
  console.log("loadprogress", fraction)
  initialized.value = true
  current.value = fraction * 100
  view.goToFraction(fraction)
  document.getElementById("reader-content").style.visibility = "inherit"
}

const locationChange = async (detail) => {
  let { fraction } = detail
  if (fraction !== book_metadata.value.progress.position) {
    book_metadata.value.progress = {
      position: fraction,
      lastUpdated: new Date().getTime()
    }
    let tr = toRaw(book_metadata.value);
    await saveToIndexedDB("books", "books", tr, book_metadata.value.id)
  }
  current.value = Math.floor(fraction * 100)
}
</script>
<style>
.progress {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  left: 1rem;
  z-index: 1;
  color: #000;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
}

.progress > input[type='number'] {
  text-align: center;
}

.progress > input[type='range'] {
  width: 100%;
  height: 2px;
  accent-color: #000;
  opacity: 0.5;
}
#reader-content {
  visibility: inherit;
}
</style>