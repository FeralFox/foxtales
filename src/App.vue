<template>
  <div v-if="url" style="position: relative;width:100%;height:100%">
    <vue-reader
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
  <input v-if="!url" class="input" type="file" accept=".epub,.mobi,.azw3,.FB2,.CBZ,.PDF" @change="onchange"/>


</template>

<script setup>
import VueReader from './modules/VueReader/VueReader.vue'
import {ref} from 'vue'

const url = ref('')
const onchange = (e) => {
  const file = e.target.files[0]
  console.log(file)
  url.value = file
}

let view = null
const current = ref(0)
const change = (e) => {
  const value = e.target.value
  current.value = value
  view.goToFraction(parseFloat(value / 100))
}
const getRendition = (val) => (view = val)

const locationChange = (detail) => {
  const { fraction } = detail
  const percent = Math.floor(fraction * 100)
  current.value = percent
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
</style>