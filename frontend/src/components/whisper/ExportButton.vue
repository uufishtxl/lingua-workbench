<template>
  <el-dropdown @command="handleExport" trigger="click">
    <el-button class="export-btn">
      导出
      <el-icon class="el-icon--right"><ArrowDown /></el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="copy">
          <el-icon><CopyDocument /></el-icon>
          复制到剪贴板
        </el-dropdown-item>
        <el-dropdown-item command="txt" divided>
          <el-icon><Document /></el-icon>
          导出 TXT
        </el-dropdown-item>
        <el-dropdown-item command="srt">
          <el-icon><Document /></el-icon>
          导出 SRT 字幕
        </el-dropdown-item>
        <el-dropdown-item command="json">
          <el-icon><Document /></el-icon>
          导出 JSON
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { ArrowDown, CopyDocument, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Segment {
  text: string
  start: number
  end: number
}

const props = defineProps<{
  segments: Segment[]
  title?: string
}>()

const handleExport = (command: string) => {
  switch (command) {
    case 'copy':
      copyToClipboard()
      break
    case 'txt':
      exportTxt()
      break
    case 'srt':
      exportSrt()
      break
    case 'json':
      exportJson()
      break
  }
}

const copyToClipboard = () => {
  const text = props.segments.map(seg => seg.text).join('\n')
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const exportTxt = () => {
  const text = props.segments.map(seg => {
    const time = formatTime(seg.start)
    return `[${time}] ${seg.text}`
  }).join('\n')
  
  downloadFile(text, `${props.title || 'transcript'}.txt`, 'text/plain')
}

const exportSrt = () => {
  const srt = props.segments.map((seg, index) => {
    const startTime = formatSrtTime(seg.start)
    const endTime = formatSrtTime(seg.end)
    return `${index + 1}\n${startTime} --> ${endTime}\n${seg.text}\n`
  }).join('\n')
  
  downloadFile(srt, `${props.title || 'transcript'}.srt`, 'text/plain')
}

const exportJson = () => {
  const json = JSON.stringify(props.segments, null, 2)
  downloadFile(json, `${props.title || 'transcript'}.json`, 'application/json')
}

const downloadFile = (content: string, filename: string, mimeType: string) => {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  ElMessage.success(`已导出 ${filename}`)
}

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const formatSrtTime = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 1000)
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`
}
</script>

<style scoped>
.export-btn {
  background: #2563EB;
  border-color: #2563EB;
  color: #fff;
}

.export-btn:hover {
  background: #1d4ed8;
  border-color: #1d4ed8;
  color: #fff;
}
</style>
