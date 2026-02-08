<template>
  <div class="container">
    <ContextMenu
      v-model="displayBookContextMenu"
      v-if="displayBookContextMenu"
      :x="displayBookContextMenu.x"
      :y="displayBookContextMenu.y"
    >
      <ContextMenuItem
        @click="removeAnnotation(displayBookContextMenu.annotation)"
        :icon="IconTrash"
      >
        Delete
      </ContextMenuItem>
    </ContextMenu>
    <div
      class="readerArea"
      :class="{ containerExpanded: expandedToc }"
      :style="{ background: styles.background }"
    >
      <div class="progress">
        <input
          type="range"
          :value="current"
          :min="0"
          :max="100"
          :step="1"
          @change="change"
          :style="{ color: styles.color }"
        />
      </div>
      <div
        v-if="showToc"
        class="tocButton"
        :class="{ tocButtonExpanded: expandedToc }"
        type="button"
        @click="toggleToc"
      >
        <span
          class="tocButtonBar"
          :style="{ top: '35%', background: styles.color }"
        ></span>
        <span
          class="tocButtonBar"
          :style="{ top: '66%', background: styles.color }"
        ></span>
      </div>

      <book-view
        ref="bookRef"
        v-bind="$attrs"
        :location="props.location"
        @update:location="onUpdateLocation"
        :tocChanged="onTocChange"
        :getRendition="onGetRendition"
      >
        <template #loadingView>
          <slot name="loadingView">
            <div class="loadingView">Loading…</div>
          </slot>
        </template>
      </book-view>

      <!-- color picker displayed when user selects text -->
      <div v-if="colorPicker.show" class="choose-annotation-category">
        <button
          v-for="category in Object.keys(ANNOTATION_CATEGORIES)"
          class="picker-btn"
          @click="chooseHighlight(category)"
          :style="{ background: ANNOTATION_CATEGORIES[category].color }"
        >
          {{ category }}
        </button>
      </div>

      <div class="arrow pre" @click="pre" :style="{ color: styles.color }">
        ‹
      </div>
      <div class="arrow next" @click="next" :style="{ color: styles.color }">
        ›
      </div>
    </div>

    <div v-if="showToc && expandedToc">
      <div class="tocArea">
        <div class="sidebarTabs">
          <div
            @click="selectNavigation"
            :class="selectedTab === 'navigation' ? 'selectedTab' : ''"
          >
            <IconBook />
          </div>
          <div
            @click="selectAnnotations"
            :class="selectedTab === 'annotations' ? 'selectedTab' : ''"
          >
            <IconPen />
          </div>
          <div
            @click="selectView"
            :class="selectedTab === 'view' ? 'selectedTab' : ''"
          >
            <IconBookRead />
          </div>
        </div>

        <div v-if="selectedTab === 'navigation'">
          <button
            @click="closeBook"
            style="margin-left: 50%; transform: translate(-50%, 0)"
          >
            Back to library
          </button>
          <hr style="margin: 1rem" />
          <TocComponent
            :toc="toc"
            :current="currentHref"
            :setLocation="setLocation"
          />
        </div>

        <div v-if="selectedTab === 'annotations'">
          <div v-for="chapter in Object.keys(annotations)">
            <div class="annotationsChapter">Chapter {{ chapter }}</div>
            <div
              v-for="annotation of annotations[chapter]"
              class="annotationCard"
              @contextmenu.prevent="openContextMenu($event, annotation)"
            >
              <div
                class="annotationCardColor"
                :style="{
                  background: ANNOTATION_CATEGORIES[annotation.category].color,
                }"
              />
              {{ annotation.text }}
            </div>
          </div>
        </div>

        <div v-if="selectedTab === 'view'">
          <div class="buttonBar">
            <span>Font size</span>
            <button
              @click="reduceFontSize"
              style="border-top-right-radius: 0; border-bottom-right-radius: 0"
            >
              -
            </button>
            <button
              @click="increaseFontSize"
              style="border-top-left-radius: 0; border-bottom-left-radius: 0"
            >
              +
            </button>
          </div>
          <div class="buttonBar">
            <span>Spacing</span>
            <button
              @click="reduceSpacing"
              style="border-top-right-radius: 0; border-bottom-right-radius: 0"
            >
              -
            </button>
            <button
              @click="increaseSpacing"
              style="border-top-left-radius: 0; border-bottom-left-radius: 0"
            >
              +
            </button>
          </div>
          <div class="style-list">
            <button
              class="style-tile"
              style="background: white; color: black"
              @click="changeTheme('#fff', '#000')"
            >
              Default
            </button>
            <button
              class="style-tile"
              style="background: #e3d8ce; color: #52443b"
              @click="changeTheme('#e3d8ce', '#52443b')"
            >
              Sepia
            </button>
            <button
              class="style-tile"
              style="background: #2d2e31; color: #d7d6d6"
              @click="changeTheme('#2d2e31', '#d7d6d6')"
            >
              Dark
            </button>
            <button
              class="style-tile"
              style="background: black; color: white"
              @click="changeTheme('#000', '#fff')"
            >
              Black
            </button>
          </div>
        </div>
      </div>

      <div v-if="expandedToc" class="tocBackground" @click="toggleToc"></div>
    </div>
  </div>
