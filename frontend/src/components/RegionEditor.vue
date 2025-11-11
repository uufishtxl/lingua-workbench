<template>
  <el-card shadow="hover" class="region-editor-card">
    <el-form :model="region" label-position="top">
      <el-row :gutter="24" align="top">

        <!-- Time Column -->
        <el-col :span="3">
          <el-form-item label="Time">
            <div class="time-display">
              <span class="text-blue-400">{{ formatTime(region.start) }}~{{ formatTime(region.end) }}</span>
            </div>
          </el-form-item>
        </el-col>

        <!-- Original Text Column -->
        <el-col :span="7">
          <el-form-item label="Original Text (Optional)">
            <el-input
              :value="region.originalText"
              @input="emit('update:field', { id: region.id, key: 'originalText', value: $event })"
              type="textarea"
              placeholder="Type the phrase here..."
              :rows="2"
            ></el-input>
          </el-form-item>
        </el-col>

        <!-- Note Column -->
        <el-col :span="7">
          <el-form-item label="Note">
            <el-input
              :value="region.note"
              @input="emit('update:field', { id: region.id, key: 'note', value: $event })"
              type="textarea"
              placeholder="Jot down a note..."
              :rows="2"
            ></el-input>
          </el-form-item>
        </el-col>

        <!-- Tags Column -->
        <el-col :span="3">
          <el-form-item label="Tags">
            <div class="tag-icons flex">
              <el-button :type="region.tags.includes('listen') ? 'primary' : ''" @click="toggleTag('listen')" circle>
                <i-tabler-headphones class="text-sm" />
              </el-button>
              <el-button :type="region.tags.includes('speak') ? 'primary' : ''" @click="toggleTag('speak')" circle>
                <i-tabler-volume class="text-sm" />
              </el-button>
            </div>
          </el-form-item>
        </el-col>

        <!-- Actions Column -->
        <el-col :span="2">
          <el-form-item label="Actions">
            <el-button type="danger" @click="emit('delete', region.id)" :icon="Delete" circle>
            </el-button>
          </el-form-item>
        </el-col>

      </el-row>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { Delete } from "@element-plus/icons-vue"


// 接收父组件 v-for 循环传来的单个 region 对象
const props = defineProps<{
  region: {
    id: string;
    start: string;
    end: string;
    originalText: string;
    tags: string[];
    note: string;
  }
}>()

// 定义 'delete' 事件，当点击删除时通知父组件
const emit = defineEmits(['delete', 'update:tags', 'update:field'])

const formatTime = (seconds: string | number): string => {
  const totalSeconds = typeof seconds === 'string' ? parseFloat(seconds) : seconds;
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const remainingSeconds = Math.floor(totalSeconds % 60);

  const pad = (num: number) => num.toString().padStart(2, '0');

  return `${pad(hours)}:${pad(minutes)}:${pad(remainingSeconds)}`;
};

const toggleTag = (tag: 'listen' | 'speak') => {
  const newTags = [...props.region.tags];
  const tagIndex = newTags.indexOf(tag);

  if (tagIndex > -1) {
    newTags.splice(tagIndex, 1);
  } else {
    newTags.push(tag);
  }
  
  emit('update:tags', { id: props.region.id, tags: newTags });
}
</script>

<style scoped>
.region-editor-card {
  margin-bottom: 16px;
}

.time-display {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 5px; /* 微调对齐 */
}
.time-display span {
  font-size: 0.9em;
  background-color: #f4f4f5;
  color: #409EFF;
  padding: 2px 8px;
  border-radius: 4px;
}

/* 让 el-form-item 里的内容撑满 el-col */
.el-form-item {
  width: 100%;
}
.el-col {
  display: flex;
}
</style>