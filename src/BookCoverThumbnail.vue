<template>
  <div class="book_card" :title="book.title">
    <div
        class="book_cover"
        :style="{
              backgroundImage: image,
            }"
    >
      <div class="book-is-read">
        <IconBookRead  v-if="book.fxtl_is_read"/>
        <IconDownloadSmall v-if="displayBookDownloadedIcon" />
      </div>
    </div>
    <div class="full-title">
      <div class="episode-title">{{ truncated_title.title }}</div>
      <div v-if="truncated_title.episode" class="episode-label">
      {{ truncated_title.episode }}</div></div>
  </div>
</template>

<script setup lang="ts">
import IconDownloadSmall from "../public/icons/download-small-svgrepo-com.svg";
import IconBookRead from "../public/icons/eye-filled-svgrepo-com.svg";
import {computed} from "vue";

  const props = defineProps({
    book: {},
    displayBookDownloadedIcon: Boolean | undefined,
    image: ""});


   const  truncated_title = computed(() => {
      const title = props.book && props.book.title ? String(props.book.title) : '';
      let episode_index = title.search(/\d+$/);
      if (episode_index !== -1) {
        return {
          title: title.slice(0, episode_index),
          episode: title.slice(episode_index, title.length)
        }
      }
      return {title: title, episode: ''}
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
.book_cover {
  position: relative;
  background-size: cover;
  width: 100%;
  height: calc(100% - 2rem);
  border: 1px solid #000;
  border-radius: 5px;
  margin-bottom: 5px
}
.episode-title {
  font-weight: bold;
  text-overflow: ellipsis;
  overflow: hidden;
  flex-grow: 1;
}

.episode-label {
  background-color: var(--color-tag);
  font-size: 0.9em;
  color: #fffd;
  font-weight: bold;
  padding: 0 6px;
  border-radius: 5px;
  display: flex;
  align-items: center;
  margin-left: 5px;
}

.book-is-read {
  position: absolute;
  bottom: 5px;
  right: 5px;
  background: #000a;
  border-radius: 5px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.book-is-read svg {
  width: 15px;
  height: 15px;
  color: white;
  margin: 3px 3px 3px 0;
}
.book-is-read svg:first-child {
  margin-left: 3px;
}

.full-title {
  display: flex;
}
</style>