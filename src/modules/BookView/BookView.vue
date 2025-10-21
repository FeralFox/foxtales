<template>
  <div class="reader">
    <div class="viewHolder">
      <div ref="viewer" id="viewer" v-show="isLoaded"></div>
      <div v-if="!isLoaded">
        <slot name="loadingView"> </slot>
      </div>
    </div>
  </div>
</template>

<script setup>
//https://github.com/johnfactotum/foliate-js
//https://github.com/johnfactotum/foliate
import '../utils/foliatejs/view.js'
import "core-js/proposals/array-grouping-v2"
import {
  clickListener,
  swipListener,
  wheelListener,
  keyListener,
} from '../utils/listener/listener'
import { ref, toRefs, watch, onMounted } from 'vue'

const props = defineProps({
  url: {
    type: [String, File],
  },
  location: {
    type: [String, Number],
  },
  tocChanged: Function,
  getRendition: Function,
  style: {
    type: Object,
  }
})

const { tocChanged, getRendition } = props
const { url, location } = toRefs(props)

const emit = defineEmits(['update:location'])

let view = null
const viewer = ref(null)
const isLoaded = ref(false)

const initBook = async () => {
  view = document.createElement('foliate-view')
  viewer.value.append(view)
  if (url.value) {
    view && view.close()
    await view.open(url.value)
    initReader()
    // if (typeof url.value === 'string') {
    // } else {
    //   view = await getView(url.value, viewer.value)
    //   initReader()
    // }
  }
}

const initReader = () => {
  isLoaded.value = true
  const { book } = view
  view.renderer.setAttribute("exportsparts", "filter")
  registerEvents()
  getRendition(view)
  tocChanged && tocChanged(book.toc)
  if (typeof location.value === "number") {
    view.goToFraction(location.value)
  } else if (location.value) {
    view?.goTo(location.value)
  } else {
    view.renderer.next()
  }
}

const flipPage = (direction) => {
  if (direction === 'next') nextPage()
  else if (direction === 'prev') prevPage()
}

const registerEvents = () => {
  view.addEventListener('load', onLoad)
  view.addEventListener('relocate', onRelocate)
}

const onLoad = ({ detail: { doc } }) => {
  wheelListener(doc, flipPage)
  swipListener(doc, flipPage)
  keyListener(doc, flipPage)
}

const onRelocate = ({ detail }) => {
  emit('update:location', detail)
}

const nextPage = () => view?.next()

const prevPage = () => view?.prev()

const setLocation = (href) => view?.goTo(href)

watch(url, () => {
  initBook()
})

onMounted(() => {
  initBook()
})

defineExpose({
  nextPage,
  prevPage,
  setLocation,
})
</script>

<style scoped>
.reader {
  position: absolute;
  inset: var(--padding-top) var(--border-horizontal) var(--padding-bottom);
}

.viewHolder {
  height: 100%;
  width: 100%;
  position: relative;
}

#viewer {
  height: 100%;
}
</style>