</template>
<script setup>
import { Overlayer } from '../utils/foliatejs/overlayer.js'
import BookView from '../BookView/BookView.vue'
import {
  ref,
  reactive,
  toRefs,
  defineComponent,
  getCurrentInstance,
  Transition,
  h as _h,
  toRaw,
} from 'vue'
import { get_uuid } from '../../lib'
import IconBookRead from '../../../public/icons/eye-svgrepo-com.svg'
import IconPen from '../../../public/icons/pen-square-svgrepo-com.svg'
import IconBook from '../../../public/icons/book-svgrepo-com.svg'
import IconTrash from '../../../public/icons/trash-bin-minimalistic-svgrepo-com.svg'
import { ANNOTATION_CATEGORIES } from '../../constants.ts'
import ContextMenu from '../../components/ContextMenu.vue'
import ContextMenuItem from '../../components/ContextMenuItem.vue'

const current = ref(0)
const displayBookContextMenu = ref(null)

function openContextMenu(event, annotation) {
  displayBookContextMenu.value = {
    annotation,
    x: event.clientX,
    y: event.clientY,
  }
}

function closeContextMenu() {
  displayBookContextMenu.value = null
}

function removeAnnotation(annotation) {
  const resolvedAnnotation = toRaw(annotation)
  closeContextMenu()
  const annotations = []
  for (let anno of userHighlights[resolvedAnnotation.index]) {
    if (anno.uuid === resolvedAnnotation.uuid) {
      continue
    }
    annotations.push(toRaw(anno))
  }
  userHighlights[resolvedAnnotation.index] = annotations
  props.onAnnotationUpdated(['delete', resolvedAnnotation], userHighlights)
  highlightFromUserHighlight(resolvedAnnotation, true)
}

function redrawUserHighlights(section) {
  for (let highlight of userHighlights[section] || []) {
    highlightFromUserHighlight(highlight)
  }
}

function onUpdateLocation(params) {
  redrawUserHighlights(params.section.current)
  current.value = Math.floor(params.fraction * 100)
}

const change = (e) => {
  const value = e.target.value
  current.value = value
  rendition.goToFraction(parseFloat(value / 100))
}
let selectedTab = ref('navigation')

function getStoredStyles() {
  const item = localStorage.getItem('vue-reader-styles')
  if (item) {
    return JSON.parse(item)
  }
  return {}
}

const defaultStyles = {
  fontSize: 140,
  spacing: 1.4,
  color: '#000',
  background: '#fff',
  ...getStoredStyles(),
}

const styles = ref(defaultStyles)

function selectNavigation() {
  selectedTab.value = 'navigation'
}

function selectView() {
  selectedTab.value = 'view'
}

function selectAnnotations() {
  selectedTab.value = 'annotations'
}

