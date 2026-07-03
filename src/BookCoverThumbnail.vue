<template>
  <div
    class="book_card"
    :class="{ 'is-list-view': isListView }"
    :title="book!.title"
  >
    <div
      class="book-cover"
      :class="{ 'is-list-view': isListView }"
      :style="{
        backgroundImage: image,
      }"
    >
      <div class="book-cover-toolbar" v-if="!isListView">
        <div v-if="book!.fxtl_status.includes('read')" title="Book read">
          <IconBookRead />
        </div>
        <div v-if="book!.fxtl_status.includes('favorite')" title="Favorite">
          <IconFavorite />
        </div>
        <div v-if="displayBookDownloadedIcon" title="Saved on device">
          <IconDownloadSmall />
        </div>
      </div>
    </div>
    <div class="book-info-container" :class="{ 'is-list-view': isListView }">
      <div class="full-title" :class="{ 'is-list-view': isListView }">
        <div class="episode-title">{{ truncated_title.title }}</div>
        <div v-if="truncated_title.episode" class="episode-label">
          {{ truncated_title.episode }}
        </div>
      </div>
      <div class="authors-label" :class="{ 'is-list-view': isListView }">
        {{ book!.authors.toString().replace('Unknown', '') }}
      </div>
      <div
        class="tags-label"
        :class="{ 'is-list-view': isListView }"
        v-if="isListView"
      >
        {{ book!.tags.toString() }}
      </div>
      <div class="list-view-icons" v-if="isListView">
        <div v-if="book!.fxtl_status.includes('read')" title="Book read">
          <IconBookRead />
        </div>
        <div v-if="book!.fxtl_status.includes('favorite')" title="Favorite">
          <IconFavorite />
        </div>
        <div v-if="displayBookDownloadedIcon" title="Saved on device">
          <IconDownloadSmall />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import IconDownloadSmall from '../public/icons/download-small-svgrepo-com.svg'
import IconBookRead from '../public/icons/eye-filled-svgrepo-com.svg'
import IconFavorite from '../public/icons/favorite-filled-svgrepo-com.svg'
import { computed } from 'vue'

const props = defineProps({
  book: { type: Object },
  displayBookDownloadedIcon: { type: Boolean || undefined },
  image: { type: String },
  isListView: { type: Boolean, default: false },
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
  font-weight: bold;
  margin: 1rem;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  width: 10em;
  height: 17em;
  font-size: 100%;
}

.book_card.is-list-view {
  width: calc(100% - 2rem);
  height: 4rem;
  display: flex;
  margin: 0.5rem 1rem;
  align-items: center;
  gap: 1rem;
}

.book-info-container {
  display: grid;
  grid-template-areas: 'title' 'authors';
  flex-grow: 1;
  overflow: hidden;
}
.book-info-container.is-list-view {
  grid-template-areas: 'title authors tags icons';
  grid-template-columns: 50% 20% 20% 10%;
}
@media (max-width: 1000px) {
  .book-info-container.is-list-view {
    grid-template-areas: 'title icons' 'authors icons' 'tags icons';
    grid-template-columns: 1fr auto;
  }
}

.list-view-icons {
  grid-area: icons;
  display: flex;
  gap: 0.5rem;
  margin-left: auto;
  margin-right: 1rem;
}

.list-view-icons svg {
  width: 1.2rem;
  height: 1.2rem;
  color: #555;
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
.authors-label {
  grid-area: authors;
  color: #0007;
  font-weight: normal;
  text-overflow: ellipsis;
  overflow: hidden;
  margin-left: 0.2em;
}
.tags-label {
  grid-area: tags;
  color: #0007;
  font-weight: normal;
  text-overflow: ellipsis;
  overflow: hidden;
  margin-left: 0.2em;
}
.book-cover {
  position: relative;
  background-size: cover;
  width: 100%;
  height: calc(100% - 3.1rem);
  border: 1px solid var(--book-border);
  border-radius: 5px;
  margin-bottom: 5px;
  box-sizing: border-box;
}
.book-cover.is-list-view {
  width: 2.5rem;
  height: 3.5rem;
  margin-bottom: 0;
  flex-shrink: 0;
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
  grid-area: title;
  display: flex;
  justify-content: flex-start;
  padding: 0 0.1rem;
  text-overflow: ellipsis;
  overflow: hidden;
}
</style>
