<template>
  <div class="details-overlay" @click.self="props.onClose">
    <div class="details-panel" v-if="book">
      <div class="details-header">
        <a class="close-btn" @click="props.onClose" aria-label="Close"> × </a>
        <div
          class="cover"
          :style="{ backgroundImage: `url(${book.cover_url})` }"
        ></div>
        <div class="meta">
          <h2 class="title">{{ book.title }}</h2>
          <div class="authors" v-if="book.authors?.length">
            {{ book.authors }}
          </div>
          <div class="pub" v-if="year">{{ year }}</div>
          <div class="buttons">
            <slot></slot>
          </div>
        </div>
      </div>
      <div class="description" v-if="book.description">
        {{ book.description }}
      </div>
      <div class="tags-container" v-if="'tags' in book">
        <div v-for="tag in currentTags" :key="tag" class="chip">
          {{ tag }}
          <span class="remove-tag" @click="removeTag(tag)">×</span>
        </div>
        <button class="chip add-tag-btn" @click="startAddTag">+ Add Tag</button>
      </div>
    </div>
  </div>

  <!-- Remove Tag Confirmation Modal -->
  <div
    v-if="isConfirmingRemoval"
    class="modal-overlay"
    @click.self="isConfirmingRemoval = false"
  >
    <div class="modal-content">
      <h3>Remove Tag</h3>
      <p>Are you sure you want to remove the tag "{{ tagToRemove }}"?</p>
      <div class="modal-footer">
        <button @click="isConfirmingRemoval = false" class="btn-secondary">
          Cancel
        </button>
        <button @click="confirmRemoveTag" class="btn-danger">Remove</button>
      </div>
    </div>
  </div>

  <!-- Add Tag Modal -->
  <div
    v-if="isAddingTag"
    class="modal-overlay"
    @click.self="isAddingTag = false"
  >
    <div class="modal-content">
      <h3>Add Tag</h3>
      <div class="modal-body">
        <div class="suggestions-container">
          <input
            v-model="newTag"
            @keyup.enter="handleEnterKey"
            placeholder="Enter tag name..."
            class="modal-input"
            ref="tagInput"
          />
          <div v-if="newTag.trim()" class="suggestions-list">
            <div
              v-for="suggestion in filteredSuggestions"
              :key="suggestion"
              class="suggestion-item"
              @click="selectSuggestion(suggestion)"
            >
              {{ suggestion }}
            </div>
            <div class="suggestion-item add-new" @click="submitTag">
              Add "{{ newTag.trim() }}"
            </div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button @click="isAddingTag = false" class="btn-secondary">
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick, onMounted } from 'vue'
import type { SearchedBook, BookMeta } from '../interfaces'
import { authHeaders, URL } from '../constants'

const props = defineProps<{
  book: (SearchedBook | BookMeta) | null | undefined
  onClose?: () => void
}>()

const emit = defineEmits(['update'])

const year = computed(() => {
  const d = props.book?.pubdate
  if (!d) return ''
  // Try to extract 4-digit year
  const m = String(d).match(/(\d{4})/)
  const year = m ? m[1] : String(d)
  if (year === '0101') {
    return ''
  }
  return year
})

const currentTags = ref<string[]>([])

watch(
  () => props.book,
  (newBook) => {
    if (newBook && 'tags' in newBook && Array.isArray(newBook.tags)) {
      currentTags.value = [...newBook.tags]
    } else {
      currentTags.value = []
    }
  },
  { immediate: true },
)

const isAddingTag = ref(false)
const newTag = ref('')
const existingTags = ref<string[]>([])
const tagInput = ref<HTMLInputElement | null>(null)

async function fetchExistingTags() {
  try {
    const response = await fetch(`${URL}/get_tags`, {
      headers: authHeaders(),
    })
    if (response.ok) {
      existingTags.value = await response.json()
    }
  } catch (e) {
    console.error('Failed to fetch existing tags:', e)
  }
}

onMounted(fetchExistingTags)

const isConfirmingRemoval = ref(false)
const tagToRemove = ref('')

const filteredSuggestions = computed(() => {
  const query = newTag.value.trim().toLowerCase()
  if (!query) return []
  return existingTags.value.filter((tag) => tag.toLowerCase().includes(query))
})

function startAddTag() {
  newTag.value = ''
  isAddingTag.value = true
  nextTick(() => {
    tagInput.value?.focus()
  })
}

function selectSuggestion(suggestion: string) {
  newTag.value = suggestion
  submitTag()
}

function handleEnterKey() {
  if (filteredSuggestions.value.length === 1) {
    newTag.value = filteredSuggestions.value[0]
  }
  submitTag()
}