function increaseFontSize() {
  if (!rendition) {
    return
  }
  styles.value.fontSize += 20
  updateStyle()
}
function reduceFontSize() {
  styles.value.fontSize -= 20
  updateStyle()
}

function increaseSpacing() {
  if (!rendition) {
    return
  }
  styles.value.spacing += 0.2
  updateStyle()
}
function reduceSpacing() {
  styles.value.spacing -= 0.2
  updateStyle()
}

function changeTheme(bg, fg) {
  styles.value.background = bg
  styles.value.color = fg
  updateStyle()
}

function updateStyle() {
  localStorage.setItem('vue-reader-styles', JSON.stringify(styles.value))
  rendition.renderer.setStyles?.(
    getCSS({
      justify: true,
      hyphenate: true,
    }),
  )
}

function closeBook() {
  window.location.hash = '/'
}

const TocComponent = defineComponent({
  name: 'TocComponent',

  props: {
    toc: {
      type: Array,
      default: () => [],
    },
    current: {
      type: [String, Number],
      default: '',
    },
    setLocation: {
      type: Function,
      required: true,
    },
    isSubmenu: {
      type: Boolean,
      default: false,
      required: false,
    },
  },

  setup(props) {
    const vm = getCurrentInstance()
    const h = _h.bind(vm)

    const { setLocation, isSubmenu } = props
    const { toc, current } = toRefs(props)

    return () =>
      toc.value.map((item, index) => {
        return h('div', { key: index }, [
          h(
            'div',
            {
              class: [
                'tocAreaButton',
                item.href === current.value ? 'active' : '',
              ],
              onClick: () => {
                if (item.subitems && item.subitems.length > 0) {
                  item.expansion = !item.expansion
                  setLocation(item.href, false)
                } else {
                  setLocation(item.href)
                }
              },
            },
            [
              isSubmenu ? ' '.repeat(4) + item.label : item.label,
              // 展开
              item.subitems &&
                item.subitems.length > 0 &&
                h('div', {
                  class: `${item.expansion ? 'open' : ''} expansion`,
                }),
            ],
          ),
          //多级目录
          item.subitems &&
            item.subitems.length > 0 &&
            h(
              Transition,
              { name: 'collapse-transition' },
              {
                default: () =>
                  h(
                    'div',
                    {
                      style: {
                        display: item.expansion ? undefined : 'none',
                      },
                    },
                    [
                      h(TocComponent, {
                        toc: item.subitems,
                        current: current.value,
                        setLocation,
                        isSubmenu: true,
                      }),
                    ],
                  ),
              },
            ),
        ])
      })
  },
})

const props = defineProps({
  showToc: {
    type: Boolean,
    default: true,
  },
  location: {
    type: [String, Number],
  },
  title: {
    type: String,
    default: '',
  },
  getRendition: {
    type: Function,
  },
  onBtnNext: {
    type: Function,
  },
  onAnnotationUpdated: { type: Function },
  annotations: { type: Object(), default: {} },
  // Optional hook: called when user selects text; receives position { x, y }
  onTextSelected: {
    type: Function,
  },
})

const book = reactive({
  toc: [],
  expandedToc: false,
})

const { getRendition } = props

const { toc, expandedToc } = toRefs(book)

const bookRef = ref(null)
const currentHref = ref(null)

const bookName = ref('')

let rendition = null

// transient color picker state
const colorPicker = reactive({
  show: false,
  range: null,
  index: null,
  doc: null,
  cfi: null,
  text: '',
})

