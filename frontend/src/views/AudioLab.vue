<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch, reactive } from 'vue'
import WaveSurfer from 'wavesurfer.js'
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.esm.js'
import type { Region } from 'wavesurfer.js/dist/plugins/regions.js'
import RegionEditor from '@/components/RegionEditor.vue'
import { ElMessage } from 'element-plus';

// --- Refs for DOM elements and instances ---
const wavesurfer = ref<WaveSurfer | null>(null)
const waveformContainer = ref<HTMLElement | null>(null)
const wsRegions = ref<RegionsPlugin | null>(null)
const recordedAudioElement = ref<HTMLAudioElement | null>(null)

// --- Component State ---
type audio_type = 'listen' | 'speak'
interface RegionInfo {
  id: string;
  start: string;
  end: string;
  originalText: string;
  tags: audio_type[];
  note: string;
}
const regionsList = ref<RegionInfo[]>([])
const loopRegion = ref(true)
const isPlaying = ref(false)
const isPlayingRecordedAudio = ref(false)

const form = reactive({
  startTime: '00:05:12',
  endTime: '00:05:18',
  originalText: '',
  tags: []
})

// --- Recording State ---
const isRecording = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const recordedAudioUrl = ref<string | null>(null)
const audioChunks = ref<Blob[]>([])

// --- Main Logic for WaveSurfer ---
onMounted(() => {
  if (waveformContainer.value) {
    wavesurfer.value = WaveSurfer.create({
      container: waveformContainer.value,
      waveColor: '#409EFF',
      progressColor: 'rgb(198, 226, 255)',
      cursorColor: 'rgb(160, 207, 255)',
      url: '/media/originals/segmented_audio_005.mp3', // TODO: Replace with a real audio URL
      barWidth: 2,
      barRadius: 3,
      barGap: 1,
      height: 200,
    })

    wavesurfer.value.on('play', () => {
      isPlaying.value = true
    })

    wavesurfer.value.on('pause', () => {
      isPlaying.value = false
    })

    wavesurfer.value.on('ready', () => {
      wsRegions.value = wavesurfer.value.registerPlugin(RegionsPlugin.create())
      wsRegions.value.enableDragSelection({ color: 'rgba(64, 158, 255, 0.1)' })

      const updateRegionsList = () => {
        if (!wsRegions.value) return
        const regions = wsRegions.value.getRegions()

        // 关键改动：
        // 我们需要保留已有的 originalText 和 tags，
        // 同时为新创建的 region 添加默认值。
        const newRegionsMap = new Map<string, RegionInfo>();

        for (const region of Object.values(regions)) {
          // 检查是否已存在于 regionsList (通过 id)
          const existingRegion = regionsList.value.find(r => r.id === region.id);

          if (existingRegion) {
            // 如果已存在，更新 start/end，但保留 originalText 和 tags
            newRegionsMap.set(region.id, {
              ...existingRegion, // 保留 originalText 和 tags
              start: region.start.toFixed(2), // 更新
              end: region.end.toFixed(2),     // 更新
            });
          } else {
            // 如果是新创建的，添加默认空字段
            newRegionsMap.set(region.id, {
              id: region.id,
              start: region.start.toFixed(2),
              end: region.end.toFixed(2),
              originalText: '', // 新增
              tags: [],         // 新增
              note: '',         // 新增
            });
          }

          // 将 Map 转回数组，完成 regionsList 的更新
          regionsList.value = Array.from(newRegionsMap.values());
        }
      }

      wsRegions.value.on('region-created', updateRegionsList)
      wsRegions.value.on('region-updated', updateRegionsList)
      wsRegions.value.on('region-removed', updateRegionsList)

      let activeRegion: Region | null = null
      wsRegions.value.on('region-in', (region) => { activeRegion = region })
      wsRegions.value.on('region-out', (region) => {
        if (activeRegion === region) {
          if (loopRegion.value) region.play()
          else activeRegion = null
        }
      })
      wsRegions.value.on('region-clicked', (region, e) => {
        e.stopPropagation()
        activeRegion = region
        region.play()
      })
    })

    wavesurfer.value.on('error', (err) => console.error('Wavesurfer error:', err))
  }

  window.addEventListener('keydown', handleKeyPress)
})

watch(recordedAudioElement, (newVal) => {
  if (newVal) {
    newVal.onplay = () => {
      isPlayingRecordedAudio.value = true
    }
    newVal.onpause = () => {
      isPlayingRecordedAudio.value = false
    }
  }
})

const handleKeyPress = (event: KeyboardEvent) => {
  if (event.altKey && event.code === 'KeyZ') {
    event.preventDefault() // Prevent default browser action
    handlePlayPause()
  } else if (event.altKey && event.code === 'KeyX') { // New shortcut for recorded audio
    event.preventDefault()
    loopRegion.value = !loopRegion.value
  } else if (event.altKey && event.code === 'KeyC') { // New shortcut for recorded audio
    event.preventDefault()
    handleRecordToggle()
  } else if (event.altKey && event.code === 'KeyV') { // New shortcut for recorded audio
    event.preventDefault()
    handleRecordedAudioPlayPause()
  }
}

// --- Methods ---
const handlePlayPause = () => {
  wavesurfer.value?.playPause()
}

