<template>
  <div class="book_card">
    <div
        :style="{
              backgroundImage: image,
              backgroundSize: 'cover',
              width: '100%',
              height: 'calc(100% - 2rem)',
              border: '1px solid #000',
              borderRadius: '5px',
              marginBottom: '5px'
            }"
    ></div>
    <span style="margin-left: 0.5rem;font-weight: bold;">{{ book.title }}</span>
  </div>
</template>
<script>
export default {
  name: 'BookCoverThumbnail',
  props: {
    book: {},
    image: ""
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
  width: 15em;
  height: 21em;
  font-size: 140%;
}
@media (max-width: 640px) {
  .book_card {
    width: 10em;
    height: 16em;
    font-size: 100%;
  }
}
</style>