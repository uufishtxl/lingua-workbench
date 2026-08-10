<template>
  <div>
    <div ref="waveformContainer" class="wavesurfer-host"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import WaveSurfer from 'wavesurfer.js'
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.esm.js'
import type { Region } from 'wavesurfer.js/dist/plugins/regions.js'

const props = withDefaults(defineProps<{
  url: string
  height?: number
  start?: number
  end?: number
  allowSelection?: boolean
}>(), {
  height: 90,
  allowSelection: true,
})

const emit = defineEmits<{
  (e: 'region-created', region: Region): void
  (e: 'region-updated', region: Region): void
  (e: 'region-removed', region: Region): void
  (e: 'region-in', region: Region): void
  (e: 'region-out', region: Region): void
  (e: 'region-clicked', region: Region, event: MouseEvent): void
  (e: 'play'): void
  (e: 'pause'): void
  (e: 'ready', wavesurfer: WaveSurfer): void
}>()

const waveformContainer = ref<HTMLElement | null>(null)
const wavesurfer = ref<WaveSurfer | null>(null)
const wsRegions = ref<RegionsPlugin | null>(null) // 创建的区域
const selectedRegion = ref<Region | null>(null); // 当前选中的区域
const managedRegion = ref<Region | null>(null); // 哨兵区域

const REGION_ID = 'start-end-segment' // 哨兵区域 ID（固定 ID，以示区分）

const syncStartEndRegion = (start?: number, end?: number) => {
  if (!wavesurfer.value || !wsRegions.value) return

  const existingRegions = Object.values(wsRegions.value.getRegions())
  console.log('[syncStartEndRegion] 调用', { start, end, existingRegionsCount: existingRegions.length })
  console.log('[syncStartEndRegion] 现有区域 IDs:', existingRegions.map(r => r.id))
  
  // 🔧 修复：删除所有同 ID 的哨兵区域（防止高频更新时重复创建）
  const regionsToRemove = existingRegions.filter(r => r.id === REGION_ID)
  if (regionsToRemove.length > 0) {
    regionsToRemove.forEach(r => r.remove())
    managedRegion.value = null
  }

  if (start !== undefined && end !== undefined && end > start) {
    // 哨兵区域：表示用户选择的区域（在 SliceCard 中会用到，只会传入 start 和 end，不允许拖动和调整大小）
    // 非哨兵区域 ID 由 WaveSurfer.js 自动创建
    // console.log('[syncStartEndRegion] 正在创建新哨兵区域...', { start, end })
    managedRegion.value = wsRegions.value.addRegion({
      id: REGION_ID,
      start,
      end,
      color: 'rgba(255, 165, 0, 0.2)',
      drag: false,
      resize: false,
      // loop: false // We handle looping manually for better control
    })
    // console.log('[syncStartEndRegion] 新区域创建完成, ID:', managedRegion.value?.id)

    if (waveformContainer.value) {
        const segmentDuration = end - start;
        if (segmentDuration > 0) {
            const containerWidth = waveformContainer.value.clientWidth;
            const paddedSegmentDuration = segmentDuration * 1.4; 
            const pxPerSec = containerWidth / paddedSegmentDuration;
            // console.log('[syncStartEndRegion] zooming to:', pxPerSec);
            wavesurfer.value.zoom(pxPerSec);
        }
    }
    
    // 🎯 确保波形渲染完成后再跳转到中心位置
    setTimeout(() => {
      const duration = wavesurfer.value?.getDuration()
      if (duration && duration > 0) {
        // 进度指向 start，如果要指向中间位置：((start + end) / 2) / duration
        const centerProgress = start / duration;
        wavesurfer.value?.seekTo(centerProgress);
      }
    }, 10);
  }
}

