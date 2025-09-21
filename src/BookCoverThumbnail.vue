<template>
  <div
      style="padding: 5px; font-weight: bold;margin: 1rem; white-space: nowrap; text-overflow: ellipsis; overflow: hidden; width: 15em; height: 23em;">
    <div
        :style="{
              backgroundImage: image,
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