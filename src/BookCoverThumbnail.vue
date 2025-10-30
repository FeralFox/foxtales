<template>
  <div class="book_card" :title="book!.title">
    <div
      class="book-cover"
      :style="{
        backgroundImage: image,
      }"
    >
      <div class="book-cover-toolbar">
        <div>109</div>
        <div v-if="book!.fxtl_is_read" title="Book read"><IconBookRead /></div>
        <div v-if="displayBookDownloadedIcon" title="Saved on device">
          <IconDownloadSmall />
        </div>
      </div>
    </div>
    <div class="full-title">
      <div class="episode-title">{{ truncated_title.title }}</div>
      <div v-if="truncated_title.episode" class="episode-label">
        {{ truncated_title.episode }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import IconDownloadSmall from '../public/icons/download-small-svgrepo-com.svg'
import IconBookRead from '../public/icons/eye-filled-svgrepo-com.svg'
import { computed } from 'vue'

const props = defineProps({
  book: { type: Object },
  displayBookDownloadedIcon: { type: Boolean || undefined },
  image: { type: String },
})

const truncated_title = computed(() => {
  const title = props.book && props.book.title ? String(props.book.title) : ''
  let episode_index = title.search(/\d+$/)
  if (episode_index !== -1) {
    return {
      title: title.slice(0, episode_index),
      episode: title.slice(episode_index, title.length),
    }
  }
  return { title: title, episode: '' }
})
</script>
<style>
.book_card {
  padding: 5px;
  font-weight: bold;
  margin: 1rem;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  width: 10em;
  height: 17em;
  font-size: 100%;
}

@media (max-width: 640px) {
  .book_card {
    width: 7em;
    height: 12em;
    font-size: 90%;
  }
}
</style>
<style scoped>
.book-cover {
  position: relative;
  background-size: cover;
  width: 100%;
  height: calc(100% - 2rem);
  border: 1px solid #000;
  border-radius: 5px;
  margin-bottom: 5px;
}
.episode-title {
  font-weight: bold;
  text-overflow: ellipsis;
  overflow: hidden;
}

.episode-label {
  margin-left: 0.2em;
}

.book-cover-toolbar {
  position: absolute;
  bottom: 5px;
  right: 5px;
  background: #000a;
  border-radius: 5px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 0;
}

.book-cover-toolbar svg {
  width: 1.1rem;
  height: 1.1rem;
  color: white;
  margin: 4px 4px 4px 0;
}
.book-cover-toolbar svg:first-child {
  margin-left: 4px;
}

.full-title {
  display: flex;
  justify-content: flex-start;
  padding: 0 0.1rem;
}
</style>