onMounted(() => {
  // 确保容器在 DOM 挂载完成后，创建 WaveSurfer 实例（需要传入 DOM 容器元素和配置参数），之后 WaveSurfer 即可在容器内绑定 canvas 并渲染波形。
  if (waveformContainer.value) {
    wavesurfer.value = WaveSurfer.create({
      container: waveformContainer.value,
      waveColor: '#409EFF',
      progressColor: 'rgb(198, 226, 255)',
      cursorColor: 'rgb(160, 207, 255)',
      // 不在此处传入 url，防止自动播放
      barWidth: 2,
      barRadius: 3,
      barGap: 1,
      height: props.height,
      autoplay: false,
    })

    wavesurfer.value.on('play', () => {
      console.log('[BaseWaveSurfer] Play event fired')
      emit('play')
    }) // 通过 on 监听 wavesurfer 的特定事件
    wavesurfer.value.on('pause', () => {
      console.log('[BaseWaveSurfer] Pause event fired')
      emit('pause')
    })

    // Manual looping logic
    wavesurfer.value.on('audioprocess', (currentTime) => {
      if (managedRegion.value && wavesurfer.value?.isPlaying()) {
        if (currentTime >= managedRegion.value.end) {
          wavesurfer.value.seekTo(managedRegion.value.start / wavesurfer.value.getDuration());
        }
      }
    });

    wavesurfer.value.on('ready', () => {
      if (!wavesurfer.value) return

      console.log('[BaseWaveSurfer] Ready event fired, isPlaying:', wavesurfer.value.isPlaying())
      // 立即暂停，防止自动播放
      if (wavesurfer.value.isPlaying()) {
        console.log('[BaseWaveSurfer] Pausing in ready event')
        wavesurfer.value.pause()
      }

      wsRegions.value = wavesurfer.value.registerPlugin(RegionsPlugin.create())
      if (props.allowSelection) {
        wsRegions.value.enableDragSelection({ color: 'rgba(64, 158, 255, 0.1)' })
      }

      wsRegions.value.on('region-created', (region) => {
        if (region.id !== REGION_ID) {
          emit('region-created', region)
        }
      })
      wsRegions.value.on('region-updated', (region) => emit('region-updated', region))
      wsRegions.value.on('region-removed', (region) => emit('region-removed', region))
      wsRegions.value.on('region-in', (region) => emit('region-in', region))
      wsRegions.value.on('region-out', (region) => emit('region-out', region))
      
      wsRegions.value.on('region-clicked', (region, e) => {
        selectedRegion.value = region;
        emit('region-clicked', region, e)
      })

      syncStartEndRegion(props.start, props.end)
      
      emit('ready', wavesurfer.value! as WaveSurfer)
    })

    wavesurfer.value.on('error', (err) => console.error('Wavesurfer error:', err))
    
    // 禁用自动播放
    const media = wavesurfer.value.getMediaElement()
    if (media && 'autoplay' in media) {
      (media as any).autoplay = false
      console.log('[BaseWaveSurfer] Set media.autoplay = false')
    }
    
    // 延迟加载音频，防止自动播放
    if (props.url) {
      console.log('[BaseWaveSurfer] Loading URL:', props.url)
      wavesurfer.value.load(props.url)
      // 立即暂停，防止自动播放
      setTimeout(() => {
        if (wavesurfer.value?.isPlaying()) {
          console.log('[BaseWaveSurfer] Auto-playing detected, pausing...')
          wavesurfer.value.pause()
        }
      }, 100)
    }
  }
})

watch(() => props.height, (newHeight) => {
  if (wavesurfer.value) {
    wavesurfer.value.setOptions({ height: newHeight })
  }
})

watch(() => props.url, (newUrl) => {
  if (wavesurfer.value) {
    selectedRegion.value = null;
    wavesurfer.value.load(newUrl);
  }
})

watch([() => props.start, () => props.end], ([newStart, newEnd]) => {
  syncStartEndRegion(newStart, newEnd)
})

onUnmounted(() => {
  wavesurfer.value?.destroy()
})

// Smarter play function for region handling
const play = () => {
  const ws = wavesurfer.value;
  const region = managedRegion.value;

  if (region && ws) {
    const currentTime = ws.getCurrentTime();
    // Seek to start only if cursor is outside the region
    if (currentTime < region.start || currentTime >= region.end) {
      ws.seekTo(region.start / ws.getDuration());
    }
    ws.play();
  } else {
    // Fallback for no region
    ws?.play();
  }
};

defineExpose({
  playPause: () => {
    if (wavesurfer.value?.isPlaying()) {
      wavesurfer.value.pause();
    } else {
      play();
    }
  },
  play: play,
  pause: () => wavesurfer.value?.pause(),
  getRegions: () => wsRegions.value?.getRegions(),
  addRegion: (options: any) => wsRegions.value?.addRegion(options),
  setPlaybackRate: (rate: number) => wavesurfer.value?.setPlaybackRate(rate),
})
</script>

<style scoped>
/* 
  WaveSurfer uses Shadow DOM, and the scrollable element has part="scroll".
  We need to use the ::part() pseudo-element to style it from outside.
  The :deep() selector is still needed to pierce the parent's scope to reach the wavesurfer-host's shadow root.
*/
.wavesurfer-host :deep(::part(scroll)) {
  scrollbar-width: none; /* For Firefox */
}

.wavesurfer-host :deep(::part(scroll)::-webkit-scrollbar) {
  display: none; /* For Webkit browsers */
}
</style>