const handleRecordedAudioPlayPause = () => {
  if (recordedAudioElement.value) {
    if (recordedAudioElement.value.paused) {
      recordedAudioElement.value.play()
    } else {
      recordedAudioElement.value.pause()
    }
  }
}

const removeRegion = (id: string) => {
  wsRegions.value?.getRegions()[id]?.remove()
}

const handleUpdateTags = (payload: { id: string, tags: ('listen' | 'speak')[] }) => {
  const region = regionsList.value.find(r => r.id === payload.id);
  if (region) {
    region.tags = payload.tags;
  }
}

const handleUpdateRegion = (payload: { id: string, key: keyof RegionInfo, value: any }) => {
  const region = regionsList.value.find(r => r.id === payload.id);
  if (region) {
    (region[payload.key] as any) = payload.value;
  }
}

const handleRecordToggle = async () => {
  if (isRecording.value) {
    // Stop recording
    mediaRecorder.value?.stop()
    isRecording.value = false
  } else {
    // Start recording
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRecorder.value = new MediaRecorder(stream)

      mediaRecorder.value.ondataavailable = (event) => {
        audioChunks.value.push(event.data)
      }

      mediaRecorder.value.onstop = () => {
        const audioBlob = new Blob(audioChunks.value, { type: 'audio/wav' })
        // Revoke old URL to prevent memory leaks
        if (recordedAudioUrl.value) {
          URL.revokeObjectURL(recordedAudioUrl.value)
        }
        recordedAudioUrl.value = URL.createObjectURL(audioBlob)
        audioChunks.value = [] // Clear for next recording
        // Stop all microphone tracks to turn off the mic indicator
        stream.getTracks().forEach(track => track.stop());
      }

      mediaRecorder.value.start()
      isRecording.value = true
    } catch (err) {
      console.error('Error accessing microphone:', err)
      alert('Could not access the microphone. Please ensure you have given permission.')
    }
  }
}

const saveRegions = () => {
  console.log('Saving regions to server:', regionsList.value);
  ElMessage({
    message: 'Regions data would be saved to the server.',
    type: 'success',
  });
};

// Clean up on component unmount
onUnmounted(() => {
  wavesurfer.value?.destroy()
  if (recordedAudioUrl.value) {
    URL.revokeObjectURL(recordedAudioUrl.value)
  }
  window.removeEventListener('keydown', handleKeyPress)
})
</script>

<template>
  <div class="audio__wrapper flex-column justify-center gap-8">
    <div class="p-4 rounded-lg shadow-sm rounded-lg bg-white shadow-xl">
      <h2 class="text-zinc-700 mb-4">Source: Friends S10E12 002</h2>

      <div ref="waveformContainer" class="mb-4 shadow-sm shadow-blue-100/50"></div>

      <!-- Controls -->
      <div class="flex justify-around items-center gap-4">
        <div class="flex gap-6 items-center">
          <el-button type="primary" @click="handlePlayPause" circle>
            <i-tabler-player-pause-filled v-if="isPlaying" class="text-sm" />
            <i-tabler-player-play-filled v-else class="text-sm" />
          </el-button>
          <el-button :type="loopRegion ? 'success' : ''" @click="loopRegion = !loopRegion" circle>
            <i-tabler-repeat class="text-sm" />
          </el-button>
          <el-button :type="isRecording ? 'danger' : 'default'" @click="handleRecordToggle" circle>
            <i-tabler-microphone class="text-sm" />
          </el-button>
        </div>
      </div>

      <!-- Recording Result Display -->
      <div v-if="recordedAudioUrl" class="mt-6 p-4 bg-slate-100 rounded-lg">
        <h3 class="font-bold text-lg mb-2">Last Recording</h3>
        <div class="flex items-center gap-4">
          <el-button type="primary" @click="handleRecordedAudioPlayPause" circle>
            <i-tabler-player-pause-filled v-if="isPlayingRecordedAudio" class="text-sm" />
            <i-tabler-player-play-filled v-else class="text-sm" />
          </el-button>
          <audio :src="recordedAudioUrl" controls class="w-full" ref="recordedAudioElement"></audio>
        </div>
      </div>


    </div>


    <!-- Region Info Display -->
    <div class="mt-6 p-4 bg-slate-100 rounded-lg">
      <h3 class="font-bold text-lg mb-2">Selected Regions</h3>
      <div v-if="regionsList.length > 0">
      <RegionEditor
        v-for="region in regionsList"
        :key="region.id"
        :region="region"
        @delete="removeRegion"
        @update:tags="handleUpdateTags"
        @update:field="handleUpdateRegion"
      />
    </div>
    <div v-else>
      <p class="text-sm text-gray-600">Click and drag on the waveform to select regions.</p>
    </div>
      <div class="mt-4 text-right">
        <el-button type="success" @click="saveRegions">Save All Changes</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.el-form--inline .el-form-item {
  vertical-align: top;
  /* 让所有表单项顶部对齐 */
}

.time-inputs {
  display: flex;
  flex-direction: column;
}

.tag-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
  /* 按钮之间的间距 */
}

/* 让文本域和创建按钮占据更多空间或在特定点换行 */
.text-area-item {
  width: 300px;
  /* 示例宽度 */
}

.create-button-item {
  /* 确保创建按钮在最后 */
  margin-left: auto;
}
</style>
