<template>
  <div class="book_card">
    <div
        class="book_cover"
        :style="{
              backgroundImage: image,
            }"
    ></div>
    <div class="full-title"><div class="episode-title">{{ truncated_title.title }}</div><div v-if="truncated_title.episode" class="episode-label">
      {{ truncated_title.episode }}</div></div>
  </div>
</template>
<script>
export default {
  name: 'BookCoverThumbnail',
  props: {
    book: {},
    image: ""
  },
  computed: {
    truncated_title() {
      const title = this.book && this.book.title ? String(this.book.title) : '';
      let episode_index = title.search(/\d+$/);
      if (episode_index !== -1) {
        return {
          title: title.slice(0, episode_index),
          episode: title.slice(episode_index, title.length)
        }
      }
      return {title: title, episode: ''}
    }
  }
}
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

.book_cover {
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
}

.full-title {
  display: flex;
}
</style>