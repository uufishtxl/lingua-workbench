<template>
  <div class="flex items-center justify-center min-h-screen bg-gray-100">
    <RouterView />
  </div>
</template>

<script setup lang="ts">
// 这个布局很简单，甚至不需要 script
import { RouterView } from 'vue-router'
</script>