<script setup lang="ts">
import { ref } from 'vue'
import IonColorFillSharp from '~icons/ion/color-fill-sharp'

const props = defineProps<{
  variant: 'dashboard' | 'blitz-header'
  hardCount: number
  reviewCount: number
}>()

const emits = defineEmits(['show-all', 'show-hard'])

const showHard = ref(false)

// 样式配置表：一眼看到所有差异，不用滚动
const theme = {
  'dashboard': {
    container: 'flex-row gap-8 mb-4',
    item: 'gap-3',
    icon: 'text-xl',
    count: 'text-xl text-slate-800 dark:text-gray-100',
    label: 'text-sm text-gray-500 block', // Dashboard 显示 Label
    cursor: "cursor-auto"
  },
  'blitz-header': {
    container: 'flex-row gap-2.5 items-center text-sm',
    item: 'gap-1.5',
    icon: 'text-base',
    count: 'text-[0.8rem]',
    label: 'text-[0.65rem] hidden sm:inline-block', // Header 自动响应式隐藏 Label
    cursor: "cursor-pointer"
  }
}[props.variant]
</script>

<template>
  <div :class="['flex font-sans items-center', theme.container]">
    <div :class="['flex items-center font-bold text-red-500', theme.item, theme.cursor]">
      <IonColorFillSharp :class="theme.icon" />
      <span :class="theme.count">{{ hardCount }}</span>
      <span :class="['uppercase tracking-wider opacity-80', theme.label]">Hard</span>
    </div>

    <span v-if="variant === 'blitz-header'" class="text-gray-300 dark:text-gray-600">/</span>

    <div :class="['flex items-center font-bold text-yellow-500', theme.item, theme.cursor]">
      <IonColorFillSharp :class="theme.icon" />
      <span :class="theme.count">{{ reviewCount }}</span>
      <span :class="['uppercase tracking-wider opacity-80', theme.label]">Review</span>
    </div>
  </div>
</template>