const getCSS = ({ justify, hyphenate }) => `
    @namespace epub "http://www.idpf.org/2007/ops";
    html {
        color-scheme: light;
        font-size: ${styles.value.fontSize}% !important;
        color: ${styles.value.color} !important;
    }
    body {
        font-size: inherit !important;
        color: inherit !important;
      }
    /* https://github.com/whatwg/html/issues/5426 */
    @media (prefers-color-scheme: dark) {
        a:link {
            color: lightblue;
        }
    }
    span {
      color: ${styles.value.color} !important;
      line-height: ${styles.value.spacing} !important;
    }
    p, li, blockquote, dd {
        line-height: ${styles.value.spacing};
        color: ${styles.value.color} !important;
        text-align: ${justify ? 'justify' : 'start'};
        -webkit-hyphens: ${hyphenate ? 'auto' : 'manual'};
        hyphens: ${hyphenate ? 'auto' : 'manual'};
        -webkit-hyphenate-limit-before: 3;
        -webkit-hyphenate-limit-after: 2;
        -webkit-hyphenate-limit-lines: 2;
        hanging-punctuation: allow-end last;
        widows: 2;
    }
    /* prevent the above from overriding the align attribute */
    [align="left"] { text-align: left; }
    [align="right"] { text-align: right; }
    [align="center"] { text-align: center; }
    [align="justify"] { text-align: justify; }

    pre {
        white-space: pre-wrap !important;
    }
    aside[epub|type~="endnote"],
    aside[epub|type~="footnote"],
    aside[epub|type~="note"],
    aside[epub|type~="rearnote"] {
        display: none;
    }
`

const onGetRendition = (val) => {
  getRendition && getRendition(val)
  const { book } = val
  rendition = val
  const title = book.metadata?.title
  bookName.value = title || ''
  userHighlights = props.annotations
  val.renderer.setStyles?.(
    getCSS({
      justify: true,
      hyphenate: true,
    }),
  )

  // helper: attach selection listeners inside current contents
  const attachSelectionHandlers = () => {
    try {
      const contents = val.renderer?.getContents?.() || []
      contents.forEach((content) => {
        if (content.__ft_sel_attached) return
        content.__ft_sel_attached = true
        const doc = content.doc
        doc.addEventListener('selectionchange', (e) => {
          try {
            const sel = doc.getSelection()
            if (!sel || sel.isCollapsed || sel.rangeCount === 0) {
              cancelHighlight()
              return
            }
            const range = sel.getRangeAt(0)
            if (!range || String(sel).trim() === '') return
            const idx = content.index
            const cfi =
              typeof val.getCFI === 'function' ? val.getCFI(idx, range) : null
            colorPicker.range = range
            colorPicker.index = idx
            colorPicker.doc = doc
            colorPicker.cfi = cfi
            colorPicker.text = String(sel)
            colorPicker.show = true
            // user hook
            if (typeof props.onTextSelected === 'function') {
              props.onTextSelected({ x: e.clientX, y: e.clientY })
            }
          } catch (_) {}
        })
      })
    } catch (_) {}
  }

  // attach now and again on further loads
  attachSelectionHandlers()
  // re-apply when a new section (chapter) is loaded
  val.addEventListener?.('load', () => {
    attachSelectionHandlers()
  })
}

// persistent user highlights across navigation
let userHighlights = {}

const cancelHighlight = () => {
  try {
    colorPicker.doc?.defaultView?.getSelection?.().removeAllRanges?.()
  } catch (_) {}
  colorPicker.show = false
  colorPicker.range = null
  colorPicker.doc = null
  colorPicker.index = null
  colorPicker.cfi = null
  colorPicker.text = ''
}

const chooseHighlight = (category) => {
  if (!colorPicker.range || !colorPicker.doc) return cancelHighlight()
  const cfi = colorPicker.cfi
  const index = colorPicker.index
  try {
    if (cfi) {
      let userHighlight = {
        uuid: get_uuid(),
        cfi,
        index,
        category,
        text: colorPicker.text,
      }
      if (!userHighlights[index]) {
        userHighlights[index] = []
      }
      userHighlights[index].push(userHighlight)
      highlightFromUserHighlight(userHighlight)
      props.onAnnotationUpdated(['add', userHighlight], userHighlights)
    }
  } catch (err) {
    console.warn('Failed to apply highlight:', err)
  }
  cancelHighlight()
}

