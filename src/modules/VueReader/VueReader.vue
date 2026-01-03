<template>
  <div class="container">
    <div
      class="readerArea"
      :class="{ containerExpanded: expandedToc }"
      :style="{ background }"
    >
      <div class="progress">
        <input
          type="range"
          :value="current"
          :min="0"
          :max="100"
          :step="1"
          @change="change"
          :style="{ color: currentFg }"
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
          :style="{ top: '35%', background: currentFg }"
        ></span>
        <span
          class="tocButtonBar"
          :style="{ top: '66%', background: currentFg }"
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

      <div class="arrow pre" @click="pre" :style="{ color: currentFg }">‹</div>
      <div class="arrow next" @click="next" :style="{ color: currentFg }">
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

        <div v-if="selectedTab === 'view'">
          <div class="buttonBar">
            <span>Font size</span>
            <button
              @click="increaseFontSize"
              style="border-top-right-radius: 0; border-bottom-right-radius: 0"
            >
              +
            </button>
            <button
              @click="reduceFontSize"
              style="border-top-left-radius: 0; border-bottom-left-radius: 0"
            >
              -
            </button>
          </div>
          <div class="buttonBar">
            <span>Spacing</span>
            <button
              @click="increaseSpacing"
              style="border-top-right-radius: 0; border-bottom-right-radius: 0"
            >
              +
            </button>
            <button
              @click="reduceSpacing"
              style="border-top-left-radius: 0; border-bottom-left-radius: 0"
            >
              -
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
import BookView from '../BookView/BookView.vue'
import {
  ref,
  reactive,
  toRefs,
  defineComponent,
  getCurrentInstance,
  Transition,
  h as _h,
} from 'vue'
import IconBookRead from '../../../public/icons/eye-svgrepo-com.svg'
import IconBook from '../../../public/icons/book-svgrepo-com.svg'

const current = ref(0)

function onUpdateLocation({ fraction }) {
  current.value = Math.floor(fraction * 100)
}

const change = (e) => {
  const value = e.target.value
  current.value = value
  rendition.goToFraction(parseFloat(value / 100))
}
let currentFontSize = 140
let currentSpacing = 1.4
let currentFg = '#000'
let selectedTab = ref('navigation')
let background = ref('#fff')

function selectNavigation() {
  selectedTab.value = 'navigation'
}

function selectView() {
  selectedTab.value = 'view'
}

function increaseFontSize() {
  if (!rendition) {
    return
  }
  currentFontSize += 20
  updateStyle()
}
function reduceFontSize() {
  currentFontSize -= 20
  updateStyle()
}

function increaseSpacing() {
  if (!rendition) {
    return
  }
  currentSpacing += 0.2
  updateStyle()
}
function reduceSpacing() {
  currentSpacing -= 0.2
  updateStyle()
}

function changeTheme(bg, fg) {
  background.value = bg
  currentFg = fg
  updateStyle()
}

function updateStyle() {
  rendition.renderer.setStyles?.(
    getCSS({
      color: currentFg,
      spacing: currentSpacing,
      justify: true,
      hyphenate: true,
      fontSize: currentFontSize,
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

const getCSS = ({ color, spacing, justify, hyphenate, fontSize }) => `
    @namespace epub "http://www.idpf.org/2007/ops";
    html {
        color-scheme: light;
        font-size: ${fontSize}%;
        color: ${color} !important;
    }
    /* https://github.com/whatwg/html/issues/5426 */
    @media (prefers-color-scheme: dark) {
        a:link {
            color: lightblue;
        }
    }
    p, li, blockquote, dd {
        line-height: ${spacing};
        color: ${color} !important;
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
  val.renderer.setStyles?.(
    getCSS({
      spacing: 1.4,
      justify: true,
      hyphenate: true,
      fontSize: 140,
    }),
  )
}

const onTocChange = (_toc) => {
  toc.value = _toc
}

const toggleToc = () => {
  expandedToc.value = !expandedToc.value
}

const next = () => {
  props.onBtnNext()
  bookRef.value?.nextPage()
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
</style>
