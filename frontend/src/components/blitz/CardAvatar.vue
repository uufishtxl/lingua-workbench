<script setup lang="ts">
defineProps<{
  avatarUrl: string
  speaker: string
}>()
</script>

<template>
  <div class="card-avatar w-24 h-24 rounded-full border-4 border-white/50 overflow-hidden shadow-sm bg-white absolute top-0">
    <!-- Use API_BASE relative path or absolute URL from backend -->
    <img :src="avatarUrl" :alt="speaker" class="w-full h-full object-cover" />
  </div>
</template>

<style scoped>
/* Optional: if we need specific styles */
</style>
