<template>
  <div class="navigation">
    <img alt="" class="logo" style="opacity: 1;padding-bottom:0.5rem" src="/public/logo_dark.svg"/>
    <div style="width: 80%;background-color:#fff6;height:2px"/>
    <a href="#/"><img alt="" class="logo"  src="/public/icons/books-stack-svgrepo-com.svg"/>Local</a>
    <a href="#/lib"><img alt="" class="logo"  src="/public/icons/books-arranged-vertically-svgrepo-com.svg"/>Library</a>
  </div>
</template>
<style>
.navigation {
  align-items: center;
  color: white;
  background: #000e;
  gap: 0.5rem;
  display: flex;
  flex-direction: column;
  letter-spacing: 0.7px;
  width: 5rem;
  text-align:center;
}
.navigation a {
  font-weight: bold;
  text-decoration: none;
}
.navigation a:hover {
  background-color: #fff3
}
.logo {
  width: 3rem;
  padding: 0.5rem;
  padding-bottom: 0;
  height: 3rem;
  opacity: 0.7;
}
</style>
<script>
export default {
  name: 'Navigation'
}
</script>