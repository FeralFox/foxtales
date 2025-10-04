<template>
  <div class="navigation">
    <Logo class="logo" style="opacity: 1"/>
    <div style="width: 80%;background-color:#fff6;height:2px"/>
    <a :class="props.active === 'local' ? 'is-active' : ''" href="#/"><BookStackIcon class="logo" />
      Local</a>
    <a :class="props.active === 'library' ? 'is-active' : ''" href="#/lib"><LibraryIcon class="logo"/>Library</a>
    <div style="flex-grow: 1" />
    <button v-if="isAuthenticated" class="logout-btn" @click="logout">Logout</button>
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
  width: 4rem;
  min-width: 4rem;
  text-align:center;
  font-size: 90%;
}
.navigation a {
  font-weight: bold;
  text-decoration: none;
  border-top-left-radius: 5px;
  border-bottom-left-radius: 5px;
  line-height: 1;
  padding-bottom: 5px;
  transition: var(--transition-default);
}
.navigation a.is-active {
  background-color: white;
  color:black;
}
.navigation a:hover {
  background-color: #fff3
}
.navigation a.is-active:hover {
  background-color: white
}
.logo {
  width: 2.5rem;
  height: 2.5rem;
  padding: 0.5rem;
  padding-bottom: 0;
  opacity: 1;
}
.logout-btn {
  margin-top: 0.5rem;
  background: transparent;
  color: white;
  border: 1px solid #fff6;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  transition: var(--transition-default)
}
.logout-btn:hover {
  background: #fff3;
}
</style>
<script setup lang="ts">
import { computed } from 'vue'
import Logo from "../public/icons/logo_dark.svg"
import BookStackIcon from "../public/icons/books-stack-svgrepo-com.svg"
import LibraryIcon from "../public/icons/books-arranged-vertically-svgrepo-com.svg"

const props = defineProps(["active"]) 

const isAuthenticated = computed(() => !!localStorage.getItem('auth_token'))

function logout() {
  localStorage.removeItem('auth_token')
  window.location.hash = '/'
}
</script>