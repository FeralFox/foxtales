<template>
  <div class="navigation">
    <img alt="" class="logo" src="/public/logo_dark.svg"/>
    <a href="#/">Local</a> |
    <a href="#/lib">Library</a> |
  </div>
</template>
<style>
.navigation {
  align-items: center;
  color: white;
  background: #000e;
  gap: 0.5rem;
  display: flex;
  letter-spacing: 0.7px;
}
.navigation a {
  font-weight: bold;
  text-decoration: none;
}
.logo {
  width: 3rem;
  padding: 0.5rem;
  padding-right: 0;
  height: 3rem;
}
</style>
<script>
export default {
  name: 'Navigation'
}
</script>