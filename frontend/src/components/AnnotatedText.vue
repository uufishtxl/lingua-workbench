<template>
  <div class="annotated-text-display">
    <div class="text-content">
      <span
        v-for="(word, index) in annotatedText"
        :key="index"
        :class="getTagClass(word.tags)"
        :title="word.tags ? `Tags: ${word.tags.join(', ')}` : ''"
      >
        {{ word.text }}
      </span>
    </div>
    <div v-if="hasTags" class="tag-legend mt-2 text-xs">
      <span v-for="tag in uniqueTags" :key="tag" class="flex items-center mr-3">
        <span :class="['w-3 h-3 mr-1 rounded-sm', tagColors[tag]]"></span>
        {{ tag }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Word {
  text: string;
  tags?: string[]; // Array to hold multiple tags
}

const props = defineProps<{
  annotatedText: Word[];
}>();

const tagColors: Record<string, string> = {
  'Link': 'bg-blue-200',
  'H-Del': 'bg-green-200',
  'Th-Del': 'bg-yellow-200',
  'Flap-T': 'bg-red-200',
};

const getTagClass = (tags?: string[]): string => {
  if (!tags || tags.length === 0) return '';
  // For now, just use the first tag's color for highlighting
  return tagColors[tags[0]] || '';
};

const uniqueTags = computed(() => {
  const tags = new Set<string>();
  props.annotatedText.forEach(word => {
    word.tags?.forEach(tag => tags.add(tag));
  });
  return Array.from(tags);
});

const hasTags = computed(() => uniqueTags.value.length > 0);
</script>

<style scoped>
.text-content span {
  padding: 0 2px;
  border-radius: 2px;
  margin-right: 0.1em; /* Small space between words */
  white-space: pre-wrap; /* Preserve spaces and allow wrapping */
}
.tag-legend {
  display: flex;
  flex-wrap: wrap;
}
</style>