async function submitTag() {
  const tagToAdd = newTag.value.trim()
  if (!tagToAdd || !props.book) return
  isAddingTag.value = false

  if (!currentTags.value.includes(tagToAdd)) {
    currentTags.value.push(tagToAdd)
    await updateTags(currentTags.value)
    if (!existingTags.value.includes(tagToAdd)) {
      existingTags.value.push(tagToAdd)
      existingTags.value.sort()
    }
  }
  newTag.value = ''
}

function removeTag(tag: string) {
  tagToRemove.value = tag
  isConfirmingRemoval.value = true
}

async function confirmRemoveTag() {
  if (!props.book || !tagToRemove.value) return
  isConfirmingRemoval.value = false
  currentTags.value = currentTags.value.filter((t) => t !== tagToRemove.value)
  await updateTags(currentTags.value)
  tagToRemove.value = ''
}

async function updateTags(newTags: string[]) {
  if (!props.book) return
  try {
    const response = await fetch(`${URL}/set_data`, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        ...authHeaders(),
      },
      body: JSON.stringify({
        book_uuid: props.book.uuid,
        tags: newTags.join(','),
      }),
    })
    if (response.ok) {
      emit('update', newTags)
    }
  } catch (e) {
    console.error('Failed to update tags:', e)
  }
}
</script>

<style scoped>
.details-header {
  display: flex;
  gap: 1rem;
}

.details-header .cover {
  width: 96px;
  height: 144px;
  background-size: cover;
  background-position: center;
  border: 1px solid var(--book-border);
  border-radius: 4px;
  flex-shrink: 0;
}

.details-header .meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.title {
  margin: 0;
  font-size: 1.25rem;
}

.authors,
.pub {
  color: #333;
  font-size: 0.95rem;
}

.buttons {
  margin-top: 0.5rem;
  display: flex;
  gap: 0.5rem;
}

.close-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.9rem;
  background: transparent;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: inherit;
}

.details-panel {
  width: 28rem;
  max-width: 100vw;
  height: 100%;
  background: #fffc;
  color: #111;
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.15);
  padding: 1rem;
  position: relative;
  overflow: auto;
  backdrop-filter: blur(10px);
  animation: slidein 0.1s linear forwards;
}

.description {
  margin-top: 1rem;
  white-space: pre-wrap;
}

.tags-container {
  margin-top: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.chip {
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: linear-gradient(180deg, #ffffff, #f6f7f9);
  color: #222;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  cursor: default;
  font-size: 0.75rem;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  box-shadow:
    0 1px 1px rgba(0, 0, 0, 0.04),
    0 6px 12px rgba(0, 0, 0, 0.06);
}

.remove-tag {
  cursor: pointer;
  font-weight: bold;
  opacity: 0.5;
  font-size: 1rem;
}

.remove-tag:hover {
  opacity: 1;
}

.add-tag-btn {
  border: 1px dashed rgba(0, 0, 0, 0.3);
  background: transparent;
  cursor: pointer;
  box-shadow: none;
}

.add-tag-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

.tag-input {
  border: 1px solid var(--book-border);
  border-radius: 999px;
  padding: 0.2rem 0.6rem;
  font-size: 0.75rem;
  outline: none;
  width: 80px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
}

.modal-content {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  width: 300px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 1rem;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.suggestions-container {
  position: relative;
}

.suggestions-list {
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
  z-index: 30;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.suggestion-item {
  padding: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
}

.suggestion-item:hover {
  background: #f0f0f0;
}

.suggestion-item.add-new {
  border-top: 1px solid #eee;
  font-style: italic;
  color: rgb(var(--primary-rgb, 60, 120, 216));
}

.modal-input {
  width: 100%;
  box-sizing: border-box;
  padding: 0.5rem;
  border: 1px solid var(--book-border);
  border-radius: 4px;
  font-size: 0.9rem;
}

.modal-footer {
  margin-top: 1.5rem;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.btn-primary {
  background: rgb(var(--primary-rgb, 60, 120, 216));
  color: white;
  border: none;
  padding: 0.4rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.btn-danger {
  background: #d32f2f;
  color: white;
  border: none;
  padding: 0.4rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.btn-danger:hover {
  background: #b71c1c;
}

.btn-secondary {
  background: #eee;
  color: #333;
  border: none;
  padding: 0.4rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.btn-primary:hover {
  filter: brightness(0.9);
}

.btn-secondary:hover {
  background: #e4e4e4;
}

/* Mobile full-screen behavior */
@media (max-width: 640px) {
  .details-overlay {
    justify-content: center;
  }
  .details-panel {
    width: 100%;
    height: 100%;
    border-radius: 0;
  }
}

/* Sidebar / overlay styles */
.details-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: flex-end;
  z-index: 10;
}

@keyframes slidein {
  from {
    transform: translate(100%);
  }
  to {
    transform: translate(0);
  }
}
</style>
