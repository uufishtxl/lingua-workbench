<template>
  <div>
    <div ref="waveformContainer"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import WaveSurfer from 'wavesurfer.js'
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.esm.js'
import type { Region } from 'wavesurfer.js/dist/plugins/regions.js'

const props = defineProps<{
  url: string
}>()

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
      height: 200,
    })

    wavesurfer.value.on('play', () => emit('play'))
    wavesurfer.value.on('pause', () => emit('pause'))

    wavesurfer.value.on('ready', () => {
      if (!wavesurfer.value) return

      wsRegions.value = wavesurfer.value.registerPlugin(RegionsPlugin.create())
      wsRegions.value.enableDragSelection({ color: 'rgba(64, 158, 255, 0.1)' })

      wsRegions.value.on('region-created', (region) => emit('region-created', region))
      wsRegions.value.on('region-updated', (region) => emit('region-updated', region))
      wsRegions.value.on('region-removed', (region) => emit('region-removed', region))
      wsRegions.value.on('region-in', (region) => emit('region-in', region))
      wsRegions.value.on('region-out', (region) => emit('region-out', region))
      wsRegions.value.on('region-clicked', (region, e) => emit('region-clicked', region, e))
      
      emit('ready', wavesurfer.value)
    })

    wavesurfer.value.on('error', (err) => console.error('Wavesurfer error:', err))
  }
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
