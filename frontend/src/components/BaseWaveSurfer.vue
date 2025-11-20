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
  height: 150,
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
const wsRegions = ref<RegionsPlugin | null>(null)

const REGION_ID = 'start-end-segment'

/**
 * Creates or updates a non-interactive region based on start/end props.
 */
const syncStartEndRegion = (start?: number, end?: number) => {
  if (!wavesurfer.value || !wsRegions.value) return

  // Find and remove any existing region with our managed ID
  const existingRegions = Object.values(wsRegions.value.getRegions())
  const region = existingRegions.find(r => r.id === REGION_ID)
  if (region) {
    region.remove()
  }

  // Add a new region if start and end are valid
  if (start !== undefined && end !== undefined && end > start) {
    wsRegions.value.addRegion({
      id: REGION_ID,
      start,
      end,
      color: 'rgba(255, 165, 0, 0.2)', // A distinct orange color
      drag: false,
      resize: false,
    })

    // Also seek to the start of the region
    const duration = wavesurfer.value.getDuration()
    if (duration > 0) {
      wavesurfer.value.seekTo(start / duration)
    }
  }
}


onMounted(() => {
  if (waveformContainer.value) {
    wavesurfer.value = WaveSurfer.create({
      container: waveformContainer.value,
      waveColor: '#409EFF',
      progressColor: 'rgb(198, 226, 255)',
      cursorColor: 'rgb(160, 207, 255)',
      url: props.url,
      barWidth: 2,
      barRadius: 3,
      barGap: 1,
      height: props.height,
    })

    wavesurfer.value.on('play', () => emit('play'))
    wavesurfer.value.on('pause', () => emit('pause'))

    wavesurfer.value.on('ready', () => {
      if (!wavesurfer.value) return

      wsRegions.value = wavesurfer.value.registerPlugin(RegionsPlugin.create())
      // Conditionally enable drag selection based on allowSelection prop
      if (props.allowSelection) {
        wsRegions.value.enableDragSelection({ color: 'rgba(64, 158, 255, 0.1)' })
      }

      wsRegions.value.on('region-created', (region) => {
        // Prevent emitting our managed region
        if (region.id !== REGION_ID) {
          emit('region-created', region)
        }
      })
      wsRegions.value.on('region-updated', (region) => emit('region-updated', region))
      wsRegions.value.on('region-removed', (region) => emit('region-removed', region))
      wsRegions.value.on('region-in', (region) => emit('region-in', region))
      wsRegions.value.on('region-out', (region) => emit('region-out', region))
      wsRegions.value.on('region-clicked', (region, e) => emit('region-clicked', region, e))

      // Create the initial region if start/end are provided
      syncStartEndRegion(props.start, props.end)
      
      emit('ready', wavesurfer.value)
    })

    wavesurfer.value.on('error', (err) => console.error('Wavesurfer error:', err))
  }
})

// Watch for changes in height
watch(() => props.height, (newHeight) => {
  if (wavesurfer.value) {
    wavesurfer.value.setOptions({ height: newHeight })
  }
})

// Watch for URL changes and reload the waveform
watch(() => props.url, (newUrl) => {
  if (wavesurfer.value) {
    wavesurfer.value.load(newUrl);
  }
})

// Watch for changes in start/end and update the region
watch([() => props.start, () => props.end], ([newStart, newEnd]) => {
  syncStartEndRegion(newStart, newEnd)
})

onUnmounted(() => {
  wavesurfer.value?.destroy()
})

// Expose public methods
defineExpose({
  playPause: () => wavesurfer.value?.playPause(),
  play: () => wavesurfer.value?.play(),
  pause: () => wavesurfer.value?.pause(),
  getRegions: () => wsRegions.value?.getRegions(),
  addRegion: (options: any) => wsRegions.value?.addRegion(options),
})
</script>

<style scoped>
.wavesurfer-host {
  overflow: hidden;
}
</style>
