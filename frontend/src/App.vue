<template>
  <router-view v-slot="{ Component }">
    <component :is="Component" />
  </router-view>
</template>

<script setup>
// Root shell. Each portal is a full-page route and brings its own chrome.
</script>
