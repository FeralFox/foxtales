<template>
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
          v-model="searchValue"
          v-on:keyup.enter="emitFilter"
          class="search-field"
          type="text"
          placeholder="Filter..."
        />
        <div @click="emitFilter" class="search-field-btn">
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
        <IconFavorite class="icon" />
        <span>Only Favorites</span>
      </div>
      <div
        class="toggle-switch"
        :class="{ 'is-active': showOnlyFavorites }"
        @click="toggleFavoriteFilter"
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
        <button v-if="tagSearch" @click="clearTagFilter" class="clear-tag-btn">
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
            filteredAuthors.length > 0 ? selectAuthor(filteredAuthors[0]) : null
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
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { URL } from '@/constants'
import { fetchAsync } from '@/lib'
import IconSearch from '../../public/icons/magnifier-svgrepo-com.svg'
import IconFilter from '../../public/icons/filter-svgrepo-com.svg'
import IconFilterFilled from '../../public/icons/filter-filled-svgrepo-com.svg'
import IconEye from '../../public/icons/eye-svgrepo-com.svg'
import IconTag from '../../public/icons/tag-svgrepo-com.svg'
import IconAuthor from '../../public/icons/author-svgrepo-com.svg'
import IconFavorite from '../../public/icons/favorite-filled-svgrepo-com.svg'
import IconList from '../../public/icons/list-svgrepo-com.svg'
import IconGrid from '../../public/icons/grid-svgrepo-com.svg'

const props = defineProps<{
  baseFilter: string
}>()

const emit = defineEmits<{
  (e: 'filter', filter: string): void
  (e: 'toggleView', isListView: boolean): void
}>()

const searchValue = ref('')
const showOnlyUnread = ref(false)
const showOnlyFavorites = ref(false)
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
    console.error('Failed to fetch existing authors:', e)
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
  return existingAuthors.value.filter((author) =>
    author.toLowerCase().includes(query),
  )
})

function selectTag(tag: string) {
  selectedTag.value = tag
  tagSearch.value = tag
  showTagSuggestions.value = false
  emitFilter()
}

function selectAuthor(author: string) {
  selectedAuthor.value = author
  authorSearch.value = author
  showAuthorSuggestions.value = false
  emitFilter()
}

function clearTagFilter() {
  selectedTag.value = ''
  tagSearch.value = ''
  showTagSuggestions.value = false
  emitFilter()
}

function clearAuthorFilter() {
  selectedAuthor.value = ''
  authorSearch.value = ''
  showAuthorSuggestions.value = false
  emitFilter()
}

function handleTagBlur() {
  setTimeout(() => (showTagSuggestions.value = false), 200)
}

function handleAuthorBlur() {
  setTimeout(() => (showAuthorSuggestions.value = false), 200)
}

function toggleUnreadFilter() {
  showOnlyUnread.value = !showOnlyUnread.value
  emitFilter()
}

function toggleFavoriteFilter() {
  showOnlyFavorites.value = !showOnlyFavorites.value
  emitFilter()
}

function toggleListView() {
  isListView.value = !isListView.value
  localStorage.setItem('isListView', isListView.value.toString())
  emit('toggleView', isListView.value)
}

function emitFilter() {
  let filter = props.baseFilter
  if (searchValue.value) {
    filter = `${searchValue.value} and ${props.baseFilter}`
  }
  if (selectedTag.value) {
    filter = `${filter} and tags:"=${selectedTag.value}"`
  }
  if (selectedAuthor.value) {
    filter = `${filter} and authors:"=${selectedAuthor.value}"`
  }
  if (showOnlyUnread.value) {
    filter = `${filter} and not #fxtl_status:"read"`
  }
  if (showOnlyFavorites.value) {
    filter = `${filter} and #fxtl_status:"favorite"`
  }
  emit('filter', filter)
}

// Initial emit to let parent know the initial filter
onMounted(() => {
  emitFilter()
})
</script>

<style scoped>
.search-field {
  padding: 0.5rem 2.5rem 0.5rem 1rem;
  border-radius: 8px;
  border: 1px solid var(--book-border);
  font-size: 1rem;
  flex-grow: 1;
  outline: none;
  background: white;
  color: #222;
  width: 100%;
}

.search-field-btn {
  position: absolute;
  right: 0.5rem;
  height: 100%;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem;
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
  border: 1px solid var(--book-border);
  border-radius: 8px;
  cursor: pointer;
  margin-left: 0.5rem;
  transition: all 0.2s;
  color: #555;
  background: white;
}

.filter-btn-colored {
  color: var(--primary);
}

.filter-btn-active {
  color: var(--primary);
  border-color: var(--primary);
  background: rgba(var(--primary-rgb), 0.1);
  text-align: center;
  width: 1.2rem;
}

.filter-row {
  display: grid;
  grid-template-columns: repeat(4, auto auto) 1fr;
  padding: 0.5rem 0;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
}

@media (max-width: 800px) {
  .filter-row {
    grid-template-columns: auto 1fr;
  }
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
  background: white;
  color: #222;
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
  color: #222;
}

.tag-suggestion-item:hover {
  background: rgba(var(--primary-rgb), 0.1);
}

.option-left {
  display: flex;
  min-width: fit-content;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: #222;
}

.option-left .icon {
  width: 1.25rem;
  height: 1.25rem;
  color: #555;
}

.toggle-switch {
  width: 2.5rem;
  height: 1.25rem;
  background-color: #9f9f9f;
  border-radius: 1rem;
  position: relative;
  transition: background-color 0.2s;
  justify-self: flex-end;
  cursor: pointer;
}

.toggle-switch.is-active {
  background-color: #4caf50;
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
</style>
