<script setup lang="ts">
/**
 * 结构化模块渲染（#27 增强）：
 * - 纯文本字符串 → 降级为 pre-wrap 文本（旧数据/未归整）
 * - 结构化对象 → 标题 h3 / 单词列表 / 正文 / Sound / 语法 tip / Project 子章节+步骤
 */
defineProps<{ module: any }>()
</script>

<template>
  <div class="module-view text-sm leading-6">
    <!-- 纯文本降级 -->
    <template v-if="typeof module === 'string'">
      <div class="whitespace-pre-wrap">{{ module }}</div>
    </template>

    <template v-else-if="module && typeof module === 'object'">
      <!-- 标题 -->
      <h3 v-if="module.title" class="text-base font-bold mb-2 text-gray-800">{{ module.title }}</h3>

      <!-- 单词列表（topic_words / words_to_use） -->
      <ul v-if="module.items && module.items.length" class="flex flex-wrap gap-2 mb-3">
        <li
          v-for="(w, i) in module.items"
          :key="i"
          class="bg-blue-50 border border-blue-200 rounded px-2 py-1 text-blue-800"
        >
          {{ w }}
        </li>
      </ul>

      <!-- 正文 -->
      <div v-if="module.content" class="whitespace-pre-wrap mb-3">{{ module.content }}</div>

      <!-- Sound（拼读） -->
      <div v-if="module.sound" class="mb-3">
        <div class="font-semibold text-indigo-700 mb-1">🔊 Sound</div>
        <div class="whitespace-pre-wrap bg-indigo-50 border border-indigo-100 rounded p-2">
          {{ module.sound }}
        </div>
      </div>

      <!-- 语法点 tip -->
      <el-alert v-if="module.grammar_tip" type="warning" :closable="false" class="mb-3">
        <template #title>
          <span class="font-semibold">💡 Find the rule（语法点）</span>
        </template>
        <div class="whitespace-pre-wrap">{{ module.grammar_tip }}</div>
      </el-alert>

      <!-- Project 子章节 + 步骤 -->
      <div v-if="module.sections && module.sections.length">
        <div v-for="(sec, i) in module.sections" :key="i" class="mb-3">
          <h4 v-if="sec.title" class="font-semibold text-gray-700 mb-2">{{ sec.title }}</h4>
          <div v-if="sec.steps && sec.steps.length">
            <div v-for="(step, j) in sec.steps" :key="j" class="flex items-start gap-2 mb-1.5">
              <el-tag size="small" type="primary" effect="plain" class="shrink-0 mt-0.5">
                {{ step.title }}
              </el-tag>
              <span class="whitespace-pre-wrap">{{ step.content }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
