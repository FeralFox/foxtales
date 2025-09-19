<template>
  <div
      style="padding: 5px; margin: 1rem; font-weight: bold; white-space: nowrap; text-overflow: ellipsis; overflow: hidden; width: 15em; height: 23em;">
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
    {{ book.title }}
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