// Accepts an entry from userHighlights: { cfi, index, category, text? }
// Returns true if the overlay highlight was added successfully
function highlightFromUserHighlight(entry, remove) {
  try {
    if (!entry || !entry.cfi || !rendition) return false
    const resolved =
      typeof rendition.resolveCFI === 'function'
        ? rendition.resolveCFI(entry.cfi)
        : null
    if (!resolved) return false
    const { index, anchor } = resolved
    const contents = rendition.renderer?.getContents?.() || []
    const content = contents.find((c) => c.index === index && c.overlayer)
    if (!content) return false
    const doc = content.doc
    const range = typeof anchor === 'function' ? anchor(doc) : null
    // if (!(range instanceof Range)) return false
    const key = entry.cfi
    // map our simple color names to solid colors (opacity handled by Overlayer)
    const color = ANNOTATION_CATEGORIES[entry.category].color
    if (remove) {
      content.overlayer.remove(key)
    } else {
      content.overlayer.add(key, range, Overlayer.highlight, { color })
    }
    return true
  } catch (e) {
    console.warn('Failed to overlay highlight from entry:', e)
    return false
  }
}

// Make the function available to parent components if needed
defineExpose({ highlightFromUserHighlight })

const onTocChange = (_toc) => {
  toc.value = _toc
}

const toggleToc = () => {
  expandedToc.value = !expandedToc.value
}

const next = () => {
  try {
    props.onBtnNext()
    bookRef.value?.nextPage()
  } catch (err) {
    alert(err.toString())
  }
}
const pre = () => {
  bookRef.value?.prevPage()
}

const setLocation = (href, close = true) => {
  bookRef.value.setLocation(href)
  expandedToc.value = false
  expandedToc.value = !close
}
</script>
<style>
.annotationsChapter {
  font-weight: bold;
  width: 100%;
  text-align: center;
}
.annotationCard {
  background: white;
  margin: 0.5rem;
  border-radius: 5px;
  box-shadow: 1px 1px 3px #0002;
  position: relative;
  padding: 0.5rem 1rem 0.5rem 0.5rem;
  overflow: hidden;
}
.annotationCardColor {
  position: absolute;
  top: 0;
  right: 0;
  width: 0.5rem;
  height: 100%;
}
.progress {
  position: absolute;
  bottom: 0;
  right: 0;
  left: 0;
  z-index: 1;
  color: currentColor;
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
  accent-color: currentColor;
  opacity: 0.5;
}
.style-list {
  display: grid;
  flex-wrap: wrap;
  grid-template-columns: 1fr 1fr;
  gap: 0.2rem;
  margin: 0.2rem;
}
.style-tile {
  line-height: 1.5rem;
  margin: 0.3rem;
  border-radius: 5px;
  border: 2px solid currentColor;
}

/* container */
.container {
  overflow: hidden;
  position: relative;
  height: 100%;
}

.containerExpanded {
  transform: translateX(256px);
}

.readerArea {
  position: relative;
  z-index: 1;
  height: 100%;
  width: 100%;
  /* background-color: #fff; */
  transition: all 0.3s ease;
}

.container .titleArea {
  position: absolute;
  top: 20px;
  left: 50px;
  right: 50px;
  text-align: center;
  color: #999;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
/* toc */
.tocBackground {
  position: absolute;
  left: 256px;
  top: 0;
  bottom: 0;
  right: 0;
  z-index: 1;
}

.buttonBar {
  justify-self: center;
  width: 90%;
  margin: 1rem;
  display: flex;
  align-items: center;
}
.buttonBar span {
  font-weight: bold;
  flex-grow: 1;
}

.sidebarTabs {
  display: flex;
  width: 100%;
  justify-content: center;
  background: black;
  color: white;
  margin-bottom: 10px;
}

.sidebarTabs div {
  padding: 0.3em 0.5em;
  cursor: pointer;
  user-select: none;
  border-radius: 5px 5px 0 0;
}

.sidebarTabs div svg {
  width: 2em;
  height: 2em;
}

.sidebarTabs .selectedTab {
  background: #f2f2f2;
  color: black;
}

.tocArea {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 0;
  width: 256px;
  height: 100vh;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  background: #f2f2f2;
}

/* 滚动条 */
.tocArea::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}

.tocArea::-webkit-scrollbar-thumb:vertical {
  height: 5px;
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 0.5rem;
}

.tocArea .tocAreaButton {
  user-select: none;
  appearance: none;
  background: none;
  border: none;
  display: block;
  font-family: sans-serif;
  width: 100%;
  font-size: 0.9em;
  text-align: left;
  padding: 0.9em 1em;
  border-bottom: 1px solid #ddd;
  color: #777;
  box-sizing: border-box;
  outline: none;
  cursor: pointer;
  position: relative;
}

.tocArea .tocAreaButton:hover {
  background: rgba(0, 0, 0, 0.05);
}

.tocArea .tocAreaButton:active {
  background: rgba(0, 0, 0, 0.1);
}

.tocArea .active {
  color: #1565c0;
  border-bottom: 2px solid #1565c0;
}

/* 二级目录 */
.tocArea .tocAreaButton .expansion {
  cursor: pointer;
  transform: translateY(-50%);
  top: 50%;
  right: 12px;
  position: absolute;
  width: 10px;
  background-color: #a2a5b4;
  transition:
    transform 0.3s ease-in-out,
    top 0.3s ease-in-out;
}

.tocArea .tocAreaButton .expansion::after,
.tocArea .tocAreaButton .expansion::before {
  content: '';
  position: absolute;
  width: 6px;
  height: 2px;
  background-color: currentcolor;
  border-radius: 2px;
  transition:
    transform 0.3s ease-in-out,
    top 0.3s ease-in-out;
}
/* ↓ */
.tocArea .tocAreaButton .expansion::before {
  transform: rotate(-45deg) translateX(2.5px);
}

.tocArea .tocAreaButton .expansion::after {
  transform: rotate(45deg) translateX(-2.5px);
}
/* ↑ */
.tocArea .tocAreaButton .open::before {
  transform: rotate(45deg) translateX(2.5px);
}

.tocArea .tocAreaButton .open::after {
  transform: rotate(-45deg) translateX(-2.5px);
}
/* tocButton */
.tocButton {
  background: none;
  border: none;
  width: 32px;
  height: 32px;
  position: absolute;
  top: 10px;
  left: 10px;
  border-radius: 2px;
  outline: none;
  cursor: pointer;
  z-index: 99;
  opacity: 0.2;
}
.tocButton:hover {
  opacity: 0.6;
}

.tocButtonBar {
  position: absolute;
  width: 60%;
  height: 2px;
  left: 50%;
  margin: -1px -30%;
  top: 50%;
  transition: all 0.5s ease;
}

.tocButtonExpanded {
  background: rgba(157, 157, 157, 0.42);
  opacity: 0.6;
  cursor: pointer;
}

.arrow {
  outline: none;
  border: none;
  background: none;
  position: absolute;
  top: 0;
  margin-top: -32px;
  font-size: 64px;
  padding: 0 5px;
  color: #e2e2e2;
  font-family: arial, sans-serif;
  cursor: pointer;
  user-select: none;
  appearance: none;
  font-weight: normal;
  height: 100%;
  align-items: center;
  display: flex;
  opacity: 0.2;
}

.arrow:hover {
  opacity: 0.6;
}

.arrow:disabled {
  cursor: not-allowed;
  color: #e2e2e2;
}

.prev {
  left: 1px;
}

.next {
  right: 1px;
}

/* loading */
.loadingView {
  position: absolute;
  top: 50%;
  left: 10%;
  right: 10%;
  color: #ccc;
  text-align: center;
  margin-top: -0.5em;
}

/* selection color picker */
.choose-annotation-category {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  z-index: 1000;
  background: rgba(40, 40, 40, 0.95);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  padding: 4px;
  display: flex;
  gap: 4px;
  font-weight: bold;
  box-sizing: border-box;
}
.picker-btn {
  border: none;
  border-radius: 4px;
  padding: 4px 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: bold;
  flex-grow: 1;
}
</style>
